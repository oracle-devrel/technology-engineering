
# Generative AI Chatbot

This repository contains a Flask-based chat application utilizing Oracle's Generative AI Agents.

**Author**: matsliwins

**Last review date**: 19/09/2025

![](files/images/image.png)
## Getting Started

# When to use this asset?

Use this asset when you want a **quick starter chatbot UI** for:

- Testing and demoing an **Oracle Generative AI Agent endpoint** from a web browser
- Building a simple internal prototype before integrating chat into a larger app
- Providing a minimal, hackable baseline (Flask + OCI SDK) for custom features (auth, logging, conversation history, etc.)

---

# How to use this asset?

## Prerequisites

- Python 3.8+
- OCI configuration available at `~/.oci/config`
- Dependencies: Flask, OCI SDK, qrcode (and whatever is listed in `requirements.txt`)

## Setup

### 1) Clone the repository

```bash
git clone [repository-link]
cd [repository-folder]
```

### 2) Configure your Agent Endpoint OCID

Open the main Python file and replace:

```python
AGENT_ENDPOINT_ID = "your-agent-endpoint-ocid-here"
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the application

```bash
python chat_agent.py
```

## Use the chatbot

Open your browser at:

```text
http://localhost:5000
```

Enter messages in the web interface to interact with your configured Oracle Generative AI Agent.

---

# Additional notes

## Configuration tips

- Ensure the OCI profile you expect is active in `~/.oci/config` (and that the user has permission to call the agent endpoint).
- If you support multiple environments, consider using environment variables instead of hardcoding:
  - `AGENT_ENDPOINT_ID`
  - `OCI_PROFILE` (if your code supports it)

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.  
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
