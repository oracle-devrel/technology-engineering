# agent-day-doc-report

Standalone server that generates professional DOCX reports using OCI Generative AI. Fully self-contained — Terraform creates everything: Agent, Knowledge Base, API Gateway, compute, networking, IAM.

Registers as an **API endpoint tool** on OCI Agent Hub. The agent orchestrates KB search (RAG tool) and report generation (HTTP endpoint tool) to produce multi-page DOCX reports from natural language requests.

## Architecture

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
                    +-- Parallel KB search per section
                    +-- Parallel section writing (LLM calls)
                    +-- Assembles DOCX + uploads to Object Storage
                    |
                    v
              Download URL returned to user
```

## What Terraform Creates

| Resource | Purpose |
|----------|---------|
| VCN + public subnet | Networking for VM and API Gateway |
| Private subnet + NAT gateway | Outbound access for OCI Agent's Private Endpoint |
| API Gateway + deployment | HTTPS termination in front of the MCP server |
| Compute instance | Oracle Linux 8 VM running the MCP server |
| Documents bucket | Upload your source documents here |
| Reports bucket | Generated DOCX reports go here |
| Knowledge Base + data source | Hybrid search over ingested documents |
| GenAI Agent + endpoint | Agent with RAG tool for KB search |
| IAM policy | Instance Principals auth (by instance OCID, no dynamic group) |

## How Deployment Works

Terraform creates the **infrastructure and runtime environment** (VM, Python 3.11, pip packages, systemd service, firewall rules) via cloud-init. The **application code** (`server.py`, `docx_report.py`, `oci_auth.py`) is deployed separately via SCP. This is by design — you can update app code without re-running Terraform. The `deploy_command` Terraform output gives you the one-liner.

## Quick Start

```bash
# 1. Edit terraform.tfvars
cd terraform
vim terraform.tfvars
# Set: tenancy_ocid, compartment_ocid, prefix, region

# 2. Deploy infrastructure
terraform init && terraform apply

# 3. Upload documents to the KB bucket
oci os object bulk-upload \
  -ns $(terraform output -raw object_storage_namespace) \
  -bn $(terraform output -raw documents_bucket) \
  --src-dir ../sample_docs --overwrite --content-type auto

# 4. Re-ingest (OCI Console: AI Services > GenAI Agents > Knowledge Bases > Create Ingestion Job)

# 5. Deploy app code
terraform output -raw ssh_private_key > /tmp/docreport_key && chmod 600 /tmp/docreport_key
IP=$(terraform output -raw mcp_server_public_ip)
scp -i /tmp/docreport_key ../oci_auth.py ../docx_report.py ../server.py opc@$IP:/home/opc/agent-day-doc-report/
ssh -i /tmp/docreport_key opc@$IP 'sudo systemctl restart mcp-server'

# 6. Register the API endpoint tool on the agent (see TUTORIAL.md)

# 7. Test via agent chat
```

## Registering the Report Tool on the OCI Agent

The server exposes a REST endpoint at `/api/generate_report` behind the API Gateway (HTTPS). Register it as an **API endpoint calling** tool on the agent:

1. Go to **AI Services > Generative AI Agents > your agent > Tools > Create Tool**
2. Select **Custom tool** > **API endpoint calling (agent execution)**
3. Paste the OpenAPI schema from `openapi.json`
4. Auth: **No authentication**
5. Select the **private subnet** (`<prefix>-agent-subnet`) — this is critical for the agent's PE to reach the API Gateway via NAT
6. Save and verify the tool shows as **Active**

### Why the Private Subnet?

The OCI Agent creates a Private Endpoint (PE) in the selected subnet to make HTTP calls. The PE only has a private IP, so it needs a **NAT gateway** for outbound internet access. The public subnet's IGW only works for resources with public IPs. The private subnet (`<prefix>-agent-subnet`) has a NAT gateway route configured by Terraform.

## Teardown

```bash
cd terraform
terraform destroy
```
