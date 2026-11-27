"""Storage service for workflow definitions and execution records."""

import json
import logging
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from services.workflow_validation import execution_order

from models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowNode,
    WorkflowEdge,
    WorkflowSchedule,
)

logger = logging.getLogger(__name__)


class WorkflowStorageError(Exception):
    """Exception raised for workflow storage errors."""

    pass


class WorkflowNotFoundError(WorkflowStorageError):
    """Exception raised when a workflow is not found."""

    pass


class WorkflowStorageService:
    """Service for persisting workflow definitions and executions as JSON files."""

    def __init__(self, upload_dir: str | Path | None = None) -> None:
        self.upload_dir = Path(upload_dir or os.getenv("UPLOAD_DIR", "uploads"))
        self.workflows_dir = self.upload_dir / ".workflow_metadata"
        self.executions_dir = self.workflows_dir / "executions"
        self.schedules_dir = self.workflows_dir / "schedules"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.executions_dir.mkdir(parents=True, exist_ok=True)
        self.schedules_dir.mkdir(parents=True, exist_ok=True)

    # --- Workflow CRUD ---

    def create_workflow(
        self,
        name: str,
        description: str = "",
        nodes: list[dict] | None = None,
        edges: list[dict] | None = None,
        created_by: str | None = None,
    ) -> Workflow:
        workflow_nodes = [WorkflowNode.model_validate(n) for n in (nodes or [])]
        workflow_edges = [WorkflowEdge.model_validate(e) for e in (edges or [])]

        self._validate_graph(workflow_nodes, workflow_edges)

        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            nodes=workflow_nodes,
            edges=workflow_edges,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by=created_by,
        )
        self._save_workflow(workflow)
        logger.info(f"Created workflow {workflow.id}: {name}")
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow:
        path = self.workflows_dir / f"{workflow_id}.json"
        if not path.exists():
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        data = self._load_json(path)
        return Workflow.model_validate(data)

    def list_workflows(self, created_by: str | None = None) -> list[Workflow]:
        workflows = []
        for f in self.workflows_dir.glob("*.json"):
            try:
                wf = Workflow.model_validate(self._load_json(f))
                if created_by is None or wf.created_by == created_by:
                    workflows.append(wf)
            except Exception as e:
                logger.warning(f"Failed to load workflow {f.stem}: {e}")
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        return workflows

    def update_workflow(self, workflow_id: str, **updates) -> Workflow:
        workflow = self.get_workflow(workflow_id)

        # Handle nodes and edges specially (need validation)
        if "nodes" in updates:
            nodes = [WorkflowNode.model_validate(n) for n in updates.pop("nodes")]
            edges_raw = updates.pop("edges", None)
            edges = (
                [WorkflowEdge.model_validate(e) for e in edges_raw]
                if edges_raw is not None
                else workflow.edges
            )
            self._validate_graph(nodes, edges)
            workflow.nodes = nodes
            workflow.edges = edges
        elif "edges" in updates:
            edges = [WorkflowEdge.model_validate(e) for e in updates.pop("edges")]
            self._validate_graph(workflow.nodes, edges)
            workflow.edges = edges

        for key, value in updates.items():
            if hasattr(workflow, key) and key not in ("id", "created_at", "created_by"):
                setattr(workflow, key, value)

        workflow.updated_at = datetime.now(UTC)
        self._save_workflow(workflow)
        logger.info(f"Updated workflow {workflow_id}")
        return workflow

    def delete_workflow(self, workflow_id: str) -> None:
        path = self.workflows_dir / f"{workflow_id}.json"
        if not path.exists():
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        path.unlink()
        logger.info(f"Deleted workflow {workflow_id}")

    # --- Execution Records ---

    def save_execution(self, execution: WorkflowExecution) -> None:
        path = self.executions_dir / f"{execution.id}.json"
        self._save_json(path, execution)

    def get_execution(self, execution_id: str) -> WorkflowExecution:
        path = self.executions_dir / f"{execution_id}.json"
        if not path.exists():
            raise WorkflowNotFoundError(f"Execution not found: {execution_id}")
        return WorkflowExecution.model_validate(self._load_json(path))

    def list_executions(
        self, workflow_id: str, triggered_by: str | None = None
    ) -> list[WorkflowExecution]:
        executions = []
        for f in self.executions_dir.glob("*.json"):
            try:
                ex = WorkflowExecution.model_validate(self._load_json(f))
                if ex.workflow_id == workflow_id:
                    if triggered_by is not None and ex.triggered_by != triggered_by:
                        continue
                    executions.append(ex)
            except Exception as e:
                logger.warning(f"Failed to load execution {f.stem}: {e}")
        executions.sort(key=lambda e: e.created_at, reverse=True)
        return executions

    # --- Schedule CRUD ---

    def save_schedule(self, schedule: WorkflowSchedule) -> None:
        self.update_workflow(schedule.workflow_id, schedule=schedule)

    def get_schedule(self, schedule_id: str) -> WorkflowSchedule:
        for workflow in self.list_workflows():
            if workflow.schedule and workflow.schedule.id == schedule_id:
                return workflow.schedule
        raise WorkflowNotFoundError(f"Schedule not found: {schedule_id}")

    def get_schedule_by_workflow(self, workflow_id: str) -> WorkflowSchedule | None:
        return self.get_workflow(workflow_id).schedule

    def delete_schedule(self, schedule_id: str) -> None:
        schedule = self.get_schedule(schedule_id)
        self.update_workflow(schedule.workflow_id, schedule=None)

    def list_schedules(self, active_only: bool = False) -> list[WorkflowSchedule]:
        return [
            wf.schedule
            for wf in self.list_workflows()
            if wf.schedule and (not active_only or wf.schedule.is_active)
        ]

    # --- Validation ---

    def _validate_graph(self, nodes: list[WorkflowNode], edges: list[WorkflowEdge]) -> None:
        try:
            execution_order(nodes, edges)
        except ValueError as exc:
            raise WorkflowStorageError(str(exc)) from exc

    # --- Helpers ---

    def _save_workflow(self, workflow: Workflow) -> None:
        path = self.workflows_dir / f"{workflow.id}.json"
        self._save_json(path, workflow)

    def _save_json(self, path, model):
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
            temporary = f.name
            json.dump(model.model_dump(mode="json"), f, indent=2)
        os.replace(temporary, path)

    def _load_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
