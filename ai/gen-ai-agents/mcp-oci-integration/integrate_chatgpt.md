# Integrate with ChatGPT

As of September 2025, there are two options to integrate private knowledge bases into ChatGPT, when hosted on Oracle OCI:

1. Deep Research (strict OpenAI MCP compliance)

2. Developer Mode (flexible integration)

The goal in both cases is to ground ChatGPT’s answers not only in its internal knowledge and web search results, but also in private data securely hosted in an **Oracle 23AI Database**, retrieved via **Vector Search**.

Both approaches rely on **MCP** (Model Context Protocol).

### Option 1: Deep Research
Requires full adherence to the official OpenAI MCP specifications.
Your MCP must implement two tools:

* search → returns a list of document snippet IDs relevant to the query.
* fetch → retrieves the full content of a document given its ID.

If these are not correctly implemented, ChatGPT will not enable the MCP integration.

### Option 2: Developer Mode
Available if you enable **Developer Mode** in ChatGPT settings.
More flexible: your MCP can expose arbitrary tools.
At a minimum, you must provide a search method to surface relevant data.

Official [OpenAI MCP specification](https://platform.openai.com/docs/mcp#create-an-mcp-server)

## Security
The MCP server must be exposed on Internet via a public IP. For this reason additional **security** is mandatory. 
One option is to expose the MCP server using an **API Gateway** in OCI. In this way only the Gateway endpoint is available,through TLS, over Internet and the MCP server, hosted in OCI, is reachable via private IP only by the gateway.

In addition, authorization can be handled using **OAUTH 2.0**.
