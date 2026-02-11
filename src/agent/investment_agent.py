"""Minimal investment agent that uses `LLMClient` to generate responses.

This module provides a `create_investment_agent` factory used by the Streamlit
app. The agent exposes an `invoke(state: AgentState) -> dict` method that
returns a dict containing an `output` key with the assistant response.
"""

from typing import Optional, Dict, Any

from src.agent.clients.llm_client import LLMClient
from src.config import config
from .state import AgentState


class InvestmentAgent:
    def __init__(self, llm_client: LLMClient, temperature: Optional[float] = None):
        self.llm = llm_client
        self.temperature = temperature

    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Run the agent on the provided state and return a result dict.

        Currently this implementation sends the `user_input` as the prompt to
        the underlying `LLMClient` and returns the assistant text under
        the `output` key. This is intentionally simple and easy to extend.
        """

        prompt = state.user_input or "\n".join(
            [m.get("content", "") for m in state.messages]
        )

        response = self.llm.invoke(
            prompt,
            temperature=self.temperature,
            max_tokens=config.AGENT_MAX_TOKENS,
        )

        return {"output": response}


def create_investment_agent(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> InvestmentAgent:
    llm = LLMClient(api_key=api_key, model=model)
    return InvestmentAgent(llm_client=llm, temperature=temperature)
