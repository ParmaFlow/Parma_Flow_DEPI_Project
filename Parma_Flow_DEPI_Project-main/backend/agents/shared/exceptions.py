# backend/agents/shared/exceptions.py
"""
Custom exceptions shared across agents.

Using specific exception types (instead of letting raw json.JSONDecodeError /
KeyError bubble up) makes failures easier to catch and handle predictably at
the orchestrator level.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""


class LLMResponseParsingError(AgentError):
    """Raised when an agent cannot parse the LLM's response as valid JSON."""


class InvalidInventoryDataError(AgentError):
    """Raised when inventory input data is missing required fields."""


class WorkflowExecutionError(AgentError):
    """
    Raised by the Orchestrator when a step in the workflow fails
    unrecoverably (e.g. an agent raises an unexpected exception).

    Caught internally by the Orchestrator to convert failures into a
    structured WorkflowState result rather than crashing the process.
    """