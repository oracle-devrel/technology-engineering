from __future__ import annotations

import os
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from oci.addons.adk import Agent, AgentClient, tool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

OCI_AI_AGENT_ENDPOINT_ID = os.getenv("OCI_AI_AGENT_ENDPOINT_ID")
OCI_CONFIG_PROFILE = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
OCI_REGION = os.getenv("OCI_REGION", "us-chicago-1")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

@tool
def get_weather(location: str, units: str = "metric") -> Dict[str, str]:
    """Return the current weather for *location* using OpenWeatherMap.

    Args:
        location: City name (e.g. "Seattle" or "Seattle,US").
        units:   Measurement system – "metric" (°C), "imperial" (°F), or
                  "standard" (Kelvin). Defaults to "metric".

    Returns:
        A dict ready for the agent response, containing temperature, unit,
        humidity, wind speed and a short description.
    """

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": units,
    }

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Weather service unavailable: {exc}") from exc

    data = resp.json()

    main = data["main"]
    weather = data["weather"][0]
    wind = data.get("wind", {})

    unit_symbol = {"metric": "°C", "imperial": "°F", "standard": "K"}.get(units, "°?")

    return {
        "location": location,
        "temperature": main["temp"],
        "unit": unit_symbol,
        "description": weather["description"],
        "humidity_percent": main.get("humidity"),
        "wind_speed_mps": wind.get("speed"),
    }


# ---------------------------------------------------------------------------
# FastAPI setup
# ---------------------------------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Agent setup (reuse from main)
# ---------------------------------------------------------------------------
if not OCI_AI_AGENT_ENDPOINT_ID:
    raise SystemExit("OCI_AI_AGENT_ENDPOINT_ID is not set. Check your .env file.")

client = AgentClient(
    auth_type="api_key",
    profile=OCI_CONFIG_PROFILE,
    region=OCI_REGION,
)

agent = Agent(
    client=client,
    agent_endpoint_id=OCI_AI_AGENT_ENDPOINT_ID,
    instructions=(
        "You are a helpful assistant that answers weather questions. "
        "Always invoke the get_weather tool when the user asks about the forecast."
    ),
    tools=[get_weather],
)

agent.setup()

# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str
    execute_functions: Optional[bool] = True
    session_id: Optional[str] = None

# ---------------------------------------------------------------------------
# /chat endpoint
# ---------------------------------------------------------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await agent.run_async(request.question)
        return {
            "answer": response.final_output,
            "session_id": request.session_id or "session123"
        }
    except Exception as e:
        return {"answer": str(e), "session_id": request.session_id or "session123"}


if __name__ == "__main__":
    main()
