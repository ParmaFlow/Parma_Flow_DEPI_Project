# backend/agents/report_agent/report_agent.py
import json
from datetime import datetime

from core.llm import LLMModel
from backend.agents.report_agent.prompt import REPORT_AGENT_PROMPT
from backend.agents.shared.base_agent import BaseAgent
from backend.agents.shared.models import (
    OperationalDecision,
    RiskAssessment,
    AuditResult,
    FinalDecision,
)
from backend.agents.shared.exceptions import LLMResponseParsingError

REPORT_SECTION_KEYS = (
    "inventory_summary",
    "operational_decision",
    "risk_assessment",
    "audit_findings",
    "final_recommendation",
    "next_actions",
)


class ReportAgent(BaseAgent):
    """
    Report Agent — merges upstream outputs into a professional executive
    report. Performs no calculation, validation, or risk evaluation.
    """

    def __init__(self, api_key: str) -> None:
        self.llm = LLMModel(api_key)

    def run(
        self,
        ops_decision: OperationalDecision,
        risk_assessment: RiskAssessment,
        audit_result: AuditResult,
    ) -> FinalDecision:
        merged = self._merge_results(ops_decision, risk_assessment, audit_result)
        final_status = self._determine_final_status(audit_result)

        summary = self._create_executive_summary(merged, final_status)

        return self._build_final_decision(ops_decision, audit_result, final_status, summary)

    def _merge_results(self, ops_decision, risk_assessment, audit_result) -> dict:
        return {
            "sku": ops_decision.sku,
            "action": ops_decision.action,
            "inventory_gap": ops_decision.inventory_gap,
            "recommended_qty": ops_decision.recommended_qty,
            "inventory_status": ops_decision.inventory_status,
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "human_review_recommended": risk_assessment.human_review_recommended,
            "approved": audit_result.approved,
            "audit_status": audit_result.audit_status,
            "failed_rules": audit_result.failed_rules,
            "warning_count": audit_result.warning_count,
            "blocking_errors": audit_result.blocking_errors,
        }

    def _determine_final_status(self, audit_result: AuditResult) -> str:
        if not audit_result.approved:
            return "BLOCKED"
        if audit_result.warning_count > 0:
            return "EXECUTED_WITH_WARNINGS"
        return "EXECUTED"

    def _build_final_decision(self, ops_decision, audit_result, final_status, summary) -> FinalDecision:
        sections = {key: summary.get(key, "") for key in REPORT_SECTION_KEYS}
        return FinalDecision(
            sku=ops_decision.sku,
            execution_allowed=audit_result.approved,
            final_status=final_status,
            recommended_action=ops_decision.action,
            executive_summary=summary.get("executive_summary", ""),
            reasoning=summary.get("reasoning", ""),
            generated_at=datetime.now(),
            report_sections=sections,
        )

    def _create_executive_summary(self, merged: dict, final_status: str) -> dict:
        llm_input = {**merged, "final_status": final_status, "execution_allowed": merged["approved"]}
        raw_response = self.llm.get_decision(REPORT_AGENT_PROMPT, llm_input)
        try:
            return json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMResponseParsingError(
                f"ReportAgent could not parse LLM response as JSON: {exc}"
            ) from exc