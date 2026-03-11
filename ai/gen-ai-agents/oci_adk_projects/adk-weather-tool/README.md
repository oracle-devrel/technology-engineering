# OCI Weather Assistant API

A FastAPI-based service that integrates with Oracle Cloud Infrastructure's Generative AI Agent and uses OpenWeather API to provide real-time weather forecasts. The agent invokes the `get_weather` tool automatically when weather-related questions are asked.

**Author**: matsliwins

**Last review date**: 19/09/2025

![](files/images/ADK.png)

# When to use this asset?

Use this asset when you want to expose a simple HTTP API that answers weather questions by combining:

- an **OCI Generative AI Agent** (for conversation + tool orchestration), and
- the **OpenWeather API** (as the real-time weather data source)

It’s useful for demos, prototypes, and reference implementations of tool-calling with an OCI agent.

---

# How to use this asset?

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
```

2. Create a `.env` file in the root directory:

```env
OCI_AI_AGENT_ENDPOINT_ID=ocid1.generativeaiendpoint.oc1..example
OCI_CONFIG_PROFILE=DEFAULT
OCI_REGION=us-chicago-1
OPENWEATHER_API_KEY=your_openweather_api_key
```

3. Run the app:

```bash
uvicorn main:app --reload --port 8000
```

## UI

To test the API via a simple UI, use the frontend from this repository:  
🔗 https://github.com/ralungei/oci-genai-agent-blackbelt

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.  
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
