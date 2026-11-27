"""
Pydantic schemas for request/response validation.
Provides type-safe API contracts with automatic validation.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from services.schedule_utils import as_utc, cron_trigger
from models.workflow import NodeType
from typing import Literal
from datetime import timezone


class ChatRole(str, Enum):
    """Role in chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: ChatRole
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class RAGSource(BaseModel):
    """Schema for RAG source references."""

    document_name: Optional[str] = None
    page_number: Optional[int] = None
    snippet: str = ""
    relevance_score: float = Field(default=0.5, ge=0, le=1)


class ModelSettings(BaseModel):
    """User-configurable model parameters for chat inference."""

    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0=deterministic, 2=creative)",
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, le=8192, description="Maximum tokens in the response"
    )
    top_p: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Nucleus sampling threshold"
    )
    frequency_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="Penalty for repeated tokens"
    )
    presence_penalty: Optional[float] = Field(
        default=None, ge=-2.0, le=2.0, description="Penalty for new topic tokens"
    )


class ChatRequest(BaseModel):
    """Schema for chat requests with conversation history."""

    message: str = Field(..., min_length=1, max_length=5000)
    document_ids: List[str] = Field(..., description="Document IDs to use as context")
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    max_sources: int = Field(default=5, ge=1, le=20)
    model_settings: Optional[ModelSettings] = Field(
        default=None, description="Optional model parameter overrides"
    )
    inference_model: Optional[str] = Field(
        default=None, description="Model ID to use for inference (overrides server default)"
    )


class ChatResponse(BaseModel):
    """Schema for chat responses with sources and confidence."""

    message: str
    sources: List[RAGSource] = []
    confidence: float = Field(default=0.0, ge=0, le=1)
    processing_time_ms: Optional[float] = None


class VectorStoreHealth(BaseModel):
    """Schema for vector store health status."""

    status: str
    table: Optional[str] = None
    total_chunks: Optional[int] = None
    embedding_dimension: Optional[int] = None
    error: Optional[str] = None

    class Config:
        extra = "allow"


class EmbeddingServiceHealth(BaseModel):
    """Schema for embedding service health status."""

    status: str
    endpoint: Optional[str] = None
    model: Optional[str] = None
    dimension: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None

    class Config:
        extra = "allow"


class WordFrequency(BaseModel):
    """A single word with its frequency count."""

    word: str
    count: int


class WordCloudRequest(BaseModel):
    """Request schema for generating a word cloud from documents."""

    document_ids: List[str] = Field(
        ..., min_length=1, description="Document IDs to extract text from"
    )
    max_words: int = Field(
        default=100, ge=10, le=300, description="Maximum number of words to return"
    )


class WordCloudResponse(BaseModel):
    """Response schema for word cloud data."""

    words: List[WordFrequency]
    total_documents: int
    total_words_processed: int


class WebSourceAddRequest(BaseModel):
    """Request schema for adding a web source."""

    url: str = Field(..., min_length=1, max_length=2000, description="URL to scrape")
    title: str = Field(default="", max_length=500, description="Optional title for the source")


class WebSourceResponse(BaseModel):
    """Response schema for a web source."""

    id: str
    url: str
    title: str
    status: str
    content_length: Optional[int] = None
    chunks_indexed: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RAGHealthResponse(BaseModel):
    """Schema for RAG health check response."""

    status: str
    endpoint: Optional[str] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    vector_search_enabled: Optional[bool] = None
    llm_status: Optional[str] = None
    llm_error: Optional[str] = None
    vector_store: Optional[VectorStoreHealth] = None
    embedding_service: Optional[EmbeddingServiceHealth] = None

    class Config:
        extra = "allow"


# --- Batch Processing Schemas ---


class ConnectorCreateRequest(BaseModel):
    """Request schema for creating an OCI Object Storage connector."""

    name: str = Field(..., min_length=1, max_length=200, description="Connector name")
    namespace: str = Field(..., min_length=1, description="OCI Object Storage namespace")
    bucket_name: str = Field(..., min_length=1, description="Bucket name")
    compartment_id: str = Field(..., min_length=1, description="OCI compartment OCID")
    region: str = Field(..., min_length=1, description="OCI region identifier")
    prefix: Optional[str] = Field(default=None, description="Optional object name prefix filter")


class ConnectorTestRequest(BaseModel):
    """Request schema for testing OCI Object Storage connectivity (no name required)."""

    namespace: str = Field(..., min_length=1, description="OCI Object Storage namespace")
    bucket_name: str = Field(..., min_length=1, description="Bucket name")
    compartment_id: str = Field(..., min_length=1, description="OCI compartment OCID")
    region: str = Field(..., min_length=1, description="OCI region identifier")


class ConnectorResponse(BaseModel):
    """Response schema for an OCI Object Storage connector."""

    id: str
    name: str
    namespace: str
    bucket_name: str
    compartment_id: str
    prefix: Optional[str] = None
    region: str
    created_at: datetime
    updated_at: datetime


