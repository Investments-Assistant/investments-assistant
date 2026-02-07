from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """State for the investment analysis agent."""
    
    messages: List[Dict[str, str]] = Field(default_factory=list, description="Conversation history")
    user_input: str = Field(description="Current user input")
    intermediate_steps: List[tuple] = Field(default_factory=list, description="Agent reasoning steps")
    output: Optional[str] = Field(default=None, description="Final agent output")
    analysis_data: Optional[Dict[str, Any]] = Field(default=None, description="Structured analysis data")
    
    class Config:
        arbitrary_types_allowed = True
