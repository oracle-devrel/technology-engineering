# AI Use Cases

This directory contains self-contained demonstration applications that showcase
AI-driven use cases built for Oracle Cloud Infrastructure (OCI). Each
sub-directory is an independent application with its own frontend, backend,
documentation, and deployment assets, designed to be deployed on OCI and to
integrate with OCI services such as OCI Generative AI, Oracle Autonomous AI
Database, Oracle Kubernetes Engine (OKE), and OCI Resource Manager.

## Applications

### [`fly-opt/`](fly-opt/README.md) — cuOPT Route Optimizer

A route optimization application for airline/delivery scenarios built on
NVIDIA cuOPT, with an AI-powered natural language interface backed by OCI
Generative AI.

- `app/` — React/Vite single-page application with an Express API proxy that
  connects to a cuOPT solver endpoint and OCI Generative AI.
- `scripts/` — Local launcher that starts the backend proxy and frontend.
- `deploy/` — Docker, Docker Compose, and OKE (Kubernetes) deployment assets.
- `architecture/` — Editable architecture diagrams and their guide.
- `demo/` — Example delivery and route data.
- `genai/` — Standalone Python helper for OCI Generative AI.

### [`sentiment-intelligence/`](sentiment-intelligence/README.md) — Sentiment Intelligence

A React and FastAPI application for brand monitoring, customer-feedback
analysis, and natural-language data access using Oracle Autonomous AI Database,
Select AI, and OCI Generative AI. It runs a coordinated six-stage pipeline that
scrapes public feedback sources, ingests reviews into the database, performs
sentiment inference with `DBMS_CLOUD_AI.GENERATE`, and streams progress to the
UI over Server-Sent Events. It also supports natural-language queries through
Select AI (NL2SQL) and an optional RAG knowledge base.

- `frontend/` — React 19, TypeScript, Vite, Tailwind, and Chart.js UI.
- `backend/` — FastAPI service using python-oracledb, Select AI, and the OCI SDK.
- `rag-documents/` — Optional sample documents for a RAG index.
- `scripts/` — Developer helper scripts for running both services locally.
- `deployment/` — OCI infrastructure as code (OKE, Autonomous DB, OCIR) with an
  OCI Resource Manager schema; a one-click "Deploy to Oracle Cloud" stack is
  packaged as `sentiment-intelligence.zip`.

## Getting started

Each application is independent. Change into the relevant sub-directory and
follow its `README.md` for prerequisites, secure configuration (`.env` files
are created locally from the provided examples and never committed), local
development, and OCI deployment instructions.
