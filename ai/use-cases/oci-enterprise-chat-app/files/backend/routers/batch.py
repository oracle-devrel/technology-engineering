"""Batch processing API endpoints for OCI Object Storage document ingestion."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from models.batch import BatchJob, BatchTrigger, ObjectStoreConnector
from models.document import ErrorResponse
from models.user import User
from routers.auth import get_optional_user
from schemas import (
    ConnectorCreateRequest,
    ConnectorRunRequest,
    ConnectorTestRequest,
    ConnectorResponse,
    TriggerCreateRequest,
    TriggerUpdateRequest,
    TriggerResponse,
    BatchJobResponse,
    BatchJobFileResponse,
)
from services.batch_service import BatchService, BatchServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/batch", tags=["Batch Processing"])

# Service instance
_batch_service: BatchService | None = None


def get_batch_service() -> BatchService:
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchService()
    return _batch_service


def set_services(batch: BatchService | None = None) -> None:
    global _batch_service
    if batch is not None:
        _batch_service = batch


BatchDep = Annotated[BatchService, Depends(get_batch_service)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


# --- Connector Endpoints ---


@router.post(
    "/connectors",
    response_model=ConnectorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new OCI Object Storage connector",
)
async def create_connector(
    request: ConnectorCreateRequest,
    batch: BatchDep,
    current_user: OptionalUser = None,
) -> ConnectorResponse:
    connector = batch.create_connector(
        name=request.name,
        namespace=request.namespace,
        bucket_name=request.bucket_name,
        compartment_id=request.compartment_id,
        region=request.region,
        prefix=request.prefix,
    )
    return ConnectorResponse.model_validate(connector.model_dump(mode="json"))


@router.get(
    "/connectors",
    response_model=list[ConnectorResponse],
    summary="List all connectors",
)
async def list_connectors(batch: BatchDep) -> list[ConnectorResponse]:
    connectors = batch.list_connectors()
    return [ConnectorResponse.model_validate(c.model_dump(mode="json")) for c in connectors]


@router.get(
    "/connectors/{connector_id}",
    response_model=ConnectorResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get connector details",
)
async def get_connector(connector_id: str, batch: BatchDep) -> ConnectorResponse:
    try:
        connector = batch.get_connector(connector_id)
        return ConnectorResponse.model_validate(connector.model_dump(mode="json"))
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_id}")


@router.put(
    "/connectors/{connector_id}",
    response_model=ConnectorResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update a connector",
)
async def update_connector(
    connector_id: str,
    request: ConnectorCreateRequest,
    batch: BatchDep,
) -> ConnectorResponse:
    try:
        connector = batch.update_connector(
            connector_id,
            name=request.name,
            namespace=request.namespace,
            bucket_name=request.bucket_name,
            compartment_id=request.compartment_id,
            region=request.region,
            prefix=request.prefix,
        )
        return ConnectorResponse.model_validate(connector.model_dump(mode="json"))
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_id}")


@router.delete(
    "/connectors/{connector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a connector",
)
async def delete_connector(connector_id: str, batch: BatchDep) -> None:
    try:
        batch.delete_connector(connector_id)
    except BatchServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/connectors/test",
    summary="Test connectivity with raw connection parameters",
)
async def test_connection(
    request: ConnectorTestRequest,
    batch: BatchDep,
) -> dict:
    """Test OCI Object Storage connectivity without saving a connector."""
    return await batch._oci_service.test_connection(
        namespace=request.namespace,
        bucket_name=request.bucket_name,
        compartment_id=request.compartment_id,
        region=request.region,
    )


@router.post(
    "/connectors/{connector_id}/test",
    summary="Test connector connectivity",
)
async def test_connector(connector_id: str, batch: BatchDep) -> dict:
    try:
        return await batch.test_connector(connector_id)
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_id}")


# --- Trigger Endpoints ---


@router.post(
    "/triggers",
    response_model=TriggerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a batch processing trigger",
)
async def create_trigger(
    request: TriggerCreateRequest,
    batch: BatchDep,
) -> TriggerResponse:
    try:
        trigger = batch.create_trigger(
            connector_id=request.connector_id,
            name=request.name,
            schedule=request.schedule,
            is_active=request.is_active,
            parallelism=request.parallelism,
        )

        # Register with scheduler if active
        if trigger.is_active:
            from services.scheduler import scheduler_service

            scheduler_service.register_trigger(trigger.id, trigger.schedule)

        return TriggerResponse.model_validate(trigger.model_dump(mode="json"))
    except BatchServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/triggers",
    response_model=list[TriggerResponse],
    summary="List all triggers",
)
async def list_triggers(batch: BatchDep) -> list[TriggerResponse]:
    triggers = batch.list_triggers()
    return [TriggerResponse.model_validate(t.model_dump(mode="json")) for t in triggers]


@router.get(
    "/triggers/{trigger_id}",
    response_model=TriggerResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get trigger details",
)
async def get_trigger(trigger_id: str, batch: BatchDep) -> TriggerResponse:
    try:
        trigger = batch.get_trigger(trigger_id)
        return TriggerResponse.model_validate(trigger.model_dump(mode="json"))
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Trigger not found: {trigger_id}")


@router.put(
    "/triggers/{trigger_id}",
    response_model=TriggerResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update a trigger",
)
async def update_trigger(
    trigger_id: str,
    request: TriggerUpdateRequest,
    batch: BatchDep,
) -> TriggerResponse:
    try:
        trigger = batch.update_trigger(trigger_id, **request.model_dump(exclude_none=True))

        # Update scheduler registration
        from services.scheduler import scheduler_service

        if trigger.is_active:
            scheduler_service.register_trigger(trigger.id, trigger.schedule)
        else:
            scheduler_service.unregister_trigger(trigger.id)

        return TriggerResponse.model_validate(trigger.model_dump(mode="json"))
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Trigger not found: {trigger_id}")


@router.delete(
    "/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a trigger",
)
async def delete_trigger(trigger_id: str, batch: BatchDep) -> None:
    try:
        from services.scheduler import scheduler_service

        scheduler_service.unregister_trigger(trigger_id)
        batch.delete_trigger(trigger_id)
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Trigger not found: {trigger_id}")


@router.post(
    "/triggers/{trigger_id}/run",
    response_model=BatchJobResponse,
    summary="Manually run a trigger now",
)
async def run_trigger(trigger_id: str, batch: BatchDep) -> BatchJobResponse:
    try:
        trigger = batch.get_trigger(trigger_id)
        job = batch.create_job(
            connector_id=trigger.connector_id,
            trigger_id=trigger_id,
            parallelism=trigger.parallelism,
        )
        # The separate batch worker consumes persisted pending jobs.

        return BatchJobResponse.model_validate(job.model_dump(mode="json"))
    except BatchServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Job Endpoints ---


@router.get(
    "/jobs",
    response_model=list[BatchJobResponse],
    summary="List batch jobs",
)
async def list_jobs(
    batch: BatchDep,
    trigger_id: str | None = None,
) -> list[BatchJobResponse]:
    jobs = batch.list_jobs(trigger_id=trigger_id)
    return [BatchJobResponse.model_validate(j.model_dump(mode="json")) for j in jobs]


@router.get(
    "/jobs/{job_id}",
    response_model=BatchJobResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get batch job details",
)
async def get_job(job_id: str, batch: BatchDep) -> BatchJobResponse:
    try:
        job = batch.get_job(job_id)
        return BatchJobResponse.model_validate(job.model_dump(mode="json"))
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")


@router.get(
    "/jobs/{job_id}/files",
    response_model=list[BatchJobFileResponse],
    summary="Get files in a batch job",
)
async def get_job_files(job_id: str, batch: BatchDep) -> list[BatchJobFileResponse]:
    try:
        batch.get_job(job_id)  # Verify job exists
        files = batch.get_job_files(job_id)
        return [BatchJobFileResponse.model_validate(f.model_dump(mode="json")) for f in files]
    except BatchServiceError:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")


@router.post("/connectors/{connector_id}/run", response_model=BatchJobResponse)
async def run_connector(connector_id: str, request: ConnectorRunRequest, batch: BatchDep):
    try:
        job = batch.create_job(
            connector_id, parallelism=request.parallelism, processing_mode=request.processing_mode
        )
        if request.processing_mode == "normal":
            job = await batch.execute_job(job.id, parallelism=request.parallelism)
        return BatchJobResponse.model_validate(job.model_dump(mode="json"))
    except BatchServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
