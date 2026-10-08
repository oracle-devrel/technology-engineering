"""Document-related API endpoints."""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from models.document import (
    Document,
    DocumentStatus,
    ErrorResponse,
    ExtractionResult,
    UploadResponse,
)
from models.user import User
from routers.auth import get_current_user, get_optional_user
from services.extraction import ExtractionService
from services.storage import DocumentNotFoundError, StorageError, StorageService
from services.rag_service import RAGService
from schemas import ChatRequest, ChatResponse, RAGSource, RAGHealthResponse, WordCloudRequest, WordCloudResponse, WordFrequency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])

# Service instances (will be overridden by dependency injection)
_storage_service: StorageService | None = None
_extraction_service: ExtractionService | None = None
_rag_service: RAGService | None = None


def get_storage_service() -> StorageService:
    """Dependency for getting the storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def get_extraction_service() -> ExtractionService:
    """Dependency for getting the extraction service instance."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service


def get_rag_service() -> RAGService:
    """Dependency for getting the RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def set_services(
    storage: StorageService | None = None,
    extraction: ExtractionService | None = None,
    rag: RAGService | None = None,
) -> None:
    """Set the service instances (for testing or custom configuration)."""
    global _storage_service, _extraction_service, _rag_service
    if storage is not None:
        _storage_service = storage
    if extraction is not None:
        _extraction_service = extraction
    if rag is not None:
        _rag_service = rag


# Type aliases for dependency injection
StorageDep = Annotated[StorageService, Depends(get_storage_service)]
ExtractionDep = Annotated[ExtractionService, Depends(get_extraction_service)]
RAGDep = Annotated[RAGService, Depends(get_rag_service)]


ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_pdf_file(file: UploadFile) -> None:
    """Validate that the uploaded file is a valid PDF.

    Args:
        file: The uploaded file to validate.

    Raises:
        HTTPException: If the file is not a valid PDF.
    """
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' is not supported. Only PDF files are accepted.",
        )

    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File extension '{ext}' is not supported. Only .pdf files are accepted.",
            )


# Type alias for optional user dependency
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Upload a PDF document",
    description="Upload a PDF file for processing. Returns a document ID for tracking.",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file to upload")],
    storage: StorageDep,
    current_user: OptionalUser = None,
) -> UploadResponse:
    """Upload a PDF document for processing.

    Args:
        file: The PDF file to upload.
        storage: Storage service instance.
        current_user: Optional authenticated user.

    Returns:
        UploadResponse with document ID and metadata.

    Raises:
        HTTPException: If file validation or storage fails.
    """
    # Validate file type
    validate_pdf_file(file)

    # Check file size (read a small chunk first)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes).",
        )

    try:
        user_id = current_user.id if current_user else None
        document = await storage.save_file(
            file=file.file,
            filename=file.filename or "document.pdf",
            content_type=file.content_type or "application/pdf",
            user_id=user_id,
        )

        logger.info(f"Document uploaded successfully: {document.id} by user {user_id}")

        return UploadResponse(
            document_id=document.id,
            filename=document.metadata.filename,
            file_size=document.metadata.file_size,
            message="File uploaded successfully",
        )

    except StorageError as e:
        logger.error(f"Storage error during upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store document: {str(e)}",
        )


@router.post(
    "/extract/{document_id}",
    response_model=ExtractionResult,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        409: {"model": ErrorResponse, "description": "Extraction already in progress"},
        500: {"model": ErrorResponse, "description": "Extraction failed"},
    },
    summary="Extract parameters from document",
    description="Trigger RAG extraction for the uploaded document using NVIDIA AIQ Corrino API. Also indexes the document in the vector store for semantic search.",
)
async def extract_document(
    document_id: str,
    storage: StorageDep,
    extraction: ExtractionDep,
    rag: RAGDep,
) -> ExtractionResult:
    """Extract parameters from a document using RAG.

    Also indexes the document in the Oracle 23ai vector store for
    semantic search during chat.

    Args:
        document_id: The document identifier.
        storage: Storage service instance.
        extraction: Extraction service instance.
        rag: RAG service instance for vector indexing.

    Returns:
        ExtractionResult with extracted parameters.

    Raises:
        HTTPException: If document not found or extraction fails.
    """
    try:
        # Get document and check status
        document = await storage.get_document(document_id)

        if document.status == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Extraction is already in progress for this document.",
            )

        # Update status to processing
        await storage.update_document_status(document_id, DocumentStatus.PROCESSING)

        try:
            # Extract text from PDF
            document_text = storage.extract_text_from_pdf(document_id)

            if not document_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Could not extract text from the PDF. The document may be image-based or corrupted.",
                )

            # Index document in vector store for semantic search
            try:
                chunks_indexed = await rag.index_document(
                    document_id=document_id,
                    text=document_text,
                    filename=document.metadata.filename,
                )
                logger.info(f"Indexed {chunks_indexed} chunks for document {document_id}")
            except Exception as e:
                # Log but don't fail extraction if indexing fails
                logger.warning(f"Vector indexing failed for document {document_id}: {e}")

            # Perform parameter extraction
            result = await extraction.extract_parameters(
                document_text=document_text,
                document_id=document_id,
            )

            # Update document with results
            final_status = (
                DocumentStatus.COMPLETED
                if not result.error_message
                else DocumentStatus.FAILED
            )
            await storage.update_document_status(
                document_id, final_status, extraction_result=result
            )

            logger.info(
                f"Extraction completed for document {document_id}: "
                f"{len(result.parameters)} parameters found"
            )

            return result

        except HTTPException:
            # Re-raise HTTP exceptions
            await storage.update_document_status(document_id, DocumentStatus.FAILED)
            raise

        except Exception as e:
            # Handle unexpected errors during extraction
            logger.error(f"Extraction failed for document {document_id}: {e}")
            error_result = ExtractionResult(
                parameters=[],
                error_message=f"Extraction failed: {str(e)}",
            )
            await storage.update_document_status(
                document_id, DocumentStatus.FAILED, extraction_result=error_result
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction failed: {str(e)}",
            )

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.get(
    "/document/{document_id}",
    response_model=Document,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Get document metadata",
    description="Return document metadata and extraction status.",
)
async def get_document(
    document_id: str,
    storage: StorageDep,
) -> Document:
    """Get document metadata and extraction status.

    Args:
        document_id: The document identifier.
        storage: Storage service instance.

    Returns:
        Document with metadata and extraction results.

    Raises:
        HTTPException: If document not found.
    """
    try:
        document = await storage.get_document(document_id)
        return document

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.get(
    "/document/{document_id}/pdf",
    response_class=FileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document or file not found"},
    },
    summary="Download PDF file",
    description="Serve the PDF file for viewing in the frontend.",
)
async def get_document_pdf(
    document_id: str,
    storage: StorageDep,
) -> FileResponse:
    """Serve the PDF file for download/viewing.

    Args:
        document_id: The document identifier.
        storage: Storage service instance.

    Returns:
        FileResponse with the PDF file.

    Raises:
        HTTPException: If document or file not found.
    """
    try:
        document = await storage.get_document(document_id)
        file_path = await storage.get_file_path(document_id)

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=document.metadata.filename,
            headers={
                "Content-Disposition": f'inline; filename="{document.metadata.filename}"'
            },
        )

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.get(
    "/documents",
    response_model=list[Document],
    summary="List all documents",
    description="Get a list of all uploaded documents with their metadata.",
)
async def list_documents(
    storage: StorageDep,
    current_user: OptionalUser = None,
    user_only: bool = Query(default=True, description="Filter to current user's documents only"),
) -> list[Document]:
    """List all uploaded documents.

    Args:
        storage: Storage service instance.
        current_user: Optional authenticated user.
        user_only: If True and user is authenticated, only return user's documents.

    Returns:
        List of documents.
    """
    user_id = current_user.id if current_user and user_only else None
    return await storage.list_documents(user_id=user_id)


@router.delete(
    "/document/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Delete a document",
    description="Delete a document, its associated files, and vector embeddings.",
)
async def delete_document(
    document_id: str,
    storage: StorageDep,
    rag: RAGDep,
) -> None:
    """Delete a document and its associated files and vectors.

    Args:
        document_id: The document identifier.
        storage: Storage service instance.
        rag: RAG service instance for vector deletion.

    Raises:
        HTTPException: If document not found.
    """
    try:
        # Delete vectors from vector store
        try:
            deleted_chunks = await rag.delete_document_vectors(document_id)
            logger.info(f"Deleted {deleted_chunks} vector chunks for document {document_id}")
        except Exception as e:
            # Log but don't fail deletion if vector deletion fails
            logger.warning(f"Vector deletion failed for document {document_id}: {e}")

        # Delete document and files
        await storage.delete_document(document_id)
        logger.info(f"Document deleted: {document_id}")

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Chat failed"},
    },
    summary="Chat with documents",
    description="Ask questions about selected documents using RAG. Returns AI response with source references and confidence.",
    tags=["Chat"],
)
async def chat_with_documents(
    request: ChatRequest,
    storage: StorageDep,
    rag: RAGDep,
    current_user: OptionalUser = None,
) -> ChatResponse:
    """Chat with documents using RAG.

    Args:
        request: Chat request with message and document IDs.
        storage: Storage service instance.
        rag: RAG service instance.
        current_user: Optional authenticated user.

    Returns:
        ChatResponse with assistant's answer, sources, and confidence.

    Raises:
        HTTPException: If documents not found or chat fails.
    """
    if not request.document_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one document or web source ID is required",
        )

    # Collect document texts with metadata (PDFs and web sources)
    document_texts = []

    for doc_id in request.document_ids:
        try:
            document = await storage.get_document(doc_id)

            # Verify user has access to document
            if current_user and document.user_id and document.user_id != current_user.id:
                continue  # Skip documents the user doesn't own

            text = storage.extract_text_from_pdf(doc_id)
            if text.strip():
                document_texts.append({
                    "id": doc_id,
                    "filename": document.metadata.filename,
                    "text": text,
                })

        except DocumentNotFoundError:
            # Try as a web source
            try:
                ws = storage.get_web_source(doc_id)
                if current_user and ws.user_id and ws.user_id != current_user.id:
                    continue
                if ws.text_content and ws.text_content.strip():
                    document_texts.append({
                        "id": doc_id,
                        "filename": ws.title or ws.url,
                        "text": ws.text_content,
                    })
            except DocumentNotFoundError:
                logger.warning(f"Source not found for chat: {doc_id}")
                continue
        except Exception as e:
            logger.warning(f"Failed to extract text from source {doc_id}: {e}")
            continue

    if not document_texts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid documents or web sources found for the provided IDs",
        )

    # Convert conversation history to dict format
    conversation_history = [
        {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]

    try:
        # Build model settings dict from request (only include non-None values)
        model_settings = None
        if request.model_settings:
            model_settings = {
                k: v for k, v in request.model_settings.model_dump().items() if v is not None
            }

        # Use RAG service for chat
        rag_response = await rag.query(
            query=request.message,
            document_texts=document_texts,
            conversation_history=conversation_history,
            max_sources=request.max_sources,
            model_settings=model_settings,
            inference_model=request.inference_model,
        )

        # Convert RAG sources to schema format
        sources = [
            RAGSource(
                document_name=source.document_name,
                page_number=source.page_number,
                snippet=source.snippet,
                relevance_score=source.relevance_score,
            )
            for source in rag_response.sources
        ]

        return ChatResponse(
            message=rag_response.message,
            sources=sources,
            confidence=rag_response.confidence,
            processing_time_ms=rag_response.processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "was", "are", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "this",
    "that", "these", "those", "not", "no", "nor", "so", "if", "then",
    "than", "too", "very", "just", "about", "above", "after", "again",
    "all", "also", "am", "any", "because", "before", "between", "both",
    "each", "few", "more", "most", "other", "our", "out", "own", "same",
    "some", "such", "their", "them", "there", "they", "through", "under",
    "until", "up", "we", "what", "when", "where", "which", "while", "who",
    "whom", "why", "you", "your", "its", "he", "she", "his", "her", "my",
    "me", "us", "over", "into", "only", "how", "here", "were", "one",
    "two", "per", "page", "during", "without", "within", "among", "upon",
})


@router.post(
    "/wordcloud",
    response_model=WordCloudResponse,
    responses={
        400: {"model": ErrorResponse, "description": "No valid documents"},
        500: {"model": ErrorResponse, "description": "Processing failed"},
    },
    summary="Generate word cloud data",
    description="Extract text from documents and return word frequency data for word cloud visualization.",
    tags=["Documents"],
)
async def generate_wordcloud(
    request: WordCloudRequest,
    storage: StorageDep,
) -> WordCloudResponse:
    """Generate word frequency data from document texts.

    Args:
        request: Word cloud request with document IDs and max words.
        storage: Storage service instance.

    Returns:
        WordCloudResponse with word frequencies.
    """
    all_text = []
    docs_processed = 0

    for doc_id in request.document_ids:
        try:
            text = storage.extract_text_from_pdf(doc_id)
            if text.strip():
                all_text.append(text)
                docs_processed += 1
        except DocumentNotFoundError:
            # Try as web source
            try:
                ws = storage.get_web_source(doc_id)
                if ws.text_content and ws.text_content.strip():
                    all_text.append(ws.text_content)
                    docs_processed += 1
            except DocumentNotFoundError:
                logger.warning(f"Source not found for word cloud: {doc_id}")
                continue
        except Exception as e:
            logger.warning(f"Failed to extract text from {doc_id}: {e}")
            continue

    if not all_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text could be extracted from the provided documents",
        )

    combined = " ".join(all_text).lower()
    # Remove page markers, numbers, special chars; keep words
    combined = re.sub(r"---\s*page\s*\d+\s*---", " ", combined)
    tokens = re.findall(r"[a-z]{3,}", combined)
    total_words = len(tokens)

    filtered = [w for w in tokens if w not in STOP_WORDS]
    counts = Counter(filtered)
    top_words = counts.most_common(request.max_words)

    words = [WordFrequency(word=w, count=c) for w, c in top_words]

    return WordCloudResponse(
        words=words,
        total_documents=docs_processed,
        total_words_processed=total_words,
    )


@router.get(
    "/rag/health",
    response_model=RAGHealthResponse,
    summary="Check RAG service health",
    description="Check if the RAG/AI service is available and healthy, including vector store status.",
    tags=["Chat"],
)
async def check_rag_health(
    rag: RAGDep,
) -> RAGHealthResponse:
    """Check RAG service health status.

    Args:
        rag: RAG service instance.

    Returns:
        RAGHealthResponse with health status.
    """
    health_data = await rag.health_check()
    return RAGHealthResponse(**health_data)


@router.get(
    "/models",
    response_model=list[dict],
    summary="List available models",
    description="List models available on the llamastack endpoint.",
    tags=["Models"],
)
async def list_models(
    rag: RAGDep,
) -> list[dict]:
    """List available models from the inference endpoint.

    Args:
        rag: RAG service instance.

    Returns:
        List of model dicts with id and type.
    """
    return await rag.list_models()


@router.post(
    "/index/{document_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Indexing failed"},
    },
    summary="Index document for vector search",
    description="Manually index or re-index a document in the vector store for semantic search.",
    tags=["Chat"],
)
async def index_document(
    document_id: str,
    storage: StorageDep,
    rag: RAGDep,
) -> dict:
    """Index a document in the vector store.

    This endpoint allows manual indexing or re-indexing of a document
    for vector search. Useful if automatic indexing failed or to update
    embeddings.

    Args:
        document_id: The document identifier.
        storage: Storage service instance.
        rag: RAG service instance.

    Returns:
        Dict with indexing status and chunk count.

    Raises:
        HTTPException: If document not found or indexing fails.
    """
    try:
        document = await storage.get_document(document_id)

        # Extract text from PDF
        document_text = storage.extract_text_from_pdf(document_id)

        if not document_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from the PDF.",
            )

        # Index document
        chunks_indexed = await rag.index_document(
            document_id=document_id,
            text=document_text,
            filename=document.metadata.filename,
        )

        logger.info(f"Manually indexed {chunks_indexed} chunks for document {document_id}")

        return {
            "document_id": document_id,
            "chunks_indexed": chunks_indexed,
            "status": "success",
        }

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )
    except Exception as e:
        logger.error(f"Indexing failed for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )
