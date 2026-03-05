# Agent in a Day - DOCX Report Server

Build and deploy a standalone server that generates professional DOCX reports
using OCI Generative AI. Everything is created from scratch by Terraform — one
agent, one Knowledge Base, one API Gateway, one VM, no dependencies on any
other project.

**Time:** ~45 minutes
**Cost:** Under $5 if you tear down the same day

---

## What You'll Build

An OCI GenAI Agent that orchestrates two tools:

1. **RAG Tool** — searches a Knowledge Base for relevant document data
2. **API Endpoint Tool** — calls your report server to generate a DOCX

The report server (FastMCP on an OCI VM behind an API Gateway) takes the
agent's RAG results and:

1. Plans 3-5 report sections using an LLM
2. Writes all sections in parallel (LLM calls)
3. Assembles a branded DOCX with tables, charts, executive summary
4. Uploads to Object Storage and returns the download URL

```
User --> OCI Agent Hub
              |
              +-- RAG Tool --> Knowledge Base (hybrid search over your documents)
              |
              +-- API Endpoint Tool (HTTPS)
                    |
                    v
              API Gateway (TLS termination)
                    |
                    v
              MCP Server (port 8000, FastMCP)
                    +-- Plans sections (LLM call)
                    +-- Parallel section writing (LLM calls)
                    +-- Assembles DOCX + uploads to Object Storage
                    |
                    v
              Download URL returned to user
```

The agent passes its RAG results as context to the report tool, so the server
can skip redundant KB searches and generate reports in ~10-30 seconds.

---

## Prerequisites

- An **OCI tenancy** with access to OCI Generative AI (Frankfurt region)
- **OCI CLI** installed and configured (`~/.oci/config`)
- **Terraform** installed (v1.5+)
- A **compartment** where you can create resources
- Some **documents** to upload (PDFs, DOCX, text files — the source data for reports)

### Check Your Region

