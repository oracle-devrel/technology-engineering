"""
Streamlit UI for MCP servers
"""

import asyncio
import traceback
import streamlit as st
from config import MODEL_LIST
from mcp_servers_config import MCP_SERVERS_CONFIG

# this one contains the backend and the test code only for console
from llm_with_mcp import AgentWithMCP, default_jwt_supplier

from utils import get_console_logger

logger = get_console_logger()

# ---------- Page setup ----------
st.set_page_config(page_title="MCP UI", page_icon="🛠️", layout="wide")
st.title("🛠️ LLM powered by MCP")

# ---------- Sidebar: connection settings ----------
with st.sidebar:
    st.header("Connection")
    mcp_url = st.text_input("MCP URL", value=MCP_SERVERS_CONFIG["default"]["url"])

    model_id = st.selectbox(
        "Model",
        MODEL_LIST,
        index=0,
    )
    timeout = st.number_input(
        "Timeout (s)", min_value=5, max_value=300, value=60, step=5
    )

    connect = st.button("🔌 Connect / Reload tools", use_container_width=True)

# ---------- Session state ----------
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat" not in st.session_state:
    # list of {"role": "user"|"assistant", "content": str}
    st.session_state.chat = []


def reset_conversation():
    """Reset the chat history."""
    st.session_state.chat = []


# ---------- Connect / reload ----------
if connect:
    with st.spinner("Connecting to MCP server and loading tools…"):
        try:
            # Create an agent (async factory) and cache it in session_state
            st.session_state.agent = asyncio.run(
                AgentWithMCP.create(
                    mcp_url=mcp_url,
                    # returns a fresh raw JWT
                    jwt_supplier=default_jwt_supplier,
                    timeout=timeout,
                    model_id=model_id,
                )
            )
            st.success("Connected. Tools loaded.")
        except Exception as e:
            st.session_state.agent = None
            st.error(f"Failed to connect: {e}")
            logger.error(e)
            STACK_STR = traceback.format_exc()
            logger.error(STACK_STR)

# Reset button
if st.sidebar.button("Clear Chat History"):
    reset_conversation()

# ---------- Chat history (display) ----------
for msg in st.session_state.chat:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(msg["content"])

# ---------- Input box ----------
prompt = st.chat_input("Ask your question…")

if prompt:
    # Show the user message immediately
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.agent is None:
        st.warning(
            "Not connected. Click ‘Connect / Reload tools’ in the sidebar first."
        )
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking with support from MCP tools…"):
                try:
                    ANSWER = asyncio.run(
                        # we pass also the history (chat)
                        st.session_state.agent.answer(prompt, st.session_state.chat)
                    )
                except Exception as e:
                    ANSWER = f"Error: {e}"
                st.write(ANSWER)
                st.session_state.chat.append({"role": "assistant", "content": ANSWER})

# ---------- The small debug panel in the bottom ----------
with st.expander("🔎 Debug / State"):
    st.json(
        {
            "connected": st.session_state.agent is not None,
            "messages_in_memory": len(st.session_state.chat),
            "mcp_url": mcp_url,
            "model_id": model_id,
            "timeout": timeout,
        }
    )
