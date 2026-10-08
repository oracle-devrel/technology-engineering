"""Pytest configuration and fixtures for AIQ RAG Application tests."""

import asyncio
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from main import app
from routers.documents import set_services
from services.extraction import ExtractionService
from services.storage import StorageService


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_upload_dir() -> Generator[Path, None, None]:
    """Create a temporary upload directory for tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aiq_rag_test_"))
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def storage_service(temp_upload_dir: Path) -> StorageService:
    """Create a storage service with a temporary directory."""
    return StorageService(upload_dir=temp_upload_dir)


@pytest.fixture
def extraction_service() -> ExtractionService:
    """Create an extraction service for testing."""
    return ExtractionService()


@pytest.fixture
def mock_extraction_service() -> ExtractionService:
    """Create a mock extraction service for tests."""
    return ExtractionService()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate minimal valid PDF bytes for testing."""
    # This is a minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
306
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_pdf_file(sample_pdf_bytes: bytes) -> io.BytesIO:
    """Create a file-like object with sample PDF content."""
    return io.BytesIO(sample_pdf_bytes)


@pytest.fixture
def test_client(
    temp_upload_dir: Path,
    mock_extraction_service: ExtractionService,
) -> Generator[TestClient, None, None]:
    """Create a test client with mocked services."""
    # Create storage service with temp directory
    storage = StorageService(upload_dir=temp_upload_dir)

    # Set services in router
    set_services(storage=storage, extraction=mock_extraction_service)

    with TestClient(app) as client:
        yield client

    # Reset services
    set_services(storage=None, extraction=None)


@pytest.fixture
async def async_client(
    temp_upload_dir: Path,
    mock_extraction_service: ExtractionService,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    # Create storage service with temp directory
    storage = StorageService(upload_dir=temp_upload_dir)

    # Set services in router
    set_services(storage=storage, extraction=mock_extraction_service)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    # Reset services
    set_services(storage=None, extraction=None)


@pytest.fixture
def sample_document_text() -> str:
    """Sample document text for extraction testing."""
    return """
    PURCHASE AGREEMENT

    Date: January 15, 2024

    This agreement is entered into between:

    Seller: ABC Corporation
    Address: 123 Main Street, New York, NY 10001
    Email: sales@abc-corp.com
    Phone: (555) 123-4567

    Buyer: John Smith
    Address: 456 Oak Avenue, Los Angeles, CA 90001
    Email: john.smith@email.com

    Purchase Amount: $150,000.00
    Down Payment: 20%
    Interest Rate: 5.5%

    Terms and Conditions:
    - Payment due within 30 days
    - 2% late fee applies after due date
    - Contract effective until December 31, 2025
    """
