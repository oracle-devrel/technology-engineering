# Complex Document RAG

An autonomous document-processing system built on Oracle Cloud Infrastructure (OCI) Generative AI. It has two modes: an **interactive Gradio UI** for manual document ingestion and RAG queries, and an **autonomous agent** that watches a directory, classifies incoming documents, and produces structured reports with full audit trail.

## Quick Start

```bash
cd complex-doc-rag/files

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-orchestrator.txt    # for the autonomous agent
pip install -r requirements-dashboard.txt       # optional: dashboard UI

# 3. Configure OCI credentials (~/.oci/config)
#    See: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm

# 4. Create .env from example
cp .env.example .env
# Edit with your OCI compartment ID and model endpoint IDs

# 5a. Run the interactive UI
python gradio_app.py                            # http://localhost:7863

# 5b. OR run the autonomous agent
python -m agentic_orchestrator watch --config config/agent_config.yaml
```

## System Components

The system has three independent components. None of them require each other to run.

| Component | Entry point | Port | What it does |
|---|---|---|---|
| **Gradio UI** | `python gradio_app.py` | 7863 | Interactive web UI for document ingestion (XLSX/PDF), vector store management, and RAG queries |
| **Autonomous Agent** | `python -m agentic_orchestrator watch --config config/agent_config.yaml` | none | Polls `incoming/` directory, classifies documents, runs domain-specific analysis, writes artifacts to `out/` |
| **Dashboard** (optional) | `python -m dashboard_backend` + `cd dashboard_frontend && npm run dev` | 8000 + 5173 | FastAPI REST API with WebSocket live events, plus React frontend for monitoring orchestrator runs |

### Gradio UI

Manual workflow for document processing and ad-hoc queries:

```bash
python gradio_app.py
```

Open `http://localhost:7863`. Three tabs:
- **Document Processing** -- ingest XLSX and PDF files into ChromaDB
- **Vector Store Viewer** -- browse collections, search chunks, manage embeddings
- **Inference & Query** -- run RAG queries against ingested documents, generate reports

### Autonomous Agent

The agent is a single Python process with a polling loop -- no HTTP servers, no Docker required. It watches the filesystem and processes documents through a 10-node LangGraph pipeline.

```bash
# Create the watched directories
mkdir -p incoming/fiscal incoming/tender incoming/esg

# Start the watcher
python -m agentic_orchestrator watch --config config/agent_config.yaml

# Drop documents to trigger processing
cp annual_report_2024.pdf incoming/fiscal/
cp vendor_proposal.pdf incoming/tender/
cp esg_sustainability_2024.pdf incoming/esg/
```

The agent will:
1. Detect the new file (polls every 5 seconds by default)
2. Deduplicate via SHA256 content hash against the registry
3. Classify by filename patterns with LLM fallback
4. Look up related documents (baselines, peer reports, RFPs)
5. Run the domain-specific comparison workflow
6. Quality-gate the output, with one LLM repair pass if gates fail
7. Write artifacts to `out/<domain>/<case_key>/<run_id>/`

If a required baseline or companion document is missing, the agent writes a `human_question.json` describing what it needs.

You can also process a single document event without running the watcher:

```bash
python -m agentic_orchestrator process-doc-event \
  --event-json event.json \
  --config config/agent_config.yaml
```

### Dashboard (Optional)

A separate FastAPI + React frontend for monitoring orchestrator runs via WebSocket:

```bash
# Terminal 1: backend
python -m dashboard_backend                     # http://localhost:8000

# Terminal 2: frontend
cd dashboard_frontend
npm install
npm run dev                                     # http://localhost:5173
```

## How the Autonomous Agent Works

Documents flow through a 10-node LangGraph StateGraph:

```
new document detected
    |
    v
observe_event --> load_registry --> classify_doc --> decide_actions
                                                          |
                                                          v
update_registry <-- publish_artifacts <-- quality_gates <-- action_executor
    |                     ^                   |                   |
    v                     |                   v                   |
   END                    |              repair_once          ingest_embed
                          |
                    (writes LATEST.json)
```

