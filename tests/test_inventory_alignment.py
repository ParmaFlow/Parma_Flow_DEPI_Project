import unittest
import sys
import types
import json


if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = lambda *args, **kwargs: object()
    for name in (
        "APIError",
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
    ):
        setattr(openai_stub, name, type(name, (Exception,), {}))
    sys.modules["openai"] = openai_stub

if "backend.rag.indexing" not in sys.modules:
    rag_indexing_stub = types.ModuleType("backend.rag.indexing")
    rag_indexing_stub.build_index = lambda *args, **kwargs: (None, None)
    sys.modules["backend.rag.indexing"] = rag_indexing_stub

if "backend.rag.retriever" not in sys.modules:
    rag_retriever_stub = types.ModuleType("backend.rag.retriever")
    rag_retriever_stub.retrieve = lambda *args, **kwargs: []
    sys.modules["backend.rag.retriever"] = rag_retriever_stub

from backend.agents.ops_agent.ops_agent import OpsAgent
from backend.agents.risk_agent.risk_agent import RiskAgent
from backend.agents.auditor_agent.auditor_agent import AuditorAgent
from backend.agents.report_agent.report_agent import ReportAgent
from backend.agents.shared.models import AuditResult, OperationalDecision, RiskAssessment
from backend.api.contracts import normalize_next_actions
from backend.rag.pipeline import RAGPipeline