This tutorial uses **Frankfurt** (`eu-frankfurt-1`). OCI GenAI Agents are available
in Frankfurt, Chicago, Ashburn, and other regions. Check the
[OCI GenAI docs](https://docs.oracle.com/en-us/iaas/Content/generative-ai/overview.htm)
for the latest list.

### Knowledge Base Limits

Each region has a limited number of KB slots (typically 15-18). If you hit the
limit, clean up unused KBs in the OCI Console or try another region.

---

## Step 1: Get the Code

```bash
cd ~/dev
git clone <repo-url> agent-day-doc-report
cd agent-day-doc-report/files
```

### What's in this Directory

```
files/
+-- server.py              # MCP server + REST endpoint (FastMCP, port 8000)
+-- docx_report.py         # Report engine (plan, parallel write, style, chart, assemble)
+-- oci_auth.py            # OCI auth + LLM chat + KB search
+-- openapi.json           # OpenAPI spec for the API endpoint tool
+-- requirements.txt       # Python dependencies
+-- README.md              # Detailed architecture and deployment reference
+-- TUTORIAL.md            # This file — step-by-step walkthrough
+-- sample_docs/           # Put your source documents here
+-- terraform/
    +-- terraform.tfvars   # <-- EDIT THIS (3 values)
    +-- variables.tf       # Input variables with defaults
    +-- provider.tf        # OCI provider
    +-- datasource.tf      # Image lookup, shape/AD discovery
    +-- network.tf         # VCN, public subnet, private subnet, NAT gateway
    +-- apigateway.tf      # API Gateway + HTTPS routes
    +-- compute.tf         # VM + IAM policy (Instance Principals)
    +-- agent.tf           # GenAI Agent + KB + RAG tool + endpoint
    +-- storage.tf         # Documents bucket + reports bucket
    +-- cloud-init.yaml    # VM bootstrap (Python, deps, systemd)
    +-- outputs.tf         # IPs, OCIDs, helper commands
```

All commands in this tutorial assume you are working from the `files/` directory.

---

## Step 2: Add Your Documents

Put the documents you want searchable into a `sample_docs/` folder at the
project root. These will be uploaded to Object Storage and ingested into the
Knowledge Base.

```bash
mkdir -p sample_docs

# Copy your files (PDFs, DOCX, TXT, etc.)
cp ~/Downloads/oracle_fy2025_report.pdf sample_docs/
cp ~/Downloads/company_overview.docx sample_docs/
```

The more relevant data you provide, the better the reports will be.

---

## Step 3: Configure terraform.tfvars

Copy the example and edit it:

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
vim terraform/terraform.tfvars
```

You need to set **three values**:

### 3.1 `tenancy_ocid`

Your tenancy OCID. Required for the IAM policy.

**How to find it:**
1. Log into the [OCI Console](https://cloud.oracle.com)
2. Click your **profile icon** (top right) > **Tenancy: <name>**
3. Copy the **OCID**

### 3.2 `compartment_ocid`

Where all resources will be created.

**How to find it:**
1. Hamburger menu > **Identity & Security** > **Compartments**
2. Click your compartment (or create a new one like `doc-report-workshop`)
3. Copy the **OCID**

### 3.3 `prefix` (optional)

A short label prepended to every resource name. Default is `docreport`.
Change it if you want to avoid name collisions.

### Example

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaaa..."
compartment_ocid = "ocid1.compartment.oc1..aaaaaaa..."
prefix           = "docreport"
region           = "eu-frankfurt-1"
genai_model      = "meta.llama-3.3-70b-instruct"
```

---

## Step 4: Deploy with Terraform

```bash
cd terraform
terraform init
terraform plan
```

Review the plan. You should see ~18 resources. Then:

```bash
terraform apply
```

Type `yes`. This takes 3-5 minutes.

### What Gets Created

| Resource | Name | Purpose |
|----------|------|---------|
| VCN | `<prefix>-vcn` | Network (10.1.0.0/16) |
| Public Subnet | `<prefix>-subnet` | VM and API Gateway live here |
| Private Subnet | `<prefix>-agent-subnet` | OCI Agent's Private Endpoint (with NAT) |
| NAT Gateway | `<prefix>-natgw` | Outbound internet for the private subnet |
| Security List | `<prefix>-seclist` | Opens SSH (22), HTTP (8000), HTTPS (443) |
| API Gateway | `<prefix>-api-gw` | HTTPS termination in front of the server |
| Compute Instance | `<prefix>-mcp-server` | Oracle Linux 8, 1 OCPU, 8GB RAM |
| Documents Bucket | `<prefix>-documents` | Upload source documents here |
| Reports Bucket | `<prefix>-reports` | Generated DOCX reports land here |
| Knowledge Base | `<prefix>-kb` | Hybrid search over your documents |
| Data Source | `<prefix>-datasource` | Links KB to the documents bucket |
| Ingestion Job | `<prefix>-initial-ingestion` | First indexing run |
| Agent | `<prefix>-agent` | GenAI Agent with RAG tool |
| Agent Endpoint | `<prefix>-endpoint` | API endpoint for agent interaction |
| RAG Tool | `rag-tool` | Connects KB to the agent |
| IAM Policy | `<prefix>-mcp-policy` | Instance Principals auth (by instance OCID) |

### Cost

| Resource | Cost |
|----------|------|
| Compute (1 OCPU, 8 GB) | ~$30/month if left running |
| Everything else | Pennies (pay-per-API-call, per-GB storage) |

> Destroy the same day = well under $5.

---

## Step 5: Upload Documents

After Terraform finishes, upload your documents to the documents bucket:

```bash
oci os object bulk-upload \
  -ns $(terraform output -raw object_storage_namespace) \
  -bn $(terraform output -raw documents_bucket) \
  --src-dir ../sample_docs --overwrite --content-type auto
```

Then trigger a KB ingestion so the agent can search them:

**Option A: OCI Console**
1. Go to **AI Services** > **Generative AI Agents** > **Knowledge Bases**
2. Click `<prefix>-kb` > **Data Sources** > `<prefix>-datasource`
3. Click **Create Ingestion Job**
4. Wait for it to complete (1-3 minutes depending on document count)

**Option B: OCI CLI**
```bash
oci generative-ai-agent data-ingestion-job create \
  --compartment-id $(terraform output -raw compartment_ocid 2>/dev/null || grep compartment_ocid terraform.tfvars | cut -d'"' -f2) \
  --data-source-id $(terraform output -raw datasource_ocid 2>/dev/null || echo "check OCI console") \
  --display-name "manual-ingestion"
```

> **Note:** Terraform runs an initial ingestion job at deploy time, but the
> documents bucket is empty then. You need to re-ingest after uploading files.

---

## Step 6: Deploy App Code to the VM

Terraform creates the VM and installs dependencies via cloud-init, but the
Python files need to be copied over:

```bash
# Save the SSH key
terraform output -raw ssh_private_key > /tmp/docreport_key
chmod 600 /tmp/docreport_key

# Get the IP
IP=$(terraform output -raw mcp_server_public_ip)
echo "Server IP: $IP"

# Copy the app files
scp -i /tmp/docreport_key \
  ../oci_auth.py ../docx_report.py ../server.py \
  opc@$IP:/home/opc/agent-day-doc-report/

# Restart the service
ssh -i /tmp/docreport_key opc@$IP 'sudo systemctl restart mcp-server'
```

### Verify

```bash
# Check service status
ssh -i /tmp/docreport_key opc@$IP 'sudo systemctl status mcp-server'

# Watch logs
ssh -i /tmp/docreport_key opc@$IP 'sudo journalctl -u mcp-server -f'
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 7: Test the REST Endpoint

Test the report generation endpoint through the API Gateway:

```bash
# Get the API Gateway URL
GW=$(cd terraform && terraform output -raw api_gateway_url)
echo "API Gateway: $GW"

# Health check
curl -s "https://$(echo $GW | cut -d/ -f3)/api/health"

# Generate a test report (adjust title/query to match your documents)
curl -X POST "https://$(echo $GW | cut -d/ -f3)/api/generate_report" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Oracle FY2025 Analysis",
    "query": "Analyze Oracle fiscal year 2025 financial results"
  }'
