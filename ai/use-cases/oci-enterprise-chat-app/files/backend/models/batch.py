"""Pydantic models for batch processing of OCI Object Storage files."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field
from models.timestamps import TimestampModel


class BatchJobStatus(str, Enum):
    """Status of a batch processing job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchFileStatus(str, Enum):
    """Status of an individual file within a batch job."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    VECTORIZING = "vectorizing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ObjectStoreConnector(TimestampModel):
    """Configuration for connecting to an OCI Object Storage bucket."""

    id: str = Field(..., description="Unique connector identifier")
    name: str = Field(..., description="Human-readable connector name")
    namespace: str = Field(..., description="OCI Object Storage namespace")
    bucket_name: str = Field(..., description="Bucket name")
    compartment_id: str = Field(..., description="OCI compartment OCID")
    prefix: str | None = Field(default=None, description="Optional object name prefix filter")
    region: str = Field(..., description="OCI region identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchTrigger(TimestampModel):
    """Scheduled trigger that initiates batch processing jobs."""

    id: str = Field(..., description="Unique trigger identifier")
    connector_id: str = Field(..., description="Associated connector ID")
    name: str = Field(..., description="Human-readable trigger name")
    schedule: str = Field(..., description="Cron expression for scheduling (e.g. '0 2 * * *')")
    is_active: bool = Field(default=True, description="Whether the trigger is enabled")
    parallelism: int = Field(default=1, ge=1, description="Number of files to process in parallel")
    last_run: datetime | None = Field(default=None, description="Timestamp of last execution")
    next_run: datetime | None = Field(default=None, description="Timestamp of next scheduled run")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchJob(TimestampModel):
    """A single batch processing job execution."""

    id: str = Field(..., description="Unique job identifier")
    trigger_id: str | None = Field(default=None, description="Trigger that initiated this job")
    connector_id: str = Field(..., description="Connector used for this job")
    status: BatchJobStatus = Field(default=BatchJobStatus.PENDING)
    parallelism: int = Field(default=1, ge=1)
    processing_mode: str = "batch"
    files_found: int = Field(default=0, description="Total files discovered in bucket")
    files_processed: int = Field(default=0, description="Files successfully processed")
    files_failed: int = Field(default=0, description="Files that failed processing")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchJobFile(TimestampModel):
    """Tracks the processing status of an individual file within a batch job."""

    id: str = Field(..., description="Unique file record identifier")
    job_id: str = Field(..., description="Parent batch job ID")
    file_name: str = Field(..., description="Object name in the bucket")
    file_size: int | None = Field(default=None, description="File size in bytes")
    status: BatchFileStatus = Field(default=BatchFileStatus.PENDING)
    error_message: str | None = Field(default=None)

    document_id: str | None = None
    chunks_indexed: int = 0
    vectorization_status: str = "pending"
    analysis_status: str = "pending"
    analysis_result: dict | None = None
