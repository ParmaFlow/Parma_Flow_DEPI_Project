# backend/agents/shared/state.py
"""
Shared workflow state for the Orchestrator.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from backend.agents.shared.models import (
    OperationalDecision,
    RiskAssessment,
    AuditResult,
    FinalDecision,
)


@dataclass
class WorkflowState:
    """
    Mutable record of a single workflow execution.

    Attributes:
        execution_id: Unique identifier for this workflow run.
        original_input: The raw item_data the workflow was started with.
        operational_result / risk_result / audit_result / report_result:
            Typed outputs of each agent, populated as the workflow
            progresses.
        current_step: Name of the step currently executing or last
            completed.
        start_time / end_time: Workflow start/end timestamps.
        execution_status: "RUNNING" / "COMPLETED" / "REJECTED" / "FAILED".
        error_message: Populated only when execution_status is "FAILED".
        failed_step: Name of the step that raised, when FAILED.
        step_durations: Seconds elapsed for each completed step, keyed by
            step name (e.g. {"ops": 0.18, "risk": 0.09}).
    """

    execution_id: str
    original_input: dict
    operational_result: Optional[OperationalDecision] = None
    risk_result: Optional[RiskAssessment] = None
    audit_result: Optional[AuditResult] = None
    report_result: Optional[FinalDecision] = None
    current_step: str = "initialized"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_status: str = "RUNNING"
    error_message: Optional[str] = None
    failed_step: Optional[str] = None
    step_durations: Dict[str, float] = field(default_factory=dict)