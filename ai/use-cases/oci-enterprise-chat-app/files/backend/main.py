"""FastAPI application entry point for AIQ RAG Application."""

import logging
import os
import sys
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.document import ErrorResponse
from routers.documents import router as documents_router, set_services
from routers.auth import router as auth_router
from routers.directory import router as directory_router
from routers.web_sources import router as web_sources_router, set_services as set_web_services
from routers.batch import router as batch_router, set_services as set_batch_services
from routers.workflows import router as workflows_router, set_services as set_workflow_services
from services.workflow_storage import WorkflowStorageService
from services.workflow_engine import WorkflowEngine
from routers.research import router as research_router
from routers.compliance import router as compliance_router
from routers.domains import router as domains_router
from routers.metrics import router as metrics_router, set_services as set_metrics_services
from services.extraction import ExtractionService
from services.storage import StorageService
from services.web_scraper import WebScraperService
from services.batch_service import BatchService
from services.scheduler import scheduler_service
from services.oracle_vector_store import OracleVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Application settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# CORS allowed origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://frontend-paas.170-9-255-66.nip.io",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

# Add any additional origins from environment
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    CORS_ORIGINS.extend([o.strip() for o in additional_origins.split(",") if o.strip()])


# Service instances
storage_service: StorageService | None = None
extraction_service: ExtractionService | None = None
web_scraper_service: WebScraperService | None = None
batch_service: BatchService | None = None
oracle_vector_store: OracleVectorStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global storage_service, extraction_service, web_scraper_service, batch_service, oracle_vector_store

    # Startup
    logger.info("Starting AIQ RAG Application...")

    # Initialize services
    storage_service = StorageService(upload_dir=UPLOAD_DIR)
    extraction_service = ExtractionService()
    web_scraper_service = WebScraperService()
    batch_service = BatchService(upload_dir=UPLOAD_DIR)
    oracle_vector_store = OracleVectorStore()

    # Set services in routers
    set_services(storage=storage_service, extraction=extraction_service)
    set_web_services(storage=storage_service, web_scraper=web_scraper_service)
    set_batch_services(batch=batch_service)
    set_metrics_services(storage=storage_service)

    workflow_storage = WorkflowStorageService(upload_dir=UPLOAD_DIR)
    set_workflow_services(storage=workflow_storage, engine=WorkflowEngine(workflow_storage))
    scheduler_service._storage = workflow_storage
    scheduler_service._batch_service = batch_service
    scheduler_service.start()
    worker = None
    if os.getenv("BATCH_WORKER_ENABLED", "true").lower() in ("true", "1", "yes"):
        worker = subprocess.Popen([sys.executable, str(Path(__file__).parent / "batch_worker.py")],
                                  env={**os.environ, "UPLOAD_DIR": str(Path(UPLOAD_DIR).resolve())})

    logger.info(f"Upload directory: {Path(UPLOAD_DIR).absolute()}")
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AIQ RAG Application...")
    scheduler_service.shutdown()
    if worker is not None:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait()
    if oracle_vector_store:
        await oracle_vector_store.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AIQ RAG Application API",
    description="""
    Retrieval-Augmented Generation API for processing PDF documents
    and extracting key parameters using NVIDIA AIQ.

    ## Features

    - **PDF Upload**: Upload PDF documents for processing
    - **Parameter Extraction**: Extract key information using RAG
    - **Document Management**: Track document status and retrieve results

    ## Usage

    1. Upload a PDF using `POST /api/upload`
    2. Trigger extraction using `POST /api/extract/{document_id}`
    3. Check status and results using `GET /api/document/{document_id}`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions with a structured error response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="internal_server_error",
        detail="An unexpected error occurred. Please try again later.",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


# Include routers
app.include_router(auth_router)
app.include_router(directory_router)
app.include_router(documents_router)
app.include_router(web_sources_router)
app.include_router(batch_router)
app.include_router(workflows_router)
app.include_router(research_router)
app.include_router(compliance_router)
app.include_router(domains_router)
app.include_router(metrics_router)


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status information.
    """
    health_status = {
        "status": "healthy",
        "service": "aiq-rag-api",
        "version": "1.0.0",
    }

    return health_status


# Oracle Vector Database validation endpoint
@app.get(
    "/health/oracle-vector-db",
    tags=["health"],
    summary="Oracle Vector Database health check",
    description="Validate Oracle Vector Database connection and functionality.",
)
async def oracle_vector_db_health() -> dict[str, Any]:
    """Oracle Vector Database health check endpoint.

    Returns:
        Oracle Vector Database connection status and statistics.
    """
    if oracle_vector_store is None:
        return {
            "status": "unavailable",
            "error": "Oracle Vector Store service not initialized",
            "service": "oracle-vector-db",
        }

    try:
        health_result = await oracle_vector_store.health_check()
        health_result["service"] = "oracle-vector-db"
        return health_result
    except Exception as e:
        logger.error(f"Oracle Vector Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": f"Health check failed: {str(e)}",
            "service": "oracle-vector-db",
        }


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API Information",
    description="Get basic API information and links to documentation.",
)
async def root() -> dict[str, Any]:
    """Root endpoint with API information.

    Returns:
        API information and documentation links.
    """
    return {
        "name": "AIQ RAG Application API",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation API for PDF document processing",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "upload": "POST /api/upload",
            "extract": "POST /api/extract/{document_id}",
            "document": "GET /api/document/{document_id}",
            "pdf": "GET /api/document/{document_id}/pdf",
            "documents": "GET /api/documents",
            "delete": "DELETE /api/document/{document_id}",
            "health": "GET /health",
            "oracle_vector_db_health": "GET /health/oracle-vector-db",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
