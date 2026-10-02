from typing import List, Dict, Optional, TypedDict
from pydantic import BaseModel

class AgentState(TypedDict):
    input_prompt: str
    target_agent: str
    agent_raw_output: str
    ui_signals: List[Dict]

class UISignal(BaseModel):
    agent_id: str
    action: str
    payload: Dict
    status: str