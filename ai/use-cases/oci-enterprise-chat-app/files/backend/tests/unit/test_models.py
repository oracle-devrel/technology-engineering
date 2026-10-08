"""Unit tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from models.document import (
    Document,
    DocumentMetadata,
    DocumentStatus,
    ExtractedParameter,
    ExtractionResult,
    UploadResponse,
    ErrorResponse,
)


class TestExtractedParameter:
    """Tests for ExtractedParameter model."""

    def test_create_minimal(self) -> None:
        """Test creating with minimal required fields."""
        param = ExtractedParameter(name="Date", value="2024-01-15")

        assert param.name == "Date"
        assert param.value == "2024-01-15"
        assert param.confidence is None
        assert param.source_page is None
        assert param.source_text is None

    def test_create_full(self) -> None:
        """Test creating with all fields."""
        param = ExtractedParameter(
            name="Amount",
            value=150000.0,
            confidence=0.95,
            source_page=1,
            source_text="Total amount: $150,000",
        )

        assert param.name == "Amount"
        assert param.value == 150000.0
        assert param.confidence == 0.95
        assert param.source_page == 1
        assert param.source_text == "Total amount: $150,000"

    def test_confidence_validation_min(self) -> None:
        """Test confidence must be >= 0."""
        with pytest.raises(ValidationError):
            ExtractedParameter(name="Test", value="test", confidence=-0.1)

    def test_confidence_validation_max(self) -> None:
        """Test confidence must be <= 1."""
        with pytest.raises(ValidationError):
            ExtractedParameter(name="Test", value="test", confidence=1.1)

    def test_value_accepts_various_types(self) -> None:
        """Test value field accepts different types."""
        # String
        param1 = ExtractedParameter(name="Name", value="John Doe")
        assert param1.value == "John Doe"

        # Number
        param2 = ExtractedParameter(name="Amount", value=100.50)
        assert param2.value == 100.50

        # List
        param3 = ExtractedParameter(name="Items", value=["item1", "item2"])
        assert param3.value == ["item1", "item2"]

        # Dict
        param4 = ExtractedParameter(name="Details", value={"key": "value"})
        assert param4.value == {"key": "value"}


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_create_default(self) -> None:
        """Test creating with defaults."""
        result = ExtractionResult()

        assert result.parameters == []
        assert result.raw_response is None
        assert result.processing_time_ms is None
        assert result.error_message is None

    def test_create_with_parameters(self) -> None:
        """Test creating with parameters."""
        params = [
            ExtractedParameter(name="Date", value="2024-01-15"),
            ExtractedParameter(name="Amount", value="$100"),
        ]
        result = ExtractionResult(
            parameters=params,
            processing_time_ms=150.5,
        )

        assert len(result.parameters) == 2
        assert result.processing_time_ms == 150.5

    def test_create_with_error(self) -> None:
        """Test creating with error message."""
        result = ExtractionResult(
            parameters=[],
            error_message="API timeout",
            processing_time_ms=30000.0,
        )

        assert result.error_message == "API timeout"


class TestDocumentMetadata:
    """Tests for DocumentMetadata model."""

    def test_create_minimal(self) -> None:
        """Test creating with minimal required fields."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            file_size=1024,
        )

        assert metadata.filename == "test.pdf"
        assert metadata.file_size == 1024
        assert metadata.page_count is None
        assert metadata.content_type == "application/pdf"
        assert isinstance(metadata.upload_timestamp, datetime)

    def test_create_full(self) -> None:
        """Test creating with all fields."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        metadata = DocumentMetadata(
            filename="contract.pdf",
            file_size=2048,
            page_count=10,
            upload_timestamp=timestamp,
            content_type="application/pdf",
        )

        assert metadata.filename == "contract.pdf"
        assert metadata.file_size == 2048
        assert metadata.page_count == 10
        assert metadata.upload_timestamp == timestamp

    def test_file_size_non_negative(self) -> None:
        """Test file size must be non-negative."""
        with pytest.raises(ValidationError):
            DocumentMetadata(filename="test.pdf", file_size=-1)


class TestDocument:
    """Tests for Document model."""

    def test_create_minimal(self) -> None:
        """Test creating with minimal required fields."""
        metadata = DocumentMetadata(filename="test.pdf", file_size=1024)
        document = Document(id="doc-123", metadata=metadata)

        assert document.id == "doc-123"
        assert document.metadata.filename == "test.pdf"
        assert document.status == DocumentStatus.UPLOADED
        assert document.extraction_result is None
        assert isinstance(document.created_at, datetime)
        assert isinstance(document.updated_at, datetime)

    def test_create_full(self) -> None:
        """Test creating with all fields."""
        metadata = DocumentMetadata(filename="test.pdf", file_size=1024, page_count=5)
        extraction = ExtractionResult(
            parameters=[ExtractedParameter(name="Date", value="2024-01-15")]
        )

        document = Document(
            id="doc-456",
            metadata=metadata,
            status=DocumentStatus.COMPLETED,
            extraction_result=extraction,
        )

        assert document.id == "doc-456"
        assert document.status == DocumentStatus.COMPLETED
        assert len(document.extraction_result.parameters) == 1

    def test_status_enum_values(self) -> None:
        """Test all status enum values are valid."""
        metadata = DocumentMetadata(filename="test.pdf", file_size=1024)

        for status in DocumentStatus:
            document = Document(id="doc-test", metadata=metadata, status=status)
            assert document.status == status

    def test_json_serialization(self) -> None:
        """Test JSON serialization."""
        metadata = DocumentMetadata(filename="test.pdf", file_size=1024)
        document = Document(id="doc-789", metadata=metadata)

        json_data = document.model_dump(mode="json")

        assert json_data["id"] == "doc-789"
        assert json_data["metadata"]["filename"] == "test.pdf"
        assert json_data["status"] == "uploaded"
        assert isinstance(json_data["created_at"], str)


class TestUploadResponse:
    """Tests for UploadResponse model."""

    def test_create(self) -> None:
        """Test creating upload response."""
        response = UploadResponse(
            document_id="doc-123",
            filename="test.pdf",
            file_size=1024,
        )

        assert response.document_id == "doc-123"
        assert response.filename == "test.pdf"
        assert response.file_size == 1024
        assert response.message == "File uploaded successfully"

    def test_custom_message(self) -> None:
        """Test creating with custom message."""
        response = UploadResponse(
            document_id="doc-456",
            filename="contract.pdf",
            file_size=2048,
            message="Document received",
        )

        assert response.message == "Document received"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_create(self) -> None:
        """Test creating error response."""
        response = ErrorResponse(
            error="validation_error",
            detail="File type not supported",
        )

        assert response.error == "validation_error"
        assert response.detail == "File type not supported"
        assert isinstance(response.timestamp, datetime)

    def test_json_serialization(self) -> None:
        """Test JSON serialization."""
        response = ErrorResponse(
            error="not_found",
            detail="Document does not exist",
        )

        json_data = response.model_dump(mode="json")

        assert json_data["error"] == "not_found"
        assert json_data["detail"] == "Document does not exist"
        assert isinstance(json_data["timestamp"], str)
