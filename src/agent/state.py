"""Simple Agent state representation used by the investment agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AgentState:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_input: str = ""
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
