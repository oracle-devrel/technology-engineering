# Developed by: Brona Nilsson
"""
Standalone MCP Server for DOCX Report Generation

Exposes a REST endpoint at /api/generate_report that:
  1. Plans sections (LLM call)
  2. Writes all sections in parallel (LLM calls)
  3. Assembles DOCX (python-docx + matplotlib charts)
  4. Uploads to Object Storage and returns URL

Registered as an API endpoint tool on OCI Agent Hub via OpenAPI spec.
"""

import os
import re
import json
import uuid
import time
import threading
import logging
from datetime import datetime

import oci
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

import oci_auth
import docx_report

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("OCI Document Report Server")

# ---------------------------------------------------------------------------
# Session store for multi-tool report orchestration
# ---------------------------------------------------------------------------
_sessions = {}
_sessions_lock = threading.Lock()
_SESSION_TTL = 30 * 60  # 30 minutes


def _cleanup_stale():
    """Remove sessions older than _SESSION_TTL. Call with lock held."""
    now = time.time()
    expired = [k for k, v in _sessions.items() if now - v["created_at"] > _SESSION_TTL]
    for k in expired:
        del _sessions[k]


def _create_session(title, query, sections_plan):
    """Create a new report session and return the report_id."""
    report_id = uuid.uuid4().hex[:12]
    with _sessions_lock:
        _cleanup_stale()
        _sessions[report_id] = {
            "title": title,
            "query": query,
            "sections_plan": sections_plan,
            "sections_written": [],
            "created_at": time.time(),
        }
    return report_id


def _get_session(report_id):
    """Return session dict or None if not found / expired."""
    with _sessions_lock:
        session = _sessions.get(report_id)
        if session and time.time() - session["created_at"] > _SESSION_TTL:
            del _sessions[report_id]
            return None
        return session


def _delete_session(report_id):
    """Remove a session after assembly."""
    with _sessions_lock:
        _sessions.pop(report_id, None)


