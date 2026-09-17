"""Batch processing service for OCI Object Storage documents."""

import asyncio
import json
import logging
import os
import uuid
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pdfplumber

from models.batch import (
    BatchFileStatus,
    BatchJob,
    BatchJobFile,
    BatchJobStatus,
    BatchTrigger,
    ObjectStoreConnector,
)
from services.oci_object_storage import OCIObjectStorageService

logger = logging.getLogger(__name__)

MAX_BATCH_PARALLELISM = int(os.getenv("MAX_BATCH_PARALLELISM", "5"))


class BatchServiceError(Exception):
    """Exception raised for batch service errors."""

    pass


class BatchService:
    """Service for managing batch processing of OCI Object Storage documents."""

    def __init__(self, upload_dir: str | Path | None = None) -> None:
        self.upload_dir = Path(upload_dir or os.getenv("UPLOAD_DIR", "uploads"))
        self.base_dir = self.upload_dir / ".batch_metadata"
        self.connectors_dir = self.base_dir / "connectors"
        self.triggers_dir = self.base_dir / "triggers"
        self.jobs_dir = self.base_dir / "jobs"
        self._ensure_directories()
        self._oci_service = OCIObjectStorageService()

    def _ensure_directories(self) -> None:
        for d in [self.connectors_dir, self.triggers_dir, self.jobs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # --- Connector CRUD ---

    def create_connector(
        self,
        name: str,
        namespace: str,
        bucket_name: str,
        compartment_id: str,
        region: str,
        prefix: str | None = None,
    ) -> ObjectStoreConnector:
        connector = ObjectStoreConnector(
            id=str(uuid.uuid4()),
            name=name,
            namespace=namespace,
            bucket_name=bucket_name,
            compartment_id=compartment_id,
            prefix=prefix,
            region=region,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._save_json(self.connectors_dir / f"{connector.id}.json", connector)
        logger.info(f"Created connector {connector.id}: {name}")
        return connector

    def get_connector(self, connector_id: str) -> ObjectStoreConnector:
        path = self.connectors_dir / f"{connector_id}.json"
        if not path.exists():
            raise BatchServiceError(f"Connector not found: {connector_id}")
        return ObjectStoreConnector.model_validate(self._load_json(path))

    def list_connectors(self) -> list[ObjectStoreConnector]:
        connectors = []
        for f in self.connectors_dir.glob("*.json"):
            try:
                connectors.append(ObjectStoreConnector.model_validate(self._load_json(f)))
            except Exception as e:
                logger.warning(f"Failed to load connector {f.stem}: {e}")
        connectors.sort(key=lambda c: c.created_at, reverse=True)
        return connectors

    def update_connector(self, connector_id: str, **updates) -> ObjectStoreConnector:
        connector = self.get_connector(connector_id)
        for key, value in updates.items():
            if hasattr(connector, key) and key not in ("id", "created_at"):
                setattr(connector, key, value)
        connector.updated_at = datetime.now(UTC)
        self._save_json(self.connectors_dir / f"{connector.id}.json", connector)
        return connector

    def delete_connector(self, connector_id: str) -> None:
        if any(t.connector_id == connector_id for t in self.list_triggers()):
            raise BatchServiceError("Remove this connector's triggers before deleting it")
        if any(
            j.connector_id == connector_id and j.status in ("pending", "running")
            for j in self.list_jobs()
        ):
            raise BatchServiceError("Connector has unfinished jobs")
        path = self.connectors_dir / f"{connector_id}.json"
        if not path.exists():
            raise BatchServiceError(f"Connector not found: {connector_id}")
        path.unlink()
        logger.info(f"Deleted connector {connector_id}")

    async def test_connector(self, connector_id: str) -> dict:
        connector = self.get_connector(connector_id)
        return await self._oci_service.test_connection(
            namespace=connector.namespace,
            bucket_name=connector.bucket_name,
            compartment_id=connector.compartment_id,
            region=connector.region,
        )

    # --- Trigger CRUD ---

    def create_trigger(
        self,
        connector_id: str,
        name: str,
        schedule: str,
        is_active: bool = True,
        parallelism: int = 1,
    ) -> BatchTrigger:
        # Validate connector exists
        self.get_connector(connector_id)

        # Cap parallelism at the configured maximum
        parallelism = max(1, min(parallelism, MAX_BATCH_PARALLELISM))

        trigger = BatchTrigger(
            id=str(uuid.uuid4()),
            connector_id=connector_id,
            name=name,
            schedule=schedule,
            is_active=is_active,
            parallelism=parallelism,
            created_at=datetime.now(UTC),
        )
        self._save_json(self.triggers_dir / f"{trigger.id}.json", trigger)
        logger.info(f"Created trigger {trigger.id}: {name} (parallelism={parallelism})")
        return trigger

    def get_trigger(self, trigger_id: str) -> BatchTrigger:
        path = self.triggers_dir / f"{trigger_id}.json"
        if not path.exists():
            raise BatchServiceError(f"Trigger not found: {trigger_id}")
        return BatchTrigger.model_validate(self._load_json(path))

    def list_triggers(self) -> list[BatchTrigger]:
        triggers = []
        for f in self.triggers_dir.glob("*.json"):
            try:
                triggers.append(BatchTrigger.model_validate(self._load_json(f)))
            except Exception as e:
                logger.warning(f"Failed to load trigger {f.stem}: {e}")
        triggers.sort(key=lambda t: t.created_at, reverse=True)
        return triggers

    def update_trigger(self, trigger_id: str, **updates) -> BatchTrigger:
        trigger = self.get_trigger(trigger_id)
        if "connector_id" in updates:
            self.get_connector(updates["connector_id"])
        if "parallelism" in updates:
            updates["parallelism"] = max(1, min(updates["parallelism"], MAX_BATCH_PARALLELISM))
        for key, value in updates.items():
            if hasattr(trigger, key) and key not in ("id", "created_at"):
                setattr(trigger, key, value)
        self._save_json(self.triggers_dir / f"{trigger.id}.json", trigger)
        return trigger

    def delete_trigger(self, trigger_id: str) -> None:
        path = self.triggers_dir / f"{trigger_id}.json"
        if not path.exists():
            raise BatchServiceError(f"Trigger not found: {trigger_id}")
        path.unlink()
        logger.info(f"Deleted trigger {trigger_id}")

    # --- Job Management ---

    def create_job(
        self,
        connector_id: str,
        trigger_id: str | None = None,
        parallelism: int = 1,
        processing_mode: str = "batch",
    ) -> BatchJob:
        self.get_connector(connector_id)
        job = BatchJob(
            id=str(uuid.uuid4()),
            trigger_id=trigger_id,
            connector_id=connector_id,
            parallelism=max(1, min(parallelism, MAX_BATCH_PARALLELISM)),
            processing_mode=processing_mode,
            status=BatchJobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        self._save_json(self.jobs_dir / f"{job.id}.json", job)
        logger.info(f"Created batch job {job.id}")
        return job

    def get_job(self, job_id: str) -> BatchJob:
        path = self.jobs_dir / f"{job_id}.json"
        if not path.exists():
            raise BatchServiceError(f"Job not found: {job_id}")
        return BatchJob.model_validate(self._load_json(path))

    def list_jobs(self, trigger_id: str | None = None) -> list[BatchJob]:
        jobs = []
        for f in self.jobs_dir.glob("*.json"):
            if f.name.startswith("file_"):
                continue
            try:
                job = BatchJob.model_validate(self._load_json(f))
                if trigger_id is None or job.trigger_id == trigger_id:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to load job {f.stem}: {e}")
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    def update_job(self, job_id: str, **updates) -> BatchJob:
        job = self.get_job(job_id)
        for key, value in updates.items():
            if hasattr(job, key) and key not in ("id", "created_at"):
                setattr(job, key, value)
        self._save_json(self.jobs_dir / f"{job.id}.json", job)
        return job

    def get_job_files(self, job_id: str) -> list[BatchJobFile]:
        files = []
        for f in self.jobs_dir.glob(f"file_{job_id}_*.json"):
            try:
                files.append(BatchJobFile.model_validate(self._load_json(f)))
            except Exception as e:
                logger.warning(f"Failed to load job file {f.stem}: {e}")
        return files

    # --- Batch Execution ---

    async def execute_job(self, job_id: str, parallelism: int = 1) -> BatchJob:
        """Execute a batch job: list files, download, extract text, chunk, embed, store.

        Args:
            job_id: The job ID to execute.
            parallelism: Number of files to process concurrently (capped at MAX_BATCH_PARALLELISM).
        """
        parallelism = max(1, min(parallelism, MAX_BATCH_PARALLELISM))
        job = self.get_job(job_id)
        rag = None
        job = self.update_job(job_id, status=BatchJobStatus.RUNNING, started_at=datetime.now(UTC))

        try:
            connector = self.get_connector(job.connector_id)
            # List objects from OCI
            objects = await self._oci_service.list_objects(
                namespace=connector.namespace,
                bucket_name=connector.bucket_name,
                region=connector.region,
                prefix=connector.prefix,
            )

            # Filter for PDF files
            pdf_objects = [o for o in objects if o["name"].lower().endswith(".pdf")]
            job = self.update_job(job_id, files_found=len(pdf_objects))

            # Create a single RAG service instance for all files
            from services.rag_service import RAGService

            rag = RAGService()
            await rag._get_vector_store()

            semaphore = asyncio.Semaphore(parallelism)
            results: list[bool] = []  # True = success, False = failure
            progress = {"processed": 0, "failed": 0}

            async def _process_file(obj: dict) -> bool:
                file_record = BatchJobFile(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    file_name=obj["name"],
                    file_size=obj.get("size"),
                    status=BatchFileStatus.PENDING,
                )
                self._save_json(
                    self.jobs_dir / f"file_{job_id}_{file_record.id}.json",
                    file_record,
                )

                async with semaphore:
                    file_path = None
                    try:
                        # Download
                        file_record.status = BatchFileStatus.DOWNLOADING
                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json",
                            file_record,
                        )

                        file_path = await self._oci_service.download_object(
                            namespace=connector.namespace,
                            bucket_name=connector.bucket_name,
                            object_name=obj["name"],
                            region=connector.region,
                        )

                        # Process: extract text
                        file_record.status = BatchFileStatus.PROCESSING
                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json",
                            file_record,
                        )

                        text = await asyncio.to_thread(self._extract_text_from_pdf, file_path)
                        if not text.strip():
                            raise BatchServiceError("No extractable text; OCR may be required")
                        doc_id = f"batch_{job_id}_{file_record.id}"
                        file_record.document_id = doc_id
                        file_record.status = BatchFileStatus.VECTORIZING
                        file_record.vectorization_status = "running"
                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json", file_record
                        )
                        indexed = await rag.index_document(
                            document_id=doc_id, text=text, filename=obj["name"]
                        )
                        if indexed <= 0:
                            raise BatchServiceError("Vectorization produced no indexed chunks")
                        file_record.chunks_indexed = indexed
                        file_record.vectorization_status = "completed"
                        file_record.status = BatchFileStatus.ANALYZING
                        file_record.analysis_status = "running"
                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json", file_record
                        )
                        file_record.analysis_result = await self._analyze_document(
                            text, obj["name"]
                        )
                        file_record.analysis_status = "completed"
                        file_record.status = BatchFileStatus.COMPLETED

                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json",
                            file_record,
                        )
                        return True

                    except Exception as e:
                        logger.error(f"Failed to process {obj['name']}: {e}")
                        file_record.status = BatchFileStatus.FAILED
                        file_record.error_message = str(e)
                        if file_record.vectorization_status == "running":
                            file_record.vectorization_status = "failed"
                        if file_record.analysis_status == "running":
                            file_record.analysis_status = "failed"
                        self._save_json(
                            self.jobs_dir / f"file_{job_id}_{file_record.id}.json",
                            file_record,
                        )
                        return False
                    finally:
                        if file_path is not None:
                            file_path.unlink(missing_ok=True)
                        progress[
                            "processed" if file_record.status == "completed" else "failed"
                        ] += 1
                        self.update_job(
                            job_id,
                            files_processed=progress["processed"],
                            files_failed=progress["failed"],
                        )

            logger.info(f"Processing {len(pdf_objects)} files with parallelism={parallelism}")
            results = await asyncio.gather(*[_process_file(obj) for obj in pdf_objects])

            files_processed = sum(1 for r in results if r)
            files_failed = sum(1 for r in results if not r)

            job = self.update_job(
                job_id,
                status=BatchJobStatus.FAILED if files_failed else BatchJobStatus.COMPLETED,
                error_message=f"{files_failed} file(s) failed; inspect file results"
                if files_failed
                else None,
                files_processed=files_processed,
                files_failed=files_failed,
                completed_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(f"Batch job {job_id} failed: {e}")
            job = self.update_job(
                job_id,
                status=BatchJobStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )

        finally:
            if rag is not None:
                await rag.close()

        if job.trigger_id:
            try:
                self.update_trigger(job.trigger_id, last_run=datetime.now(UTC))
            except BatchServiceError:
                pass

        return job

    async def _analyze_document(self, text: str, filename: str) -> dict:
        from models.workflow import WorkflowNode
        from services.workflow_engine import WorkflowEngine
        from services.workflow_storage import WorkflowStorageService

        engine = WorkflowEngine(WorkflowStorageService(self.upload_dir))
        node = WorkflowNode(
            id="analysis",
            type="agent",
            label="Document analysis",
            position={"x": 0, "y": 0},
            config={
                "prompt": "Analyze the supplied document. Summarize its purpose, key facts, obligations, "
                "and open questions. Ground your response in the document and identify uncertainty."
            },
        )
        # Analyze bounded sections, then synthesize for documents exceeding one context window.
        sections = [text[start : start + 24000] for start in range(0, len(text), 24000)]
        analyses = []
        for section in sections:
            output = await engine._execute_agent_node(
                node, {filename: {"type": "data", "data": section}}, {}
            )
            analyses.append(output["data"])
        synthesis_rounds = 0
        while len(analyses) > 1:
            synthesis_rounds += 1
            if synthesis_rounds > 8:
                raise BatchServiceError("Analysis exceeded the synthesis limit")
            combined = "\n\n".join(analyses)
            analyses = []
            for start in range(0, len(combined), 24000):
                result = await engine._execute_agent_node(
                    node, {filename: {"type": "data", "data": combined[start : start + 24000]}}, {}
                )
                analyses.append(result["data"])
        return {"filename": filename, "summary": analyses[0], "sections_analyzed": len(sections)}

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file."""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return ""

    # --- JSON Helpers ---

    def _save_json(self, path: Path, model: object) -> None:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
            temporary = f.name
            json.dump(model.model_dump(mode="json"), f, indent=2)
        os.replace(temporary, path)

    def _load_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
