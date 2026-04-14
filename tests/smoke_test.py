from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.state import AgentState


def test_agent_state_defaults() -> None:
    state = AgentState()

    assert state.messages == []
    assert state.user_input == ""
    assert state.intermediate_steps == []
