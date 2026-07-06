# backend/agents/orchestrator/orchestrator.py
"""
Orchestrator for the Pharma-Flow multi-agent workflow.
"""
import time
import uuid
from datetime import datetime
from typing import Any, Dict

from backend.agents.shared.registry import AgentRegistry
from backend.agents.shared.logger import WorkflowLogger
from backend.agents.shared.state import WorkflowState
from backend.agents.shared.exceptions import WorkflowExecutionError
from backend.agents.shared.constants import ExecutionStatus


class Orchestrator:
    """
    Coordinates execution of the Ops -> Risk -> Audit -> Report pipeline.

    Unchanged architecture from the prior version: the Orchestrator is
    still the only component that invokes agents, still contains no
    business logic, and still returns a WorkflowState. This revision only
    adds per-step latency tracking and failed-step attribution.
    """

    def __init__(self, registry: AgentRegistry, logger: WorkflowLogger, api_key: str) -> None:
        self._logger = logger
        self._ops_agent = registry.create("ops", api_key)
        self._risk_agent = registry.create("risk", api_key)
        self._audit_agent = registry.create("audit", api_key)
        self._report_agent = registry.create("report", api_key)

    def run(self, item_data: Dict[str, Any]) -> WorkflowState:
        """
        Execute the full multi-agent workflow for a single inventory item.

        Inputs:
            item_data: raw inventory item dict.
        Outputs:
            WorkflowState: complete record of the run, including
                per-step durations and, on failure, the failed step name.
        """
        state = WorkflowState(execution_id=str(uuid.uuid4()), original_input=item_data)
        self._logger.log_step(state.execution_id, "workflow", "Workflow Started")

        try:
            self._run_ops_step(state)
            self._run_risk_step(state)
            self._run_audit_step(state)

            if not state.audit_result.approved:
                self._reject_workflow(state)
                return state

            self._run_report_step(state)
            self._complete_workflow(state)
            return state

        except Exception as exc:  # noqa: BLE001 - intentional top-level guard
            state.failed_step = state.current_step
            self._fail_workflow(state, exc)
            return state

    def _timed_run(self, state: WorkflowState, step: str, fn, *args):
        state.current_step = step
        start = time.perf_counter()
        with self._logger.timed_step(state.execution_id, step):
            try:
                result = fn(*args)
            except Exception as exc:
                raise WorkflowExecutionError(f"{step} step failed: {exc}") from exc
        state.step_durations[step] = round(time.perf_counter() - start, 4)
        return result

    def _run_ops_step(self, state: WorkflowState) -> None:
        state.operational_result = self._timed_run(state, "ops", self._ops_agent.run, state.original_input)

    def _run_risk_step(self, state: WorkflowState) -> None:
        state.risk_result = self._timed_run(
            state, "risk", self._risk_agent.run, state.operational_result, state.original_input
        )

    def _run_audit_step(self, state: WorkflowState) -> None:
        state.audit_result = self._timed_run(
            state,
            "audit",
            self._audit_agent.run,
            state.operational_result,
            state.risk_result,
            state.original_input,
        )
        if not state.audit_result.approved:
            self._logger.log_step(state.execution_id, "audit", "Audit Failed - workflow will stop")

    def _run_report_step(self, state: WorkflowState) -> None:
        state.report_result = self._timed_run(
            state,
            "report",
            self._report_agent.run,
            state.operational_result,
            state.risk_result,
            state.audit_result,
        )

    def _complete_workflow(self, state: WorkflowState) -> None:
        state.current_step = "done"
        # M-4 fix: use ExecutionStatus enum — raw strings risk silent typos.
        state.execution_status = ExecutionStatus.COMPLETED
        state.end_time = datetime.now()
        self._logger.log_step(state.execution_id, "workflow", "Workflow Completed")

    def _reject_workflow(self, state: WorkflowState) -> None:
        state.execution_status = ExecutionStatus.REJECTED
        state.end_time = datetime.now()
        self._logger.log_step(state.execution_id, "workflow", "Workflow Finished (Rejected)")

    def _fail_workflow(self, state: WorkflowState, exc: Exception) -> None:
        state.execution_status = ExecutionStatus.FAILED
        state.error_message = str(exc)
        state.end_time = datetime.now()
        self._logger.log_error(state.execution_id, state.current_step, str(exc))
        self._logger.log_step(state.execution_id, "workflow", "Workflow Finished (Failed)")