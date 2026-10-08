"""Pydantic models for document management and extraction."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Status of document processing."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractedParameter(BaseModel):
    """A single extracted parameter from the document."""

    name: str = Field(..., description="Name of the extracted parameter")
    value: Any = Field(..., description="Extracted value")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0-1)",
    )
    source_page: int | None = Field(
        default=None, description="Page number where the parameter was found"
    )
    source_text: str | None = Field(
        default=None, description="Source text snippet for context"
    )


class ComplianceEvidence(BaseModel):
    """A precise location in a document that supports a compliance finding."""

    page: int | None = Field(default=None, ge=1, description="One-based PDF page number")
    section: str | None = Field(default=None, description="Nearest detected section heading")
    quote: str = Field(..., description="Short source quote containing the match")
    matched_text: str = Field(..., description="Configured term or extracted field label")
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)


class ComplianceFinding(BaseModel):
    """A versioned compliance-rule result with source evidence."""

    rule_id: str
    category: str = ""
    status: Literal["pass", "warning", "review", "fail", "not_assessable"] = "review"
    message: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    extracted_value: str | None = None
    evidence: list[ComplianceEvidence] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_human_review: bool = True


class ComplianceAssessment(BaseModel):
    """Durable outcome of one document assessment against one ruleset version."""

    industry: str
    ruleset_version: str
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    document_sha256: str | None = None
    assessment_status: Literal["completed", "not_assessable", "failed"] = "completed"
    error_message: str | None = None
    findings: list[ComplianceFinding] = Field(default_factory=list)
    review_status: Literal["pending", "approved", "changes_requested"] = "pending"
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


class ComplianceAuditEvent(BaseModel):
    """Append-only audit metadata for compliance assessment and review actions."""

    event_type: Literal["assessment_created", "review_recorded"]
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    actor: str | None = None
    ruleset_version: str | None = None
    document_sha256: str | None = None
    details: str | None = None


class ExtractionResult(BaseModel):
    """Result of RAG extraction process."""

    parameters: list[ExtractedParameter] = Field(
        default_factory=list, description="List of extracted parameters"
    )
    raw_response: dict[str, Any] | None = Field(
        default=None, description="Raw API response for debugging"
    )
    processing_time_ms: float | None = Field(
        default=None, description="Time taken for extraction in milliseconds"
    )
    error_message: str | None = Field(
        default=None, description="Error message if extraction failed"
    )
    compliance_assessment: ComplianceAssessment | None = Field(
        default=None,
        description="Latest persisted evidence-backed compliance assessment",
    )


class DocumentMetadata(BaseModel):
    """Metadata about an uploaded document."""

    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    page_count: int | None = Field(default=None, description="Number of pages in PDF")
    upload_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the document was uploaded"
    )
    content_type: str = Field(default="application/pdf", description="MIME type")


class Document(BaseModel):
    """Complete document record with metadata and extraction results."""

    id: str = Field(..., description="Unique document identifier")
    user_id: str | None = Field(default=None, description="Owner user ID")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED, description="Current processing status"
    )
    extraction_result: ExtractionResult | None = Field(
        default=None, description="Extraction results if processing is complete"
    )
    compliance_audit_log: list[ComplianceAuditEvent] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class WebSourceStatus(str, Enum):
    """Status of web source processing."""

    PENDING = "pending"
    SCRAPING = "scraping"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebSource(BaseModel):
    """A scraped web source record."""

    id: str = Field(..., description="Unique web source identifier")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Page title or user-provided title")
    user_id: str | None = Field(default=None, description="Owner user ID")
    status: WebSourceStatus = Field(default=WebSourceStatus.PENDING)
    text_content: str | None = Field(default=None, description="Extracted text")
    content_length: int | None = Field(default=None, description="Length of extracted text")
    chunks_indexed: int | None = Field(default=None, description="Number of vector chunks indexed")
    error_message: str | None = Field(default=None, description="Error if scraping failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UploadResponse(BaseModel):
    """Response returned after successful file upload."""

    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    message: str = Field(default="File uploaded successfully")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Error type or code")
    detail: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the error occurred"
    )
