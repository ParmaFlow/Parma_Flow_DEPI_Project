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
from backend.agents.shared.constants import ActionType

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
        final_status = self._determine_final_status(audit_result, risk_assessment)

        summary = self._create_executive_summary(merged, final_status)

        return self._build_final_decision(
            ops_decision, audit_result, risk_assessment, final_status, summary
        )

    def _merge_results(self, ops_decision, risk_assessment, audit_result) -> dict:
        return {
            "sku": ops_decision.sku,
            "action": ops_decision.action,
            "needs_reorder": ops_decision.needs_reorder,
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

    def _determine_final_status(
        self, audit_result: AuditResult, risk_assessment: RiskAssessment
    ) -> str:
        if not audit_result.approved or risk_assessment.human_review_recommended:
            return "BLOCKED"
        if audit_result.warning_count > 0:
            return "EXECUTED_WITH_WARNINGS"
        return "EXECUTED"

    def _build_final_decision(
        self, ops_decision, audit_result, risk_assessment, final_status, summary
    ) -> FinalDecision:
        sections = {key: summary.get(key, "") for key in REPORT_SECTION_KEYS}
        execution_allowed = audit_result.approved and not risk_assessment.human_review_recommended
        recommended_action = (
            ActionType.URGENT_DISPOSAL_AND_REPLACEMENT.value
            if "EXPIRY_DOMINANCE_OVERRIDE" in (audit_result.failed_rules or [])
            else ops_decision.action
        )
        return FinalDecision(
            sku=ops_decision.sku,
            execution_allowed=execution_allowed,
            final_status=final_status,
            recommended_action=recommended_action,
            executive_summary=summary.get("executive_summary", ""),
            reasoning=summary.get("reasoning", ""),
            generated_at=datetime.now(),
            report_sections=sections,
        )

    def _create_executive_summary(self, merged: dict, final_status: str) -> dict:
        execution_allowed = merged["approved"] and not merged["human_review_recommended"]
        return self._build_grounded_executive_summary(merged, final_status, execution_allowed)

    def _build_grounded_executive_summary(
        self, merged: dict, final_status: str, execution_allowed: bool
    ) -> dict:
        sku = merged["sku"]
        action = merged["action"]
        gap = merged["inventory_gap"]
        qty = merged["recommended_qty"]
        inventory_status = merged["inventory_status"]
        risk_score = merged["risk_score"]
        risk_level = merged["risk_level"]
        audit_status = merged["audit_status"]
        failed_rules = merged["failed_rules"] or []
        warning_count = merged["warning_count"]
        blocking_errors = merged["blocking_errors"]
        human_review = merged["human_review_recommended"]
        expiry_override = "EXPIRY_DOMINANCE_OVERRIDE" in failed_rules

        if expiry_override:
            action = ActionType.URGENT_DISPOSAL_AND_REPLACEMENT.value

        if expiry_override:
            operational_sentence = (
                "Quantity-based procurement is overridden by imminent expiry. "
                "The required action is urgent disposal/quarantine and replacement planning, "
                f"with the rounded replacement reference remaining {qty:,} units if replenishment "
                "is later cleared by governance."
            )
            next_procurement = (
                f"1. [Quality Officer] Quarantine expiring {sku} stock and initiate urgent "
                "disposal-and-replacement workflow within 2 hours."
            )
        elif action == "REORDER":
            operational_sentence = (
                f"A procurement requisition for {qty:,} units has been generated to bridge "
                f"the {gap:,}-unit supply gap."
            )
            next_procurement = (
                f"1. [Procurement Officer] Issue emergency procurement requisition for {qty:,} units "
                f"of {sku} within 4 hours."
            )
        else:
            operational_sentence = (
                "No procurement requisition has been generated because the deterministic "
                f"inventory gap is {gap:,} units."
            )
            next_procurement = (
                f"1. [Inventory Control] Continue monitoring {sku}; do not issue a purchase order "
                "unless a positive inventory gap is detected."
            )

        if final_status == "BLOCKED":
            if expiry_override:
                final_recommendation = (
                    "Autonomous reorder/monitor execution is blocked by expiry dominance. "
                    "Proceed only with urgent disposal, quarantine, and replacement governance."
                )
            else:
                final_recommendation = (
                    "Autonomous execution is blocked and the case must be escalated for human "
                    "adjudication before resubmission."
                )
        elif final_status == "EXECUTED_WITH_WARNINGS":
            final_recommendation = (
                "Conditional execution is allowed with warning deviations logged in the audit trail."
            )
        else:
            final_recommendation = "Execution is cleared; proceed with the operational directive."

        safe_ai_text = (
            "The Safe AI Guardrail is active and autonomous execution is disabled."
            if human_review
            else "The Safe AI Guardrail did not require manual downgrade."
        )
        failed_rules_text = ", ".join(failed_rules) if failed_rules else "No rule violations detected"

        return {
            "executive_summary": (
                f"{sku} is classified as {inventory_status} with a {gap:,}-unit inventory gap and "
                f"{risk_level} risk. Recommended action is {action}. Final status is {final_status}; execution_allowed is "
                f"{execution_allowed}."
            ),
            "reasoning": (
                f"The operational layer produced action={action}, inventory_gap={gap:,}, and "
                f"recommended_qty={qty:,}, creating the supply continuity basis for this case. "
                f"RiskAgent assigned risk_score={risk_score} and risk_level={risk_level}. "
                f"AuditorAgent returned audit_status={audit_status}, warning_count={warning_count}, "
                f"and blocking_errors={blocking_errors}. {safe_ai_text} The final recommendation "
                f"therefore matches final_status={final_status} and execution_allowed={execution_allowed}."
            ),
            "inventory_summary": (
                f"{sku} is in {inventory_status} inventory status with a deterministic "
                f"{gap:,}-unit supply gap. This is a shortage condition when the gap is positive "
                "and a monitor condition only when the gap is zero."
            ),
            "operational_decision": (
                f"The operational action is {action}. {operational_sentence}"
            ),
            "risk_assessment": (
                f"Risk posture is {risk_level} with a score of {risk_score}/100. "
                f"Human review recommended is {human_review}, so workflow execution is "
                f"{'downgraded to review' if human_review else 'not downgraded by risk'}."
            ),
            "audit_findings": (
                f"Audit disposition is {audit_status}. Failed rules: {failed_rules_text}. "
                f"Warnings={warning_count}; blocking_errors={blocking_errors}."
            ),
            "final_recommendation": final_recommendation,
            "next_actions": (
                f"{next_procurement} 2. [Clinical Governance] Record {risk_level} risk posture "
                f"and audit status {audit_status} in the decision log. 3. [Supply Chain Lead] "
                "Recheck stock position after supplier confirmation or next inventory refresh."
            ),
        }

    def _create_llm_executive_summary(self, merged: dict, final_status: str) -> dict:
        execution_allowed = merged["approved"] and not merged["human_review_recommended"]
        llm_input = {**merged, "final_status": final_status, "execution_allowed": execution_allowed}
        raw_response = self.llm.get_decision(REPORT_AGENT_PROMPT, llm_input)
        try:
            return json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMResponseParsingError(
                f"ReportAgent could not parse LLM response as JSON: {exc}"
            ) from exc
