# backend/agents/risk_agent/risk_agent.py
import json
import logging

from backend.core.llm import LLMModel
from backend.agents.risk_agent.prompt import RISK_AGENT_PROMPT
from backend.agents.shared.base_agent import BaseAgent
from backend.agents.shared.models import OperationalDecision, RiskAssessment
from backend.agents.shared.constants import (
    LOW_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_THRESHOLD,
    HUMAN_REVIEW_RISK_THRESHOLD,
    EXPIRY_WARNING_DAYS,
    LONG_LEAD_TIME_DAYS,
    CONFIDENCE_WIDTH_WEIGHT,
    LOW_STOCK_WEIGHT,
    SHORTAGE_RISK_WEIGHT,
    EXPIRY_RISK_WEIGHT,
    CRITICAL_DRUG_WEIGHT,
    LONG_LEAD_TIME_WEIGHT,
    CONFIDENCE_WIDTH_RATIO_THRESHOLD,
    LOW_STOCK_RATIO_THRESHOLD,
    CRITICAL_DRUG_CATEGORIES,
    MIN_RISK_SCORE,
    MAX_RISK_SCORE,
    ActionType,
)
from backend.agents.shared.exceptions import LLMResponseParsingError

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Risk Agent â€” deterministic, multi-factor risk scoring.

    Computes a 0-100 risk score from confidence interval width, stock
    level, shortage size, expiry proximity, drug criticality, and lead
    time â€” entirely in Python. The LLM is used ONLY to explain the result.
    """

    def __init__(self, api_key):
        self.llm = LLMModel(api_key)

    def run(self, ops_decision: OperationalDecision, item_data: dict) -> RiskAssessment:
        """
        Evaluate risk for an inventory item.

        Inputs:
            ops_decision: OperationalDecision produced by OpsAgent.run().
            item_data: original inventory item dict; may optionally
                contain "confidence_low", "confidence_high",
                "expiry_days", "drug_category", "lead_time",
                "available_stock", "forecast_demand".
        Outputs:
            RiskAssessment: deterministic score/level plus LLM explanation.
        """
        confidence_width = self._calculate_confidence_width(item_data)
        shortage_risk = self._calculate_shortage_risk(ops_decision, item_data)
        expiry_risk = self._calculate_expiry_risk(item_data)
        criticality = self._calculate_criticality(item_data)
        low_stock = self._is_low_stock(item_data)
        long_lead_time = self._is_long_lead_time(item_data)

        risk_score = self._calculate_risk_score(
            item_data=item_data,
            ops_decision=ops_decision,
            confidence_width=confidence_width,
            shortage_risk=shortage_risk,
            expiry_risk=expiry_risk,
            criticality=criticality,
            low_stock=low_stock,
            long_lead_time=long_lead_time,
        )
        risk_level = self._determine_risk_level(risk_score)
        human_review_recommended = self._recommend_human_review(risk_score)

        summary = self._create_risk_summary(
            ops_decision=ops_decision,
            item_data=item_data,
            risk_score=risk_score,
            risk_level=risk_level,
            shortage_risk=shortage_risk,
            expiry_risk=expiry_risk,
            criticality=criticality,
            low_stock=low_stock,
            long_lead_time=long_lead_time,
            confidence_width=confidence_width,
            human_review_recommended=human_review_recommended,
        )

        return RiskAssessment(
            sku=ops_decision.sku,
            risk_score=risk_score,
            risk_level=risk_level,
            shortage_risk=shortage_risk,
            expiry_risk=expiry_risk,
            criticality=criticality,
            alert_level=risk_level,
            confidence_width=confidence_width,
            human_review_recommended=human_review_recommended,
            reasoning=summary.get("reasoning", ""),
        )

    # ------------------------------------------------------------------
    # Deterministic factor calculations
    # ------------------------------------------------------------------
    def _calculate_confidence_width(self, item_data: dict):
        confidence_low = item_data.get("confidence_low")
        confidence_high = item_data.get("confidence_high")
        if confidence_low is None or confidence_high is None:
            return None
        return confidence_high - confidence_low

    def _calculate_shortage_risk(self, ops_decision: OperationalDecision, item_data: dict) -> bool:
        if (item_data.get("forecast_demand", 0) or 0) <= 0:
            logger.warning("Zero demand input detected; inventory tracking paused.")
            return False
        if ops_decision.action == ActionType.HOLD_MONITOR.value:
            return False
        return bool(ops_decision.needs_reorder and ops_decision.inventory_gap > 0)

    def _calculate_expiry_risk(self, item_data: dict) -> bool:
        expiry_days = item_data.get("expiry_days")
        if expiry_days is None:
            return False
        return expiry_days < EXPIRY_WARNING_DAYS

    def _calculate_criticality(self, item_data: dict) -> str:
        drug_category = item_data.get("drug_category")
        if not drug_category:
            return "STANDARD"
        if drug_category.strip().lower() in CRITICAL_DRUG_CATEGORIES:
            return "CRITICAL"
        return "STANDARD"

    def _is_low_stock(self, item_data: dict) -> bool:
        """Stock is low if available_stock is below a fraction of forecast_demand."""
        available_stock = item_data.get("available_stock")
        forecast_demand = item_data.get("forecast_demand")
        if available_stock is None or not forecast_demand:
            return False
        if forecast_demand <= 0:
            return False
        return available_stock < forecast_demand * LOW_STOCK_RATIO_THRESHOLD

    def _is_long_lead_time(self, item_data: dict) -> bool:
        lead_time = item_data.get("lead_time")
        if lead_time is None:
            return False
        return lead_time >= LONG_LEAD_TIME_DAYS

    # ------------------------------------------------------------------
    # Score aggregation
    # ------------------------------------------------------------------
    def _calculate_confidence_severity(self, item_data: dict, confidence_width) -> float:
        """Normalized (0.0-1.0) severity for a wide confidence interval."""
        forecast_demand = item_data.get("forecast_demand")
        if confidence_width is None or not forecast_demand:
            return 0.0
        ratio = confidence_width / forecast_demand
        if ratio <= CONFIDENCE_WIDTH_RATIO_THRESHOLD:
            return 0.0
        return min(ratio / (CONFIDENCE_WIDTH_RATIO_THRESHOLD * 2), 1.0)

    def _calculate_shortage_severity(self, ops_decision: OperationalDecision) -> float:
        """Normalized (0.0-1.0) severity for shortage size, relative to a
        doubling of the recommended reorder threshold."""
        if ops_decision.inventory_gap <= 0:
            return 0.0
        reference = max(ops_decision.recommended_qty, 1)
        return min(ops_decision.inventory_gap / (reference * 2), 1.0)

    def _calculate_expiry_severity(self, item_data: dict) -> float:
        expiry_days = item_data.get("expiry_days")
        if expiry_days is None or expiry_days >= EXPIRY_WARNING_DAYS:
            return 0.0
        if expiry_days <= 0:
            return 1.0
        return 1.0 - (expiry_days / EXPIRY_WARNING_DAYS)

    def _calculate_risk_score(
        self,
        item_data: dict,
        ops_decision: OperationalDecision,
        confidence_width,
        shortage_risk: bool,
        expiry_risk: bool,
        criticality: str,
        low_stock: bool,
        long_lead_time: bool,
    ) -> int:
        """
        Weighted deterministic risk score (0-100). Weights come from
        shared/constants.py â€” no magic numbers.
        """
        score = 0.0

        score += self._calculate_confidence_severity(item_data, confidence_width) * CONFIDENCE_WIDTH_WEIGHT

        if low_stock:
            score += LOW_STOCK_WEIGHT

        if shortage_risk:
            score += self._calculate_shortage_severity(ops_decision) * SHORTAGE_RISK_WEIGHT

        if expiry_risk:
            score += self._calculate_expiry_severity(item_data) * EXPIRY_RISK_WEIGHT

        if criticality == "CRITICAL":
            score += CRITICAL_DRUG_WEIGHT

        if long_lead_time:
            score += LONG_LEAD_TIME_WEIGHT

        return int(max(MIN_RISK_SCORE, min(MAX_RISK_SCORE, round(score))))

    def _determine_risk_level(self, risk_score: int) -> str:
        if risk_score <= LOW_RISK_THRESHOLD:
            return "LOW"
        if risk_score <= MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        if risk_score <= HIGH_RISK_THRESHOLD:
            return "HIGH"
        return "CRITICAL"

    def _recommend_human_review(self, risk_score: int) -> bool:
        return risk_score >= HUMAN_REVIEW_RISK_THRESHOLD

    # ------------------------------------------------------------------
    # LLM used strictly for explanation text generation
    # ------------------------------------------------------------------
    def _create_risk_summary(self, ops_decision: OperationalDecision, item_data: dict, **computed) -> dict:
        return self._build_grounded_risk_summary(ops_decision, item_data, **computed)

    def _build_grounded_risk_summary(self, ops_decision: OperationalDecision, item_data: dict, **computed) -> dict:
        risk_score = computed["risk_score"]
        risk_level = computed["risk_level"]
        shortage_risk = computed["shortage_risk"]
        expiry_risk = computed["expiry_risk"]
        criticality = computed["criticality"]
        confidence_width = computed["confidence_width"]
        human_review = computed["human_review_recommended"]

        if (item_data.get("forecast_demand", 0) or 0) <= 0:
            return {
                "reasoning": (
                    "Zero demand input detected; inventory tracking paused. "
                    f"Risk level is {risk_level} with score {risk_score}/100, shortage risk is suppressed, "
                    f"and the approved rounded quantity is {ops_decision.recommended_qty:,} units."
                )
            }

        confidence_text = (
            f"confidence width {confidence_width}" if confidence_width is not None else "no confidence interval supplied"
        )
        review_text = "manual review is required" if human_review else "manual review is not required"
        return {
            "reasoning": (
                f"{ops_decision.sku} risk level is {risk_level} with score {risk_score}/100. "
                f"Shortage risk={shortage_risk}, expiry risk={expiry_risk}, criticality={criticality}, "
                f"and {confidence_text}. The approved rounded quantity is "
                f"{ops_decision.recommended_qty:,} units, and {review_text}."
            )
        }

    def _create_llm_risk_summary(self, ops_decision: OperationalDecision, item_data: dict, **computed) -> dict:
        llm_input = {
            "sku_name": ops_decision.sku,
            "location_type": item_data.get("location_type"),
            "action": ops_decision.action,
            "inventory_gap": ops_decision.inventory_gap,
            "recommended_qty": ops_decision.recommended_qty,
            **computed,
        }

        raw_response = self.llm.get_decision(RISK_AGENT_PROMPT, llm_input)

        try:
            return json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMResponseParsingError(
                f"RiskAgent could not parse LLM response as JSON: {exc}"
            ) from exc