def _upload_to_object_storage(docx_path, title):
    """Upload a DOCX file to Object Storage and return (url, object_name)."""
    namespace = os.getenv("OBJECT_STORAGE_NAMESPACE")
    bucket = os.getenv("REPORTS_BUCKET", "reports-bucket")
    region = os.getenv("OCI_REGION", os.getenv("TF_VAR_region"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r"[^\w\s-]", "", title)[:50].strip().replace(" ", "_")
    object_name = f"reports/{timestamp}_{safe_title}.docx"

    os_client = oci.object_storage.ObjectStorageClient(
        config=oci_auth.config, signer=oci_auth.signer
    )
    with open(docx_path, "rb") as f:
        os_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=object_name,
            put_object_body=f.read(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    os.remove(docx_path)

    url = (
        f"https://objectstorage.{region}.oraclecloud.com"
        f"/n/{namespace}/b/{bucket}/o/{object_name}"
    )
    return url, object_name


# ---------------------------------------------------------------------------
# Tool: plan_report  (orchestrated path — step 1)
# ---------------------------------------------------------------------------
@mcp.tool()
def plan_report(title: str, query: str, context: str = "") -> dict:
    """Plan the structure of a DOCX report.

    Returns a report_id and a list of section topics. The caller should then:
    1. For each section, search the knowledge base for relevant context
    2. Call write_section(report_id, topic, context) with the results
    3. Call assemble_report(report_id) to produce the final DOCX

    Args:
        title: The report title (e.g. "Acme Corp Q3 2025 Fiscal Analysis")
        query: What the report should analyze or compare
        context: Optional additional context to help plan sections
    """
    logging.info("<plan_report> title='%s' query='%s'", title, query)

    sections = docx_report.plan_sections(query, context)
    report_id = _create_session(title, query, sections)

    return {
        "report_id": report_id,
        "title": title,
        "sections": sections,
        "next_step": (
            "For each section, search the knowledge base for that topic, "
            "then call write_section with the report_id, topic, and search results as context."
        ),
    }


# ---------------------------------------------------------------------------
# Tool: write_section  (orchestrated path — step 2, called per section)
# ---------------------------------------------------------------------------
@mcp.tool()
def write_section(report_id: str, topic: str, context: str = "") -> dict:
    """Write one section of a planned report using provided context.

    Call this after plan_report, once per section. The context should contain
    the knowledge base search results relevant to this section topic.

    Args:
        report_id: The report_id returned by plan_report
        topic: The section topic (from the plan_report sections list)
        context: The knowledge base search results for this section
    """
    logging.info("<write_section> report_id='%s' topic='%s'", report_id, topic)

    session = _get_session(report_id)
    if not session:
        return {"error": f"Session '{report_id}' not found or expired. Call plan_report first."}

    section = docx_report.write_section_with_context(topic, session["query"], context)

    with _sessions_lock:
        s = _sessions.get(report_id)
        if s:
            s["sections_written"].append(section)

    return {
        "heading": section.get("heading", topic),
        "text_preview": section.get("text", "")[:200],
        "has_table": bool(section.get("table")),
        "has_chart": bool(section.get("chart_data")),
        "sections_completed": len(session["sections_written"]),
        "sections_planned": len(session["sections_plan"]),
    }


# ---------------------------------------------------------------------------
# Tool: assemble_report  (orchestrated path — step 3)
# ---------------------------------------------------------------------------
@mcp.tool()
def assemble_report(report_id: str) -> dict:
    """Assemble all written sections into a final DOCX report and upload it.

    Call this after all write_section calls are complete. Generates executive
    summary and conclusion, renders charts, and uploads to Object Storage.

    Args:
        report_id: The report_id returned by plan_report
    """
    logging.info("<assemble_report> report_id='%s'", report_id)

    session = _get_session(report_id)
    if not session:
        return {"error": f"Session '{report_id}' not found or expired. Call plan_report first."}

    if not session["sections_written"]:
        return {"error": "No sections written yet. Call write_section for each section first."}

    title = session["title"]
    query = session["query"]
    sections = session["sections_written"]

    docx_path = docx_report.assemble_docx(title, query, sections)
    url, object_name = _upload_to_object_storage(docx_path, title)

    _delete_session(report_id)

    logging.info("<assemble_report> uploaded to %s", url)
    return {
        "status": "uploaded",
        "format": "docx",
        "title": title,
        "url": url,
        "object_name": object_name,
        "sections_count": len(sections),
        "generated_at": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Tool: generate_docx_report  (monolithic — backward compat)
# ---------------------------------------------------------------------------
@mcp.tool()
def generate_docx_report(title: str, query: str, context: str = "") -> dict:
    """Generate a professional DOCX report and upload to Object Storage.

    Args:
        title: Report title
        query: What the report should analyze
        context: Optional pre-gathered context (KB is also searched per-section)

    Returns:
        dict with status, url, object_name, and metadata
    """
    docx_path = docx_report.build_docx_report(title, query, context)
    url, object_name = _upload_to_object_storage(docx_path, title)

    return {
        "status": "uploaded",
        "format": "docx",
        "title": title,
        "url": url,
        "object_name": object_name,
        "generated_at": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Async job store for REST API
# ---------------------------------------------------------------------------
_jobs = {}
_jobs_lock = threading.Lock()
_JOBS_TTL = 30 * 60  # 30 minutes


def _cleanup_jobs():
    now = time.time()
    expired = [k for k, v in _jobs.items() if now - v["created_at"] > _JOBS_TTL]
    for k in expired:
        del _jobs[k]


def _run_report_job(job_id, title, query, context):
    """Run report generation in a background thread."""
    try:
        docx_path = docx_report.build_docx_report(title, query, context)
        url, object_name = _upload_to_object_storage(docx_path, title)
        with _jobs_lock:
            _jobs[job_id].update({
                "status": "completed",
                "url": url,
                "object_name": object_name,
                "generated_at": datetime.now().isoformat(),
            })
        logging.info("<job %s> completed: %s", job_id, url)
    except Exception as e:
        logging.error("<job %s> failed: %s", job_id, e)
        with _jobs_lock:
            _jobs[job_id].update({"status": "failed", "error": str(e)})


# ---------------------------------------------------------------------------
# REST API endpoints (for OCI Agent API endpoint calling tool)
# ---------------------------------------------------------------------------

@mcp.custom_route("/api/generate_report", methods=["POST"])
async def rest_generate_report(request: Request):
    """Generate a DOCX report synchronously and return the download URL."""
    body = await request.json()
    title = body.get("title", "Untitled Report")
    query = body.get("query", "")
    context = body.get("context", "")

    if not query:
        return JSONResponse({"error": "query is required"}, status_code=400)

    logging.info("<rest_generate_report> title='%s' query='%s'", title, query)

    try:
        docx_path = docx_report.build_docx_report(title, query, context)
        url, object_name = _upload_to_object_storage(docx_path, title)
        logging.info("<rest_generate_report> uploaded to %s", url)
        return JSONResponse({
            "status": "completed",
            "title": title,
            "url": url,
            "object_name": object_name,
            "generated_at": datetime.now().isoformat(),
        })
    except Exception as e:
        logging.error("<rest_generate_report> failed: %s", e)
        return JSONResponse({"status": "failed", "error": str(e)}, status_code=500)


@mcp.custom_route("/api/report_status", methods=["GET"])
async def rest_report_status(request: Request):
    """Check the status of a report generation job."""
    job_id = request.query_params.get("job_id", "")
    if not job_id:
        return JSONResponse({"error": "job_id query parameter is required"}, status_code=400)

    with _jobs_lock:
        job = _jobs.get(job_id)

    if not job:
        return JSONResponse({"error": f"Job '{job_id}' not found or expired"}, status_code=404)

    result = {"job_id": job_id, "status": job["status"], "title": job["title"]}
    if job["status"] == "completed":
        result["url"] = job["url"]
        result["object_name"] = job["object_name"]
        result["generated_at"] = job["generated_at"]
    elif job["status"] == "failed":
        result["error"] = job.get("error", "Unknown error")

    return JSONResponse(result)


@mcp.custom_route("/api/health", methods=["GET"])
async def rest_health(request: Request):
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
