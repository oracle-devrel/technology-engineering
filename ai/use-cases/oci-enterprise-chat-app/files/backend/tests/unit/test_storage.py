"""Unit tests for the storage service."""

import io
from pathlib import Path

import pytest

from services.storage import (
    DocumentNotFoundError,
    StorageError,
    StorageService,
)
from models.document import DocumentStatus


class TestStorageService:
    """Tests for StorageService class."""

    @pytest.mark.asyncio
    async def test_save_file_success(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful file save."""
        file = io.BytesIO(sample_pdf_bytes)

        document = await storage_service.save_file(
            file=file,
            filename="test.pdf",
            content_type="application/pdf",
        )

        assert document.id is not None
        assert document.metadata.filename == "test.pdf"
        assert document.metadata.file_size == len(sample_pdf_bytes)
        assert document.status == DocumentStatus.UPLOADED

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful document retrieval."""
        file = io.BytesIO(sample_pdf_bytes)
        saved_doc = await storage_service.save_file(
            file=file,
            filename="test.pdf",
            content_type="application/pdf",
        )

        retrieved_doc = await storage_service.get_document(saved_doc.id)

        assert retrieved_doc.id == saved_doc.id
        assert retrieved_doc.metadata.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self,
        storage_service: StorageService,
    ) -> None:
        """Test document retrieval with non-existent ID."""
        with pytest.raises(DocumentNotFoundError):
            await storage_service.get_document("non-existent-id")

    @pytest.mark.asyncio
    async def test_get_file_path_success(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful file path retrieval."""
        file = io.BytesIO(sample_pdf_bytes)
        document = await storage_service.save_file(
            file=file,
            filename="test.pdf",
            content_type="application/pdf",
        )

        file_path = await storage_service.get_file_path(document.id)

        assert file_path.exists()
        assert file_path.suffix == ".pdf"

    @pytest.mark.asyncio
    async def test_update_document_status(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test document status update."""
        file = io.BytesIO(sample_pdf_bytes)
        document = await storage_service.save_file(
            file=file,
            filename="test.pdf",
            content_type="application/pdf",
        )

        updated_doc = await storage_service.update_document_status(
            document.id,
            DocumentStatus.PROCESSING,
        )

        assert updated_doc.status == DocumentStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test successful document deletion."""
        file = io.BytesIO(sample_pdf_bytes)
        document = await storage_service.save_file(
            file=file,
            filename="test.pdf",
            content_type="application/pdf",
        )

        await storage_service.delete_document(document.id)

        with pytest.raises(DocumentNotFoundError):
            await storage_service.get_document(document.id)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        storage_service: StorageService,
    ) -> None:
        """Test deletion of non-existent document."""
        with pytest.raises(DocumentNotFoundError):
            await storage_service.delete_document("non-existent-id")

    @pytest.mark.asyncio
    async def test_list_documents(
        self,
        storage_service: StorageService,
        sample_pdf_bytes: bytes,
    ) -> None:
        """Test listing all documents."""
        # Create multiple documents
        for i in range(3):
            file = io.BytesIO(sample_pdf_bytes)
            await storage_service.save_file(
                file=file,
                filename=f"test_{i}.pdf",
                content_type="application/pdf",
            )

        documents = await storage_service.list_documents()

        assert len(documents) == 3

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self,
        storage_service: StorageService,
    ) -> None:
        """Test listing documents when none exist."""
        documents = await storage_service.list_documents()
        assert documents == []

    def test_generate_document_id(
        self,
        storage_service: StorageService,
    ) -> None:
        """Test that generated document IDs are unique."""
        ids = {storage_service._generate_document_id() for _ in range(100)}
        assert len(ids) == 100

    def test_ensure_directories(
        self,
        temp_upload_dir: Path,
    ) -> None:
        """Test directory creation."""
        new_dir = temp_upload_dir / "new_uploads"
        service = StorageService(upload_dir=new_dir)

        assert new_dir.exists()
        assert (new_dir / ".metadata").exists()
