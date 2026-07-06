# backend/agents/auditor_agent/auditor_agent.py
import json

from core.llm import LLMModel
from backend.agents.auditor_agent.prompt import AUDITOR_AGENT_PROMPT
from backend.agents.shared.base_agent import BaseAgent
from backend.agents.shared.models import (
    OperationalDecision,
    RiskAssessment,
    AuditResult,
    AuditRuleResult,
)
from backend.agents.shared.constants import (
    VALID_ACTIONS,
    VALID_RISK_LEVELS,
    MIN_RISK_SCORE,
    MAX_RISK_SCORE,
    MAX_BLOCKING_ERRORS,
    MAX_ALLOWED_WARNINGS,
    EXPIRED_PRODUCT_DAYS,
    ABSURD_FORECAST_THRESHOLD,
    RuleSeverity,
)
from backend.agents.shared.exceptions import LLMResponseParsingError


class AuditorAgent(BaseAgent):
    """
    Auditor Agent — deterministic rule engine and Safe AI Guardrail.

    Every check below is a pure Python rule producing an AuditRuleResult
    (rule_name, severity, message). The LLM only summarizes the pre-decided
    outcome; it never validates or decides approval.
    """

    def __init__(self, api_key):
        self.llm = LLMModel(api_key)

    def run(
        self,
        ops_decision: OperationalDecision,
        risk_assessment: RiskAssessment,
        item_data: dict,
    ) -> AuditResult:
        """
        Validate an item's operational decision and risk assessment.

        Inputs:
            ops_decision: OperationalDecision from OpsAgent.run().
            risk_assessment: RiskAssessment from RiskAgent.run().
            item_data: original inventory item dict.
        Outputs:
            AuditResult: full rule engine verdict. approved=False halts
                the workflow.
        """
        rule_results = []
        rule_results.extend(self._validate_inventory(item_data))
        rule_results.extend(self._validate_business_rules(ops_decision, risk_assessment))
        rule_results.extend(self._validate_consistency(ops_decision, risk_assessment, item_data))

        blocking_errors = self._count_by_severity(rule_results, RuleSeverity.BLOCKER)
        error_count = self._count_by_severity(rule_results, RuleSeverity.ERROR)
        warning_count = self._count_by_severity(rule_results, RuleSeverity.WARNING)

        approved = self._determine_approval(blocking_errors, warning_count)
        audit_status = self._determine_audit_status(approved, warning_count)
        failed_rules = [r.rule_name for r in rule_results]

        summary = self._generate_audit_summary(
            ops_decision=ops_decision,
            risk_assessment=risk_assessment,
            approved=approved,
            audit_status=audit_status,
            rule_results=rule_results,
        )

        return AuditResult(
            approved=approved,
            audit_status=audit_status,
            failed_rules=failed_rules,
            warning_count=warning_count,
            blocking_errors=blocking_errors,
            error_count=error_count,
            rule_results=rule_results,
            reasoning=summary.get("reasoning", ""),
        )

    # ------------------------------------------------------------------
    # Inventory validation
    # ------------------------------------------------------------------
    def _validate_inventory(self, item_data: dict) -> list:
        """
        Validate the raw inventory input data for presence, type, and
        basic sanity before any downstream agent output is trusted.

        Inputs:
            item_data: original inventory item dict.
        Outputs:
            list[AuditRuleResult]: one entry per failed rule.
        """
        rules = []

        sku_name = item_data.get("sku_name")
        if not sku_name:
            rules.append(
                AuditRuleResult(
                    "UNKNOWN_SKU",
                    RuleSeverity.BLOCKER.value,
                    "SKU name is missing.",
                )
            )

        location_id = item_data.get("location_id")
        location_type = item_data.get("location_type")
        if not location_id and not location_type:
            rules.append(
                AuditRuleResult(
                    "MISSING_LOCATION",
                    RuleSeverity.BLOCKER.value,
                    "No location_id or location_type provided.",
                )
            )

        available_stock = item_data.get("available_stock")
        if available_stock is None:
            rules.append(
                AuditRuleResult(
                    "MISSING_AVAILABLE_STOCK",
                    RuleSeverity.BLOCKER.value,
                    "available_stock is missing.",
                )
            )
        elif not isinstance(available_stock, (int, float)) or isinstance(available_stock, bool):
            rules.append(
                AuditRuleResult(
                    "INVALID_STOCK_TYPE",
                    RuleSeverity.BLOCKER.value,
                    f"available_stock must be numeric, got {type(available_stock).__name__}.",
                )
            )
        elif available_stock < 0:
            rules.append(
                AuditRuleResult(
                    "NEGATIVE_STOCK",
                    RuleSeverity.BLOCKER.value,
                    f"available_stock is negative ({available_stock}).",
                )
            )

        forecast_demand = item_data.get("forecast_demand")
        if forecast_demand is None:
            rules.append(
                AuditRuleResult(
                    "MISSING_FORECAST",
                    RuleSeverity.BLOCKER.value,
                    "forecast_demand is missing.",
                )
            )
        elif not isinstance(forecast_demand, (int, float)) or isinstance(forecast_demand, bool):
            rules.append(
                AuditRuleResult(
                    "INVALID_FORECAST_TYPE",
                    RuleSeverity.BLOCKER.value,
                    f"forecast_demand must be numeric, got {type(forecast_demand).__name__}.",
                )
            )
        else:
            if forecast_demand < 0:
                rules.append(
                    AuditRuleResult(
                        "NEGATIVE_DEMAND",
                        RuleSeverity.BLOCKER.value,
                        f"forecast_demand is negative ({forecast_demand}).",
                    )
                )
            if forecast_demand > ABSURD_FORECAST_THRESHOLD:
                rules.append(
                    AuditRuleResult(
                        "INVALID_FORECAST",
                        RuleSeverity.ERROR.value,
                        f"forecast_demand ({forecast_demand}) exceeds the plausible "
                        f"maximum ({ABSURD_FORECAST_THRESHOLD}).",
                    )
                )

        confidence_low = item_data.get("confidence_low")
        confidence_high = item_data.get("confidence_high")
        if (
            confidence_low is not None
            and confidence_high is not None
            and confidence_low > confidence_high
        ):
            rules.append(
                AuditRuleResult(
                    "INVALID_CONFIDENCE_INTERVAL",
                    RuleSeverity.ERROR.value,
                    "confidence_low is greater than confidence_high.",
                )
            )

        if item_data.get("safety_stock") is None:
            rules.append(
                AuditRuleResult(
                    "MISSING_SAFETY_STOCK",
                    RuleSeverity.WARNING.value,
                    "No externally supplied safety_stock; Ops Agent estimate was used.",
                )
            )

        expiry_days = item_data.get("expiry_days")
        if expiry_days is not None and expiry_days <= EXPIRED_PRODUCT_DAYS:
            rules.append(
                AuditRuleResult(
                    "EXPIRED_PRODUCT",
                    RuleSeverity.BLOCKER.value,
                    f"Product has expired (expiry_days={expiry_days}).",
                )
            )

        return rules

    # ------------------------------------------------------------------
    # Business rule validation
    # ------------------------------------------------------------------
    def _validate_business_rules(
        self, ops_decision: OperationalDecision, risk_assessment: RiskAssessment
    ) -> list:
        """
        Validate that agent outputs fall within allowed business ranges.

        Inputs:
            ops_decision: upstream OperationalDecision.
            risk_assessment: upstream RiskAssessment.
        Outputs:
            list[AuditRuleResult]: one entry per failed rule.
        """
        rules = []

        if ops_decision.recommended_qty < 0:
            rules.append(
                AuditRuleResult(
                    "INVALID_RECOMMENDED_QTY",
                    RuleSeverity.BLOCKER.value,
                    "recommended_qty is negative.",
                )
            )

        if ops_decision.action not in VALID_ACTIONS:
            rules.append(
                AuditRuleResult(
                    "INVALID_ACTION",
                    RuleSeverity.BLOCKER.value,
                    f"action '{ops_decision.action}' is not a recognized value.",
                )
            )

        if risk_assessment.risk_level not in VALID_RISK_LEVELS:
            rules.append(
                AuditRuleResult(
                    "INVALID_RISK_LEVEL",
                    RuleSeverity.BLOCKER.value,
                    f"risk_level '{risk_assessment.risk_level}' is not recognized.",
                )
            )

        if not (MIN_RISK_SCORE <= risk_assessment.risk_score <= MAX_RISK_SCORE):
            rules.append(
                AuditRuleResult(
                    "RISK_SCORE_OUT_OF_RANGE",
                    RuleSeverity.BLOCKER.value,
                    "risk_score is outside the valid 0-100 range.",
                )
            )

        if ops_decision.recommended_qty > 0 and ops_decision.action != "REORDER":
            rules.append(
                AuditRuleResult(
                    "INVALID_REORDER_QTY",
                    RuleSeverity.BLOCKER.value,
                    "recommended_qty is positive but action is not REORDER.",
                )
            )

        return rules

    # ------------------------------------------------------------------
    # Consistency validation
    # ------------------------------------------------------------------
    def _validate_consistency(
        self,
        ops_decision: OperationalDecision,
        risk_assessment: RiskAssessment,
        item_data: dict,
    ) -> list:
        """
        Validate logical consistency across OperationalDecision,
        RiskAssessment, and the original inventory data.

        Inputs:
            ops_decision: upstream OperationalDecision.
            risk_assessment: upstream RiskAssessment.
            item_data: original inventory item dict.
        Outputs:
            list[AuditRuleResult]: one entry per failed rule.
        """
        rules = []

        if not ops_decision.needs_reorder and ops_decision.recommended_qty > 0:
            rules.append(
                AuditRuleResult(
                    "REORDER_QTY_WITHOUT_NEED",
                    RuleSeverity.BLOCKER.value,
                    "recommended_qty > 0 despite needs_reorder being False.",
                )
            )

        if ops_decision.inventory_gap > 0 and ops_decision.action != "REORDER":
            rules.append(
                AuditRuleResult(
                    "SHORTAGE_WITHOUT_REORDER",
                    RuleSeverity.BLOCKER.value,
                    "inventory_gap is positive but action is not REORDER.",
                )
            )

        if ops_decision.inventory_gap <= 0 and ops_decision.action == "REORDER":
            rules.append(
                AuditRuleResult(
                    "REORDER_WITHOUT_SHORTAGE",
                    RuleSeverity.BLOCKER.value,
                    "Action is REORDER but there is no positive inventory gap.",
                )
            )

        if ops_decision.needs_reorder and ops_decision.recommended_qty == 0:
            rules.append(
                AuditRuleResult(
                    "ZERO_REORDER_QTY",
                    RuleSeverity.BLOCKER.value,
                    "needs_reorder is True but recommended_qty is zero.",
                )
            )

        if (
            ops_decision.action == "REORDER"
            and ops_decision.inventory_gap > 0
            and 0 < ops_decision.recommended_qty < ops_decision.inventory_gap
        ):
            rules.append(
                AuditRuleResult(
                    "INSUFFICIENT_REORDER_QTY",
                    RuleSeverity.ERROR.value,
                    f"recommended_qty ({ops_decision.recommended_qty}) is less than "
                    f"the inventory_gap ({ops_decision.inventory_gap}) it should cover.",
                )
            )

        available_stock = item_data.get("available_stock")
        if available_stock == 0 and ops_decision.action == "MONITOR":
            rules.append(
                AuditRuleResult(
                    "ZERO_STOCK_WITH_MONITOR",
                    RuleSeverity.ERROR.value,
                    "Stock is zero but action is MONITOR instead of REORDER.",
                )
            )

        if item_data.get("forecast_demand") == 0:
            rules.append(
                AuditRuleResult(
                    "ZERO_FORECAST_DEMAND",
                    RuleSeverity.WARNING.value,
                    "forecast_demand is zero; recommendation may be unreliable.",
                )
            )

        if risk_assessment.risk_level in ("HIGH", "CRITICAL") and risk_assessment.alert_level == "LOW":
            rules.append(
                AuditRuleResult(
                    "RISK_ALERT_MISMATCH",
                    RuleSeverity.BLOCKER.value,
                    "High/critical risk level does not match a LOW alert level.",
                )
            )

        return rules

    def _count_by_severity(self, rule_results: list, severity: RuleSeverity) -> int:
        return sum(1 for r in rule_results if r.severity == severity.value)

    def _determine_approval(self, blocking_errors: int, warning_count: int) -> bool:
        return blocking_errors <= MAX_BLOCKING_ERRORS and warning_count <= MAX_ALLOWED_WARNINGS

    def _determine_audit_status(self, approved: bool, warning_count: int) -> str:
        if not approved:
            return "REJECTED"
        if warning_count > 0:
            return "APPROVED_WITH_WARNINGS"
        return "APPROVED"

    # ------------------------------------------------------------------
    # LLM used strictly for explanation text generation
    # ------------------------------------------------------------------
    def _generate_audit_summary(self, ops_decision, risk_assessment, approved, audit_status, rule_results) -> dict:
        llm_input = {
            "sku_name": ops_decision.sku,
            "action": ops_decision.action,
            "risk_level": risk_assessment.risk_level,
            "approved": approved,
            "audit_status": audit_status,
            "rule_results": [
                {"rule_name": r.rule_name, "severity": r.severity, "message": r.message}
                for r in rule_results
            ],
        }

        raw_response = self.llm.get_decision(AUDITOR_AGENT_PROMPT, llm_input)

        try:
            return json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMResponseParsingError(
                f"AuditorAgent could not parse LLM response as JSON: {exc}"
            ) from exc