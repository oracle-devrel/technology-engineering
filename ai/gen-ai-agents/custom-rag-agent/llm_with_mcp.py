"""
Test LLM and MCP
Based on fastmcp library.
This one provide also support for security in MCP calls, using JWT token.

This is the backend for the Streamlit MCP UI.
"""

import json
import asyncio
from typing import List, Dict, Any, Callable, Sequence, Optional

from fastmcp import Client as MCPClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

# our code imports
from oci_jwt_client import OCIJWTClient
from oci_models import get_llm
from utils import get_console_logger
from config import IAM_BASE_URL, ENABLE_JWT_TOKEN
from config_private import SECRET_OCID
from mcp_servers_config import MCP_SERVERS_CONFIG

logger = get_console_logger()

# ---- Config ----
MAX_HISTORY = 10
MCP_URL = MCP_SERVERS_CONFIG["default"]["url"]
TIMEOUT = 60
# the scope for the JWT token
SCOPE = "urn:opc:idm:__myscopes__"

# eventually you can taylor the SYSTEM prompt here
SYSTEM_PROMPT = """You are an AI assistant equipped with an MCP server and several tools.
Provide all the needed information with a detailed query when you use a tool.
If the collection name is not provided in the user's prompt, 
use the collection BOOKS to get the additional information you need to answer.
"""


def default_jwt_supplier() -> str:
    """
    Get a valid JWT token to make the call to MCP server
    """
    if ENABLE_JWT_TOKEN:
        # Always return a FRESH token; do not include "Bearer " (FastMCP adds it)
        token, _, _ = OCIJWTClient(IAM_BASE_URL, SCOPE, SECRET_OCID).get_token()
    else:
        # JWT security disabled
        token = None
    return token


