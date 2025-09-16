"""
Test client for the FastAPI agent.
This client sends a request to the FastAPI agent and prints the response.
"""

import asyncio
import json
import httpx
from utils import get_console_logger
from config import AGENT_API_URL

logger = get_console_logger("agent_fastapi_client_logger", level="INFO")


async def stream_invoke(_user_input: str):
    """
    Stream the chat with the agent.
    Args:
        user_input (str): User input for the travel agent.
    """
    # Prepare the input
    params = {"user_input": _user_input}

    async with httpx.AsyncClient(timeout=None) as client:
        print("--------------------")
        print("Streaming response:")
        print("--------------------")

        async with client.stream("GET", AGENT_API_URL, params=params) as response:
            async for line in response.aiter_lines():
                if line.strip():  # skip empty lines
                    try:
                        data = json.loads(line)

                        for key, value in data.items():
                            # key here is the name of the node
                            logger.info("Step: %s completed...", key)

                            if key == "synthesize_plan":
                                print("")
                                print(value["final_plan"])
                            if key == "generate_itinerary":
                                print("")
                                print(value["itinerary"])

                    except json.JSONDecodeError as e:
                        print("Failed to parse JSON:", e)


if __name__ == "__main__":

    USER_INPUT = """I want to go from Rome to Florence
    from June 10 to June 15 with my partner.
    I want to go by train and I need a hotel in the city center."""

    print("--------------------")
    print("User input:")
    print(USER_INPUT)
    print("--------------------")

    asyncio.run(stream_invoke(USER_INPUT))
