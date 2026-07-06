# services/query_service.py
"""
Query Service — API-facing entry point for inventory analysis.

Responsibility is now strictly limited to:
Receive Request -> Run Orchestrator -> Map Response -> Execute Action -> Return Response.

All dependency construction (bootstrap.py), status/mapping logic
(WorkflowMapper), and side-effect execution (ActionService) have been
extracted elsewhere, so this file contains none of that logic itself.
"""
from backend.bootstrap import build_orchestrator
from backend.agents.shared.mappers import WorkflowMapper
from backend.agents.shared.logger import WorkflowLogger
from backend.agents.shared.constants import ExecutionStatus
from services.action_service import ActionService


class QueryService:
    """
    API-facing service for running inventory analysis.

    Public interface is unchanged from the single-agent version:
    - __init__(api_key)
    - execute_agent_decision(item_data) -> dict

    Internally, this delegates entirely to the multi-agent Orchestrator
    (built via backend.bootstrap) and never constructs the agent
    dependency graph itself.
    """

    def __init__(self, api_key: str) -> None:
        self.orchestrator = build_orchestrator(api_key)
        self._logger = WorkflowLogger()

    def execute_agent_decision(self, item_data: dict) -> dict:
        """
        Run the multi-agent workflow for a single inventory item and
        return a response compatible with the original single-agent API
        contract.

        Inputs:
            item_data: raw inventory item dict, same shape as before
                (sku_name, location_id, forecast_demand, available_stock,
                and any optional fields).
        Outputs:
            dict: on success/rejection, contains "action", "reasoning",
                "recommendation" (matching the original response schema)
                plus supplementary fields. On failure, returns
                {"status": "FAILED", "message": ..., "details": ...}.
                Never raises — Python exceptions are never exposed to the
                API caller.
        """
        try:
            state = self.orchestrator.run(item_data)
        except Exception as exc:  # noqa: BLE001 - defensive boundary guard
            self._logger.log_error("unknown", "workflow", str(exc))
            return WorkflowMapper.to_error_response(str(exc)).to_dict()

        if state.execution_status == ExecutionStatus.FAILED:
            self._logger.log_error(
                state.execution_id, state.current_step, state.error_message
            )
        elif state.execution_status == ExecutionStatus.REJECTED:
            self._logger.log_step(
                state.execution_id, "audit", "Audit Rejection returned to API caller"
            )

        response = WorkflowMapper.to_legacy_response(state)

        if state.execution_status != ExecutionStatus.FAILED:
            ActionService.execute(response)

        return response.to_dict()