```

The response includes an Object Storage URL where you can download the DOCX.

---

## Step 8: Register the API Endpoint Tool on the Agent

This is the key step — connecting the report server to the OCI Agent so it can
call it automatically alongside the RAG tool.

1. **OCI Console** > **AI Services** > **Generative AI Agents**
2. Click your agent (`<prefix>-agent`) > **Tools** > **Create Tool**
3. Select **Custom tool** > **API endpoint calling (agent execution)**
4. Paste the OpenAPI schema from `openapi.json` in the repo root
5. Auth: **No authentication**
6. **Important:** Select the **private subnet** (`<prefix>-agent-subnet`)
7. Save and verify the tool shows as **Active**

### Why the Private Subnet?

The OCI Agent creates a Private Endpoint (PE) in the selected subnet to make
HTTP calls. The PE only has a private IP, so it needs a **NAT gateway** for
outbound internet access. The public subnet's IGW only works for resources
with public IPs. The private subnet (`<prefix>-agent-subnet`) has a NAT
gateway route configured by Terraform.

> **If you select the public subnet, the agent will fail with "Internal
> Execution Error" and requests will never reach your server.**

### Test via Agent Chat

Go to the agent's chat interface and try:

```
Search the knowledge base for Oracle FY2025 financial data, then use the
generateReport tool to create a DOCX report titled "Oracle FY2025 Analysis"
analyzing Oracle's fiscal year 2025 results. Pass the search results as
the context parameter.
```

The agent should:
1. Call the RAG tool to search the KB
2. Call generateReport with the title, query, and RAG results as context
3. Return a download URL for the DOCX report

---

## How It Works

When `generateReport` is called via the API endpoint:

```
1. PLAN (1 LLM call)
   "What sections should this report have?"
   --> ["Revenue Performance", "Cloud Growth", "Profitability", "Outlook", "Risk Factors"]