class TriggerCreateRequest(BaseModel):
    """Request schema for creating a batch processing trigger."""

    connector_id: str = Field(..., description="Associated connector ID")
    name: str = Field(..., min_length=1, max_length=200, description="Trigger name")
    schedule: str = Field(..., min_length=5, description="Cron expression (e.g. '0 2 * * *')")
    is_active: bool = Field(default=True, description="Whether the trigger is enabled")
    parallelism: int = Field(default=1, ge=1, description="Number of files to process in parallel")

    @field_validator("schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have exactly 5 fields: minute hour day month day_of_week"
            )
        cron_trigger(v)
        return v.strip()


class TriggerUpdateRequest(BaseModel):
    connector_id: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    parallelism: Optional[int] = Field(default=None, ge=1)

    @field_validator("schedule")
    @classmethod
    def validate_cron(cls, value):
        if value is not None:
            cron_trigger(value)
        return value


class TriggerResponse(BaseModel):
    """Response schema for a batch processing trigger."""

    id: str
    connector_id: str
    name: str
    schedule: str
    is_active: bool
    parallelism: int = 1
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime


class ConnectorRunRequest(BaseModel):
    processing_mode: Literal["normal", "batch"] = "batch"
    parallelism: int = Field(default=1, ge=1, le=5)


class BatchJobResponse(BaseModel):
    """Response schema for a batch processing job."""

    id: str
    trigger_id: Optional[str] = None
    connector_id: str
    status: str
    processing_mode: str = "batch"
    files_found: int = 0
    files_processed: int = 0
    files_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class BatchJobFileResponse(BaseModel):
    """Response schema for a file within a batch job."""

    id: str
    job_id: str
    file_name: str
    file_size: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    document_id: Optional[str] = None
    chunks_indexed: int = 0
    vectorization_status: str = "pending"
    analysis_status: str = "pending"
    analysis_result: Optional[dict] = None


# --- Workflow Schemas ---


class WorkflowNodeSchema(BaseModel):
    """Schema for a workflow node in requests."""

    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type: agent, data_source, input, output, chat")
    label: str = Field(..., description="Display label")
    position: dict = Field(..., description="Canvas position (x, y)")
    config: dict = Field(default_factory=dict, description="Node configuration")


class WorkflowEdgeSchema(BaseModel):
    """Schema for a workflow edge in requests."""

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    """Request schema for creating a workflow."""

    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: str = Field(default="", max_length=1000, description="Workflow description")
    nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    edges: List[WorkflowEdgeSchema] = Field(default_factory=list)


class WorkflowUpdateRequest(BaseModel):
    """Request schema for updating a workflow."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    nodes: Optional[List[WorkflowNodeSchema]] = None
    edges: Optional[List[WorkflowEdgeSchema]] = None


class WorkflowResponse(BaseModel):
    """Response schema for a workflow."""

    id: str
    name: str
    description: str
    nodes: List[dict] = []
    edges: List[dict] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    is_active: bool = True
    schedule: Optional[dict] = None


class WorkflowExecuteRequest(BaseModel):
    """Request schema for executing a workflow."""

    input_data: dict = Field(default_factory=dict, description="Input data for the workflow")


class WorkflowExecutionResponse(BaseModel):
    """Response schema for a workflow execution."""

    id: str
    workflow_id: str
    status: str
    input_data: dict = {}
    output_data: Optional[dict] = None
    node_results: dict = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    triggered_by: Optional[str] = None


# --- Workflow Schedule Schemas ---


class ScheduleCreateRequest(BaseModel):
    """Request schema for creating or updating a workflow schedule."""

    schedule_type: str = Field(..., description="'one_time' or 'recurring'")
    cron_expression: Optional[str] = Field(
        default=None, description="Cron expression for recurring (min hour dom month dow)"
    )
    run_at: Optional[datetime] = Field(default=None, description="Datetime for one-time execution")
    input_data: Optional[dict] = Field(
        default=None, description="Static input for scheduled execution"
    )
    is_active: bool = Field(default=True, description="Whether the schedule is enabled")

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v: str) -> str:
        if v not in ("one_time", "recurring"):
            raise ValueError("schedule_type must be 'one_time' or 'recurring'")
        return v

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            parts = v.strip().split()
            if len(parts) != 5:
                raise ValueError(
                    "Cron expression must have exactly 5 fields: minute hour day month day_of_week"
                )
            cron_trigger(v)
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.schedule_type == "recurring":
            if not self.cron_expression:
                raise ValueError("Recurring schedules require a cron expression")
            self.run_at = None
        else:
            if not self.run_at:
                raise ValueError("One-time schedules require a run time")
            self.run_at = as_utc(self.run_at)
            if self.run_at <= datetime.now(timezone.utc):
                raise ValueError("One-time schedule must be in the future")
            self.cron_expression = None
        return self


class ScheduleToggleRequest(BaseModel):
    """Request schema for toggling a schedule's active state."""

    is_active: bool = Field(..., description="Whether to enable or disable the schedule")


class ScheduleResponse(BaseModel):
    """Response schema for a workflow schedule."""

    id: str
    workflow_id: str
    schedule_type: str
    cron_expression: Optional[str] = None
    run_at: Optional[datetime] = None
    input_data: Optional[dict] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class ScheduledRunResponse(BaseModel):
    """Response schema for a scheduled workflow run."""

    execution_id: str
    workflow_id: str
    status: str
    triggered_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
