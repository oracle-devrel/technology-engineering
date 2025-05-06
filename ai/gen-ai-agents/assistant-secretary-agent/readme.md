# Assistant Secretary Agent

An AI-powered assistant that routes user input across tools like Gmail, Google Calendar, Weather API, Calculator, and Oracle’s Generative AI services for smart, dynamic task automation.

Reviewed: 23.04.2025

# When to use this asset?

Use this asset when you want to:
- Automate tasks across Gmail, Calendar, and Weather  
- Get answers via OCI’s AI Agents and RAG-powered chat  
- Use a simple UI to interact with multiple tools seamlessly  
- Demo a multi-tool assistant combining local logic and cloud intelligence  

Ideal for:
- AI developers building assistants  
- Showcasing GenAI + agent capabilities  
- Technical users exploring LLM + API routing in real-world use cases  

# How to use this asset?

This assistant can be launched via:
- Terminal (CLI mode)  
- Streamlit UI for visual interaction  

It supports:
- Reading and replying to emails  
- Summarizing or replying smartly using GenAI  
- Scheduling calendar events  
- Fetching and advising based on weather  
- Answering user queries via RAG and fallback GenAI tools  

## Setup Instructions

### OCI Generative AI (Cohere on OCI)

1. Go to OCI Console → Generative AI  
2. Select a model like `cohere.command-r-plus-08-2024`  
3. Copy the following values:  
   - model_id  
   - compartment_id  
   - endpoint (e.g., `https://inference.generativeai.us-chicago-1.oci.oraclecloud.com`)  
4. Paste these in `oci_models.py`  

[OCI GenAI Agent Guide](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/overview.htm)

Also create an AI Agent in OCI with a knowledge base, and upload your RAG documents into that knowledge base.

### Google API (Gmail + Calendar)

1. Go to [Google Cloud Console](https://console.cloud.google.com)  
2. Enable the Gmail API and Calendar API  
3. Create OAuth 2.0 Credentials and download `credentials.json`  
4. Place `credentials.json` in your project root  
5. The first time you run the assistant, a `token.json` will be created automatically  

### Weather API

1. Sign up at [weatherapi.com](https://www.weatherapi.com/)  
2. Get a free API key  
3. In `tools.py`, update this line with your key:  
```python
WEATHER_API_KEY = "your_api_key_here"
```

### Start the Assistant

Terminal Mode:
```bash
python assistant.py
```

Streamlit UI:
```bash
streamlit run frontend.py
```

## Key Features

| Tool               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Fetch Gmail        | Retrieves and summarizes unread emails                                      |
| Select Email       | Shows full email body                                                       |
| OCI AI Agent (RAG) | Answers based on Oracle AI Agent + RAG knowledge base                       |
| Smart Replies      | Drafts professional responses with OCI GenAI                               |
| Send Email         | Sends reply to the original sender                                          |
| Schedule Emails    | Delays email sending using background job                                  |
| Weather + Advice   | Gives weather report with clothing suggestion                              |
| Book Meetings      | Creates Google Calendar events and checks weather for that date            |
| Fallback Q&A       | Handles general questions using OCI GenAI                                  |
| Calculator         | Parses and evaluates math queries                                           |

## Notes

- The assistant dynamically routes user queries using Cohere (hosted on OCI)  
- Each tool is modular — easy to extend or replace  
- Streamlit UI provides real-time visibility on tool routing  

## Update Email Mappings (Required)

To match received emails to locations (for RAG/OCI agent logic), update:

At line 397 in the code:
```python
EMPLOYEE_DATA = {
    "example example <example@example.com>": "Netherlands",
    "example 2@example.com": "Poland",
    "example 3@example.com": "Italy"
}
```

At line 812 in the code:
```python
EMPLOYEE_CITY_MAP = {
    "example example <example@example.com>": "Netherlands",
    "example 2@example.com": "Poland",
    "example 3@example.com": "Italy"
}
```

Replace these keys with the actual email addresses you'll be receiving messages from.

---

# Useful Links (Optional)

- [Oracle Generative AI Agents](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/overview.htm)  
  Overview of OCI's GenAI agent features  
- [Oracle Cloud Docs](https://docs.oracle.com/en/cloud/)  
  Full documentation for OCI services  
- [Weather API](https://www.weatherapi.com/)  
  Used for real-time weather data  
- [Oracle](https://www.oracle.com)  
  Oracle Website  

---

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

