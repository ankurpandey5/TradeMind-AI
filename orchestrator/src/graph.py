import datetime
import json
import sys

from langgraph.graph import StateGraph, END

# Centralized LLM configuration
from orchestrator.llm import get_llm

# Agent imports
from orchestrator.agents.opportunity_finder import execute_opportunity_search
from orchestrator.agents.compliance_agent import execute_compliance_check
from shared.schemas import AgentState

 
llm = get_llm(temperature=0)


# ============================================================
# 1. TASK ALLOCATOR
# ============================================================

def task_allocator(state: AgentState):

    if "compliance" in state["input_prompt"].lower():
        return {
            "target_agent": {
                "agent": "compliance_agent",
                "action": "check_compliance"
            }
        }

    return {
        "target_agent": {
            "agent": "opportunity_finder",
            "action": "add_opportunity"
        }
    }

# ============================================================
# 2. SPECIALIZED AGENT EXECUTION
# ============================================================

def call_specialized_agent(state: AgentState):

    agent = state["target_agent"]["agent"]

    if agent == "opportunity_finder":
        result = execute_opportunity_search(
            state["input_prompt"]
        )

    elif agent == "compliance_agent":
        result = execute_compliance_check(
            state["input_prompt"]
        )

    else:
        result = "No suitable agent found."

    return {
        "agent_raw_output": result
    }

# ============================================================
# 3. UI CONTROLLER
# ============================================================

def ui_controller(state: AgentState):
    """
    Converts the specialized agent's output into a
    standardized UI signal for the frontend.
    """

    raw_output = state["agent_raw_output"]
    agent = state["target_agent"]["agent"]

    print(
        f"\n[UI_CONTROLLER] Raw output from agent:\n"
        f"{raw_output}\n",
        file=sys.stderr
    )

    try:
        # Convert JSON string → Python dictionary
        parsed_data = json.loads(raw_output)

        print(
            "[UI_CONTROLLER] Successfully parsed JSON:\n"
            f"{json.dumps(parsed_data, indent=2)}",
            file=sys.stderr
        )

    except json.JSONDecodeError as e:

        print(
            f"[UI_CONTROLLER] JSON parse error: {e}",
            file=sys.stderr
        )

        # Different fallback depending on agent
        if agent == "opportunity_finder":
            parsed_data = {
                "message": "Opportunity analysis partially failed.",
                "opportunities": []
            }

        elif agent == "compliance_agent":
            parsed_data = {
                "message": "Compliance analysis partially failed.",
                "requirements": [],
                "certifications": [],
                "risks": []
            }

        else:
            parsed_data = {
                "message": "Analysis partially failed."
            }

    # --------------------------------------------------------
    # Opportunity Finder UI Signal
    # --------------------------------------------------------

    if agent == "opportunity_finder":

        signal = {
            "agent": agent,

            "action": "add_opportunity",

            "payload": {
                "message": parsed_data.get(
                    "message",
                    "Scouting complete."
                ),

                "opportunities": parsed_data.get(
                    "opportunities",
                    []
                ),

                "timestamp": datetime.datetime.now(
                    datetime.UTC
                ).isoformat()
            },

            "status": "success"
        }

    # --------------------------------------------------------
    # Compliance Agent UI Signal
    # --------------------------------------------------------

    elif agent == "compliance_agent":

        signal = {
            "agent": agent,

            "action": "add_compliance",

            "payload": {
                "message": parsed_data.get(
                    "message",
                    "Compliance analysis complete."
                ),

                "requirements": parsed_data.get(
                    "requirements",
                    []
                ),

                "certifications": parsed_data.get(
                    "certifications",
                    []
                ),

                "risks": parsed_data.get(
                    "risks",
                    []
                ),

                "timestamp": datetime.datetime.now(
                    datetime.UTC
                ).isoformat()
            },

            "status": "success"
        }

    # --------------------------------------------------------
    # Unknown Agent
    # --------------------------------------------------------

    else:

        signal = {
            "agent": agent,

            "action": "unknown",

            "payload": {
                "message": parsed_data.get(
                    "message",
                    "Agent completed the task."
                ),

                "timestamp": datetime.datetime.now(
                    datetime.UTC
                ).isoformat()
            },

            "status": "success"
        }

    print(
        "[UI_CONTROLLER] Final signal:\n"
        f"{json.dumps(signal, indent=2)}",
        file=sys.stderr
    )

    return {
        "ui_signals": [signal]
    }

# ============================================================
# 4. ASSEMBLE LANGGRAPH WORKFLOW
# ============================================================

workflow = StateGraph(AgentState)


# Add nodes
workflow.add_node(
    "allocator",
    task_allocator
)

workflow.add_node(
    "specialist",
    call_specialized_agent
)

workflow.add_node(
    "ui_controller",
    ui_controller
)


# Define workflow
workflow.set_entry_point("allocator")

workflow.add_edge(
    "allocator",
    "specialist"
)

workflow.add_edge(
    "specialist",
    "ui_controller"
)

workflow.add_edge(
    "ui_controller",
    END
)


# Compile graph
agentic_brain = workflow.compile()