"""
FastAPI server for the travel agent example using LangChain.
This server provides a simple chat interface to interact with the travel agent.
"""

import json
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from workflow import create_travel_planner_graph
from travel_state import TravelState
from utils import get_console_logger

MEDIA_TYPE = "application/json"

app = FastAPI()

# here we create the graph
travel_agent_graph = create_travel_planner_graph()

logger = get_console_logger("agent_fastapi_logger", level="INFO")


async def stream_graph_updates(user_input: str):
    """
    Stream the updates from the travel agent graph.
    Args:
        user_input (str): User input for the travel agent.
    Yields:
        str: JSON string of the step output.
    """
    # prepare the input
    state = TravelState(user_input=user_input)

    # here we call the agent and return the state
    # update the state with the user input
    async for step_output in travel_agent_graph.astream(state):
        # using stream with LangGraph returns state updates
        # for each node in the graph
        # yield returns the state update
        yield json.dumps(step_output) + "\n"


@app.get("/invoke")
async def invoke(user_input: str = Query(...)):
    """
    endpoint to interact with the travel agent.
    Args:
        user_input (str): User input for the travel agent.
    Returns:
        StreamingResponse: Stream of JSON responses from the travel agent.
    """
    logger.info("Invoked Agent API...")

    return StreamingResponse(stream_graph_updates(user_input), media_type=MEDIA_TYPE)
