from pydantic import BaseModel, Field

from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

class InputState(BaseModel):
    pass


class OverallState(AgentStatePydantic, InputState):
    is_chitchat: bool = Field(default=False)
    chitchat_rationale: str = Field(default="")
    
    search_plan: dict = Field(default={})
    search_result: dict = Field(default={})