| Node | Purpose |
|------|---------|
| **Observe Event** | Deduplicate via content hash in the document registry |
| **Load Registry** | Query related records for same entity/domain |
| **Classify** | Heuristic classification by filename patterns + LLM fallback |
| **Decide Actions** | Select baseline documents and choose workflow |
| **Ingest & Embed** | Process the document into ChromaDB via OCI Cohere embeddings |
| **Action Executor** | Run the domain workflow via MCP RAG tools |
| **Quality Gates** | Domain-specific quality checks |
| **Repair** | One-shot LLM repair if gates fail, then re-check |
| **Publish Artifacts** | Write outputs with decision contract, trace, and LATEST.json |
| **Update Registry** | Mark document as completed/failed |

### Document Registry

A persistent registry (SQLite or Oracle ADB) tracks every document:
- Content hash for deduplication
- Classification (domain, doc_role, entity, period)
- Case key for grouping related documents
- Status progression: pending -> classified -> ingested -> processing -> completed

### Domain Workflows

| Domain | Trigger | Workflow | Output |
|--------|---------|----------|--------|
| **Fiscal** | Annual/quarterly report | YoY comparison against baseline period | `fiscal_diff.json` + `report.docx` |
| **Tender** | RFP or vendor response | Compliance matrix + vendor ranking | `matrix.json` + `report.docx` |
| **ESG** | ESG/sustainability report | Peer comparison against configured entity | `esg_comparison.json` + `report.docx` |

### Evaluation Dimensions

Configurable per domain in `dimensions/`:

- **Fiscal** (`fiscal_compare.json`): Revenue & Growth, Profitability & Margins, Cash Flow & Liquidity, Debt & Leverage, Operational Efficiency
- **Tender** (`tender_eval.json`): Security, Integration, Operations, Compliance, Cost, Timeline, Support, Scalability
- **ESG** (`esg_compare.json`): Emissions, Energy, Biodiversity, Social Impact, Governance & Compliance

## Output Artifacts

Each agent run produces outputs at `out/<domain>/<case_key>/<run_id>/`:

| File | Description |
|------|-------------|
| `decision.json` | Full decision contract (classification, baseline, actions, gates) |
| `trace.jsonl` | Execution trace with timestamps and tool calls |
| `report.docx` | Generated DOCX report |
| `matrix.json` / `fiscal_diff.json` / `esg_comparison.json` | Domain-specific analysis data |
| `human_question.json` | Emitted when the agent needs additional documents |
| `LATEST.json` | Points to the most recent run for a case |

## Dependency Resolution / Awaiting Conditions

When a document is uploaded and the agent determines that prerequisites are missing (e.g., an RFP for a vendor response, or a prior-period report for fiscal comparison), it records **awaiting conditions** in the registry's `case_memory` table. When a subsequent document arrives, the system checks whether it satisfies any open condition and, if so, resumes the case automatically.

Causal linkage is recorded in `decision.json`:

```json
{
  "schema_version": "2.2",
  "awaiting_conditions": [
    {
      "kind": "needs_rfp",
      "match": {"domain": "tender", "doc_role": "rfp"},
      "description": "Tender case 'ecopump africa ltd.' has vendor responses but no RFP."
    }
  ],
  "satisfied_conditions": [
    {
      "kind": "needs_rfp",
      "satisfied_case_key": "ecopump africa ltd.",
      "satisfied_run_id": "abc-123",
      "new_doc_id": "rfp-doc-456"
    }
  ],
  "resumed_cases": ["ecopump africa ltd."]
}
```

### Adding a new domain

Create a plugin in `agentic_orchestrator/domains/<name>.py` implementing the `DomainPlugin` protocol, add a dimensions JSON file, and register the plugin. No edits to core graph nodes are required.

## Semantic Filing

When enabled, the agent copies key artifacts (report, decision contract) to a business-friendly folder structure in addition to the standard `out/<domain>/<case_key>/<run_id>/` path.

Filing is configured in `config/agent_config.yaml`:

```yaml
filing:
  enabled: true
  base_path: ./filed_reports
  domain_folders:
    fiscal: fiscal_reports
    tender: rfp_docs
    esg: esg_reports
  default_folder: other_reports
```

