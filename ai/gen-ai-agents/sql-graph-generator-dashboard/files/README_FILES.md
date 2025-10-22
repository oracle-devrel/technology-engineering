# Files Directory - Quick Start Guide

This directory contains all necessary files to run the SQL Graph Generator Dashboard.

## Directory Structure

```
files/
├── backend/
│   ├── api/
│   │   └── main.py                          # FastAPI server entry point
│   ├── orchestration/
│   │   ├── langchain_orchestrator_v2.py     # Main orchestrator with routing logic
│   │   ├── oci_direct_runnables.py          # OCI GenAI Chat API wrappers
│   │   ├── oci_runnables.py                 # OCI Agent Runtime wrappers
│   │   └── conversation_manager.py          # Conversation state management
│   ├── tools/
│   │   └── genai_chart_generator.py         # Chart generation with GenAI
│   ├── utils/
│   │   └── config.py                        # OCI configuration (UPDATE THIS)
│   └── requirements.txt                     # Python dependencies
├── frontend/
│   ├── services/
│   │   └── genaiAgentService.js             # Backend API communication
│   ├── contexts/
│   │   └── ChatContext.js                   # Chat state management
│   └── package.json                         # Node.js dependencies
├── database/
│   ├── customers.csv                        # Sample customer data
│   ├── products.csv                         # Sample product data
│   ├── orders.csv                           # Sample order data
│   └── order_items.csv                      # Sample order items data
├── SETUP_GUIDE.md                           # Detailed setup instructions
├── DATABASE_SETUP.md                        # Database schema and setup
└── README_FILES.md                          # This file
```

## Quick Start (5 Steps)

### 1. Update OCI Configuration

Edit `backend/utils/config.py`:
```python
MODEL_ID = "ocid1.generativeaimodel.oc1.YOUR_REGION.YOUR_MODEL_ID"
AGENT_ENDPOINT_ID = "ocid1.genaiagentendpoint.oc1.YOUR_REGION.YOUR_ENDPOINT_ID"
COMPARTMENT_ID = "ocid1.compartment.oc1..YOUR_COMPARTMENT_ID"
SERVICE_ENDPOINT = "https://inference.generativeai.YOUR_REGION.oci.oraclecloud.com"
```

### 2. Setup OCI CLI

Create `~/.oci/config`:
```
[DEFAULT]
user=ocid1.user.oc1..YOUR_USER_OCID
fingerprint=YOUR_FINGERPRINT
tenancy=ocid1.tenancy.oc1..YOUR_TENANCY_OCID
region=YOUR_REGION
key_file=~/.oci/oci_api_key.pem
```

### 3. Install Dependencies

Backend:
```bash
cd backend
pip install -r requirements.txt
```

Frontend (in project root):
```bash
npm install
```

### 4. Setup Database

The database CSV files are included in `database/` directory.
Configure your OCI Agent Runtime to access these files or load them into your database.

See `DATABASE_SETUP.md` for SQL schema.

### 5. Run the Application

Terminal 1 - Backend:
```bash
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend (from project root):
```bash
npm run dev
```

Open: http://localhost:3000

## Key Files Explained

### Backend

**main.py** - FastAPI server with `/query` endpoint
- Receives natural language questions
- Returns data, charts, or text responses

**langchain_orchestrator_v2.py** - Main orchestration logic
- Routes queries to appropriate agents
- Manages conversation state
- Coordinates data retrieval and chart generation

**oci_direct_runnables.py** - OCI GenAI Chat API integration
- Router for intelligent query routing
- Uses GenAI for decision making

**oci_runnables.py** - OCI Agent Runtime integration
- SQL Agent for database queries
- Extracts structured data from tool outputs

**genai_chart_generator.py** - Chart generation
- Uses GenAI to create matplotlib code
- Executes code safely
- Returns base64-encoded images

**conversation_manager.py** - State management
- Tracks conversation history
- Maintains data context

### Frontend

**genaiAgentService.js** - API client
- Communicates with backend
- Maps response fields (chart_base64 → diagram_base64)

**ChatContext.js** - React context
- Manages chat state
- Processes responses for display
- Handles different message types

## Configuration Tips

1. **Region Consistency**: Ensure all OCIDs and endpoints use the same region
2. **Model Selection**: OpenAI GPT OSS 120B recommended for routing and generation
3. **Agent Tools**: Configure database tools in OCI Agent Runtime console
4. **Permissions**: Ensure OCI user has GenAI and Agent Runtime permissions

## Common Issues

**Authentication Error:**
- Check `~/.oci/config` file
- Verify API key is uploaded to OCI Console
- Test with: `oci iam region list`

**Module Import Error:**
- Ensure you're in the correct directory
- Check all `__init__.py` files exist
- Verify Python path includes backend directory

**Chart Not Displaying:**
- Check browser console for errors
- Verify chart_base64 field in API response
- Ensure frontend compiled successfully

**SQL Agent Timeout:**
- Check AGENT_ENDPOINT_ID is correct
- Verify agent is deployed and active
- Test agent in OCI Console first

## Next Steps

1. Customize DATABASE_SCHEMA in config.py for your database
2. Adjust prompts in oci_direct_runnables.py for your use case
3. Add custom chart types in genai_chart_generator.py
4. Extend routing logic for additional query types

## Support

For OCI GenAI documentation:
https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm

For OCI Agent Runtime:
https://docs.oracle.com/en-us/iaas/Content/generative-ai/agent-runtime.htm
