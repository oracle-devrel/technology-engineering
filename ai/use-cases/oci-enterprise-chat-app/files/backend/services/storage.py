"""File storage service for managing PDF documents."""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import pdfplumber

from models.document import (
    ComplianceAuditEvent,
    ComplianceAssessment,
    Document,
    DocumentMetadata,
    DocumentStatus,
    ExtractionResult,
    WebSource,
    WebSourceStatus,
)

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Exception raised for storage-related errors."""

    pass


class DocumentNotFoundError(StorageError):
    """Exception raised when a document is not found."""

    pass


class StorageService:
    """Service for managing document storage and metadata."""

    def __init__(self, upload_dir: str | Path = "uploads") -> None:
        """Initialize the storage service.

        Args:
            upload_dir: Directory path for storing uploaded files.
        """
        self.upload_dir = Path(upload_dir)
        self.metadata_dir = self.upload_dir / ".metadata"
        self.web_metadata_dir = self.upload_dir / ".web_metadata"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.web_metadata_dir.mkdir(parents=True, exist_ok=True)

    def _generate_document_id(self) -> str:
        """Generate a unique document ID.

        Returns:
            A unique string identifier.
        """
        return str(uuid.uuid4())

    def _get_file_path(self, document_id: str) -> Path:
        """Get the file path for a document.

        Args:
            document_id: The document identifier.

        Returns:
            Path to the PDF file.
        """
        return self.upload_dir / f"{document_id}.pdf"

    def _get_metadata_path(self, document_id: str) -> Path:
        """Get the metadata file path for a document.

        Args:
            document_id: The document identifier.

        Returns:
            Path to the metadata JSON file.
        """
        return self.metadata_dir / f"{document_id}.json"

    def _count_pdf_pages(self, file_path: Path) -> int | None:
        """Count the number of pages in a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Number of pages, or None if counting failed.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.warning(f"Failed to count PDF pages: {e}")
            return None

    def _save_metadata(self, document: Document) -> None:
        """Save document metadata to disk.

        Args:
            document: The document to save.
        """
        metadata_path = self._get_metadata_path(document.id)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(document.model_dump(mode="json"), f, indent=2, default=str)

    def _load_metadata(self, document_id: str) -> Document:
        """Load document metadata from disk.

        Args:
            document_id: The document identifier.

        Returns:
            The loaded Document object.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        metadata_path = self._get_metadata_path(document_id)
        if not metadata_path.exists():
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Document.model_validate(data)

    async def save_file(
        self, file: BinaryIO, filename: str, content_type: str, user_id: str | None = None
    ) -> Document:
        """Save an uploaded file and create a document record.

        Args:
            file: The file object to save.
            filename: Original filename.
            content_type: MIME type of the file.
            user_id: Optional owner user ID.

        Returns:
            The created Document object.

        Raises:
            StorageError: If file saving fails.
        """
        document_id = self._generate_document_id()
        file_path = self._get_file_path(document_id)

        try:
            # Read file content
            content = file.read()
            file_size = len(content)

            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(content)

            # Count PDF pages
            page_count = self._count_pdf_pages(file_path)

            # Create document metadata
            metadata = DocumentMetadata(
                filename=filename,
                file_size=file_size,
                page_count=page_count,
                upload_timestamp=datetime.utcnow(),
                content_type=content_type,
            )

            # Create document record
            document = Document(
                id=document_id,
                user_id=user_id,
                metadata=metadata,
                status=DocumentStatus.UPLOADED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Save metadata
            self._save_metadata(document)

            logger.info(f"Saved document {document_id}: {filename} ({file_size} bytes) for user {user_id}")
            return document

        except Exception as e:
            # Clean up on failure
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to save file: {e}")
            raise StorageError(f"Failed to save file: {e}") from e

    async def get_document(self, document_id: str) -> Document:
        """Retrieve a document by ID.

        Args:
            document_id: The document identifier.

        Returns:
            The Document object.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        return self._load_metadata(document_id)

    async def get_file_path(self, document_id: str) -> Path:
        """Get the file path for a document.

        Args:
            document_id: The document identifier.

        Returns:
            Path to the PDF file.

        Raises:
            DocumentNotFoundError: If the document or file doesn't exist.
        """
        # Verify document exists
        await self.get_document(document_id)

        file_path = self._get_file_path(document_id)
        if not file_path.exists():
            raise DocumentNotFoundError(f"File not found for document: {document_id}")

        return file_path

    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        extraction_result: ExtractionResult | None = None,
    ) -> Document:
        """Update the status and extraction result of a document.

        Args:
            document_id: The document identifier.
            status: New status to set.
            extraction_result: Optional extraction result.

        Returns:
            The updated Document object.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        document = await self.get_document(document_id)

        document.status = status
        document.updated_at = datetime.utcnow()

        if extraction_result is not None:
            document.extraction_result = extraction_result

        self._save_metadata(document)

        logger.info(f"Updated document {document_id} status to {status.value}")
        return document

    def get_document_sha256(self, document_id: str) -> str:
        """Return the SHA-256 digest of the stored PDF for an audit record."""
        file_path = self._get_file_path(document_id)
        if not file_path.exists():
            raise DocumentNotFoundError(f"File not found for document: {document_id}")

        digest = hashlib.sha256()
        with open(file_path, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def update_compliance_assessment(
        self, document_id: str, assessment: ComplianceAssessment
    ) -> Document:
        """Persist the latest evidence-backed compliance assessment for a document."""
        document = await self.get_document(document_id)
        if document.extraction_result is None:
            document.extraction_result = ExtractionResult()

        document.extraction_result.compliance_assessment = assessment
        document.compliance_audit_log.append(
            ComplianceAuditEvent(
                event_type="assessment_created",
                ruleset_version=assessment.ruleset_version,
                document_sha256=assessment.document_sha256,
                details=f"{len(assessment.findings)} rule findings; {assessment.assessment_status}",
            )
        )
        document.updated_at = datetime.utcnow()
        self._save_metadata(document)
        logger.info("Persisted compliance assessment for document %s", document_id)
        return document

    async def review_compliance_assessment(
        self,
        document_id: str,
        review_status: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ) -> Document:
        """Record an accountable human decision against the latest assessment."""
        document = await self.get_document(document_id)
        assessment = (
            document.extraction_result.compliance_assessment
            if document.extraction_result is not None
            else None
        )
        if assessment is None:
            raise StorageError("No compliance assessment exists for this document")

        assessment.review_status = review_status
        assessment.reviewed_by = reviewed_by
        assessment.reviewed_at = datetime.utcnow()
        assessment.review_notes = review_notes
        document.compliance_audit_log.append(
            ComplianceAuditEvent(
                event_type="review_recorded",
                actor=reviewed_by,
                ruleset_version=assessment.ruleset_version,
                document_sha256=assessment.document_sha256,
                details=f"{review_status}: {review_notes or 'No review note provided'}",
            )
        )
        document.updated_at = datetime.utcnow()
        self._save_metadata(document)
        logger.info("Recorded %s review for document %s", review_status, document_id)
        return document

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and its associated files.

        Args:
            document_id: The document identifier.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        # Verify document exists
        await self.get_document(document_id)

        # Delete files
        file_path = self._get_file_path(document_id)
        metadata_path = self._get_metadata_path(document_id)

        if file_path.exists():
            file_path.unlink()

        if metadata_path.exists():
            metadata_path.unlink()

        logger.info(f"Deleted document {document_id}")

    async def list_documents(self, user_id: str | None = None) -> list[Document]:
        """List all documents, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter documents.

        Returns:
            List of Document objects.
        """
        documents = []

        for metadata_file in self.metadata_dir.glob("*.json"):
            document_id = metadata_file.stem
            try:
                document = await self.get_document(document_id)
                # Filter by user if specified
                if user_id is None or document.user_id == user_id:
                    documents.append(document)
            except Exception as e:
                logger.warning(f"Failed to load document {document_id}: {e}")

        # Sort by creation date, newest first
        documents.sort(key=lambda d: d.created_at, reverse=True)
        return documents

    # --- Web Source Methods ---

    def _get_web_metadata_path(self, web_source_id: str) -> Path:
        return self.web_metadata_dir / f"{web_source_id}.json"

    def _save_web_metadata(self, web_source: WebSource) -> None:
        path = self._get_web_metadata_path(web_source.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(web_source.model_dump(mode="json"), f, indent=2, default=str)

    def save_web_source(self, url: str, title: str, user_id: str | None = None) -> WebSource:
        """Create a new web source record."""
        ws = WebSource(
            id=str(uuid.uuid4()),
            url=url,
            title=title or url,
            user_id=user_id,
            status=WebSourceStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._save_web_metadata(ws)
        logger.info(f"Created web source {ws.id}: {url}")
        return ws

    def get_web_source(self, web_source_id: str) -> WebSource:
        """Load a web source by ID. Raises DocumentNotFoundError if missing."""
        path = self._get_web_metadata_path(web_source_id)
        if not path.exists():
            raise DocumentNotFoundError(f"Web source not found: {web_source_id}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return WebSource.model_validate(data)

    def update_web_source(self, web_source_id: str, **updates) -> WebSource:
        """Update web source fields and save."""
        ws = self.get_web_source(web_source_id)
        for key, value in updates.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        ws.updated_at = datetime.utcnow()
        self._save_web_metadata(ws)
        return ws

    def delete_web_source(self, web_source_id: str) -> None:
        """Delete a web source metadata file."""
        path = self._get_web_metadata_path(web_source_id)
        if not path.exists():
            raise DocumentNotFoundError(f"Web source not found: {web_source_id}")
        path.unlink()
        logger.info(f"Deleted web source {web_source_id}")

    def list_web_sources(self, user_id: str | None = None) -> list[WebSource]:
        """List all web sources, optionally filtered by user."""
        sources = []
        for meta_file in self.web_metadata_dir.glob("*.json"):
            try:
                ws = self.get_web_source(meta_file.stem)
                if user_id is None or ws.user_id == user_id:
                    sources.append(ws)
            except Exception as e:
                logger.warning(f"Failed to load web source {meta_file.stem}: {e}")
        sources.sort(key=lambda w: w.created_at, reverse=True)
        return sources

    def extract_text_from_pdf(self, document_id: str) -> str:
        """Extract text content from a PDF file.

        Args:
            document_id: The document identifier.

        Returns:
            Extracted text content.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
            StorageError: If text extraction fails.
        """
        file_path = self._get_file_path(document_id)
        if not file_path.exists():
            raise DocumentNotFoundError(f"File not found for document: {document_id}")

        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise StorageError(f"Failed to extract text from PDF: {e}") from e
