import datetime
import json
import sys
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Absolute Imports to prevent path errors
from orchestrator.agents.opportunity_finder import execute_opportunity_search
from shared.schemas import AgentState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- 1. TASK ALLOCATOR ---
def task_allocator(state: AgentState):
    """Routes the prompt. For now, forces to opportunity_finder."""
    opportunity_finder = {"agent":"opportunity_finder",
                          "action":"add_opportunity"
                         }   


    return {"target_agent": opportunity_finder}

# --- 2. AGENT EXECUTION NODE ---
def call_specialized_agent(state: AgentState):
    """Calls the specialized logic based on the allocator's decision."""
    if state["target_agent"]["agent"] == "opportunity_finder":
        # Ensure function name matches the import above
        result = execute_opportunity_search(state["input_prompt"])
        return {"agent_raw_output": result}
    return {"agent_raw_output": "No suitable agent found."}

# --- 3. UI CONTROLLER ---
def ui_controller(state: AgentState):
    """Packages the result into a UISignal JSON for the frontend."""
    raw_output = state["agent_raw_output"]
    
    print(f"\n[UI_CONTROLLER] Raw output from agent:\n{raw_output}\n", file=sys.stderr)
    
    try:
        # 1. Parse the raw string into a Python Dictionary
        parsed_data = json.loads(raw_output)
        print(f"[UI_CONTROLLER] Successfully parsed JSON: {json.dumps(parsed_data, indent=2)}", file=sys.stderr)
    except json.JSONDecodeError as e:
        # Fallback if the LLM output is messy
        print(f"[UI_CONTROLLER] JSON parse error: {e}", file=sys.stderr)
        parsed_data = {
            "message": "Analysis partially failed. Raw data preserved.",
            "opportunities": []
        }

    # 2. Map the data into the Signal format your UI expects
    signal = {
        "agent": state["target_agent"]["agent"],  # Extract just the agent name
        "action": "add_opportunity",  # ✅ CORRECT action name for frontend
        "payload": {
            # THIS LINE FIXES THE MISSING MESSAGE:
            "message": parsed_data.get("message", "Scouting complete."), 
            "opportunities": parsed_data.get("opportunities", []),
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
        },
        "status": "success"
    }
    
    print(f"[UI_CONTROLLER] Final signal: {json.dumps(signal, indent=2)}", file=sys.stderr)
    
    # We return a list of signals so you can trigger multiple UI changes at once
    return {"ui_signals": [signal]}

# --- ASSEMBLE GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("allocator", task_allocator)
workflow.add_node("specialist", call_specialized_agent)
workflow.add_node("ui_controller", ui_controller)

workflow.set_entry_point("allocator")
workflow.add_edge("allocator", "specialist")
workflow.add_edge("specialist", "ui_controller")
workflow.add_edge("ui_controller", END)

agentic_brain = workflow.compile()