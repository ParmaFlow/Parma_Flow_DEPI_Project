# backend/bootstrap.py
"""
Composition root for Pharma-Flow's multi-agent workflow.

This is the single place responsible for wiring together the AgentRegistry,
WorkflowLogger, and Orchestrator. FastAPI services should never construct
this dependency graph themselves; they ask bootstrap for a ready-to-use
Orchestrator.
"""
from backend.agents.orchestrator.orchestrator import Orchestrator
from backend.agents.shared.registry import AgentRegistry
from backend.agents.shared.logger import WorkflowLogger


def build_orchestrator(api_key: str) -> Orchestrator:
    """
    Build a fully-wired Orchestrator ready to run workflows.

    Inputs:
        api_key: LLM API key forwarded to every agent's constructor.
    Outputs:
        Orchestrator: instance backed by the default agent registry
            (ops, risk, audit, report) and a WorkflowLogger.
    """
    registry = AgentRegistry.build_default()
    logger = WorkflowLogger()
    return Orchestrator(registry, logger, api_key)


