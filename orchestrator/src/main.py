import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Path injection: Ensure Python sees the project root G:\TradeMind-AI
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if root not in sys.path:
    sys.path.insert(0, root)

from orchestrator.src.graph import agentic_brain

app = FastAPI(title="TradeMind Workstation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    prompt: str


@app.post("/api/v1/execute")
async def handle_request(request: QueryRequest):
    state = {
        "input_prompt": request.prompt,
        "target_agent": "",
        "agent_raw_output": "",
        "ui_signals": []
    }

    final_state = agentic_brain.invoke(state)

    return {
        "signals": final_state["ui_signals"]
    }


@app.get("/health")
def health():
    return {
        "status": "online",
        "workstation": "TradeMind Laptop 2"
    }