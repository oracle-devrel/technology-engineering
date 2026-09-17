"""PRD3 regression tests with isolated storage and external service responses."""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from openai import AsyncOpenAI

from models.workflow import WorkflowNode
from routers import batch as batch_routes, workflows
from services.batch_service import BatchService
from services.scheduler import SchedulerService
from services.workflow_engine import WorkflowEngine, _minimal_pdf
from services.workflow_storage import WorkflowStorageService


def node(id, kind, config=None):
    return dict(id=id, type=kind, label=id, position={"x": 0, "y": 0}, config=config or {})


def edge(source, target):
    return dict(id=f"{source}-{target}", source=source, target=target)


@pytest.fixture
async def env(tmp_path, monkeypatch):
    storage, batch = WorkflowStorageService(tmp_path), BatchService(tmp_path)
    engine = WorkflowEngine(storage)
    scheduler = SchedulerService(storage, batch, engine)
    app = FastAPI()
    app.include_router(workflows.router)
    app.include_router(batch_routes.router)
    app.dependency_overrides[workflows.get_workflow_storage] = lambda: storage
    app.dependency_overrides[workflows.get_workflow_engine] = lambda: engine
    app.dependency_overrides[batch_routes.get_batch_service] = lambda: batch
    monkeypatch.setattr(workflows, "scheduler_service", scheduler)
    monkeypatch.setattr("services.scheduler.scheduler_service", scheduler)
    calls = []

    def respond(request):
        payload = json.loads(request.content)
        calls.append(payload)
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": payload["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": f"answer-{len(calls)}"},
                    }
                ],
            },
        )

    monkeypatch.setenv("RAG_ENDPOINT_URL", "https://llm.test/v1")
    monkeypatch.setenv("RAG_API_KEY", "test-only-key")
    monkeypatch.setenv("RAG_MODEL", "test-model")
    monkeypatch.setattr(
        "services.workflow_engine.AsyncOpenAI",
        lambda **kw: AsyncOpenAI(
            **kw, http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond))
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        yield SimpleNamespace(
            client=client,
            storage=storage,
            batch=batch,
            engine=engine,
            scheduler=scheduler,
            calls=calls,
            path=tmp_path,
        )
    scheduler.shutdown()


