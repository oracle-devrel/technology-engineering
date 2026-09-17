"""Workflow API endpoints for creating, managing, and executing agent pipelines."""

import asyncio
import io
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from models.document import ErrorResponse
from models.user import User
from models.workflow import WorkflowSchedule, ScheduleType
from routers.auth import get_optional_user
from schemas import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowResponse,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    ScheduleCreateRequest,
    ScheduleToggleRequest,
    ScheduleResponse,
    ScheduledRunResponse,
)
from services.workflow_storage import (
    WorkflowStorageService,
    WorkflowNotFoundError,
    WorkflowStorageError,
)
from services.workflow_engine import WorkflowEngine
from services.scheduler import scheduler_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# Service instances
_workflow_storage: WorkflowStorageService | None = None
_workflow_engine: WorkflowEngine | None = None


def get_workflow_storage() -> WorkflowStorageService:
    global _workflow_storage
    if _workflow_storage is None:
        _workflow_storage = WorkflowStorageService()
    return _workflow_storage


def get_workflow_engine() -> WorkflowEngine:
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine(storage=get_workflow_storage())
    return _workflow_engine


def set_services(
    storage: WorkflowStorageService | None = None,
    engine: WorkflowEngine | None = None,
) -> None:
    global _workflow_storage, _workflow_engine
    if storage is not None:
        _workflow_storage = storage
    if engine is not None:
        _workflow_engine = engine


StorageDep = Annotated[WorkflowStorageService, Depends(get_workflow_storage)]
EngineDep = Annotated[WorkflowEngine, Depends(get_workflow_engine)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


def _to_response(wf) -> WorkflowResponse:
    schedule_data = None
    if wf.schedule is not None:
        schedule_data = wf.schedule.model_dump(mode="json")
    return WorkflowResponse(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        nodes=[n.model_dump(mode="json") for n in wf.nodes],
        edges=[e.model_dump(mode="json") for e in wf.edges],
        created_at=wf.created_at,
        updated_at=wf.updated_at,
        created_by=wf.created_by,
        is_active=wf.is_active,
        schedule=schedule_data,
    )


def _to_execution_response(ex) -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(
        id=ex.id,
        workflow_id=ex.workflow_id,
        status=ex.status.value if hasattr(ex.status, "value") else ex.status,
        input_data=ex.input_data,
        output_data=ex.output_data,
        node_results=ex.node_results,
        started_at=ex.started_at,
        completed_at=ex.completed_at,
        error_message=ex.error_message,
        created_at=ex.created_at,
        triggered_by=ex.triggered_by,
    )


def _to_schedule_response(schedule: WorkflowSchedule) -> ScheduleResponse:
    """Convert a WorkflowSchedule model to a ScheduleResponse schema."""
    return ScheduleResponse(
        id=schedule.id,
        workflow_id=schedule.workflow_id,
        schedule_type=schedule.schedule_type.value
        if hasattr(schedule.schedule_type, "value")
        else schedule.schedule_type,
        cron_expression=schedule.cron_expression,
        run_at=schedule.run_at,
        input_data=schedule.input_data,
        is_active=schedule.is_active,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
    )


# --- Workflow CRUD ---


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
)
async def create_workflow(
    request: WorkflowCreateRequest,
    storage: StorageDep,
    current_user: OptionalUser = None,
) -> WorkflowResponse:
    try:
        user_id = current_user.id if current_user else None
        wf = storage.create_workflow(
            name=request.name,
            description=request.description,
            nodes=[n.model_dump() for n in request.nodes] if request.nodes else [],
            edges=[e.model_dump() for e in request.edges] if request.edges else [],
            created_by=user_id,
        )
        return _to_response(wf)
    except WorkflowStorageError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=list[WorkflowResponse],
    summary="List all workflows",
)
async def list_workflows(
    storage: StorageDep,
    current_user: OptionalUser = None,
) -> list[WorkflowResponse]:
    user_id = current_user.id if current_user else None
    workflows = storage.list_workflows(created_by=user_id)
    return [_to_response(wf) for wf in workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get workflow details",
)
async def get_workflow(workflow_id: str, storage: StorageDep) -> WorkflowResponse:
    try:
        wf = storage.get_workflow(workflow_id)
        return _to_response(wf)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update a workflow",
)
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    storage: StorageDep,
) -> WorkflowResponse:
    try:
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.nodes is not None:
            updates["nodes"] = [n.model_dump() for n in request.nodes]
        if request.edges is not None:
            updates["edges"] = [e.model_dump() for e in request.edges]

        wf = storage.update_workflow(workflow_id, **updates)
        return _to_response(wf)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    except WorkflowStorageError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a workflow",
)
async def delete_workflow(workflow_id: str, storage: StorageDep) -> None:
    try:
        wf = storage.get_workflow(workflow_id)
        if wf.schedule:
            scheduler_service.unschedule_workflow(wf.schedule.id)
        storage.delete_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


# --- Execution Endpoints ---


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    summary="Execute a workflow",
)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    storage: StorageDep,
    engine: EngineDep,
) -> WorkflowExecutionResponse:
    try:
        wf = storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    execution = await engine.execute(wf, request.input_data)
    return _to_execution_response(execution)