class AgentWithMCP:
    """
    LLM + MCP orchestrator.
    - Discovers tools from an MCP server (JWT-protected)
    - Binds tool JSON Schemas to the LLM
    - Executes tool calls emitted by the LLM and loops until completion

    This is a rather simple agent, it does only tool calling,
    but tools are provided by the MCP server.
    The code introspects the MCP server and decide which tool to call
    and what parameters to provide.
    """

    def __init__(
        self,
        mcp_url: str,
        jwt_supplier: Callable[[], str],
        timeout: int,
        llm,
    ):
        self.mcp_url = mcp_url
        self.jwt_supplier = jwt_supplier
        self.timeout = timeout
        self.llm = llm
        self.model_with_tools = None
        # optional: cache tools to avoid re-listing every run
        self._tools_cache = None

    # ---------- helpers now INSIDE the class ----------

    @staticmethod
    def _tool_to_schema(t: object) -> dict:
        """
        Convert an MCP tool (name, description, inputSchema) to a JSON-Schema dict
        that LangChain's ChatCohere.bind_tools accepts (top-level schema).
        """
        input_schema = (getattr(t, "inputSchema", None) or {}).copy()
        if input_schema.get("type") != "object":
            input_schema.setdefault("type", "object")
            input_schema.setdefault("properties", {})
        return {
            "title": getattr(t, "name", "tool"),
            "description": getattr(t, "description", "") or "",
            **input_schema,
        }

    async def _list_tools(self):
        """
        Fetch tools from the MCP server using FastMCP. Must be async.
        """
        jwt = self.jwt_supplier()
        
        logger.info("Listing tools from %s ...", self.mcp_url)

        # FastMCP requires async context + await for client ops.
        async with MCPClient(self.mcp_url, auth=jwt, timeout=self.timeout) as c:
            # returns Tool objects
            return await c.list_tools()

    async def _call_tool(self, name: str, args: Dict[str, Any]):
        """
        Execute a single MCP tool call.
        """
        jwt = self.jwt_supplier()
        logger.info("Calling MCP tool '%s' with args %s", name, args)
        async with MCPClient(self.mcp_url, auth=jwt, timeout=self.timeout) as c:
            return await c.call_tool(name, args or {})

    @classmethod
    async def create(
        cls,
        mcp_url: str = MCP_URL,
        jwt_supplier: Callable[[], str] = default_jwt_supplier,
        timeout: int = TIMEOUT,
        model_id: str = "cohere.command-a-03-2025",
    ):
        """
        Async factory: fetch tools, bind them to the LLM, return a ready-to-use agent.
        Important: Avoids doing awaits in __init__.
        """
        # should return a LangChain Chat model supporting .bind_tools(...)
        llm = get_llm(model_id=model_id)
        # after, we call init()
        self = cls(mcp_url, jwt_supplier, timeout, llm)

        tools = await self._list_tools()
        if not tools:
            logger.warning("No tools discovered at %s", mcp_url)
        self._tools_cache = tools

        schemas = [self._tool_to_schema(t) for t in tools]
        self.model_with_tools = self.llm.bind_tools(schemas)
        return self

    def _build_messages(
        self,
        history: Sequence[Dict[str, Any]],
        system_prompt: str,
        current_user_prompt: str,
        *,
        max_history: Optional[
            int
        ] = MAX_HISTORY,  # keep only the last N items; None = keep all
        exclude_last: bool = True,  # drop the very last history entry before building
    ) -> List[Any]:
        """
        Create: [SystemMessage(system_prompt), <trimmed history except last>,
        HumanMessage(current_user_prompt)]
        History items are dicts like {"role": "user"|"assistant", "content": "..."}
        in chronological order.
        """
        # 1) Trim to the last `max_history` entries (if set)
        if max_history is not None and max_history > 0:
            working = list(history[-max_history:])
        else:
            working = list(history)

        # 2) Optionally remove the final entry from trimmed history
        if exclude_last and working:
            working = working[:-1]

        # 3) Build LangChain messages
        msgs: List[Any] = [SystemMessage(content=system_prompt)]
        for m in working:
            role = (m.get("role") or "").lower()
            content: Optional[str] = m.get("content")
            if not content:
                continue
            if role == "user":
                msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                msgs.append(AIMessage(content=content))
            # ignore other/unknown roles (e.g., 'system', 'tool') in this simple variant

        # 4) Add the current user prompt
        msgs.append(HumanMessage(content=current_user_prompt))
        return msgs

    #
    # ---------- main loop ----------
    #
    async def answer(self, question: str, history: list = None) -> str:
        """
        Run the LLM+MCP loop until the model stops calling tools.
        """
        messages = self._build_messages(
            history=history,
            system_prompt=SYSTEM_PROMPT,
            current_user_prompt=question,
        )

        # List[Any] = [
        #    SystemMessage(content=SYSTEM_PROMPT),
        #    HumanMessage(content=question),
        # ]

        while True:
            ai: AIMessage = await self.model_with_tools.ainvoke(messages)

            tool_calls = getattr(ai, "tool_calls", None) or []
            if not tool_calls:
                # Final answer
                return ai.content

            messages.append(ai)  # keep the AI msg that requested tools

            # Execute tool calls and append ToolMessage for each
            for tc in tool_calls:
                name = tc["name"]
                args = tc.get("args") or {}
                try:
                    # here we call the tool
                    result = await self._call_tool(name, args)
                    payload = (
                        getattr(result, "data", None)
                        or getattr(result, "content", None)
                        or str(result)
                    )
                    messages.append(
                        ToolMessage(
                            content=json.dumps(payload),
                            # must match the call id
                            tool_call_id=tc["id"],
                            name=name,
                        )
                    )
                except Exception as e:
                    messages.append(
                        ToolMessage(
                            content=json.dumps({"error": str(e)}),
                            tool_call_id=tc["id"],
                            name=name,
                        )
                    )


# ---- Example CLI usage ----
# this code is good for CLI, not Streamlit. See ui_mcp_agent.py
if __name__ == "__main__":
    QUESTION = "Tell me about Luigi Saetta. I need his e-mail address also."
    agent = asyncio.run(AgentWithMCP.create())
    print(asyncio.run(agent.answer(QUESTION)))
