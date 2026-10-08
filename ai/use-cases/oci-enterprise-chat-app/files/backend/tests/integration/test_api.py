"""Integration tests for API endpoints."""

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from models.document import DocumentStatus, ExtractionResult, ExtractedParameter


class TestUploadEndpoint:
    """Tests for POST /api/upload endpoint."""

    def test_upload_valid_pdf(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful PDF upload."""
        response = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.pdf"
        assert data["file_size"] > 0
        assert data["message"] == "File uploaded successfully"

    def test_upload_invalid_content_type(
        self,
        test_client: TestClient,
    ) -> None:
        """Test upload rejection for non-PDF content type."""
        response = test_client.post(
            "/api/upload",
            files={"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")},
        )

        assert response.status_code == 415
        assert "not supported" in response.json()["detail"]

    def test_upload_invalid_extension(
        self,
        test_client: TestClient,
    ) -> None:
        """Test upload rejection for non-PDF extension."""
        response = test_client.post(
            "/api/upload",
            files={"file": ("test.doc", io.BytesIO(b"content"), "application/pdf")},
        )

        assert response.status_code == 415
        assert ".pdf" in response.json()["detail"]

    def test_upload_no_file(
        self,
        test_client: TestClient,
    ) -> None:
        """Test upload without file."""
        response = test_client.post("/api/upload")

        assert response.status_code == 422


class TestDocumentEndpoint:
    """Tests for GET /api/document/{document_id} endpoint."""

    def test_get_document_success(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful document retrieval."""
        # First upload a document
        upload_response = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )
        document_id = upload_response.json()["document_id"]

        # Then retrieve it
        response = test_client.get(f"/api/document/{document_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["metadata"]["filename"] == "test.pdf"
        assert data["status"] == "uploaded"

    def test_get_document_not_found(
        self,
        test_client: TestClient,
    ) -> None:
        """Test document retrieval with non-existent ID."""
        response = test_client.get("/api/document/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDocumentPdfEndpoint:
    """Tests for GET /api/document/{document_id}/pdf endpoint."""

    def test_get_pdf_success(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful PDF file retrieval."""
        # First upload a document
        upload_response = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )
        document_id = upload_response.json()["document_id"]

        # Then retrieve the PDF
        response = test_client.get(f"/api/document/{document_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers

    def test_get_pdf_not_found(
        self,
        test_client: TestClient,
    ) -> None:
        """Test PDF retrieval with non-existent ID."""
        response = test_client.get("/api/document/non-existent-id/pdf")

        assert response.status_code == 404


class TestExtractEndpoint:
    """Tests for POST /api/extract/{document_id} endpoint."""

    def test_extract_success(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
        mock_extraction_service,
    ) -> None:
        """Test successful extraction."""
        # Upload a document first
        upload_response = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )
        document_id = upload_response.json()["document_id"]

        # Mock the extraction service to return results
        mock_result = ExtractionResult(
            parameters=[
                ExtractedParameter(name="Date", value="2024-01-15", confidence=0.9),
                ExtractedParameter(name="Amount", value="$100", confidence=0.85),
            ],
            processing_time_ms=150.0,
        )

        with patch.object(
            mock_extraction_service,
            "extract_parameters",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = test_client.post(f"/api/extract/{document_id}")

        # Should return results (may use fallback extraction)
        assert response.status_code == 200
        data = response.json()
        assert "parameters" in data

    def test_extract_document_not_found(
        self,
        test_client: TestClient,
    ) -> None:
        """Test extraction with non-existent document."""
        response = test_client.post("/api/extract/non-existent-id")

        assert response.status_code == 404


class TestListDocumentsEndpoint:
    """Tests for GET /api/documents endpoint."""

    def test_list_documents_returns_ok(
        self,
        test_client: TestClient,
    ) -> None:
        """Test listing documents returns 200 OK."""
        response = test_client.get("/api/documents")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_documents_includes_uploaded(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test that uploaded documents appear in list."""
        # Upload a document
        upload_response = test_client.post(
            "/api/upload",
            files={"file": ("unique_test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )
        document_id = upload_response.json()["document_id"]

        # List documents
        response = test_client.get("/api/documents")

        assert response.status_code == 200
        documents = response.json()
        # Check that our uploaded document is in the list
        doc_ids = [doc["id"] for doc in documents]
        assert document_id in doc_ids


class TestDeleteDocumentEndpoint:
    """Tests for DELETE /api/document/{document_id} endpoint."""

    def test_delete_document_success(
        self,
        test_client: TestClient,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful document deletion."""
        # Upload a document first
        upload_response = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )
        document_id = upload_response.json()["document_id"]

        # Delete it
        delete_response = test_client.delete(f"/api/document/{document_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = test_client.get(f"/api/document/{document_id}")
        assert get_response.status_code == 404

    def test_delete_document_not_found(
        self,
        test_client: TestClient,
    ) -> None:
        """Test deletion of non-existent document."""
        response = test_client.delete("/api/document/non-existent-id")

        assert response.status_code == 404


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_check(
        self,
        test_client: TestClient,
    ) -> None:
        """Test health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aiq-rag-api"


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_endpoint(
        self,
        test_client: TestClient,
    ) -> None:
        """Test root endpoint returns API information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        assert "documentation" in data
