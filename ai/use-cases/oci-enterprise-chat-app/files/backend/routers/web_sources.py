"""Web source API endpoints for scraping, indexing, and managing web URLs."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from models.document import ErrorResponse, WebSourceStatus
from models.user import User
from routers.auth import get_optional_user
from services.storage import DocumentNotFoundError, StorageService
from services.rag_service import RAGService
from services.web_scraper import WebScraperService, WebScraperError
from schemas import WebSourceAddRequest, WebSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web", tags=["Web Sources"])

# Service instances
_storage_service: StorageService | None = None
_rag_service: RAGService | None = None
_web_scraper_service: WebScraperService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def get_web_scraper_service() -> WebScraperService:
    global _web_scraper_service
    if _web_scraper_service is None:
        _web_scraper_service = WebScraperService()
    return _web_scraper_service


def set_services(
    storage: StorageService | None = None,
    rag: RAGService | None = None,
    web_scraper: WebScraperService | None = None,
) -> None:
    global _storage_service, _rag_service, _web_scraper_service
    if storage is not None:
        _storage_service = storage
    if rag is not None:
        _rag_service = rag
    if web_scraper is not None:
        _web_scraper_service = web_scraper


StorageDep = Annotated[StorageService, Depends(get_storage_service)]
RAGDep = Annotated[RAGService, Depends(get_rag_service)]
ScraperDep = Annotated[WebScraperService, Depends(get_web_scraper_service)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


def _to_response(ws) -> WebSourceResponse:
    return WebSourceResponse(
        id=ws.id,
        url=ws.url,
        title=ws.title,
        status=ws.status.value if hasattr(ws.status, "value") else ws.status,
        content_length=ws.content_length,
        chunks_indexed=ws.chunks_indexed,
        error_message=ws.error_message,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.post(
    "/scrape",
    response_model=WebSourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL or scraping failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Scrape a web URL and index for RAG",
    description="Fetch a web page, extract text, chunk and index into the vector store for RAG chat.",
)
async def scrape_web_url(
    request: WebSourceAddRequest,
    storage: StorageDep,
    rag: RAGDep,
    scraper: ScraperDep,
    current_user: OptionalUser = None,
) -> WebSourceResponse:
    """Scrape a URL, extract text, and index it for RAG."""
    user_id = current_user.id if current_user else None

    # Create web source record
    ws = storage.save_web_source(url=request.url, title=request.title, user_id=user_id)

    try:
        # Scrape
        storage.update_web_source(ws.id, status=WebSourceStatus.SCRAPING)
        result = await scraper.scrape(url=request.url, fallback_title=request.title)

        # Store text content
        storage.update_web_source(
            ws.id,
            title=result.title,
            text_content=result.text_content,
            content_length=result.content_length,
            status=WebSourceStatus.INDEXING,
        )

        # Index into vector store
        try:
            chunks_indexed = await rag.index_document(
                document_id=ws.id,
                text=result.text_content,
                filename=result.title,
            )
            ws = storage.update_web_source(
                ws.id,
                status=WebSourceStatus.COMPLETED,
                chunks_indexed=chunks_indexed,
            )
            logger.info(f"Web source {ws.id} indexed: {chunks_indexed} chunks")
        except Exception as e:
            logger.warning(f"Vector indexing failed for web source {ws.id}: {e}")
            # Still mark as completed — text is stored for fallback
            ws = storage.update_web_source(
                ws.id,
                status=WebSourceStatus.COMPLETED,
                chunks_indexed=0,
                error_message=f"Indexed text stored, but vector indexing failed: {e}",
            )

        return _to_response(ws)

    except WebScraperError as e:
        ws = storage.update_web_source(
            ws.id,
            status=WebSourceStatus.FAILED,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error scraping {request.url}: {e}")
        storage.update_web_source(
            ws.id,
            status=WebSourceStatus.FAILED,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process web source: {e}",
        )


@router.get(
    "/sources",
    response_model=list[WebSourceResponse],
    summary="List all web sources",
)
async def list_web_sources(
    storage: StorageDep,
    current_user: OptionalUser = None,
) -> list[WebSourceResponse]:
    user_id = current_user.id if current_user else None
    sources = storage.list_web_sources(user_id=user_id)
    return [_to_response(ws) for ws in sources]


@router.get(
    "/{web_source_id}",
    response_model=WebSourceResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get web source details",
)
async def get_web_source(
    web_source_id: str,
    storage: StorageDep,
) -> WebSourceResponse:
    try:
        ws = storage.get_web_source(web_source_id)
        return _to_response(ws)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Web source not found: {web_source_id}",
        )


@router.delete(
    "/{web_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a web source and its vectors",
)
async def delete_web_source(
    web_source_id: str,
    storage: StorageDep,
    rag: RAGDep,
) -> None:
    try:
        # Delete vector embeddings
        try:
            deleted = await rag.delete_document_vectors(web_source_id)
            logger.info(f"Deleted {deleted} vector chunks for web source {web_source_id}")
        except Exception as e:
            logger.warning(f"Vector deletion failed for web source {web_source_id}: {e}")

        storage.delete_web_source(web_source_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Web source not found: {web_source_id}",
        )


@router.post(
    "/{web_source_id}/rescrape",
    response_model=WebSourceResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Re-scrape and re-index a web source",
)
async def rescrape_web_source(
    web_source_id: str,
    storage: StorageDep,
    rag: RAGDep,
    scraper: ScraperDep,
) -> WebSourceResponse:
    try:
        ws = storage.get_web_source(web_source_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Web source not found: {web_source_id}",
        )

    try:
        # Delete old vectors
        try:
            await rag.delete_document_vectors(web_source_id)
        except Exception:
            pass

        storage.update_web_source(ws.id, status=WebSourceStatus.SCRAPING, error_message=None)
        result = await scraper.scrape(url=ws.url, fallback_title=ws.title)

        storage.update_web_source(
            ws.id,
            title=result.title,
            text_content=result.text_content,
            content_length=result.content_length,
            status=WebSourceStatus.INDEXING,
        )

        chunks_indexed = await rag.index_document(
            document_id=ws.id,
            text=result.text_content,
            filename=result.title,
        )

        ws = storage.update_web_source(
            ws.id,
            status=WebSourceStatus.COMPLETED,
            chunks_indexed=chunks_indexed,
        )
        return _to_response(ws)

    except WebScraperError as e:
        storage.update_web_source(ws.id, status=WebSourceStatus.FAILED, error_message=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        storage.update_web_source(ws.id, status=WebSourceStatus.FAILED, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-scrape failed: {e}",
        )
