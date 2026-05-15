# OCI GenAI Agent - DOCX Report Generator

This repository provides a fully self-contained solution for generating professional DOCX reports using OCI Generative AI Agents.
Terraform creates everything from scratch: Agent, Knowledge Base, API Gateway, compute, networking, and IAM.

The OCI Agent orchestrates two tools — a RAG tool for knowledge base search and an API endpoint tool for report generation — to produce multi-page DOCX reports from natural language requests.

Reviewed: 25.02.2026

## When to use this asset

You should use this asset when you need to demonstrate:

- How to build and register an **API endpoint tool** on OCI GenAI Agent Hub
- How an OCI Agent can **orchestrate multiple tools** (RAG search + custom REST endpoint)
- How to generate **professional DOCX reports** (tables, charts, branded styling) from knowledge base data
- A complete **Terraform-managed** OCI deployment (VCN, API Gateway, compute, GenAI Agent, Knowledge Base)

## How to use this asset

### Security Configuration

The compute instance authenticates to OCI services via **Instance Principals** (by instance OCID, no dynamic group needed). Terraform creates the IAM policy automatically.

For local development, ensure your OCI configuration (`~/.oci/config` and private key) is correctly set up.

### Architecture

```
User --> OCI Agent Hub
              |
              +-- RAG Tool --> Knowledge Base (hybrid search)
              |
              +-- API Endpoint Tool (HTTPS)
                    |
                    v
              API Gateway --> MCP Server (FastMCP)
                    |
                    +-- Plans sections (LLM)
                    +-- Parallel section writing (LLM)
                    +-- Assembles DOCX + uploads to Object Storage
                    |
                    v
              Download URL returned to user
```

### Quick Start

```bash
cd files/terraform
vim terraform.tfvars
# Set: tenancy_ocid, compartment_ocid, prefix, region

terraform init && terraform apply

# Upload documents, deploy app code, register tool
# See files/TUTORIAL.md for step-by-step instructions
```

For the full step-by-step walkthrough, see [files/TUTORIAL.md](files/TUTORIAL.md).

### Dependencies

| Dependency | Purpose |
|------------|---------|
| OCI Python SDK | Access OCI services (GenAI, Object Storage, Agent Runtime) |
| FastMCP | MCP server framework with REST endpoint support |
| python-docx | DOCX document generation |
| matplotlib / numpy | Chart rendering |
| Terraform | Infrastructure-as-code deployment |

### Environment Setup

```bash
# Install Python dependencies
pip install -r files/requirements.txt

# Set environment variables (get values from terraform output)
export OCI_REGION=eu-frankfurt-1
export AGENT_ENDPOINT_OCID=<from terraform output>
export COMPARTMENT_OCID=<your compartment>
export GENAI_MODEL=meta.llama-3.3-70b-instruct
export OBJECT_STORAGE_NAMESPACE=<from terraform output>
export REPORTS_BUCKET=<from terraform output>

# Run locally
python files/server.py
```

## License

This asset is licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE).
