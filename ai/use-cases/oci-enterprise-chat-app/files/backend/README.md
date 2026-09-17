# AIQ RAG Application Backend

A FastAPI-based backend for the Retrieval-Augmented Generation (RAG) application that processes PDF documents and extracts key parameters using NVIDIA AIQ.

## Features

- **PDF Upload**: Upload PDF documents for processing
- **Parameter Extraction**: Extract key information (dates, amounts, names, emails, etc.) using RAG
- **Document Management**: Track document status, retrieve results, and manage files
- **Microsoft Entra ID configuration**: Admin-only OIDC configuration, group-to-role mappings, and OpenID discovery checks
- **CORS Support**: Configured for frontend integration
- **Fallback Extraction**: Local regex-based extraction when API is unavailable

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration and tool settings
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── .env.example         # Environment variables template
├── routers/
│   └── documents.py     # Document-related API endpoints
├── services/
│   ├── extraction.py    # RAG extraction service
│   └── storage.py       # File storage service
├── models/
│   └── document.py      # Pydantic models
├── tests/
│   ├── conftest.py      # Pytest fixtures
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
└── uploads/             # PDF storage directory
```

## Requirements

- Python 3.11+
- pip or a package manager

## Setup

### 1. Create a Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

For development (includes testing and linting tools):

```bash
pip install -r requirements.txt
# Or with all dev dependencies
pip install -e ".[dev]"
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `UPLOAD_DIR` | Directory for uploaded files | `uploads` |
| `CORRINO_API_URL` | NVIDIA AIQ Corrino API URL | `https://api.170-9-255-66.nip.io` |
| `CORRINO_API_KEY` | API key for authentication | (empty) |
| `CORS_ORIGINS` | Additional CORS origins | (empty) |
| `ENTRA_TENANT_ID` | Microsoft Entra tenant ID or verified tenant domain | (empty) |
| `ENTRA_CLIENT_ID` | Microsoft Entra application (client) ID | (empty) |
| `ENTRA_CLIENT_SECRET` | Microsoft Entra confidential-client secret; inject from a secret store | (empty) |
| `ENTRA_REDIRECT_URI` | Registered OIDC redirect URI | (empty) |
| `ENTRA_GROUP_SYNC_ENABLED` | Enable configured group-to-role mappings | `false` |

### 4. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Running the Application

### Development Mode

```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py script
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Upload Document

```bash
POST /api/upload
Content-Type: multipart/form-data

# Example with curl
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

Response:
```json
{
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "file_size": 12345,
  "message": "File uploaded successfully"
}
```

### Extract Parameters

```bash
POST /api/extract/{document_id}

# Example
curl -X POST http://localhost:8000/api/extract/uuid-here
```

Response:
```json
{
  "parameters": [
    {
      "name": "Date",
      "value": "January 15, 2024",
      "confidence": 0.95,
      "source_page": 1,
      "source_text": "Contract date: January 15, 2024"
    }
  ],
  "processing_time_ms": 150.5
}
```

### Get Document Metadata

```bash
GET /api/document/{document_id}

# Example
curl http://localhost:8000/api/document/uuid-here
```

### Download PDF

```bash
GET /api/document/{document_id}/pdf

# Example
curl http://localhost:8000/api/document/uuid-here/pdf --output document.pdf
```

### List All Documents

```bash
GET /api/documents

# Example
curl http://localhost:8000/api/documents
```

### Delete Document

```bash
DELETE /api/document/{document_id}

# Example
curl -X DELETE http://localhost:8000/api/document/uuid-here
```

### Health Check

```bash
GET /health

# Example
curl http://localhost:8000/health
```

### Configure Microsoft Entra ID

The administrator can configure the Active Directory card in Profile Settings. The browser calls these authenticated endpoints:

- `GET /api/auth/directory` — safe-to-display configuration for signed-in users
- `PUT /api/auth/directory` — admin-only OIDC configuration; `client_secret` is write-only
- `POST /api/auth/directory/test-connection` — admin-only OpenID discovery check

For persistent deployments, set the `ENTRA_*` values through the deployment secret store. Runtime changes made in the UI are intentionally held only in memory so a directory client secret is not written to the application filesystem.

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
# View coverage report at coverage_html/index.html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_storage.py

# Specific test
pytest tests/unit/test_storage.py::TestStorageService::test_save_file_success
```

## Code Quality

### Linting

```bash
# Check code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Formatting

```bash
# Check formatting
ruff format --check .

# Apply formatting
ruff format .
```

### Type Checking

```bash
mypy .
```

### Run All Pre-commit Checks

```bash
pre-commit run --all-files
```

## Architecture

### Services

- **StorageService**: Handles file storage, metadata persistence, and PDF text extraction
- **ExtractionService**: Interfaces with NVIDIA AIQ Corrino API for RAG-based parameter extraction

### Data Flow

1. User uploads PDF via `/api/upload`
2. File is stored locally and metadata is persisted
3. User triggers extraction via `/api/extract/{document_id}`
4. Text is extracted from PDF using pdfplumber
5. Text is sent to Corrino API for parameter extraction
6. Results are stored and returned to user

### Error Handling

- Proper HTTP status codes (400, 404, 413, 415, 422, 500)
- Structured error responses with timestamps
- Graceful fallback to local extraction when API is unavailable

## CORS Configuration

The API allows requests from:
- `http://localhost:3000`
- `https://frontend-paas.170-9-255-66.nip.io`
- `http://localhost:8000`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8000`

Additional origins can be configured via the `CORS_ORIGINS` environment variable.

## License

MIT

### Workflow and batch runtime (PRD3)

Workflow definitions, schedules and execution history are stored under
`UPLOAD_DIR/.workflow_metadata`. Batch connectors, triggers and jobs use
`UPLOAD_DIR/.batch_metadata`. Configure the same `UPLOAD_DIR` for API and worker.

The API starts a separate batch worker automatically. To supervise workers
independently, set `BATCH_WORKER_ENABLED=false` on the API and run
`venv/bin/python batch_worker.py` from this directory. Workers claim persisted
jobs with OS file locks and respect each job's parallelism (maximum
`MAX_BATCH_PARALLELISM`, default 5). Pending work survives restarts; interrupted
running work is marked failed for explicit review/retry. This is a local
filesystem queue. Run only one scheduler instance per store; a distributed
broker/leader election is not included.

Recurring schedules use UTC with standard weekday numbers (Sunday 0/7, Monday
1). One-time timestamps accept an explicit offset and are normalized to UTC.
Agents require `RAG_ENDPOINT_URL` and use `RAG_MODEL` / `RAG_API_KEY` when set.
OCI connections use the existing server-side SDK configuration or instance
principal; vectorization uses the existing embedding and Oracle DB settings.

For same-origin development, start Vite with `VITE_API_URL=''` and optionally
`LOCAL_BACKEND_URL=http://127.0.0.1:8000`. Workflow and batch paths go to this
backend; other API paths retain the configured EnterpriseAI proxy. Production
Nginx also routes workflow and batch paths to `backend-service:8000`.

See `../notes/PRD3-workflow-validation.md` for requirements, checks and known
runtime limits. Regression tests use isolated storage and controlled service
responses: `BATCH_WORKER_ENABLED=false venv/bin/python -m pytest --no-cov -q`.
