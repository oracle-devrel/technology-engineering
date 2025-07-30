# OCI Weather Assistant API

A FastAPI-based service that integrates with Oracle Cloud Infrastructure's Generative AI Agent and uses OpenWeather API to provide real-time weather forecasts. The agent invokes the `get_weather` tool automatically when weather-related questions are asked.

## Features

- FastAPI backend with async support
- OCI Generative AI Agent integration
- Weather tool using OpenWeather API
- `.env` configuration for secrets

## Setup

1. Clone the repo & install dependencies:

```bash
git clone https://github.com/your-username/oci-weather-assistant.git
cd oci-weather-assistant
pip install -r requirements.txt

## Create a .env file in the root directory:

OCI_AI_AGENT_ENDPOINT_ID=ocid1.generativeaiendpoint.oc1..example
OCI_CONFIG_PROFILE=DEFAULT
OCI_REGION=us-chicago-1
OPENWEATHER_API_KEY=your_openweather_api_key

## Run the app

uvicorn main:app --reload --port 8000

## UI

To test the API via a simple UI, use the frontend from this repository:
🔗 https://github.com/ralungei/oci-genai-agent-blackbelt