This produces paths like `filed_reports/fiscal_reports/acme/fy2024/report.docx`. The filing decision is recorded in `decision.json` under the `filing` key.

## Configuration

### Environment Variables (`.env`)

```bash
# OCI compartment IDs
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaa...
COMPARTMENT_ID_DAC=ocid1.compartment.oc1..aaaaaaaa...    # for dedicated AI clusters

# Model endpoint IDs (from OCI Console > Generative AI > Endpoints)
OCI_GROK_3_MODEL_ID=ocid1.generativeaiendpoint.oc1.us-chicago-1.aaaaaaaa...
OCI_GROK_4_MODEL_ID=ocid1.generativeaiendpoint.oc1.us-chicago-1.aaaaaaaa...
OCI_LLAMA_3_3_MODEL_ID=ocid1.generativeaiendpoint.oc1.us-chicago-1.aaaaaaaa...
OCI_COHERE_COMMAND_A_MODEL_ID=ocid1.generativeaiendpoint.oc1.us-chicago-1.aaaaaaaa...

# Defaults (optional)
DEFAULT_EMBEDDING_MODEL=cohere-embed-multilingual-v3.0
DEFAULT_LLM_MODEL=grok-3
```

### Agent Config (`config/agent_config.yaml`)

```yaml
watcher:
  type: local                   # local | oci
  incoming_path: ./incoming
  poll_interval: 5              # seconds

registry:
  type: sqlite                  # sqlite | adb
  sqlite_path: ./registry.db

models:
  llm: grok-3
  embedder: cohere-embed-multilingual-v3.0

output:
  base_path: ./out

dimensions:
  fiscal: dimensions/fiscal_compare.json
  esg: dimensions/esg_compare.json
  tender: dimensions/tender_eval.json

our_entity: "acme"              # entity name for ESG peer comparison
confidence_threshold: 0.6       # below this, emit human_question
```

## LLM and Embedding Models

All models are accessed via OCI Generative AI through `llm_factory.py`, which provides a unified `OCIChat` wrapper compatible with LangChain's interface.

### LLM Models

| Model | Best for | Max output tokens |
|-------|----------|-------------------|
| **Grok-3** | Comprehensive reports | 16K |
| **Grok-4** | Advanced reasoning | 120K |
| **Llama 3.3** | Fast inference | 4K |
| **Cohere Command A** | Instruction following | 4K |

### Embedding Models

| Model | Dimensions | Notes |
|-------|-----------|-------|
| `cohere-embed-multilingual-v3.0` | 1024 | Default, multilingual support |
| `cohere-embed-v4.0` | 1024 | Latest Cohere embeddings |
| `chromadb-default` | 384 | Local, no OCI needed |

## Docker

A `docker-compose.yml` is provided for containerised deployment of the autonomous agent. Functionality is identical to running natively -- Docker just adds isolation and portability.

```bash
docker compose up
```

The `orchestrator-watcher` service mounts `./incoming` and `./out` as volumes and starts the watcher. Note: a `Dockerfile` needs to be created before this will work.

## Project Structure

