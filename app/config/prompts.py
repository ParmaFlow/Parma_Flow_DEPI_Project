# app/config/prompts.py
"""
DEPRECATED — this module is no longer used.

The PHARMA_AGENT_PROMPT defined here was the system prompt for the old
single-agent architecture where the LLM was asked to:
  - Calculate inventory gaps (arithmetic)
  - Determine HUMAN_REVIEW thresholds
  - Set the risk_level and action autonomously

This violates the Explainable AI contract of the current multi-agent
system, where ALL calculations are performed deterministically in Python
and the LLM is used ONLY for explanation text generation.

DO NOT import or reuse this prompt.  It will be removed in the next sprint.

The replacement prompts live in each agent's own module:
    backend/agents/ops_agent/prompt.py       → OPS_AGENT_PROMPT
    backend/agents/risk_agent/prompt.py      → RISK_AGENT_PROMPT
    backend/agents/auditor_agent/prompt.py   → AUDITOR_AGENT_PROMPT
    backend/agents/report_agent/prompt.py    → REPORT_AGENT_PROMPT
"""
import warnings

warnings.warn(
    "app.config.prompts (PHARMA_AGENT_PROMPT) is deprecated and unused. "
    "See backend/agents/*/prompt.py for current agent prompts.",
    DeprecationWarning,
    stacklevel=2,
)