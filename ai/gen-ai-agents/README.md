# SQL Graph Generator Dashboard

SQL Graph Generator Dashboard is an AI-powered assistant that enables natural language database queries and intelligent chart generation.
It extracts data from your database using conversational queries, automatically generates appropriate visualizations, and provides multi-turn conversational context for data exploration.
It runs as an interactive Next.js web app backed by a FastAPI server, LangChain orchestration, and Oracle Cloud Infrastructure GenAI models.

Reviewed: October 13, 2025

# When to use this asset?

Use this asset when you want to:

- Query databases using natural language instead of SQL
- Automatically generate charts and visualizations from query results
- Build conversational data exploration interfaces
- Integrate OCI GenAI models with database operations
- Demonstrate intelligent routing between data queries, visualizations, and insights

Ideal for:

- AI engineers building conversational data analytics tools
- Data teams needing natural language database interfaces
- OCI customers integrating GenAI into business intelligence workflows
- Anyone showcasing LangChain + OCI GenAI + dynamic visualization generation

# How to use this asset?

This assistant can be launched via:

- Next.js Web UI

It supports:

- Natural language to SQL conversion
- Automatic chart generation from query results
- Multi-turn conversations with context preservation
- Multiple chart types: bar, line, pie, scatter, heatmap
- Real-time data visualization using matplotlib/seaborn
- Intelligent routing between data queries, visualizations, and insights

## Setup Instructions

### OCI Generative AI Model Configuration

1. Go to: OCI Console → Generative AI
2. Select your model (this demo uses OpenAI GPT OSS 120B):
   `ocid1.generativeaimodel.oc1.eu-frankfurt-1.amaaaaaask7dceyav...`
3. Set up an OCI Agent Runtime endpoint for SQL queries
4. Copy the following values:
   - MODEL_ID
   - AGENT_ENDPOINT_ID
   - COMPARTMENT_ID
   - SERVICE_ENDPOINT (e.g., `https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com`)
5. Configure them in `backend/utils/config.py`

Documentation:
[OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

No API key is required — authentication is handled via OCI identity.

Ensure your OCI CLI credentials are configured.
Edit or create the following config file at `~/.oci/config`:

```
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=c6:4f:66:e7:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

### Install Dependencies

Backend:

```bash
cd backend
pip install -r requirements.txt
```

Frontend:

```bash
cd ..
npm install
```

### Configure Database

1. Set up your database connection in OCI Agent Runtime
2. The demo uses a sample e-commerce database with tables:
   - orders
   - customers
   - products
   - order_items

### Start the Application

Backend (FastAPI):

```bash
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Next.js):

```bash
npm run dev
```

Access the application at: http://localhost:3000

## Key Features

| Feature                  | Description                                                      |
| ------------------------ | ---------------------------------------------------------------- |
| Natural Language Queries | Ask questions like "show me the top 5 orders"                    |
| Intelligent Routing      | GenAI-powered routing between data queries, charts, and insights |
| Auto Chart Generation    | Automatically creates appropriate visualizations from data       |
| Multi-Turn Conversations | Maintains context across multiple queries                        |
| Real-Time Visualization  | Generates matplotlib/seaborn charts as base64 images             |
| Multiple Chart Types     | Supports bar, line, pie, scatter, and heatmap charts             |
| OCI GenAI Integration    | Uses OCI Agent Runtime and Chat API                              |
| LangChain Runnables      | Clean integration pattern wrapping OCI SDK calls                 |
| Conversation Management  | Tracks query history and data state                              |
| Error Handling           | Clear error messages and fallback behavior                       |

## Architecture

### Backend Components

1. **Router Agent** (OCI Chat API)

   - Intelligent query routing using GenAI
   - Routes: DATA_QUERY, CHART_EDIT, INSIGHT_QA
   - Returns structured JSON decisions

2. **SQL Agent** (OCI Agent Runtime)

   - Natural language to SQL conversion
   - Database query execution
   - Structured data extraction

3. **Chart Generator** (OCI Chat API + Python Execution)

   - GenAI generates matplotlib/seaborn code
   - Safe code execution in sandboxed environment
   - Returns base64-encoded chart images

4. **Orchestrator**
   - Coordinates agents based on routing decisions
   - Manages conversation state
   - Handles multi-turn context

### Frontend Components

1. **Chat Interface**

   - Real-time message display
   - Support for text, tables, and images
   - Speech recognition integration

2. **Service Layer**

   - API communication with backend
   - Response transformation
   - Error handling

3. **Context Management**
   - User session handling
   - Message history
   - State management

## Example Queries

```
"Show me the top 5 orders"
→ Returns table with order data

"Make a bar chart of those orders by total amount"
→ Generates bar chart visualization

"Show me orders grouped by region"
→ Returns data aggregated by region

"Create a pie chart of the order distribution"
→ Generates pie chart from current data

"What insights can you provide about these sales?"
→ Provides AI-generated analysis
```

## Configuration Files

Key configuration in `backend/utils/config.py`:

- MODEL_ID: Your OCI GenAI model OCID
- AGENT_ENDPOINT_ID: Your OCI Agent Runtime endpoint
- COMPARTMENT_ID: Your OCI compartment
- SERVICE_ENDPOINT: GenAI service endpoint URL
- DATABASE_SCHEMA: Database table definitions

## Notes

- Prompts can be customized in `backend/orchestration/oci_direct_runnables.py`
- Chart generation code is dynamically created by GenAI
- Designed specifically for Oracle Cloud Infrastructure + Generative AI
- Sample database schema included for e-commerce use case
- Frontend uses Material-UI for consistent design

# Useful Links

- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
  Official documentation for Oracle Generative AI

- [OCI Agent Runtime](https://docs.oracle.com/en-us/iaas/Content/generative-ai/agent-runtime.htm)
  Documentation for OCI Agent Runtime

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
  LangChain framework documentation

- [Next.js Documentation](https://nextjs.org/docs)
  Next.js framework documentation

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