class InventoryAlignmentTests(unittest.TestCase):
    def test_ops_agent_clopidogrel_stockout_forces_reorder(self):
        agent = OpsAgent("dummy-api-key")
        item = {
            "sku_name": "Clopidogrel",
            "location_type": "hospital",
            "available_stock": 205,
            "forecast_demand": 300,
            "lead_time": 10,
            "max_daily_demand": 336,
            "avg_daily_demand": 300,
            "max_lead_time": 10.970238095238095,
            "avg_lead_time": 10,
        }

        decision = agent.run(item)

        self.assertEqual(decision.reorder_point, 3686)
        self.assertEqual(decision.inventory_gap, 3481)
        self.assertTrue(decision.needs_reorder)
        self.assertEqual(decision.action, "REORDER")
        self.assertGreaterEqual(decision.recommended_qty, decision.inventory_gap)
        self.assertEqual(decision.inventory_status, "CRITICAL")
        self.assertNotIn("overstock", decision.reasoning.lower())
        self.assertIn("3,490 units", decision.reasoning)
        self.assertNotIn("3,481-unit", decision.reasoning)

    def test_report_agent_uses_one_gap_and_one_procurement_quantity(self):
        report_agent = ReportAgent("dummy-api-key")
        ops = OperationalDecision(
            sku="Clopidogrel",
            action="REORDER",
            needs_reorder=True,
            inventory_gap=3481,
            recommended_qty=3500,
            safety_stock=686,
            reorder_point=3686,
            inventory_status="CRITICAL",
            assignee="Pharmacy Manager",
            recommendation_details="",
            reasoning="",
        )
        risk = RiskAssessment(
            sku="Clopidogrel",
            risk_score=60,
            risk_level="HIGH",
            shortage_risk=True,
            expiry_risk=False,
            criticality="STANDARD",
            alert_level="HIGH",
            reasoning="",
            human_review_recommended=False,
        )
        audit = AuditResult(approved=True, audit_status="APPROVED")

        final = report_agent.run(ops, risk, audit)
        sections = json.dumps(final.report_sections)

        self.assertTrue(final.execution_allowed)
        self.assertEqual(final.final_status, "EXECUTED")
        self.assertIn("3,500 units", sections)
        self.assertNotIn("3,481-unit", sections)
        self.assertNotIn("for 0 units", sections)
        self.assertNotIn("0-unit requisition", sections)
        self.assertNotIn("16-unit", sections)
        self.assertEqual(
            [row["role"] for row in final.report_sections["next_actions"]],
            ["Procurement Officer", "Clinical Governance", "Supply Chain Lead"],
        )

    def test_zero_stock_uses_zero_cover_and_full_safety_reset(self):
        agent = OpsAgent("dummy-api-key")
        item = {
            "sku_name": "Emergency Insulin",
            "location_type": "hospital",
            "available_stock": 0,
            "forecast_demand": 100,
            "lead_time": 5,
            "max_daily_demand": 130,
            "avg_daily_demand": 100,
            "max_lead_time": 6,
            "avg_lead_time": 5,
        }

        decision = agent.run(item)

        self.assertEqual(decision.safety_stock, 280)
        self.assertEqual(decision.reorder_point, 780)
        self.assertEqual(decision.inventory_gap, 1060)
        self.assertEqual(decision.recommended_qty, 1060)
        self.assertEqual(decision.action, "REORDER")
        self.assertEqual(decision.inventory_status, "OUT_OF_STOCK")
        self.assertIn("0.00 demand cycles", decision.reasoning)

    def test_zero_demand_positive_stock_pauses_tracking_without_shortage_alarm(self):
        ops_agent = OpsAgent("dummy-api-key")
        risk_agent = RiskAgent("dummy-api-key")
        item = {
            "sku_name": "Paused Demand SKU",
            "location_type": "warehouse",
            "available_stock": 500,
            "forecast_demand": 0,
            "lead_time": 10,
            "expiry_days": 90,
        }

        ops = ops_agent.run(item)
        risk = risk_agent.run(ops, item)

        self.assertEqual(ops.action, "HOLD_MONITOR")
        self.assertEqual(ops.inventory_gap, 0)
        self.assertEqual(ops.recommended_qty, 0)
        self.assertFalse(risk.shortage_risk)
        self.assertIn("Zero demand input detected; inventory tracking paused.", risk.reasoning)

    def test_expiry_dominance_blocks_and_reports_disposal_replacement(self):
        ops = OperationalDecision(
            sku="Massive Stock Expiry SKU",
            action="MONITOR",
            needs_reorder=False,
            inventory_gap=0,
            recommended_qty=0,
            safety_stock=50,
            reorder_point=500,
            inventory_status="NORMAL",
            assignee="Warehouse Ops",
            recommendation_details="",
            reasoning="",
        )
        risk = RiskAssessment(
            sku="Massive Stock Expiry SKU",
            risk_score=10,
            risk_level="LOW",
            shortage_risk=False,
            expiry_risk=True,
            criticality="STANDARD",
            alert_level="LOW",
            reasoning="",
            human_review_recommended=False,
        )
        item = {
            "sku_name": "Massive Stock Expiry SKU",
            "location_type": "warehouse",
            "available_stock": 10000,
            "forecast_demand": 100,
            "lead_time": 20,
            "expiry_days": 10,
            "safety_stock": 50,
        }
        audit = AuditorAgent("dummy-api-key").run(ops, risk, item)
        final = ReportAgent("dummy-api-key").run(ops, risk, audit)

        self.assertFalse(audit.approved)
        self.assertEqual(audit.audit_status, "FAILED_AUDIT")
        self.assertEqual(audit.blocking_errors, 1)
        self.assertFalse(final.execution_allowed)
        self.assertEqual(final.final_status, "BLOCKED")
        self.assertEqual(final.recommended_action, "URGENT_DISPOSAL_AND_REPLACEMENT")
        self.assertIn("urgent disposal", json.dumps(final.report_sections["next_actions"]).lower())

    def test_rag_cleaning_drops_metadata_and_emails(self):
        chunks = [
            "Author information:\nDepartment of Pharmacy, Example University\nElectronic address: researcher@example.edu",
            "Drug shortage protocols require validated alternative sourcing when clinical continuity is threatened by stockout risk.",
        ]

        cleaned = RAGPipeline._clean_chunks(chunks)

        self.assertEqual(cleaned, [
            "Drug shortage protocols require validated alternative sourcing when clinical continuity is threatened by stockout risk."
        ])

    def test_api_normalizes_next_actions_contract_for_react(self):
        normalized = normalize_next_actions("Issue purchase order immediately.")

        self.assertEqual(
            [row["role"] for row in normalized],
            ["Procurement Officer", "Clinical Governance", "Supply Chain Lead"],
        )
        self.assertEqual(normalized[0]["action"], "Issue purchase order immediately.")
        self.assertTrue(all(row["action"] for row in normalized))


if __name__ == "__main__":
    unittest.main()



