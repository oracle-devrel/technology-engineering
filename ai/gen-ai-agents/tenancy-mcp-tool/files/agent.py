import asyncio
import itertools
import json
import logging
import os
import streamlit as st
from datetime import datetime
from langchain.globals import set_debug, set_verbose
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_oci import ChatOCIGenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from oci_utils import list_models
from pprint import pprint
from dotenv import load_dotenv

from langgraph_callback import attempt_to_write_json, get_streamlit_cb

set_debug(False)
set_verbose(True)

load_dotenv()


DEFAULT_LLM = "cohere.command-latest"


COMPARTMENT_ID = os.getenv("COMPARTMENT_ID")


SYSTEM_PROMPT = """
You are a helpful assistant to answer details about the users tenancy with the
tools provided.

Make sure that you have the most recent date and time information before making
time-based queries.

Use the tools as documented, do not make up additonal arguments for tool calls.

When a tool requires a parameter in form of an OCID, always use OCID
identifiers from previous tool calls or specified by the user (starting with
ocid1...). Never generate OCID identifiers, query for them.

Use Markdown formatting for complex answers.  Take care to escape dollar signs
when you write currency.

Say "I cannot provide the required information" when you don't know.
"""


INITIAL_PROMPT = """
Hello there!

I am your tenancy assistant.  I can help you query resources with your tenancy,
perform simple tasks, and answer questions about OCI.

How can I help you today?
"""


@tool
def get_current_date() -> datetime:
    """Gets the current date."""
    return datetime.now()


@st.cache_resource
def build_graph(model_id):
    logging.info("Setting up MCP clients")
    client = MultiServerMCPClient({
        "documentation": {
            "command": "python",
            "args": ["oci_mcp_server.py"],
            "transport": "stdio",
        },
    })
    tools = asyncio.run(client.get_tools())
    tools = [get_current_date] + tools
    logging.info("Using LLM model '%s'", model_id)
    provider, _ = model_id.split(".", 1)

    model_kwargs = {}
    tool_kwargs = {}
    if provider == "cohere":
        model_kwargs["model_kwargs"] = {"max_tokens": 4_000}
    elif provider == "meta":
        tool_kwargs["tool_choice"] = "auto"

    model = ChatOCIGenAI(
        model_id=model_id,
        compartment_id=COMPARTMENT_ID,
        **model_kwargs,
        # is_stream=provider != "openai",
    )
    model_with_tools = model.bind_tools(
        tools,
        **tool_kwargs,
    )
    tool_node = ToolNode(tools)

    def _should_continue(state: MessagesState):
        if state["messages"][-1].tool_calls:
            return "tools"
        return END

    async def _call_model(state: MessagesState):
        return {
            "messages": await model_with_tools.ainvoke(state["messages"]),
        }

    logging.info("Building graph")
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", _call_model)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        _should_continue,
    )
    builder.add_edge("tools", "call_model")

    return builder.compile()


st.sidebar.title("Settings")

models = st.cache_data(list_models)(COMPARTMENT_ID)
model_idx = 0
if DEFAULT_LLM in models:
    model_idx = models.index(DEFAULT_LLM)

model = st.sidebar.selectbox("Model", models, model_idx)

graph = build_graph(model)


async def main():
    pprint(
        await graph.ainvoke({
            "messages": [{
                "role": "user",
                "content": "list the names of all buckets in my tenancy?"
            }]
        })
    )

# asyncio.run(main())

st.title("OCI Tenancy Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        AIMessage(content=INITIAL_PROMPT),
    ]

groups = itertools.groupby(st.session_state.messages,
                           key=lambda m: isinstance(m, HumanMessage))
for human, group in groups:
    group = [m for m in group if not isinstance(m, SystemMessage)]
    if human:
        for msg in group:
            st.chat_message("user").write(msg.content)
    elif group:
        with st.chat_message("assistant"):
            while group:
                msg = group.pop(0)
                if isinstance(msg, AIMessage):
                    if msg.content:
                        st.write(msg.content)
                    else:
                        for call in msg.tool_calls:
                            for idx, invocation in enumerate(group):
                                if (tcid := getattr(invocation, "tool_call_id")) == call["id"]:
                                    break
                            else:
                                continue

                            content = invocation.content
                            try:
                                content = json.loads(content)
                            except:
                                pass

                            if len(str(call["args"])) <= 60:
                                with st.status(
                                    label=f"**{call["name"]}:** {call["args"]}",
                                    state="complete",
                                ):
                                    attempt_to_write_json(st, content)
                            else:
                                with st.status(
                                    label=f"**{call["name"]
                                               }:** {str(call["args"])[:60]}...",
                                    state="complete",
                                ):
                                    st.markdown(
                                        f"**Input:**\n\n{call["args"]}\n\n**Output:**"
                                    )
                                    attempt_to_write_json(st, content)


if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        response = asyncio.run(
            graph.ainvoke(
                {"messages": st.session_state.messages},
                {"callbacks": [get_streamlit_cb(st.container())]},
            )
        )
        print("--------------")
        for msg in response["messages"]:
            print(type(msg))
        st.session_state.messages = response["messages"]
        last_message = response["messages"][-1]
        if isinstance(last_message, AIMessage):
            response_text = last_message.content
            st.markdown(response_text)