@router.get(
    "/{workflow_id}/executions",
    response_model=list[WorkflowExecutionResponse],
    summary="List executions for a workflow",
)
async def list_executions(
    workflow_id: str,
    storage: StorageDep,
) -> list[WorkflowExecutionResponse]:
    try:
        storage.get_workflow(workflow_id)  # Verify workflow exists
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    executions = storage.list_executions(workflow_id)
    return [_to_execution_response(ex) for ex in executions]


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get execution details",
)
async def get_execution(
    execution_id: str,
    storage: StorageDep,
) -> WorkflowExecutionResponse:
    try:
        ex = storage.get_execution(execution_id)
        return _to_execution_response(ex)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")


# --- Schedule Endpoints ---


@router.post(
    "/{workflow_id}/schedule",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a workflow schedule",
)
async def create_or_update_schedule(
    workflow_id: str,
    request: ScheduleCreateRequest,
    storage: StorageDep,
) -> ScheduleResponse:
    """Create or update the schedule for a workflow."""
    try:
        wf = storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    try:
        now = datetime.now(UTC)
        schedule_id = wf.schedule.id if wf.schedule else str(uuid.uuid4())

        schedule = WorkflowSchedule(
            id=schedule_id,
            workflow_id=workflow_id,
            schedule_type=ScheduleType(request.schedule_type),
            cron_expression=request.cron_expression,
            run_at=request.run_at,
            input_data=request.input_data,
            is_active=request.is_active,
            created_at=wf.schedule.created_at if wf.schedule else now,
            updated_at=now,
        )

        scheduler_service.register_workflow(schedule)
        storage.save_schedule(schedule)

        logger.info(f"Schedule {schedule.id} saved for workflow {workflow_id}")
        return _to_schedule_response(schedule)

    except (ValueError, WorkflowStorageError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{workflow_id}/schedule",
    response_model=ScheduleResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get the current schedule for a workflow",
)
async def get_schedule(
    workflow_id: str,
    storage: StorageDep,
) -> ScheduleResponse:
    """Retrieve the schedule attached to a workflow."""
    try:
        wf = storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    if wf.schedule is None:
        raise HTTPException(
            status_code=404, detail=f"No schedule found for workflow: {workflow_id}"
        )

    return _to_schedule_response(wf.schedule)


@router.delete(
    "/{workflow_id}/schedule",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    summary="Remove the schedule from a workflow",
)
async def delete_schedule(
    workflow_id: str,
    storage: StorageDep,
) -> None:
    """Delete the schedule for a workflow and unregister it from the scheduler."""
    try:
        wf = storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    if wf.schedule is None:
        raise HTTPException(
            status_code=404, detail=f"No schedule found for workflow: {workflow_id}"
        )

    schedule_id = wf.schedule.id
    scheduler_service.unschedule_workflow(schedule_id)
    storage.update_workflow(workflow_id, schedule=None)
    logger.info(f"Schedule {schedule_id} deleted for workflow {workflow_id}")


@router.patch(
    "/{workflow_id}/schedule/toggle",
    response_model=ScheduleResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Enable or disable a workflow schedule",
)
async def toggle_schedule(
    workflow_id: str,
    request: ScheduleToggleRequest,
    storage: StorageDep,
) -> ScheduleResponse:
    """Toggle a workflow schedule's active state."""
    try:
        wf = storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    if wf.schedule is None:
        raise HTTPException(
            status_code=404, detail=f"No schedule found for workflow: {workflow_id}"
        )

    schedule = wf.schedule
    schedule.is_active = request.is_active
    schedule.updated_at = datetime.now(UTC)

    try:
        scheduler_service.register_workflow(schedule)
        storage.save_schedule(schedule)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info(f"Schedule {schedule.id} toggled to is_active={schedule.is_active}")
    return _to_schedule_response(schedule)


@router.get(
    "/{workflow_id}/scheduled-runs",
    response_model=list[ScheduledRunResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List scheduled executions for a workflow",
)
async def list_scheduled_runs(
    workflow_id: str,
    storage: StorageDep,
) -> list[ScheduledRunResponse]:
    """List all executions that were triggered by a schedule for this workflow."""
    try:
        storage.get_workflow(workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    executions = [
        ex
        for ex in storage.list_executions(workflow_id)
        if ex.triggered_by and ex.triggered_by != "user"
    ]
    return [
        ScheduledRunResponse(
            execution_id=ex.id,
            workflow_id=ex.workflow_id,
            status=ex.status.value if hasattr(ex.status, "value") else ex.status,
            triggered_by=ex.triggered_by,
            started_at=ex.started_at,
            completed_at=ex.completed_at,
            error_message=ex.error_message,
        )
        for ex in executions
    ]


@router.post("/input-file")
async def read_input_file(file: UploadFile):
    """Extract a user-selected file for a saved workflow input node."""
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB")
    filename = file.filename or "input.txt"
    try:
        if filename.lower().endswith(".pdf"):

            def extract():
                import pdfplumber

                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    return "\n\n".join(page.extract_text() or "" for page in pdf.pages)

            text = await asyncio.to_thread(extract)
        elif filename.lower().endswith((".txt", ".md", ".json", ".csv")):
            text = content.decode("utf-8-sig")
        else:
            raise ValueError("Choose a PDF, TXT, Markdown, JSON or CSV file")
        if not text.strip():
            raise ValueError("File contains no readable text; OCR may be required")
        return {"filename": filename, "text": text}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        await file.close()
