import streamlit as st
import json
import time
from assistant import TOOLS, router, state

# ==============================
#  STREAMLIT UI CONFIGURATION
# ==============================
st.set_page_config(page_title="OCI Assistant Chatbot", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>OCI Assistant Chatbot</h1>",
    unsafe_allow_html=True
)
st.write("Manage your emails, schedule meetings, check the weather, and more...")

# ==============================
#  INITIALIZE SESSION STATE
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_email" not in st.session_state:
    st.session_state.selected_email = None

if "latest_response" not in st.session_state:
    st.session_state.latest_response = ""

# ==============================
#  CHATBOT INTERFACE
# ==============================

# Display chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["bot"])

# User input field
user_input = st.text_input("Type your message here...", key="user_input")

# Process user message
if st.button("Send"):
    if user_input:
        # Display steps
        step_placeholder = st.empty()  # This will dynamically update
        step_placeholder.markdown("🟢 **Step 1:** Capturing user input...")

        # Update state with user input
        state["input"] = user_input

        # Display second step
        step_placeholder.markdown("🟢 **Step 2:** Identifying the correct tool...")

        # Show spinner while routing
        with st.spinner("Processing..."):
            time.sleep(1)  # Simulating delay

            # Route input to the correct function
            routing_result = router.route(state)
            state["decisions"] = routing_result.get("decisions", [])

        # Show detected decisions
        step_placeholder.markdown(f"🟢 **Step 3:** Decision made → `{state['decisions']}`")

        # Execute tool functions
        responses = []
        for i, decision in enumerate(state["decisions"], start=1):
            step_placeholder.markdown(f"🟢 **Step 4.{i}:** Executing `{decision}`...")

            tool = TOOLS.get(decision)
            if tool:
                with st.spinner(f"Running `{decision}`..."):
                    time.sleep(1)  # Simulate processing time
                    result = tool(state)
                    responses.append(result["output"])
            else:
                responses.append(f"❌ Invalid decision: `{decision}`.")

        # Finalize response
        step_placeholder.markdown("✅ **Step 5:** Formatting response...")

        # Store response
        state["output"] = "\n\n".join(
            [json.dumps(resp, indent=2) if isinstance(resp, list) else str(resp) for resp in responses]
        )

        # Update chat history
        st.session_state.chat_history.append({"user": user_input, "bot": state["output"]})

        # Store latest response
        st.session_state.latest_response = state["output"]

        # Refresh UI
        st.rerun()
