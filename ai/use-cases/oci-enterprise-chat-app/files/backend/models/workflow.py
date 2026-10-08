"""Pydantic models for the visual workflow builder."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field
from models.timestamps import TimestampModel


class NodeType(str, Enum):
    """Types of nodes in a workflow graph."""

    AGENT = "agent"
    DATA_SOURCE = "data_source"
    INPUT = "input"
    OUTPUT = "output"
    CHAT = "chat"


class ExecutionStatus(str, Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleType(str, Enum):
    """Type of workflow schedule."""

    ONE_TIME = "one_time"
    RECURRING = "recurring"


class WorkflowNode(TimestampModel):
    """A single node in the workflow graph."""

    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Type of node")
    label: str = Field(..., description="Display label for the node")
    position: dict = Field(..., description="Position on canvas (x, y)")
    config: dict = Field(default_factory=dict, description="Node-type-specific configuration")


class WorkflowEdge(TimestampModel):
    """A connection between two nodes in the workflow graph."""

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: str | None = Field(default=None, description="Source output handle")
    target_handle: str | None = Field(default=None, description="Target input handle")


class WorkflowSchedule(TimestampModel):
    """Schedule configuration for automated workflow execution."""

    id: str = Field(..., description="Unique schedule identifier")
    workflow_id: str = Field(..., description="Workflow this schedule belongs to")
    schedule_type: ScheduleType = Field(..., description="One-time or recurring")
    cron_expression: str | None = Field(
        default=None, description="Cron expression for recurring (min hour dom month dow)"
    )
    run_at: datetime | None = Field(default=None, description="Datetime for one-time execution")
    input_data: dict | None = Field(default=None, description="Static input for non-chat workflows")
    is_active: bool = Field(default=True, description="Whether the schedule is enabled")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_run_at: datetime | None = Field(default=None)
    next_run_at: datetime | None = Field(default=None)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Workflow(TimestampModel):
    """A complete workflow definition with nodes and edges."""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = Field(default=None, description="Owner user ID")
    is_active: bool = Field(default=True)
    schedule: WorkflowSchedule | None = Field(
        default=None, description="Optional schedule for automated execution"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowExecution(TimestampModel):
    """Record of a single workflow execution run."""

    id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow that was executed")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_data: dict = Field(default_factory=dict)
    output_data: dict | None = Field(default=None)
    node_results: dict[str, dict] = Field(
        default_factory=dict, description="Per-node execution results keyed by node ID"
    )
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    triggered_by: str | None = Field(default=None, description="'user', 'schedule', or schedule ID")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
