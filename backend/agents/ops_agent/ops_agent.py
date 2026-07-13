# backend/agents/ops_agent/ops_agent.py
import json

from backend.core.llm import LLMModel
from backend.agents.ops_agent.prompt import OPS_AGENT_PROMPT
from backend.agents.shared.base_agent import BaseAgent
from backend.agents.shared.models import OperationalDecision
from backend.agents.shared.constants import (
    REORDER_ROUNDING,
    DEFAULT_HOSPITAL_ASSIGNEE,
    DEFAULT_WAREHOUSE_ASSIGNEE,
    SAFETY_STOCK_MAX_DEMAND_MULTIPLIER,
    SAFETY_STOCK_MAX_LEAD_TIME_MULTIPLIER,
    SAFETY_STOCK_MINIMUM,
    BASELINE_DEMAND_FLOOR,
    CRITICAL_STOCK_RATIO,
    LOW_STOCK_RATIO,
    InventoryStatus,
    ActionType,
)
from backend.agents.shared.exceptions import LLMResponseParsingError
from backend.agents.shared.utils import round_up_to_nearest


class OpsAgent(BaseAgent):
    """
    Ops Agent â€” deterministic operational inventory logic only.

    Computes inventory gap, safety stock, reorder point, recommended
    quantity, and inventory status entirely in Python. The LLM is used
    ONLY to produce human-readable explanation/recommendation text.
    """

    def __init__(self, api_key):
        self.llm = LLMModel(api_key)

    def run(self, item_data: dict) -> OperationalDecision:
        """
        Analyze a single inventory item and produce an operational decision.

        Inputs:
            item_data: dict with "sku_name", "forecast_demand",
                "available_stock", and optionally "avg_daily_demand",
                "max_daily_demand", "avg_lead_time", "max_lead_time",
                "lead_time", "location_type".
        Outputs:
            OperationalDecision: deterministic calculations plus
                LLM-generated explanation text.
        """
        safety_stock = self._calculate_safety_stock(item_data)
        reorder_point = self._calculate_reorder_point(item_data, safety_stock)
        inventory_status = self._determine_inventory_status(item_data, reorder_point)
        
        needs_reorder = self._needs_reorder(item_data, reorder_point, safety_stock)
        inventory_gap = self._calculate_inventory_gap(item_data, reorder_point, safety_stock)
        recommended_qty = self._calculate_reorder_quantity(inventory_gap, needs_reorder)
        action = self._determine_action(needs_reorder, item_data)

        summary = self._create_operational_summary(
            item_data,
            inventory_gap=inventory_gap,
            needs_reorder=needs_reorder,
            recommended_qty=recommended_qty,
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            inventory_status=inventory_status,
            action=action,
        )

        # M-3 fix: pick the correct default assignee based on location_type
        # so a hospital shortage is never silently routed to the warehouse team
        # when the LLM omits the assignee field.
        is_hospital = str(item_data.get("location_type", "")).lower() == "hospital"
        default_assignee = DEFAULT_HOSPITAL_ASSIGNEE if is_hospital else DEFAULT_WAREHOUSE_ASSIGNEE

        return OperationalDecision(
            sku=item_data.get("sku_name", "Unknown SKU"),
            action=action,
            needs_reorder=needs_reorder,
            inventory_gap=inventory_gap,
            recommended_qty=recommended_qty,
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            inventory_status=inventory_status,
            assignee=summary.get("assignee") or default_assignee,
            recommendation_details=summary.get("recommendation_details", ""),
            reasoning=summary.get("reasoning", ""),
        )

    # ------------------------------------------------------------------
    # Deterministic business logic
    # ------------------------------------------------------------------
    def _calculate_inventory_gap(self, item_data: dict, reorder_point: int, safety_stock: int = 0) -> int:
        """
        Inventory gap = how many units short of the target stock level we are.

        Target = max(reorder_point, forecast_demand) so that a reorder always
        covers at least the immediate cycle demand AND restores the safety buffer.
        Zero-stock cases add the safety target once more to force a full
        emergency reset of the shelf position.

        Returns 0 (never negative) when stock already exceeds the target.
        """
        if self._is_demand_paused(item_data):
            return 0

        forecast_demand = self._get_effective_forecast_demand(item_data)
        available_stock = max(0, item_data.get("available_stock", 0) or 0)
        target_stock = max(reorder_point, forecast_demand)
        if available_stock == 0:
            target_stock += max(0, safety_stock)
        return max(0, target_stock - available_stock)

    def _needs_reorder(self, item_data: dict, reorder_point: int, safety_stock: int = 0) -> bool:
        """
        Reorder is needed if and only if inventory_gap > 0.
        Using the gap (not a raw threshold comparison) ensures that REORDER
        and MONITOR decisions are always mathematically consistent with the
        reported gap figure â€” eliminating the green-light-on-stockout bug.
        """
        if self._is_demand_paused(item_data):
            return False
        gap = self._calculate_inventory_gap(item_data, reorder_point, safety_stock)
        return gap > 0

    def _calculate_reorder_quantity(self, inventory_gap: int, needs_reorder: bool) -> int:
        if not needs_reorder:
            return 0
        return round_up_to_nearest(inventory_gap, REORDER_ROUNDING)

    def _calculate_safety_stock(self, item_data: dict) -> int:
        """
        Safety Stock = (max_daily_demand * max_lead_time)
                       - (avg_daily_demand * avg_lead_time)

        Inputs:
            item_data: may contain "max_daily_demand", "avg_daily_demand",
                "max_lead_time", "avg_lead_time". Missing values are
                estimated deterministically from "forecast_demand" and
                "lead_time" using fixed multipliers (documented in
                shared/constants.py) rather than left undefined.
        Outputs:
            int: safety stock, floored at SAFETY_STOCK_MINIMUM.
        """
        forecast_demand = self._get_effective_forecast_demand(item_data)
        lead_time = item_data.get("lead_time", 0) or 0

        avg_daily_demand = item_data.get("avg_daily_demand", forecast_demand / 30.0)
        max_daily_demand = item_data.get(
            "max_daily_demand", (forecast_demand / 30.0) * SAFETY_STOCK_MAX_DEMAND_MULTIPLIER
        )
        avg_lead_time = item_data.get("avg_lead_time", lead_time)
        max_lead_time = item_data.get(
            "max_lead_time", lead_time * SAFETY_STOCK_MAX_LEAD_TIME_MULTIPLIER
        )

        safety_stock = (max_daily_demand * max_lead_time) - (
            avg_daily_demand * avg_lead_time
        )
        return int(max(SAFETY_STOCK_MINIMUM, round(safety_stock)))

    def _calculate_reorder_point(self, item_data: dict, safety_stock: int) -> int:
        """
        ROP = forecast during lead time + safety stock.

        Inputs:
            item_data: uses "forecast_demand" and "lead_time" to estimate
                daily demand rate * lead_time (forecast during lead time).
            safety_stock: result of _calculate_safety_stock().
        Outputs:
            int: reorder point.
        """
        forecast_demand = self._get_effective_forecast_demand(item_data)
        lead_time = item_data.get("lead_time", 0) or 0
        avg_daily_demand = item_data.get("avg_daily_demand")
        if avg_daily_demand is not None and lead_time:
            forecast_during_lead_time = avg_daily_demand * lead_time
        else:
            forecast_during_lead_time = (forecast_demand / 30.0) * lead_time if lead_time else forecast_demand
        return int(round(forecast_during_lead_time + safety_stock))

    def _determine_inventory_status(self, item_data: dict, reorder_point: int) -> str:
        """
        Classify current stock health relative to the reorder point.

        Inputs:
            item_data: uses "available_stock".
            reorder_point: result of _calculate_reorder_point().
        Outputs:
            str: one of InventoryStatus values.
        """
        available_stock = item_data.get("available_stock", 0) or 0

        if available_stock <= 0:
            return InventoryStatus.OUT_OF_STOCK.value

        if reorder_point <= 0:
            return InventoryStatus.NORMAL.value

        ratio = available_stock / reorder_point
        if ratio <= CRITICAL_STOCK_RATIO:
            return InventoryStatus.CRITICAL.value
        if ratio <= LOW_STOCK_RATIO:
            return InventoryStatus.LOW.value
        return InventoryStatus.NORMAL.value

    def _determine_action(self, needs_reorder: bool, item_data: dict) -> str:
        if self._is_demand_paused(item_data):
            return ActionType.HOLD_MONITOR.value
        return ActionType.REORDER.value if needs_reorder else ActionType.MONITOR.value

    def _get_effective_forecast_demand(self, item_data: dict) -> int:
        forecast_demand = item_data.get("forecast_demand", 0) or 0
        if forecast_demand <= 0:
            return BASELINE_DEMAND_FLOOR
        return forecast_demand

    def _is_demand_paused(self, item_data: dict) -> bool:
        return (item_data.get("forecast_demand", 0) or 0) <= 0

    # ------------------------------------------------------------------
    # LLM used strictly for explanation text generation
    # ------------------------------------------------------------------
    def _create_operational_summary(self, item_data: dict, **computed) -> dict:
        """
        Generate human-readable explanation text via the LLM.

        Inputs:
            item_data: original inventory item data (context/tone).
            **computed: pre-computed results (inventory_gap, needs_reorder,
                recommended_qty, safety_stock, reorder_point,
                inventory_status, action).
        Outputs:
            dict: parsed LLM response with "assignee",
                "recommendation_details", "reasoning".
        Raises:
            LLMResponseParsingError: if the LLM response is not valid JSON.
        """
        return self._build_grounded_operational_summary(item_data, **computed)

    def _build_grounded_operational_summary(self, item_data: dict, **computed) -> dict:
        sku_name = item_data.get("sku_name", "Unknown SKU")
        location_type = str(item_data.get("location_type", "")).lower()
        is_hospital = location_type == "hospital"
        assignee = DEFAULT_HOSPITAL_ASSIGNEE if is_hospital else DEFAULT_WAREHOUSE_ASSIGNEE

        action = computed["action"]
        inventory_gap = computed["inventory_gap"]
        recommended_qty = computed["recommended_qty"]
        safety_stock = computed["safety_stock"]
        reorder_point = computed["reorder_point"]
        inventory_status = computed["inventory_status"]
        available_stock = max(0, item_data.get("available_stock", 0) or 0)
        demand_paused = self._is_demand_paused(item_data)
        forecast_demand = self._get_effective_forecast_demand(item_data)
        lead_time = max(0, item_data.get("lead_time", 0) or 0)

        if demand_paused and available_stock > 0:
            runway_text = "0.00 demand cycles; zero demand input detected and inventory tracking is paused"
        elif available_stock == 0:
            runway_text = "0.00 demand cycles of stock cover"
        elif forecast_demand > 0:
            stock_cover = round(available_stock / forecast_demand, 2)
            runway_text = f"{stock_cover:.2f} demand cycles of stock cover"
        else:
            runway_text = "0.00 demand cycles of stock cover"

        if action == ActionType.REORDER.value:
            recommendation = (
                f"Initiate emergency procurement requisition for {recommended_qty:,} units of "
                f"{sku_name} for the target location immediately. The order quantity covers the "
                "rounded supply requirement and restores the safety stock buffer."
            )
            reasoning = (
                f"{sku_name} is in {inventory_status} inventory status with {available_stock:,} units "
                f"available against a reorder point of {reorder_point:,} units. The procurement "
                f"trigger threshold has been breached, so the action is REORDER. The approved "
                f"rounded quantity is {recommended_qty:,} units to preserve clinical formulary "
                f"continuity while accounting for the safety stock buffer and {lead_time}-day lead "
                f"time buffer. Current stock cover indicates {runway_text}, so "
                f"delaying replenishment increases stockout runway and service-continuity risk."
            )
        elif action == ActionType.HOLD_MONITOR.value:
            recommendation = (
                f"Pause active procurement for {sku_name}; zero demand input detected and inventory "
                "tracking is on hold until demand is restored."
            )
            reasoning = (
                f"{sku_name} is in {inventory_status} inventory status with {available_stock:,} units "
                f"available and zero or negative raw demand input. The active demand parameter was "
                f"floored to {BASELINE_DEMAND_FLOOR} only to keep calculations safe, but the "
                f"action is HOLD_MONITOR and the approved rounded quantity is {recommended_qty:,} "
                f"units. Current stock cover is exactly "
                f"{runway_text}, so no shortage alarm is raised until valid demand resumes."
            )
        else:
            recommendation = (
                f"Maintain monitoring for {sku_name}; no procurement requisition is generated because "
                "the deterministic inventory gap is zero."
            )
            reasoning = (
                f"{sku_name} is in {inventory_status} inventory status with {available_stock:,} units "
                f"available against a reorder point of {reorder_point:,} units. The action is "
                "MONITOR and the approved rounded quantity is 0 units. "
                f"The {safety_stock:,}-unit safety stock buffer remains represented in the reorder "
                f"point, and current stock cover indicates {runway_text}; a future reorder is triggered "
                "only if available stock falls below the target stock level."
            )

        return {
            "assignee": assignee,
            "recommendation_details": recommendation,
            "reasoning": reasoning,
        }

    def _create_llm_operational_summary(self, item_data: dict, **computed) -> dict:
        """
        Legacy LLM summary path retained for future experimentation.
        Production output uses _build_grounded_operational_summary so prose
        cannot contradict deterministic quantities.
        """
        llm_input = {
            "sku_name": item_data.get("sku_name"),
            "location_type": item_data.get("location_type"),
            "forecast_demand": item_data.get("forecast_demand"),
            "available_stock": item_data.get("available_stock"),
            "lead_time": item_data.get("lead_time"),
            **computed,
        }

        raw_response = self.llm.get_decision(OPS_AGENT_PROMPT, llm_input)

        try:
            return json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMResponseParsingError(
                f"OpsAgent could not parse LLM response as JSON: {exc}"
            ) from exc



