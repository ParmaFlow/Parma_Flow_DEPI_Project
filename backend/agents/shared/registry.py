# backend/agents/shared/registry.py
"""
Agent registry supporting dependency injection.

The Orchestrator must never hardcode agent construction (e.g. `OpsAgent()`
inline). Instead, agent classes are registered here by name, and the
Orchestrator resolves/creates instances through the registry. This keeps
the Orchestrator decoupled from concrete agent implementations and makes
it trivial to swap or mock agents in tests.
"""
from typing import Callable, Dict, Type

from backend.agents.shared.base_agent import BaseAgent
from backend.agents.shared.exceptions import AgentError
from backend.agents.ops_agent.ops_agent import OpsAgent
from backend.agents.risk_agent.risk_agent import RiskAgent
from backend.agents.auditor_agent.auditor_agent import AuditorAgent
from backend.agents.report_agent.report_agent import ReportAgent


class AgentNotRegisteredError(AgentError):
    """Raised when the registry is asked to resolve an unknown agent name."""


class AgentRegistry:
    """
    Registry mapping agent names to agent classes.

    Usage:
        registry = AgentRegistry.build_default()
        ops_agent = registry.create("ops", api_key)
    """

    def __init__(self) -> None:
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def build_default(cls) -> "AgentRegistry":
        """
        Build a registry pre-populated with all standard Pharma-Flow
        agents (ops, risk, audit, report).

        Centralizing registration here means callers (e.g. bootstrap.py,
        QueryService) never need to know which concrete agent classes
        exist — they just ask for a ready-to-use registry.

        Inputs:
            None.
        Outputs:
            AgentRegistry: registry with "ops", "risk", "audit", "report"
                registered to their respective agent classes.
        """
        registry = cls()
        registry.register("ops", OpsAgent)
        registry.register("risk", RiskAgent)
        registry.register("audit", AuditorAgent)
        registry.register("report", ReportAgent)
        return registry

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class under a given name.

        Inputs:
            name: unique identifier for the agent (e.g. "ops").
            agent_class: the agent's class (subclass of BaseAgent), not an
                instance.
        Outputs:
            None.
        """
        self._agent_classes[name] = agent_class

    def create(self, name: str, *args, **kwargs) -> BaseAgent:
        """
        Instantiate a registered agent by name.

        Inputs:
            name: identifier previously passed to register().
            *args, **kwargs: forwarded to the agent class constructor
                (e.g. api_key).
        Outputs:
            BaseAgent: a new instance of the registered agent class.
        Raises:
            AgentNotRegisteredError: if no agent was registered under name.
        """
        agent_class = self._resolve(name)
        return agent_class(*args, **kwargs)

    def get_class(self, name: str) -> Callable[..., BaseAgent]:
        """
        Retrieve the registered class (not an instance) for a given name.

        Inputs:
            name: identifier previously passed to register().
        Outputs:
            Type[BaseAgent]: the registered agent class.
        Raises:
            AgentNotRegisteredError: if no agent was registered under name.
        """
        return self._resolve(name)

    def _resolve(self, name: str) -> Type[BaseAgent]:
        if name not in self._agent_classes:
            raise AgentNotRegisteredError(
                f"No agent registered under name '{name}'."
            )
        return self._agent_classes[name]