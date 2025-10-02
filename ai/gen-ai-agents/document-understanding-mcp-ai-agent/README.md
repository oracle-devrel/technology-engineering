# MCP Document Understanding Invoice Agent

The **Document Understanding Agent** is an AI-powered assistant designed to extract and understand text from documents (e.g., PDFs, images) using Oracle Cloud Infrastructure (OCI) Generative AI Agents and Document Understanding services.

This tool demonstrates an end-to-end workflow involving:

- File upload (via React frontend)
- File storage in OCI Object Storage
- Text extraction with OCI Document Understanding
- Summary and reasoning via a GenAI Agent powered by MCP (Model Context Protocol)

The architecture is modular and can be easily extended by adding tools directly from the OCI Console, such as a RAG (Retrieval-Augmented Generation) tool or any other custom MCP-compatible tool, enabling more advanced workflows beyond document extraction—such as contextual question answering, validation, enrichment, or classification

---

## When to use this asset?

Use this assistant when you want to:

- Automatically extract text from scanned documents (images, PDFs)
- Invoke OCI Document Understanding tools through an AI agent
- Demonstrate AI-based document orchestration on OCI and Validation

### Ideal for:

- AI developers building document understanding pipelines
- Oracle Cloud users integrating Generative AI with Object Storage
- Showing document AI capabilities

---

## How to use this asset?

### Start the Backend

Navigate to the backend directory and run:

```bash
cd backend
python mcp_server_docunderstandingobjectextract.py
(In a different terminal)
uvicorn apiserverdocunderstandingobjectextract:app --reload --port 8001
```

This does the following:

- Starts a local MCP server with a tool (`ocr_extract_from_object_storage2`) that wraps OCI Document Understanding.
- Starts a FastAPI server that handles file uploads and routes them to Object Storage + the agent.

### Start the Frontend

In a separate terminal:

```bash
cd oci-genai-agent-llama-react-frontend
npm install
npm run dev
```

You will see a chat interface at [http://localhost:3000](http://localhost:3000), with support for file uploads (PDF, PNG, etc).

When you send a file:

- It's shown as a preview
- Uploaded to the backend
- Saved in OCI Object Storage
- Routed to the GenAI Agent with an instruction like:

```
Extract text from object storage. Namespace: <namespace>, Bucket: <bucket>, Name: <filename>
```

---

## ⚙️ Setup Instructions

### 1. OCI Config

Set the following in `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=xx:xx:xx:xx
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-chicago-1
```

### 2. Object Storage Setup

- Create a bucket (e.g., `bucket-20250714-1419`)
- Make sure the user has permission to `put_object` and `get_namespace`

### 3. MCP Tooling

- `mcp_server_docunderstandingobjectextract.py` exposes a tool `ocr_extract_from_object_storage2`
- This is picked up by the agent automatically on FastAPI startup

---

## ✨ Key Features

| Feature                | Description                                                       |
| ---------------------- | ----------------------------------------------------------------- |
| File Upload            | Upload images or PDFs through the React UI                        |
| OCI Object Storage     | All files are stored securely in your OCI bucket                  |
| OCR Extraction         | Uses OCI Document Understanding to extract text from scanned docs |
| GenAI Agent            | Routes and responds to user requests intelligently                |
| Tool Orchestration     | Agent can invoke tools dynamically (via MCP)                      |
| Natural Language Reply | AI explains extracted results in human-readable format            |

---

## Prompt Customization

The main agent prompt is set as:

```
If the user wants to extract text from a document in Object Storage,
call the `ocr_extract_from_object_storage2` tool with the `namespace`, `bucket`, and `name`.
```

You can modify this in `apiserverdocunderstandingobjectextract.py` under `Agent(...)` setup.

---

## Useful for:

- Demos of OCI Document Understanding + GenAI Agents
- Building your own document processing pipeline
- AI chatbots that take file input and analyze content

---

## Directory Structure

```bash
backend/
├── apiserverdocunderstandingobjectextract.py   # FastAPI app
├── mcp_server_docunderstandingobjectextract.py # MCP server with document OCR tool

oci-genai-agent-llama-react-frontend/
├── src/
│   └── app/
│       └── contexts/
│           └── ChatContext.js                  # Hooks into backend API
```

---

## License

Copyright (c) 2025 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