```
files/
├── gradio_app.py                   # Interactive Gradio UI (port 7863)
├── llm_factory.py                  # Unified OCI LLM wrapper (OCIChat)
├── local_rag_agent.py              # Core RAG pipeline
├── vector_store.py                 # ChromaDB vector store
├── contracts.py                    # Pydantic models (Chunk, Plan, SectionDraft, Report)
├── oci_embedding_handler.py        # OCI embedding model manager
├── llm_concurrency.py              # Thread-safe LLM access
├── ingest_xlsx.py                  # XLSX ingestion pipeline
├── ingest_pdf.py                   # PDF ingestion pipeline
├── disable_telemetry.py            # Telemetry opt-out (side-effect import)
│
├── agents/
│   ├── agent_factory.py            # Agent classes: Planner, Researcher, ChunkRewriter
│   └── report_writer_agent.py      # Section and report writing agents
│
├── handlers/
│   ├── xlsx_handler.py             # Gradio XLSX upload handler
│   ├── pdf_handler.py              # Gradio PDF upload handler
│   ├── query_handler.py            # Gradio query/inference handler
│   └── vector_handler.py           # Gradio vector store management handler
│
├── agentic_orchestrator/           # Autonomous agent (LangGraph)
│   ├── __main__.py                 # Entry: python -m agentic_orchestrator
│   ├── cli.py                      # CLI: watch, process-doc-event
│   ├── doc_event_graph.py          # 10-node LangGraph StateGraph
│   ├── event_models.py             # Pydantic models + DocEventState
│   ├── config.py                   # YAML config loader + registry factory
│   ├── mcp_client.py               # In-process MCP client
│   ├── trace.py                    # Execution trace recorder
│   ├── decision_contract.py        # Decision serialisation
│   ├── filing/                     # Semantic filing resolver
│   │   └── filing_resolver.py      # Pure function: classification → filing path
│   ├── nodes/                      # Graph node implementations
│   │   ├── observe_event.py
│   │   ├── load_registry.py
│   │   ├── classify_event.py
│   │   ├── decide_actions.py
│   │   ├── ingest_embed_event.py
│   │   ├── action_executor.py
│   │   ├── quality_gates_event.py
│   │   ├── repair_event.py
│   │   ├── publish_event.py
│   │   └── update_registry_node.py
│   ├── registry/                   # Document registry backends
│   │   ├── base.py                 # DocumentRegistry Protocol
│   │   ├── sqlite_registry.py
│   │   └── adb_registry.py         # Oracle Autonomous DB backend
│   └── watchers/                   # File system watchers
│       ├── base.py                 # DocumentWatcher Protocol
│       ├── local_watcher.py        # Local filesystem (polling)
│       └── oci_watcher.py          # OCI Object Storage
│
├── mcp_rag_server/                 # MCP tool server (RAG tools)
├── mcp_storage_server/             # MCP tool server (storage tools)
│
├── dashboard_backend/              # Optional: FastAPI REST + WebSocket
│   ├── __main__.py
│   ├── app.py
│   ├── run_manager.py
│   └── ws_manager.py
├── dashboard_frontend/             # Optional: React + Vite + Tailwind
│
├── config/
│   └── agent_config.yaml           # Agent configuration
├── dimensions/                     # Evaluation dimension schemas
│   ├── fiscal_compare.json
│   ├── esg_compare.json
│   └── tender_eval.json
├── sample_queries/                 # Example prompts for the Gradio UI
│
├── tests/
│   ├── conftest.py                 # Shared fixtures (FakeLLM, FakeVectorStore, FakeMCP)
│   ├── test_contract_validation.py # Pydantic model tests
│   ├── test_classification.py      # Document classification tests
│   ├── test_baseline_selection.py  # Baseline selection logic tests
│   ├── test_registry_dedupe.py     # Registry deduplication tests
│   ├── test_doc_event_smoke.py     # End-to-end graph smoke tests
│   ├── test_smoke_pipeline.py      # RAG pipeline smoke tests (needs OCI)
│   └── test_typed_pipeline.py      # Typed pipeline tests (needs OCI)
│
├── requirements.txt                # Core dependencies
├── requirements-orchestrator.txt   # LangGraph dependency
├── requirements-dashboard.txt      # FastAPI/Uvicorn dependencies
└── docker-compose.yml              # Containerised watcher deployment
```

## Running Tests

```bash
# Unit tests (no OCI credentials needed)
pytest tests/ --ignore=tests/test_smoke_pipeline.py --ignore=tests/test_typed_pipeline.py -v

# Integration tests (requires OCI credentials and .env)
pytest tests/test_smoke_pipeline.py tests/test_typed_pipeline.py -v
```

## Troubleshooting

- **OCI Authentication Error** -- verify `~/.oci/config` exists and compartment IDs in `.env` are correct
- **Duplicate detected** -- the registry tracks content hashes; re-processing the same file is a no-op. Delete `registry.db` to reset.
- **Human question emitted** -- the agent needs additional documents (e.g., a baseline period report or an RFP). Check `human_question.json` in the run output.
- **Low confidence classification** -- use clearer filenames matching the expected patterns (e.g., `acme_FY2024_annual_report.pdf`)
- **Quality gate failures** -- the agent attempts one repair pass automatically. Check `trace.jsonl` for details.
