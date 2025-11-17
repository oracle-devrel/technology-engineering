# CrewAI ↔ OCI Generative AI Integration

This repository provides examples and configuration guidelines for integrating **[CrewAI](https://github.com/joaomdmoura/crewAI)** with **Oracle Cloud Infrastructure (OCI) Generative AI** services.  
The goal is to demonstrate how CrewAI agents can seamlessly leverage OCI-hosted models through the **LiteLLM gateway**.

Reviewed: 31.10.2025

---

## 🔐 Security Configuration

Before running the demos, you must configure access credentials for OCI.

In these examples, we use a **locally stored key pair** for authentication.  
Ensure your local OCI configuration (`~/.oci/config` and private key) is correctly set up and accessible to the Python SDK.

To correctly start the **LiteLLM gateway** you need to create and configure correctly a **config.yml** file. To create this file use the [template](./config_template.yml).

In addition, you should be **enabled** to use OCI Generative AI Service in your tenant. If you haven't yet used OCI GenAI ask to your tenant's admin to setup the **needed policies**.

---

## 🧩 Demos Included

- [Simple CrewAI Agent](./simple_test_crewai_agent.py) — basic CrewAI agent interacting with an LLM through OCI
- [OCi Consumption Report](./crew_agent_mcp02.py)
- *(More demos to be added soon)*

---

## 📦 Dependencies

The project relies on the following main packages:

| Dependency | Purpose |
|-------------|----------|
| **CrewAI** | Framework for creating multi-agent workflows |
| **OCI Python SDK** | Access OCI services programmatically |
| **LiteLLM (Gateway)** | OpenAI-compatible proxy for accessing OCI Generative AI models |

To connect CrewAI to OCI models, we use a **LiteLLM gateway**, which exposes OCI GenAI via an **OpenAI-compatible** REST API.

---

## ⚙️ Environment Setup

1. **Create a Conda environment**
```bash
conda create -n crewai python=3.11
```

2. **Activate** the environment
```
conda activate crewai
```

3. **Install** the required **packages**
```
pip install -U oci litellm "litellm[proxy]" crewai
```

4. Run the LiteLLM Gateway

Start the LiteLLM gateway using your configuration file (config.yml):
```
./start_gateway.sh
```

Make sure the gateway starts successfully and is listening on the configured port (e.g., http://localhost:4000/v1).

🧠 Test the Integration

Run the sample CrewAI agent to verify that CrewAI can connect to OCI through LiteLLM:

```
python simple_test_crewai_agent.py
```

If the setup is correct, you should see the agent’s output using an OCI model.

## Integrate Agents with **MCP** servers.
Install this additional package:

```
pip install 'crewai-tools[mcp]'
```

You can test the integration with **MCP** using [OCI Consumption report](./crew_agent_mcp02.py) that generates a report
of the consumption in your tenant (top 5 compartments, for 4 weeks).

To have this demo up&running:
* download the code for the MCP server from [here](https://github.com/oracle-devrel/technology-engineering/blob/main/ai/gen-ai-agents/mcp-oci-integration/mcp_consumption.py)
* start the MCP server, on a free port (for example 9500)
* register the URL, in [source](./crew_agent_mcp02.py), in the section:
```
server_params = {
    "url": "http://localhost:9500/mcp",
    "transport": "streamable-http"
}
```

If you don't want to secure (with JWT) the communication with the MCP server, put 
```
ENABLE_JWT_TOKEN = False
```
in the config.py file.

