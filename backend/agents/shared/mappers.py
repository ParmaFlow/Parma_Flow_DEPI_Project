# backend/agents/shared/mappers.py
"""
Mapping logic between internal workflow types and the legacy-compatible
API response shape.

This is the single place that knows how to translate a WorkflowState
(the Orchestrator's internal source of truth) into the flat response
structure the existing frontend expects. Neither QueryService nor the
Orchestrator needs to know this mapping.
"""
from backend.agents.shared.state import WorkflowState
from backend.agents.shared.models import LegacyDecisionResponse
from backend.agents.shared.constants import ExecutionStatus, ActionType


class WorkflowMapper:
    """
    Converts WorkflowState into LegacyDecisionResponse.

    Kept as a class of static methods (rather than requiring
    instantiation) since it holds no state of its own — it is a pure
    translation layer.
    """

    @staticmethod
    def to_legacy_response(state: WorkflowState) -> LegacyDecisionResponse:
        """
        Convert a completed/rejected/failed WorkflowState into the legacy
        response shape.

        Inputs:
            state: WorkflowState returned by Orchestrator.run().
        Outputs:
            LegacyDecisionResponse: response matching the original
                single-agent API contract for the given execution status.
        """
        if state.execution_status == ExecutionStatus.FAILED:
            return WorkflowMapper._map_failed(state)

        if state.execution_status == ExecutionStatus.REJECTED:
            return WorkflowMapper._map_rejected(state)

        return WorkflowMapper._map_completed(state)

    @staticmethod
    def to_error_response(details: str) -> LegacyDecisionResponse:
        """
        Build a structured error response for failures that occur outside
        a WorkflowState (e.g. the Orchestrator call itself raising).

        Inputs:
            details: description of the underlying error.
        Outputs:
            LegacyDecisionResponse: failure-shaped response.
        """
        return LegacyDecisionResponse(
            status=ExecutionStatus.FAILED.value,
            message="Workflow execution failed.",
            details=details,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _map_failed(state: WorkflowState) -> LegacyDecisionResponse:
        return LegacyDecisionResponse(
            status=ExecutionStatus.FAILED.value,
            message="Workflow execution failed.",
            details=state.error_message,
        )

    @staticmethod
    def _map_rejected(state: WorkflowState) -> LegacyDecisionResponse:
        ops = state.operational_result
        audit = state.audit_result
        report = state.report_result

        return LegacyDecisionResponse(
            sku_name=ops.sku if ops else state.original_input.get("sku_name"),
            action=(report.recommended_action if report else ActionType.HUMAN_REVIEW.value),
            recommended_qty=ops.recommended_qty if ops else 0,
            assignee=ops.assignee if ops else "Pharmacy Manager",
            reasoning=(report.reasoning if report else (audit.reasoning if audit else ""))
            or "Audit rejected this decision.",
            recommendation=(report.executive_summary if report else "Autonomous execution blocked pending manual review."),
            audit_status=audit.audit_status if audit else ExecutionStatus.REJECTED.value,
            failed_rules=audit.failed_rules if audit else [],
        )

    @staticmethod
    def _map_completed(state: WorkflowState) -> LegacyDecisionResponse:
        ops = state.operational_result
        report = state.report_result
        risk = state.risk_result
        audit = state.audit_result

        return LegacyDecisionResponse(
            sku_name=ops.sku if ops else state.original_input.get("sku_name"),
            action=(report.recommended_action if report else (ops.action if ops else ActionType.MONITOR.value)),
            recommended_qty=ops.recommended_qty if ops else 0,
            assignee=ops.assignee if ops else "Warehouse Ops",
            reasoning=report.reasoning if report else (ops.reasoning if ops else ""),
            recommendation=report.executive_summary if report else "",
            risk_level=risk.risk_level if risk else None,
            audit_status=audit.audit_status if audit else None,
        )
