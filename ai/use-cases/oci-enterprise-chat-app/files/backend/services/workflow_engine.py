"""Workflow execution engine for processing node-based agent pipelines.

Supports node types: INPUT, AGENT, DATA_SOURCE, OUTPUT, CHAT.
Handles fan-in (multi-input agent), fan-out (multi-output agent),
agent-to-agent chaining, project-based RAG inputs, chat blocks,
and object store output destinations.
"""

import asyncio
import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timezone
from typing import Any

from openai import AsyncOpenAI
from services.workflow_validation import execution_order

from models.workflow import (
    ExecutionStatus,
    NodeType,
    Workflow,
    WorkflowExecution,
)
from services.workflow_storage import WorkflowStorageService

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """Exception raised for workflow engine errors."""

    pass


class WorkflowEngine:
    """Executes workflow graphs by processing nodes in topological order.

    The engine traverses the workflow DAG using Kahn's algorithm, executing
    each node with the collected outputs of its predecessors. It supports:

    - Fan-in: multiple predecessor outputs are merged into a single agent context
    - Fan-out: a single node's output is available to all downstream consumers
    - Agent-to-agent chaining: upstream agent output becomes downstream context
    - Project RAG input: input nodes backed by a project's vectorized documents
    - Chat nodes: interactive input/output that can be skipped during scheduling
    - Object store output: results uploaded to OCI Object Storage
    """

    def __init__(self, storage: WorkflowStorageService | None = None) -> None:
        self._storage = storage or WorkflowStorageService()

    # ------------------------------------------------------------------
    # Public execution entry point
    # ------------------------------------------------------------------

    async def execute(
        self,
        workflow: Workflow,
        input_data: dict,
        *,
        interactive: bool = True,
        triggered_by: str = "user",
    ) -> WorkflowExecution:
        """Execute a workflow with the given input data.

        Args:
            workflow: The workflow definition to execute.
            input_data: Input data passed to input and chat nodes.
                Expected keys: ``message`` (str), optionally ``project_id``.
            interactive: When True (default), CHAT nodes pass through user
                input. When False (scheduled execution), CHAT nodes are
                skipped and static *input_data* is used instead.

        Returns:
            WorkflowExecution with per-node results and final output.
        """
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            input_data=input_data,
            triggered_by=triggered_by,
            started_at=datetime.now(UTC),
        )
        self._storage.save_execution(execution)

        try:
            if not workflow.nodes:
                raise WorkflowEngineError("Add at least one node before executing")
            execution_order = self._topological_sort(workflow)

            node_map: dict[str, Any] = {node.id: node for node in workflow.nodes}

            # incoming edges: target_node_id -> [source_node_ids]
            incoming: dict[str, list[str]] = defaultdict(list)
            for edge in workflow.edges:
                incoming[edge.target].append(edge.source)

            node_outputs: dict[str, dict] = {}

            for node_id in execution_order:
                node = node_map[node_id]

                # Gather outputs from all predecessor nodes (fan-in)
                node_input: dict[str, dict] = {}
                for source_id in incoming[node_id]:
                    if source_id in node_outputs:
                        node_input[source_id] = node_outputs[source_id]

                try:
                    execution.node_results[node_id] = {"status": "running"}
                    self._storage.save_execution(execution)
                    result = await self._execute_node(
                        node,
                        node_input,
                        input_data,
                        node_map=node_map,
                        interactive=interactive,
                        workflow_name=workflow.name,
                        execution_id=execution.id,
                    )
                    node_outputs[node_id] = result
                    execution.node_results[node_id] = {
                        "status": "completed",
                        "output": result,
                    }
                    self._storage.save_execution(execution)
                except Exception as e:
                    logger.error("Node %s (%s) failed: %s", node_id, node.label, e)
                    execution.node_results[node_id] = {
                        "status": "failed",
                        "error": str(e),
                    }
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = f"Node '{node.label}' failed: {e}"
                    execution.completed_at = datetime.now(UTC)
                    self._storage.save_execution(execution)
                    return execution

            # Collect output from OUTPUT and CHAT nodes
            output_data: dict[str, dict] = {}
            for node in workflow.nodes:
                if node.type in (NodeType.OUTPUT, NodeType.CHAT) and node.id in node_outputs:
                    output_data[node.id] = node_outputs[node.id]

            if not output_data:
                sources = {edge.source for edge in workflow.edges}
                output_data = {
                    key: value for key, value in node_outputs.items() if key not in sources
                }
            execution.status = ExecutionStatus.COMPLETED
            execution.output_data = output_data
            execution.completed_at = datetime.now(UTC)

        except Exception as e:
            logger.error("Workflow execution failed: %s", e)
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(UTC)

        self._storage.save_execution(execution)
        return execution

    # ------------------------------------------------------------------
    # Topological sort (Kahn's algorithm)
    # ------------------------------------------------------------------

    def _topological_sort(self, workflow: Workflow) -> list[str]:
        """Compute topological ordering of workflow nodes.

        Raises:
            WorkflowEngineError: If the graph contains a cycle.
        """
        return execution_order(workflow.nodes, workflow.edges)

    # ------------------------------------------------------------------
    # Node dispatcher
    # ------------------------------------------------------------------

    async def _execute_node(
        self,
        node,
        node_input: dict[str, dict],
        workflow_input: dict,
        *,
        node_map: dict[str, Any],
        interactive: bool,
        workflow_name: str,
        execution_id: str,
    ) -> dict:
        """Execute a single node based on its type.

        Args:
            node: The workflow node to execute.
            node_input: Outputs from predecessor nodes keyed by source node ID.
            workflow_input: Original workflow input data.
            node_map: Mapping of node_id -> node for label lookups.
            interactive: Whether this is an interactive (chat) execution.
            workflow_name: Name of the parent workflow (for template variables).
            execution_id: Current execution ID (for template variables).

        Returns:
            Node output as a dict with at least ``type`` and ``data`` keys.
        """
        if node.type == NodeType.INPUT:
            return await self._execute_input_node(node, workflow_input)
        elif node.type == NodeType.AGENT:
            return await self._execute_agent_node(node, node_input, node_map)
        elif node.type == NodeType.DATA_SOURCE:
            return await self._execute_data_source_node(node, node_input)
        elif node.type == NodeType.OUTPUT:
            return await self._execute_output_node(
                node,
                node_input,
                workflow_name=workflow_name,
                execution_id=execution_id,
            )
        elif node.type == NodeType.CHAT:
            return self._execute_chat_node(
                node, node_input, workflow_input, interactive=interactive
            )
        else:
            raise WorkflowEngineError(f"Unknown node type: {node.type}")

    # ------------------------------------------------------------------
    # INPUT node
    # ------------------------------------------------------------------

    async def _execute_input_node(self, node, workflow_input: dict) -> dict:
        """Execute an input node.

        Handles two input types:
        - ``text`` (default): passes through the workflow message.
        - ``project``: performs a RAG query against the project's vectorized
          documents and returns retrieved chunks.
        """
        input_type = node.config.get("input_type", "text")

        if input_type == "project":
            return await self._execute_project_input(node, workflow_input)

        if input_type == "file":
            if not node.config.get("file_content"):
                raise WorkflowEngineError("Attach a file and save the node configuration")
            return {
                "type": "data",
                "data": [
                    {
                        "filename": node.config.get("file_name", "input"),
                        "content": node.config["file_content"],
                    }
                ],
            }
        # Default text pass-through
        return {
            "type": input_type,
            "data": workflow_input.get("message", workflow_input),
        }

    async def _execute_project_input(self, node, workflow_input: dict) -> dict:
        """Handle a project-based RAG input node.

        Queries the project's vector store with the workflow input message and
        returns the retrieved document chunks.

        Expected node config::

            {
                "input_type": "project",
                "project_id": "<uuid>",
                "document_ids": ["doc1", "doc2", ...],  // optional filter
                "top_k": 5                                // optional
            }

        Returns:
            Dict with ``type`` = ``"rag"``, ``data`` = list of chunk dicts,
            and ``project_id``.
        """
        try:
            from services.embedding_service import EmbeddingService
            from services.oracle_vector_store import OracleVectorStore

            project_id = node.config.get("project_id") or node.config.get("project", {}).get(
                "project_id", ""
            )
            document_ids = node.config.get("document_ids", [])
            top_k = node.config.get("top_k", 5)

            if not project_id or not document_ids:
                raise WorkflowEngineError(
                    "Select a project with indexed documents and save its configuration"
                )
            query = workflow_input.get("message", "")
            if not query:
                raise WorkflowEngineError("Project retrieval requires an input message")

            embedding_service = EmbeddingService()
            vector_store = OracleVectorStore()
            try:
                await vector_store.initialize()
                query_embedding = await embedding_service.generate_embedding(query)
                if not query_embedding:
                    raise WorkflowEngineError("Failed to generate query embedding")

                search_kwargs: dict[str, Any] = {
                    "query_embedding": query_embedding,
                    "top_k": top_k,
                }
                if document_ids:
                    search_kwargs["document_ids"] = document_ids

                results = await vector_store.search(**search_kwargs)

                chunks = [
                    {
                        "content": r.content,
                        "score": r.score,
                        "filename": r.filename,
                        "document_id": r.document_id,
                    }
                    for r in results
                ]

                return {
                    "type": "rag"
                    if node.config.get("project", {}).get("use_as_rag", True)
                    else "text",
                    "data": chunks,
                    "project_id": project_id,
                }
            finally:
                await vector_store.close()
                await embedding_service.close()

        except Exception as e:
            logger.error("Project input node %s failed: %s", node.id, e)
            raise WorkflowEngineError(f"Project retrieval failed: {e}") from e

    # ------------------------------------------------------------------
    # AGENT node (fan-in aware)
    # ------------------------------------------------------------------

    async def _execute_agent_node(
        self,
        node,
        node_input: dict[str, dict],
        node_map: dict[str, Any],
    ) -> dict:
        """Execute an agent node by calling the LLM endpoint.

        Fan-in behaviour: when multiple predecessor nodes feed into this agent,
        their outputs are merged into the context. Each source is labelled with
        ``[Source: <node_label>]`` so the LLM can distinguish them.

        RAG-type inputs (from project-based input nodes or data source nodes)
        are injected as retrieval context in the system prompt, separate from
        direct user/agent message content.
        """
        prompt = node.config.get("prompt", "You are a helpful assistant.")
        model = (
            node.config.get("model")
            or os.getenv("RAG_MODEL")
            or os.getenv("CORRINO_MODEL", "meta.llama-4-maverick-17b-128e-instruct-fp8")
        )
        temperature = node.config.get("temperature", 0.3)
        max_tokens = node.config.get("max_tokens", 2048)

        # Separate RAG context from direct message context
        rag_context_parts: list[str] = []
        message_context_parts: list[str] = []

        for source_id, output in node_input.items():
            source_node = node_map.get(source_id)
            source_label = source_node.label if source_node else source_id

            output_type = output.get("type", "text")
            data = output.get("data", "")

            # RAG / retrieval context (from project inputs or data source nodes)
            if output_type == "rag" or output_type == "data":
                formatted = self._format_rag_context(data, source_label)
                if formatted:
                    rag_context_parts.append(formatted)
            else:
                # Direct content: text from other agents, chat, or plain input
                text = self._extract_text(data)
                if text:
                    message_context_parts.append(f"[Source: {source_label}] {text}")

        # Build system prompt with optional retrieval context
        system_content = prompt
        if rag_context_parts:
            retrieval_block = "\n\n".join(rag_context_parts)
            system_content = (
                f"{prompt}\n\n"
                f"--- Retrieved Context ---\n"
                f"{retrieval_block}\n"
                f"--- End Retrieved Context ---"
            )

        # Build user message from direct context
        user_message = (
            "\n\n".join(message_context_parts) if message_context_parts else "Execute the task."
        )

        try:
            endpoint_url = os.getenv("RAG_ENDPOINT_URL", "").rstrip("/")
            if not endpoint_url:
                raise WorkflowEngineError("RAG_ENDPOINT_URL is not configured")
            client = AsyncOpenAI(
                base_url=endpoint_url if endpoint_url.endswith("/v1") else f"{endpoint_url}/v1",
                api_key=os.getenv("RAG_API_KEY") or "no-key-required",
                timeout=60.0,
            )

            async with client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            answer = response.choices[0].message.content if response.choices else ""
            if not answer:
                raise WorkflowEngineError("Agent returned an empty response")
            return {"type": "text", "data": answer}

        except Exception as e:
            logger.error("Agent node %s LLM call failed: %s", node.id, e)
            raise WorkflowEngineError(f"LLM call failed: {e}")

    # ------------------------------------------------------------------
    # DATA_SOURCE node
    # ------------------------------------------------------------------

    async def _execute_data_source_node(self, node, node_input: dict) -> dict:
        """Execute a data source node by querying the vector store."""
        source_type = node.config.get("source_type", "oracle_vector_db")

        if source_type == "oracle_vector_db":
            return await self._query_vector_store(node, node_input)

        if source_type == "object_storage":
            return await self._read_object_storage(node)
        raise WorkflowEngineError(f"Unsupported source type: {source_type}")

    async def _read_object_storage(self, node):
        from services.batch_service import BatchService
        from services.oci_object_storage import OCIObjectStorageService

        batch = BatchService(upload_dir=self._storage.upload_dir)
        connector = batch.get_connector(node.config.get("connector_id", ""))
        service = OCIObjectStorageService()
        objects = await service.list_objects(
            namespace=connector.namespace,
            bucket_name=connector.bucket_name,
            region=connector.region,
            prefix=connector.prefix,
        )
        chunks = []
        supported = (".pdf", ".txt", ".md", ".json", ".csv")
        objects = [obj for obj in objects if obj["name"].lower().endswith(supported)]
        max_files = int(node.config.get("max_files", 20))
        if not 1 <= max_files <= 100 or len(objects) > max_files:
            raise WorkflowEngineError(
                "Source exceeds the file limit; narrow the connector prefix or use Batch processing"
            )
        for obj in objects:
            if obj.get("size", 0) > 10 * 1024 * 1024:
                raise WorkflowEngineError(
                    "Object exceeds the 10 MB workflow source limit; use Batch processing"
                )
            path = await service.download_object(
                namespace=connector.namespace,
                bucket_name=connector.bucket_name,
                object_name=obj["name"],
                region=connector.region,
            )
            try:
                if path.suffix.lower() == ".pdf":
                    content = await asyncio.to_thread(batch._extract_text_from_pdf, path)
                else:
                    content = await asyncio.to_thread(path.read_text, encoding="utf-8")
                if not content.strip():
                    raise WorkflowEngineError(
                        f"No readable text in {obj['name']}; OCR may be required"
                    )
                chunks.append({"filename": obj["name"], "content": content})
            finally:
                path.unlink(missing_ok=True)
        if not chunks:
            raise WorkflowEngineError("No supported documents found for this connector")
        return {"type": "data", "data": chunks}

    async def _query_vector_store(self, node, node_input: dict) -> dict:
        """Query the Oracle Vector Store for relevant documents."""
        try:
            from services.embedding_service import EmbeddingService
            from services.oracle_vector_store import OracleVectorStore

            # Extract query string from incoming nodes
            query = ""
            for _source_id, output in node_input.items():
                data = output.get("data", "")
                if isinstance(data, str) and data:
                    query = data
                    break

            if not query:
                raise WorkflowEngineError("No query provided to data source")

            embedding_service = EmbeddingService()
            vector_store = OracleVectorStore()
            try:
                await vector_store.initialize()
                query_embedding = await embedding_service.generate_embedding(query)
                if not query_embedding:
                    raise WorkflowEngineError("Failed to generate embedding")

                top_k = node.config.get("top_k", 5)
                results = await vector_store.search(
                    query_embedding=query_embedding,
                    top_k=top_k,
                )

                chunks = [
                    {"content": r.content, "score": r.score, "filename": r.filename}
                    for r in results
                ]

                return {"type": "data", "data": chunks}
            finally:
                await vector_store.close()
                await embedding_service.close()

        except Exception as e:
            logger.error("Vector store query failed: %s", e)
            raise WorkflowEngineError(f"Vector store query failed: {e}") from e

    # ------------------------------------------------------------------
    # OUTPUT node (with object store support)
    # ------------------------------------------------------------------

    async def _execute_output_node(
        self,
        node,
        node_input: dict,
        *,
        workflow_name: str,
        execution_id: str,
    ) -> dict:
        """Execute an output node.

        Supports output types:
        - ``text`` (default): passes through collected inputs.
        - ``chat``: returns data formatted for the chat interface.
        - ``object_store``: uploads the result to OCI Object Storage.
        """
        output_type = node.config.get("output_type", "text")

        # Combine all predecessor outputs
        combined: dict[str, dict] = {}
        for source_id, output in node_input.items():
            combined[source_id] = output

        if len(combined) == 1:
            result_data = list(combined.values())[0].get("data", "")
        else:
            result_data = combined

        if output_type == "object_store":
            upload_result = await self._upload_to_object_store(
                node=node,
                data=result_data,
                workflow_name=workflow_name,
                execution_id=execution_id,
            )
            return {
                "type": "object_store",
                "data": result_data,
                "upload": upload_result,
            }

        if output_type == "json" and isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except ValueError as exc:
                raise WorkflowEngineError("Output is not valid JSON") from exc
        if output_type == "chat":
            return {"type": "chat", "data": result_data}

        return {"type": output_type, "data": result_data}

    # ------------------------------------------------------------------
    # CHAT node
    # ------------------------------------------------------------------

    def _execute_chat_node(
        self,
        node,
        node_input: dict[str, dict],
        workflow_input: dict,
        *,
        interactive: bool,
    ) -> dict:
        """Execute a chat node.

        In interactive mode the chat node acts as an I/O boundary:
        - When it has no predecessors (start of graph), it provides the user
          message as input to downstream nodes.
        - When it has predecessors (end of graph), it collects their outputs
          to return as the chat response.

        In non-interactive (scheduled) mode the chat node is effectively
        skipped: it passes through the static ``input_data`` so the rest
        of the pipeline can still execute without a live user.
        """
        if not interactive and not node_input:
            # Scheduled source: pass through static input data
            return {
                "type": "chat",
                "data": workflow_input.get("message", ""),
            }

        # Interactive mode
        if node_input:
            # Chat node at the end: aggregate predecessor outputs as the response
            parts: list[str] = []
            for _source_id, output in node_input.items():
                text = self._extract_text(output.get("data", ""))
                if text:
                    parts.append(text)
            return {
                "type": "chat",
                "data": "\n\n".join(parts) if parts else "",
            }

        # Chat node at the start: provide user message as input
        return {
            "type": "chat",
            "data": workflow_input.get("message", ""),
        }

    # ------------------------------------------------------------------
    # Object Store upload helper
    # ------------------------------------------------------------------

    async def _upload_to_object_store(
        self,
        *,
        node,
        data: Any,
        workflow_name: str,
        execution_id: str,
    ) -> dict:
        """Upload output data to OCI Object Storage.

        The node config is expected to contain::

            {
                "output_type": "object_store",
                "object_store": {
                    "bucket_name": "my-bucket",
                    "object_path": "workflows/{{workflow_name}}/{{timestamp}}/result.json",
                    "file_format": "json"   // json | txt | csv | pdf
                }
            }

        Template variables in ``object_path``:
        - ``{{workflow_name}}``: name of the workflow
        - ``{{timestamp}}``: ISO-8601 timestamp (file-system safe)
        - ``{{execution_id}}``: unique execution identifier

        Returns:
            Dict describing the upload result (bucket, path, status).
        """
        try:
            from services.oci_object_storage import OCIObjectStorageService

            os_config = node.config.get("object_store", {})
            if os_config.get("connector_id"):
                from services.batch_service import BatchService

                connector = BatchService(upload_dir=self._storage.upload_dir).get_connector(
                    os_config["connector_id"]
                )
                os_config = {
                    **os_config,
                    "bucket_name": connector.bucket_name,
                    "namespace": connector.namespace,
                    "region": connector.region,
                }
            bucket_name = os_config.get("bucket_name", "")
            object_path_template = os_config.get("object_path", "")
            file_format = os_config.get("file_format", "json")

            if not bucket_name or not object_path_template:
                raise WorkflowEngineError(
                    "Missing bucket_name or object_path in object_store config"
                )

            # Resolve template variables
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safe_workflow_name = workflow_name.replace(" ", "_").replace("/", "_")

            object_path = (
                object_path_template.replace("{{workflow_name}}", safe_workflow_name)
                .replace("{{timestamp}}", timestamp)
                .replace("{{execution_id}}", execution_id)
            )

            # Serialize data according to file format
            content_bytes = self._serialize_output(data, file_format)

            # Upload via OCI Object Storage client
            namespace = os_config.get("namespace") or os.getenv("OCI_NAMESPACE", "")
            region = os_config.get("region") or os.getenv("OCI_REGION", "")
            if not namespace or not region:
                raise WorkflowEngineError(
                    "Configure an OCI connector or namespace and region for the output"
                )
            await OCIObjectStorageService().upload_object(
                namespace=namespace,
                bucket_name=bucket_name,
                object_name=object_path,
                data=content_bytes,
                region=region,
            )

            logger.info(
                "Uploaded workflow output to oci://%s/%s/%s",
                namespace,
                bucket_name,
                object_path,
            )

            return {
                "status": "uploaded",
                "bucket_name": bucket_name,
                "object_path": object_path,
                "file_format": file_format,
                "size_bytes": len(content_bytes),
            }

        except Exception as e:
            logger.error("Object store upload failed: %s", e)
            raise WorkflowEngineError(f"Object store upload failed: {e}") from e

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_output(data: Any, file_format: str) -> bytes:
        """Serialize output data to bytes for the requested file format."""
        if file_format == "json":
            return json.dumps(data, indent=2, default=str).encode("utf-8")

        if file_format == "csv":
            # Best-effort CSV: if data is a list of dicts, convert to CSV rows
            import csv
            import io

            buf = io.StringIO()
            if isinstance(data, list) and data and isinstance(data[0], dict):
                writer = csv.DictWriter(buf, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                buf.write(str(data))
            return buf.getvalue().encode("utf-8")

        if file_format == "pdf":
            # Minimal PDF generation -- store plain text in a PDF wrapper.
            # A full PDF library (e.g. reportlab) is not assumed to be available.
            text_content = str(data) if not isinstance(data, str) else data
            return _minimal_pdf(text_content)

        # Default: plain text
        if isinstance(data, str):
            return data.encode("utf-8")
        return str(data).encode("utf-8")

    @staticmethod
    def _extract_text(data: Any) -> str:
        """Extract a plain-text representation from heterogeneous node output data."""
        if isinstance(data, str):
            return data
        if isinstance(data, list):
            # List of chunks (RAG results) -- join their content fields
            parts = []
            for item in data:
                if isinstance(item, dict) and "content" in item:
                    parts.append(item["content"])
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        if isinstance(data, dict):
            # Possibly a nested node output -- try common keys
            if "data" in data:
                return WorkflowEngine._extract_text(data["data"])
            return json.dumps(data, ensure_ascii=False)
        return str(data)

    @staticmethod
    def _format_rag_context(data: Any, source_label: str) -> str:
        """Format RAG/data-source output as a labelled retrieval context block."""
        if isinstance(data, list):
            # List of chunk dicts
            chunk_lines: list[str] = []
            for chunk in data:
                if isinstance(chunk, dict):
                    content = chunk.get("content", str(chunk))
                    filename = chunk.get("filename", "")
                    prefix = f"[{filename}] " if filename else ""
                    chunk_lines.append(f"{prefix}{content}")
                else:
                    chunk_lines.append(str(chunk))
            if chunk_lines:
                joined = "\n".join(chunk_lines)
                return f"[Source: {source_label}]\n{joined}"
            return ""
        if isinstance(data, str) and data:
            return f"[Source: {source_label}] {data}"
        return ""


# ----------------------------------------------------------------------
# Minimal PDF helper (no external dependency)
# ----------------------------------------------------------------------


def _minimal_pdf(text: str) -> bytes:
    """Export every line as a paginated PDF using the built-in Latin-1 font.

    Reject unsupported characters explicitly rather than corrupting the output.
    JSON/TXT outputs support full Unicode.
    """
    import textwrap

    try:
        text.encode("latin-1")
    except UnicodeEncodeError as exc:
        raise WorkflowEngineError(
            "PDF export supports Latin-1 text; use JSON or TXT for Unicode output"
        ) from exc
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, 85, replace_whitespace=False) or [""])
    pages = [lines[start : start + 50] for start in range(0, len(lines), 50)] or [[""]]
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids = []
    for page_lines in pages:
        page_id = len(objects) + 1
        page_ids.append(page_id)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {page_id + 1} 0 R /Resources << /Font << /F1 3 0 R >> >> >>"
        )
        ops = ["BT /F1 10 Tf 14 TL 40 750 Td"]
        for line in page_lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({safe}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops)
        objects.append(
            f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream"
        )
    objects[1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{id} 0 R' for id in page_ids)}] /Count {len(pages)} >>"
    )
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
    xref = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    result.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:]).encode())
    result.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(result)
