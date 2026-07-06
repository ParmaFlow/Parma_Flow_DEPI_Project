# backend/agents/ops_agent/ops_agent.py
import json

from core.llm import LLMModel
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
    CRITICAL_STOCK_RATIO,
    LOW_STOCK_RATIO,
    InventoryStatus,
    ActionType,
)
from backend.agents.shared.exceptions import LLMResponseParsingError
from backend.agents.shared.utils import round_up_to_nearest


class OpsAgent(BaseAgent):
    """
    Ops Agent — deterministic operational inventory logic only.

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
        inventory_gap = self._calculate_inventory_gap(item_data)
        needs_reorder = self._needs_reorder(inventory_gap)
        recommended_qty = self._calculate_reorder_quantity(inventory_gap, needs_reorder)
        safety_stock = self._calculate_safety_stock(item_data)
        reorder_point = self._calculate_reorder_point(item_data, safety_stock)
        inventory_status = self._determine_inventory_status(item_data, reorder_point)
        action = self._determine_action(needs_reorder)

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
    def _calculate_inventory_gap(self, item_data: dict) -> int:
        """gap = forecast_demand - available_stock."""
        forecast_demand = item_data.get("forecast_demand", 0) or 0
        available_stock = item_data.get("available_stock", 0) or 0
        return forecast_demand - available_stock

    def _needs_reorder(self, inventory_gap: int) -> bool:
        return inventory_gap > 0

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
        forecast_demand = item_data.get("forecast_demand", 0) or 0
        lead_time = item_data.get("lead_time", 0) or 0

        avg_daily_demand = item_data.get("avg_daily_demand", forecast_demand)
        max_daily_demand = item_data.get(
            "max_daily_demand", forecast_demand * SAFETY_STOCK_MAX_DEMAND_MULTIPLIER
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
        forecast_demand = item_data.get("forecast_demand", 0) or 0
        lead_time = item_data.get("lead_time", 0) or 0
        forecast_during_lead_time = forecast_demand * lead_time if lead_time else forecast_demand
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

    def _determine_action(self, needs_reorder: bool) -> str:
        return ActionType.REORDER.value if needs_reorder else ActionType.MONITOR.value

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