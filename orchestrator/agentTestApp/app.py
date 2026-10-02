import streamlit as st
import sys
import os

# Absolute Path Fix to Project Root (G:\TradeMind-AI)
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Import the brain using the full package path
try:
    from orchestrator.src.graph import agentic_brain
except ImportError as e:
    st.error(f"Structural Error: {e}")
    st.stop()

st.set_page_config(page_title="TradeMind | Brain Lab", layout="wide")
st.title("🤖 TradeMind Agentic Workstation")
st.subheader("Neural Test Environment (Laptop 2)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter trade command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Brain Orchestrating..."):
            try:
                initial_state = {
                    "input_prompt": prompt,
                    "target_agent": "",
                    "agent_raw_output": "",
                    "ui_signals": []
                }

                final_state = agentic_brain.invoke(initial_state)

                response_text = final_state.get(
                    "agent_raw_output",
                    "Agent failed to respond."
                )

                st.markdown(response_text)

                with st.expander("📡 Raw UI Signals (Zustand Context)"):
                    st.json(final_state.get("ui_signals", []))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })

            except Exception as e:
                st.error(f"Execution Error: {str(e)}")