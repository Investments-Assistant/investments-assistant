from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agent.clients.llm_client import LLMClient


class ChatState(TypedDict):
    user_input: str
    response: str


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    """Lazily initialize and cache the LLM client."""
    global _llm

    if _llm is None:
        _llm = LLMClient()

    return _llm


def call_model(state: ChatState) -> ChatState:
    llm = get_llm()

    text = llm.invoke(
        state["user_input"],
        system_message="You are a helpful assistant.",
    )

    return {
        "user_input": state["user_input"],
        "response": text,
    }


def build_graph():
    builder = StateGraph(ChatState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    builder.add_edge("call_model", END)

    return builder.compile()


graph = build_graph()
