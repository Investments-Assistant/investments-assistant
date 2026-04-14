"""Agent package exports."""

from .state import AgentState

__all__ = ["create_investment_agent", "AgentState"]


def create_investment_agent(*args, **kwargs):
    from .investment_agent import create_investment_agent as _create_investment_agent

    return _create_investment_agent(*args, **kwargs)
