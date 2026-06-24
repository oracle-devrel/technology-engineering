"""
RAG Agent API

Expose the RAG agent as a REST API using FastAPI

For now it is not supporting chat_history
"""

import uuid
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag_agent import create_workflow
from agent_state import State
from utils import get_console_logger
from config import DEBUG, DEFAULT_COLLECTION, LLM_MODEL_ID, EMBED_MODEL_TYPE

MEDIA_TYPE = "application/json"


class InvokeRequest(BaseModel):
    """
    This class represent the input
    """

    user_input: str


app = FastAPI()

# here we create the graph
agent_graph = create_workflow()

logger = get_console_logger("rag_agent_logger", level="INFO")


def safe_json(data):
    """
    To help serialize the generator
    """

    def default_serializer(obj):
        try:
            return str(obj)
        except Exception:
            return "unserializable"

    return json.dumps(data, default=default_serializer)


def generate_request_id():
    """
    Generate a unique request id

    Returns:
        str: A unique identifier for the request.
    """
    return str(uuid.uuid4())


async def stream_graph_updates(user_input: str, config=None):
    """
    Stream the updates from the rag agent graph.
    Args:
        user_input (str): User input for the agent.
    Yields:
        str: JSON string of the step output.
    """
    # prepare the input
    state = State(user_request=user_input, chat_history=[])

    # here we call the agent and return the state
    # update the state with the user input
    async for step_output in agent_graph.astream(state, config=config):
        # using stream with LangGraph returns state updates
        # for each node in the graph
        yield safe_json(step_output) + "\n"


@app.post("/invoke")
async def invoke(request: InvokeRequest):
    """
    POST endpoint to interact with the agent.
    Args:
        request (InvokeRequest): Contains the user_input as JSON body.
    Returns:
        StreamingResponse: Stream of JSON responses from the agent.
    """
    _thread_id = generate_request_id()
    _config = {
        "configurable": {
            "model_id": LLM_MODEL_ID,
            "embed_model_type": EMBED_MODEL_TYPE,
            "enable_reranker": True,
            "enable_tracing": False,
            "collection_name": DEFAULT_COLLECTION,
            "thread_id": _thread_id,
            "main_language": "same as the question",
        }
    }

    if DEBUG:
        logger.info("Invoked Agent API with config: %s", _config)

    try:
        # added to make it more reliable
        return StreamingResponse(
            stream_graph_updates(request.user_input, _config), media_type=MEDIA_TYPE
        )
    except Exception as e:
        logger.error("Error in invoke endpoint: %s", e)
        return {"error": str(e)}
