# backend/agents/shared/logger.py
"""
Structured workflow logger.

Provides consistent, timestamped, execution-scoped logging for the
Orchestrator, so every workflow run produces an auditable trail
(step transitions, durations, failures) suitable for a healthcare
production system.

Fix m-6: The original implementation guarded handler attachment with
`if not self._logger.handlers` at the *instance* level. In any scenario
where two WorkflowLogger() instances share the same underlying logger name
(which Python's logging module caches globally), the second instance would
pass the guard only if the first had not yet attached a handler â€” a race
condition in multi-threaded contexts. The fix moves handler setup to a
module-level function that is called exactly once per logger name.
"""
import logging
import time
from contextlib import contextmanager
from typing import Iterator, Optional


def _get_configured_logger(name: str) -> logging.Logger:
    """
    Return a logger configured with a StreamHandler, ensuring the handler
    is added at most once regardless of how many WorkflowLogger instances
    are created with the same name.

    This is the correct pattern for avoiding log-line duplication in
    multi-instance / multi-threaded Python programs.
    """
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


class WorkflowLogger:
    """
    Thin wrapper around the standard logging module for workflow events.

    All log lines are prefixed with the execution_id so multiple concurrent
    workflow runs can be told apart in shared log output.
    """

    def __init__(self, name: str = "pharma_flow.orchestrator") -> None:
        # m-6 fix: delegate to module-level function that is idempotent
        # across multiple instances sharing the same logger name.
        self._logger = _get_configured_logger(name)

    def log_step(
        self,
        execution_id: str,
        step: str,
        message: str,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """
        Log a workflow step event.

        Inputs:
            execution_id: identifier of the current workflow run.
            step: name of the step being logged (e.g. "ops", "risk").
            message: human-readable event description.
            duration_seconds: optional elapsed time to include.
        Outputs:
            None.
        """
        if duration_seconds is not None:
            self._logger.info(
                "[%s] [%s] %s (took %.3fs)",
                execution_id,
                step,
                message,
                duration_seconds,
            )
        else:
            self._logger.info("[%s] [%s] %s", execution_id, step, message)

    def log_error(self, execution_id: str, step: str, message: str) -> None:
        """
        Log a workflow error event.

        Inputs:
            execution_id: identifier of the current workflow run.
            step: name of the step where the error occurred.
            message: human-readable error description.
        Outputs:
            None.
        """
        self._logger.error("[%s] [%s] %s", execution_id, step, message)

    @contextmanager
    def timed_step(self, execution_id: str, step: str) -> Iterator[None]:
        """
        Context manager that logs a step's start/finish with duration.

        Inputs:
            execution_id: identifier of the current workflow run.
            step: name of the step being timed.
        Outputs:
            None (context manager; yields control to the caller's block).
        """
        self.log_step(execution_id, step, "Started")
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.log_step(execution_id, step, "Finished", duration_seconds=elapsed)