async def create(env, nodes=None, edges=None):
    response = await env.client.post(
        "/api/workflows",
        json={
            "name": "Test workflow",
            "nodes": nodes or [node("in", "input"), node("out", "output")],
            "edges": edges if edges is not None else [edge("in", "out")],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_crud_chaining_fan_in_and_persistence(env):
    id = await create(
        env,
        [
            node("in", "input"),
            node("a", "agent", {"prompt": "First task"}),
            node("b", "agent"),
            node("out", "output"),
        ],
        [edge("in", "a"), edge("in", "b"), edge("a", "b"), edge("b", "out")],
    )
    data = (
        await env.client.post(
            f"/api/workflows/{id}/execute", json={"input_data": {"message": "initial input"}}
        )
    ).json()
    assert data["status"] == "completed", data
    assert data["output_data"]["out"]["data"] == "answer-2"
    assert env.calls[0]["messages"][0]["content"] == "First task"
    assert "initial input" in env.calls[1]["messages"][1]["content"]
    assert "answer-1" in env.calls[1]["messages"][1]["content"]
    assert env.calls[0]["model"] == "test-model"
    assert WorkflowStorageService(env.path).get_execution(data["id"]).status == "completed"
    assert (await env.client.get(f"/api/workflows/{id}/executions")).json()[0]["id"] == data["id"]
    assert (await env.client.put(f"/api/workflows/{id}", json={"name": "Renamed"})).json()[
        "name"
    ] == "Renamed"
    assert (await env.client.delete(f"/api/workflows/{id}")).status_code == 204
    assert (await env.client.get(f"/api/workflows/{id}")).status_code == 404


@pytest.mark.parametrize(
    "nodes,edges",
    [
        ([node("a", "agent")], [edge("a", "a")]),
        ([node("a", "agent"), node("b", "agent")], [edge("a", "b"), edge("b", "a")]),
        ([node("a", "agent")], [edge("a", "missing")]),
        ([node("a", "agent"), node("a", "agent")], []),
        ([node("a", "output"), node("b", "agent")], [edge("a", "b")]),
        ([node("a", "input"), node("b", "output")], [edge("a", "b"), edge("a", "b")]),
    ],
)
async def test_invalid_graph_rejected(env, nodes, edges):
    response = await env.client.post(
        "/api/workflows", json={"name": "Bad", "nodes": nodes, "edges": edges}
    )
    assert response.status_code == 400


async def test_empty_and_storage_failures_are_failed_runs(env):
    assert (await env.engine.execute(env.storage.create_workflow("Empty"), {})).status == "failed"
    id = await create(
        env, [node("in", "input"), node("out", "output", {"output_type": "object_store"})]
    )
    run = (await env.client.post(f"/api/workflows/{id}/execute", json={})).json()
    assert run["status"] == "failed" and run["node_results"]["out"]["status"] == "failed"
    assert "Missing bucket_name" in run["error_message"]


async def test_object_source_and_sink_use_connector(env, monkeypatch):
    c = env.batch.create_connector(
        "Test bucket", "namespace", "bucket", "compartment", "eu-frankfurt-1"
    )
    path = env.path / "test.txt"
    path.write_text("Retrieved storage evidence")
    monkeypatch.setattr(
        "services.oci_object_storage.OCIObjectStorageService.list_objects",
        AsyncMock(return_value=[{"name": "test.txt", "size": 26}]),
    )
    monkeypatch.setattr(
        "services.oci_object_storage.OCIObjectStorageService.download_object",
        AsyncMock(return_value=path),
    )
    upload = AsyncMock(return_value={"status": "uploaded"})
    monkeypatch.setattr("services.oci_object_storage.OCIObjectStorageService.upload_object", upload)
    id = await create(
        env,
        [
            node("source", "data_source", {"source_type": "object_storage", "connector_id": c.id}),
            node("a", "agent"),
            node(
                "out",
                "output",
                {
                    "output_type": "object_store",
                    "object_store": {
                        "connector_id": c.id,
                        "object_path": "runs/{{execution_id}}.json",
                    },
                },
            ),
        ],
        [edge("source", "a"), edge("a", "out")],
    )
    result = (await env.client.post(f"/api/workflows/{id}/execute", json={})).json()
    assert result["status"] == "completed", result
    assert "Retrieved storage evidence" in env.calls[0]["messages"][0]["content"]
    assert upload.call_args.kwargs["bucket_name"] == "bucket"
    assert result["id"] in upload.call_args.kwargs["object_name"]
    assert not path.exists()
    upload.side_effect = RuntimeError("Access denied")
    workflow = env.storage.get_workflow(id)
    workflow.nodes = [n for n in workflow.nodes if n.type != "data_source"]
    workflow.edges = [e for e in workflow.edges if e.source != "source"]
    assert (await env.engine.execute(workflow, {})).status == "failed"


async def test_project_filter_required_and_preserved(env, monkeypatch):
    n = WorkflowNode.model_validate(
        node("in", "input", {"input_type": "project", "project": {"project_id": "p"}})
    )
    with pytest.raises(Exception, match="indexed documents"):
        await env.engine._execute_project_input(n, {"message": "query"})
    n.config["document_ids"] = ["doc-1"]
    store = SimpleNamespace(
        initialize=AsyncMock(), close=AsyncMock(), search=AsyncMock(return_value=[])
    )
    embedding = SimpleNamespace(generate_embedding=AsyncMock(return_value=[0.1]), close=AsyncMock())
    monkeypatch.setattr("services.oracle_vector_store.OracleVectorStore", lambda: store)
    monkeypatch.setattr("services.embedding_service.EmbeddingService", lambda: embedding)
    await env.engine._execute_project_input(n, {"message": "query"})
    assert store.search.call_args.kwargs["document_ids"] == ["doc-1"]


@pytest.mark.parametrize(
    "payload",
    [
        {"schedule_type": "recurring"},
        {"schedule_type": "recurring", "cron_expression": "61 * * * *"},
        {"schedule_type": "one_time"},
        {"schedule_type": "one_time", "run_at": "2020-01-01T00:00:00Z"},
    ],
)
async def test_invalid_schedules_rejected(env, payload):
    id = await create(env)
    assert (await env.client.post(f"/api/workflows/{id}/schedule", json=payload)).status_code == 422


async def test_schedule_restore_toggle_execute_history_delete(env):
    id = await create(env)
    schedule = (
        await env.client.post(
            f"/api/workflows/{id}/schedule",
            json={
                "schedule_type": "recurring",
                "cron_expression": "0 9 * * 1",
                "input_data": {"message": "scheduled"},
            },
        )
    ).json()
    assert schedule["next_run_at"]
    assert datetime.fromisoformat(schedule["next_run_at"]).weekday() == 0
    restored = SchedulerService(WorkflowStorageService(env.path), env.batch, env.engine)
    restored.start()
    assert restored._scheduler.get_job(f"workflow_schedule_{schedule['id']}")
    restored.shutdown()
    await env.scheduler._execute_workflow_schedule(schedule["id"], id)
    runs = (await env.client.get(f"/api/workflows/{id}/scheduled-runs")).json()
    assert len(runs) == 1 and runs[0]["triggered_by"] == schedule["id"]
    await env.client.patch(f"/api/workflows/{id}/schedule/toggle", json={"is_active": False})
    assert env.scheduler._scheduler.get_job(f"workflow_schedule_{schedule['id']}") is None
    await env.scheduler._execute_workflow_schedule(schedule["id"], id)
    assert len(env.storage.list_executions(id)) == 1
    assert (await env.client.delete(f"/api/workflows/{id}/schedule")).status_code == 204
    assert not env.storage.list_schedules()


async def test_one_time_deactivates_and_chat_sink_preserves_output(env):
    id = await create(env, [node("a", "agent"), node("chat", "chat")], [edge("a", "chat")])
    response = await env.client.post(
        f"/api/workflows/{id}/schedule",
        json={
            "schedule_type": "one_time",
            "run_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
    )
    schedule = response.json()
    assert env.scheduler._scheduler.get_job(f"workflow_schedule_{schedule['id']}")
    await env.scheduler._execute_workflow_schedule(schedule["id"], id)
    assert not env.storage.get_schedule(schedule["id"]).is_active
    assert env.storage.list_executions(id)[0].output_data["chat"]["data"] == "answer-1"


@pytest.mark.parametrize(
    "text,indexed,expected",
    [("Readable content", 2, "completed"), ("", 2, "failed"), ("Readable", 0, "failed")],
)
async def test_batch_stages_analysis_and_failures(env, monkeypatch, text, indexed, expected):
    c = env.batch.create_connector("Bucket", "ns", "bucket", "compartment", "region")
    env.batch._oci_service.list_objects = AsyncMock(
        return_value=[{"name": "document.pdf", "size": 100}]
    )
    path = env.path / "document.pdf"
    path.write_bytes(_minimal_pdf(text))
    env.batch._oci_service.download_object = AsyncMock(return_value=path)
    rag = SimpleNamespace(
        _get_vector_store=AsyncMock(),
        index_document=AsyncMock(return_value=indexed),
        close=AsyncMock(),
    )
    monkeypatch.setattr("services.rag_service.RAGService", lambda: rag)
    job = env.batch.create_job(c.id)
    result = await env.batch.execute_job(job.id, parallelism=2)
    assert result.status == expected
    file = env.batch.get_job_files(job.id)[0]
    if expected == "completed":
        assert file.chunks_indexed == 2 and file.vectorization_status == "completed"
        assert file.analysis_result["summary"] == "answer-1" and file.analysis_status == "completed"
    else:
        assert file.error_message and result.files_failed == 1
    assert not path.exists()
    rag.close.assert_awaited_once()


async def test_partial_trigger_toggle_and_durable_worker(env, monkeypatch):
    c = env.batch.create_connector("Bucket", "ns", "bucket", "compartment", "region")
    trigger = (
        await env.client.post(
            "/api/batch/triggers",
            json={"name": "Daily", "connector_id": c.id, "schedule": "0 2 * * *"},
        )
    ).json()
    response = await env.client.put(
        f"/api/batch/triggers/{trigger['id']}", json={"is_active": False}
    )
    assert response.status_code == 200 and not response.json()["is_active"]
    assert response.json()["connector_id"] == c.id
    result = (await env.client.post(f"/api/batch/triggers/{trigger['id']}/run")).json()
    assert BatchService(env.path).get_job(result["id"]).status == "pending"
    from batch_worker import process_pending

    execute = AsyncMock()
    monkeypatch.setattr(env.batch, "execute_job", execute)
    await process_pending(env.batch)
    execute.assert_awaited_once_with(result["id"], parallelism=1)
    env.batch.update_job(result["id"], status="running")
    await process_pending(env.batch)
    assert env.batch.get_job(result["id"]).status == "failed"


async def test_normal_waits_and_batch_only_enqueues(env, monkeypatch):
    c = env.batch.create_connector("Modes", "ns", "bucket", "compartment", "region")

    async def execute(id, parallelism=1):
        return env.batch.update_job(id, status="completed")

    mocked = AsyncMock(side_effect=execute)
    monkeypatch.setattr(env.batch, "execute_job", mocked)
    normal = await env.client.post(
        f"/api/batch/connectors/{c.id}/run", json={"processing_mode": "normal"}
    )
    assert normal.json()["status"] == "completed"
    queued = await env.client.post(
        f"/api/batch/connectors/{c.id}/run", json={"processing_mode": "batch"}
    )
    assert queued.json()["status"] == "pending" and mocked.await_count == 1


async def test_oci_pagination():
    from services.oci_object_storage import OCIObjectStorageService

    service = OCIObjectStorageService()
    client = MagicMock()
    obj = SimpleNamespace(name="file.pdf", size=1, time_created=None, md5="abc")
    client.list_objects.side_effect = [
        SimpleNamespace(data=SimpleNamespace(objects=[obj], next_start_with="page2")),
        SimpleNamespace(data=SimpleNamespace(objects=[obj], next_start_with=None)),
    ]
    service._client = client
    result = await service.list_objects(namespace="ns", bucket_name="bucket", region="region")
    assert len(result) == 2 and client.list_objects.call_args.kwargs["start"] == "page2"


async def test_scheduler_actually_fires_once(env):
    import asyncio

    id = await create(env)
    env.scheduler.start()
    response = await env.client.post(
        f"/api/workflows/{id}/schedule",
        json={
            "schedule_type": "one_time",
            "run_at": (datetime.now(timezone.utc) + timedelta(milliseconds=100)).isoformat(),
            "input_data": {"message": "timer fired"},
        },
    )
    assert response.status_code == 201
    for _ in range(50):
        if env.storage.list_executions(id):
            break
        await asyncio.sleep(0.02)
    executions = env.storage.list_executions(id)
    assert len(executions) == 1 and executions[0].output_data["out"]["data"] == "timer fired"
    assert not env.storage.get_workflow(id).schedule.is_active


async def test_attached_file_input_and_unreadable_rejection(env):
    result = await env.client.post(
        "/api/workflows/input-file", files={"file": ("test.txt", b"File evidence", "text/plain")}
    )
    assert result.status_code == 200
    file = result.json()
    id = await create(
        env,
        [
            node(
                "in",
                "input",
                {"input_type": "file", "file_name": file["filename"], "file_content": file["text"]},
            ),
            node("out", "output"),
        ],
    )
    run = (await env.client.post(f"/api/workflows/{id}/execute", json={})).json()
    assert run["output_data"]["out"]["data"][0]["content"] == "File evidence"
    empty = await env.client.post(
        "/api/workflows/input-file",
        files={"file": ("empty.pdf", _minimal_pdf(""), "application/pdf")},
    )
    assert empty.status_code == 400 and "OCR" in empty.json()["detail"]


def test_pdf_keeps_content_beyond_first_page():
    import io
    import pdfplumber

    with pdfplumber.open(
        io.BytesIO(_minimal_pdf("\n".join(f"Line {i}" for i in range(120))))
    ) as pdf:
        assert len(pdf.pages) == 3
        assert "Line 119" in pdf.pages[-1].extract_text()


def test_legacy_timestamps_remain_sortable():
    from models.workflow import Workflow

    old = Workflow(id="old", name="old", created_at="2026-01-01T00:00:00")
    new = Workflow(id="new", name="new")
    assert old.created_at < new.created_at


async def test_document_filter_uses_bound_parameters(monkeypatch):
    from contextlib import asynccontextmanager
    from services.oracle_vector_store import OracleVectorStore

    cursor = AsyncMock()
    cursor.fetchall.return_value = []
    connection = MagicMock()
    connection.cursor.return_value = cursor
    cursor.__aenter__.return_value = cursor

    @asynccontextmanager
    async def get_connection():
        yield connection

    store = OracleVectorStore()
    store._initialized = True
    monkeypatch.setattr(store, "_get_connection", get_connection)
    identifier = "doc'with-quote"
    await store.search([0.1], document_ids=[identifier])
    sql, params = cursor.execute.call_args.args
    assert identifier not in sql
    assert ":document_0" in sql and params["document_0"] == identifier


async def test_batch_vectorization_runs_with_bounded_parallelism(env, monkeypatch):
    import asyncio

    c = env.batch.create_connector("Parallel", "ns", "bucket", "compartment", "region")
    objects = [{"name": f"{i}.pdf", "size": 100} for i in range(3)]
    for obj in objects:
        (env.path / obj["name"]).write_bytes(_minimal_pdf("Parallel test document"))
    env.batch._oci_service.list_objects = AsyncMock(return_value=objects)

    async def download(**kwargs):
        return env.path / kwargs["object_name"]

    env.batch._oci_service.download_object = download
    active = peak = 0

    async def index(**kwargs):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.05)
        active -= 1
        return 1

    rag = SimpleNamespace(_get_vector_store=AsyncMock(), index_document=index, close=AsyncMock())
    monkeypatch.setattr("services.rag_service.RAGService", lambda: rag)
    job = env.batch.create_job(c.id, parallelism=2)
    result = await env.batch.execute_job(job.id, parallelism=2)
    assert peak == 2
    assert result.files_processed == 3 and result.status == "completed"
