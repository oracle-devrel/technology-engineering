# Setup Guide

## Prerequisites

1. Oracle Cloud Infrastructure (OCI) account
2. Python 3.8+
3. Node.js 18+
4. OCI CLI configured

## Step 1: OCI Configuration

Create `~/.oci/config`:

```
[DEFAULT]
user=ocid1.user.oc1..YOUR_USER_OCID
fingerprint=YOUR_FINGERPRINT
tenancy=ocid1.tenancy.oc1..YOUR_TENANCY_OCID
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

Generate API key:
```bash
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

Upload public key to OCI Console → User Settings → API Keys

## Step 2: OCI GenAI Setup

1. Go to OCI Console → Generative AI
2. Create or select a model (e.g., OpenAI GPT OSS 120B)
3. Note the MODEL_ID
4. Create an Agent Runtime endpoint for SQL queries
5. Note the AGENT_ENDPOINT_ID
6. Get your COMPARTMENT_ID

## Step 3: Update Configuration

Edit `backend/utils/config.py`:
- Replace MODEL_ID with your model OCID
- Replace AGENT_ENDPOINT_ID with your agent endpoint OCID
- Replace COMPARTMENT_ID with your compartment OCID
- Update region if different from eu-frankfurt-1

## Step 4: Install Dependencies

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

## Step 5: Database Setup

This demo uses OCI Agent Runtime with database tools.
Configure your database connection in the OCI Agent Runtime console:
1. Go to OCI Console → Generative AI → Agents
2. Create or configure your agent
3. Add database tool/function
4. Configure connection to your database

Sample schema is provided in `config.py` for reference.

## Step 6: Run the Application

Terminal 1 (Backend):
```bash
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
npm run dev
```

Access: http://localhost:3000

## Troubleshooting

**OCI Authentication Error:**
- Verify ~/.oci/config is correct
- Check API key permissions in OCI Console
- Ensure key_file path is absolute

**Model Not Found:**
- Verify MODEL_ID matches your OCI model OCID
- Check model is in same region as config
- Ensure compartment access permissions

**Agent Endpoint Error:**
- Verify AGENT_ENDPOINT_ID is correct
- Check agent is deployed and active
- Ensure database tools are configured

**Chart Generation Fails:**
- Check matplotlib/seaborn are installed
- Verify python code execution permissions
- Check logs for specific errors

## Environment Variables (Optional)

Instead of editing config.py, you can use environment variables:

```bash
export MODEL_ID="ocid1.generativeaimodel..."
export AGENT_ENDPOINT_ID="ocid1.genaiagentendpoint..."
export COMPARTMENT_ID="ocid1.compartment..."
```