2. WRITE ALL SECTIONS IN PARALLEL (1 LLM call per section)
   Each section receives the RAG context passed by the agent.
   All sections written concurrently via ThreadPoolExecutor.

3. ASSEMBLE DOCX
   - Template-based executive summary and conclusion (no LLM calls)
   - Oracle-branded styling, data tables, bar charts, centered title page
   - Upload to reports bucket, return download URL
```

When the agent passes RAG results as context (the recommended flow), the
server skips per-section KB searches entirely. This brings generation time
down to ~10-15 seconds for a 5-section report.

Without context (direct API call), the server falls back to parallel KB
searches per section, taking ~30 seconds for a 3-section report.

---

## Local Development

Run the server locally with `~/.oci/config` credentials:

```bash
pip install -r requirements.txt

# Set env vars (get values from terraform output)
export OCI_REGION=eu-frankfurt-1
export AGENT_REGION=eu-frankfurt-1
export AGENT_ENDPOINT_OCID=$(cd terraform && terraform output -raw agent_endpoint_ocid)
export COMPARTMENT_OCID=ocid1.compartment.oc1..aaaaaaa...
export GENAI_MODEL=meta.llama-3.3-70b-instruct
export OBJECT_STORAGE_NAMESPACE=$(cd terraform && terraform output -raw object_storage_namespace)
export REPORTS_BUCKET=$(cd terraform && terraform output -raw reports_bucket)

# Optional: specify OCI config profile
export OCI_CLI_PROFILE=FRANKFURT

python server.py
```

### Quick Syntax Check (No OCI Needed)

```bash
python -c "
import ast
for f in ['oci_auth.py', 'docx_report.py', 'server.py']:
    with open(f) as fh:
        ast.parse(fh.read())
    print(f'{f}: syntax OK')
"
```

---

## Troubleshooting

### "Connection refused" on port 8000

Cloud-init takes a few minutes after the instance starts. Check:
```bash
ssh -i /tmp/docreport_key opc@$IP 'sudo journalctl -u mcp-server --no-pager -n 50'
```

### Agent returns "Internal Execution Error"

This almost always means the agent's Private Endpoint can't reach the API
Gateway. Check:
- Did you select the **private subnet** (`<prefix>-agent-subnet`) when
  creating the API endpoint tool? The public subnet will NOT work.
- Is the NAT gateway active? (OCI Console > Networking > NAT Gateways)
- Is the API Gateway healthy? Test with curl from your laptop first.

### KB search returns empty

- Did you upload documents? (Step 5)
- Did you re-run ingestion after uploading? The initial ingestion runs on an empty bucket.
- Check the KB in OCI Console: does it show ingested documents?

### "No module named 'oci'"

SSH in and install manually:
```bash
ssh -i /tmp/docreport_key opc@$IP
cd /home/opc/agent-day-doc-report
python3.11 -m pip install --user -r requirements.txt
sudo systemctl restart mcp-server
```

### Agent only calls RAG, not generateReport

The agent may need an explicit prompt. Try:
```
Search the knowledge base for <topic>, then use the generateReport tool to
create a DOCX report. Pass the search results as the context parameter.
```

### Knowledge Base limit reached

Each region has ~15-18 KB slots. Delete unused KBs in OCI Console or use
a different region.

### Instance Principals not working

The IAM policy takes a few minutes to propagate after `terraform apply`.
Wait 5 minutes and restart:
```bash
ssh -i /tmp/docreport_key opc@$IP 'sudo systemctl restart mcp-server'
```

---

## Teardown

Destroy everything when you're done:

```bash
cd terraform
terraform destroy
```

Type `yes`. This removes all resources: VM, Agent, KB, API Gateway, buckets,
networking, IAM policy — everything.

**Double-check:** OCI Console > your compartment > look for anything with
`<prefix>-*`. Delete any stragglers manually.

> Do this the same day to avoid ongoing compute charges.
