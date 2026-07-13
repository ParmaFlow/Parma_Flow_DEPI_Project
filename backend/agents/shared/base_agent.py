# backend/agents/shared/base_agent.py
"""
Base class for all agents in the Pharma-Flow multi-agent architecture.

Provides a common contract (run()) that every specialized agent
(OpsAgent, RiskAgent, AuditorAgent, ReportAgent, ...) must implement,
enabling the future Orchestrator to interact with any agent uniformly.
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract parent class for all agents.

    Enforces that every agent exposes a single public entry point, run(),
    regardless of its internal implementation details.
    """

    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Execute the agent's primary responsibility.

        Inputs:
            Implementation-specific (defined by each concrete agent).
        Outputs:
            Implementation-specific structured result (e.g. a dataclass
            from backend.agents.shared.models).
        """
        raise NotImplementedError


