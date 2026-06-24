"""
Explore an MCP server and get list and description of tools.

The server must be accessible through HTTP streaming.
"""

import asyncio
import streamlit as st
from fastmcp import Client

from oci_jwt_client import OCIJWTClient
from utils import get_console_logger
from config import DEBUG, ENABLE_JWT_TOKEN, IAM_BASE_URL
from config_private import SECRET_OCID
from mcp_servers_config import MCP_SERVERS_CONFIG

# the scope for the JWT token
SCOPE = "urn:opc:idm:__myscopes__"

logger = get_console_logger()

st.set_page_config(page_title="MCP Explorer", layout="wide")
st.title("🚀 MCP Tool Explorer")

# Config
DEFAULT_URL = MCP_SERVERS_CONFIG["default"]["url"]
server_url = st.text_input("URL MCP:", DEFAULT_URL)
TIMEOUT = 30

# Session state
if "tools" not in st.session_state:
    st.session_state.tools = []
if "error" not in st.session_state:
    st.session_state.error = None


async def fetch_tools():
    """
    This function call the MCP server to get list and descriptions of tools
    """
    if ENABLE_JWT_TOKEN:
        # this is a client to OCI IAM to get the JWT token
        logger.info("----------------------------")
        logger.info("--- Using JWT based auth ---")
        logger.info("----------------------------")
        logger.info("Getting JWT token...")

        client_4_token = OCIJWTClient(IAM_BASE_URL, SCOPE, SECRET_OCID)

        token, _, _ = client_4_token.get_token()

        if DEBUG:
            logger.info("Token: %s", token)
            logger.info("Scope: %s", SCOPE)
            logger.info("IAM Base URL: %s", IAM_BASE_URL)

        logger.info("")

        client = Client(server_url, auth=token, timeout=TIMEOUT)
    else:
        client = Client(server_url, timeout=TIMEOUT)

    async with client:
        # get the list of available tools
        logger.info("Fetching tools from MCP server...")
        return await client.list_tools()


if st.button("🔍 Load tools..."):
    st.session_state.error = None
    st.session_state.tools = []
    with st.spinner("Calling server…"):
        try:
            tools = asyncio.run(fetch_tools())
            st.session_state.tools = tools
        except Exception as e:
            st.session_state.error = e

# Visualize
if st.session_state.error:
    st.error(f"❌ Error: {st.session_state.error}. Is the URL correct?")
elif st.session_state.tools:
    st.success(f"✅ {len(st.session_state.tools)} tools found.")
    cols = st.columns(3)

    for i, t in enumerate(st.session_state.tools):
        with cols[i % 3]:
            st.markdown(f"### **{t.name}**")
            if t.description:
                st.write(t.description)
            if t.inputSchema:
                with st.expander("📘 Input Schema"):
                    st.json(t.inputSchema)
            if t.outputSchema:
                with st.expander("📗 Output Schema"):
                    st.json(t.outputSchema)
            st.divider()
