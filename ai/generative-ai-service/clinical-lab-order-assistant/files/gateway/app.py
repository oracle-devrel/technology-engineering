"""LabSense gateway: OCI signing proxy, patient records and order evaluation.

Runs on loopback. The browser never sees OCI credentials; the Next.js app
talks to this service, which signs every request with ~/.oci/config.
"""
import base64
import io
import json
import os
from datetime import date
from pathlib import Path

import anyio
import httpx
import oci
import pymupdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from oci._vendor import requests
from PIL import Image
from pydantic import BaseModel, Field

from gateway import records, rules

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROFILE = os.getenv("OCI_PROFILE", "DEFAULT")
REGION = os.getenv("OCI_REGION", "eu-frankfurt-1")
ENDPOINT_ID = os.environ.get("OCI_ENDPOINT_ID", "")
COMPARTMENT_ID = os.environ.get("OCI_COMPARTMENT_ID", "")
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"
REASONING_EFFORTS = ("none", "low", "medium", "xhigh")

app = FastAPI(title="LabSense OCI Gateway")
m = oci.generative_ai_inference.models
client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=oci.config.from_file(profile_name=PROFILE), service_endpoint=SERVICE_ENDPOINT,
    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10, 600),
)
documents: dict[str, dict] = {}
records.ensure_seeded()


# -- model proxy --------------------------------------------------------------
@app.post("/v1/chat/completions")
async def completions(body: dict):
    if not ENDPOINT_ID or not COMPARTMENT_ID:
        raise HTTPException(500, "Set OCI_ENDPOINT_ID and OCI_COMPARTMENT_ID in .env")
    effort = body.get("reasoning_effort", "low")
    if effort not in REASONING_EFFORTS:
        raise HTTPException(422, "Unsupported reasoning effort.")
    if not isinstance(body.get("messages"), list):
        raise HTTPException(422, "Messages must be a list.")
    # The OpenAI-compatible route is the one that streams reasoning_content and
    # tool deltas for imported models. The native actions/chat stream does not.
    payload = {**body, "model": ENDPOINT_ID, "reasoning_effort": effort,
               "max_tokens": min(body.get("max_tokens") or 8192, 32768), "parallel_tool_calls": False}
    url = SERVICE_ENDPOINT + "/20231130/actions/v1/chat/completions"
    raw = json.dumps(payload).encode("utf-8")
    signed = requests.Request("POST", url, data=raw, headers={"Content-Type": "application/json", "CompartmentId": COMPARTMENT_ID}).prepare()
    client.base_client.signer(signed)
    upstream = httpx.AsyncClient(timeout=httpx.Timeout(600, connect=10))
    try:
        response = await upstream.send(upstream.build_request("POST", url, content=raw, headers=dict(signed.headers)), stream=True)
        if not response.is_success:
            detail = (await response.aread()).decode("utf-8", "replace")[:300]
            await response.aclose()
            raise HTTPException(502, f"OCI returned HTTP {response.status_code}: {detail}")
        if not payload.get("stream"):
            await response.aread()
            result = response.json()
            await response.aclose()
            await upstream.aclose()
            return result
    except BaseException:
        await upstream.aclose()
        raise

    async def stream():
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            with anyio.CancelScope(shield=True):
                await response.aclose()
                await upstream.aclose()
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/health")
def health():
    return {"gateway": "ready", "region": REGION, "endpoint": bool(ENDPOINT_ID), "patients": len(records.list_patients()), "tests": len(rules.load_catalog())}


# -- patients and catalog -----------------------------------------------------
@app.get("/patients")
def patients():
    return records.list_patients()


@app.get("/patients/{mrn}")
def patient(mrn: str):
    record = records.get_patient(mrn)
    if not record:
        raise HTTPException(404, f"No patient with MRN {mrn}.")
    return record


@app.get("/catalog")
def catalog():
    return rules.load_catalog()


class Evaluate(BaseModel):
    mrn: str
    tests: list[str] = Field(min_length=1, max_length=30)
    visit_date: str | None = None


@app.post("/orders/evaluate")
def evaluate(body: Evaluate):
    record = records.get_patient(body.mrn)
    if not record:
        raise HTTPException(404, f"No patient with MRN {body.mrn}.")
    visit_date = date.fromisoformat(body.visit_date) if body.visit_date else None
    return rules.evaluate(record, body.tests, visit_date)


class Place(BaseModel):
    mrn: str
    reason: str = Field(max_length=300)
    approved: list[str] = Field(max_length=30)
    skipped: list[str] = Field(default_factory=list, max_length=30)
    summary: str = Field(max_length=1500)
    visit_date: str | None = None


@app.post("/orders/place")
def place(body: Place):
    record = records.get_patient(body.mrn)
    if not record:
        raise HTTPException(404, f"No patient with MRN {body.mrn}.")
    index = rules.catalog_index()
    approved = [rules.resolve_code(c) or c.upper() for c in body.approved]
    skipped = [rules.resolve_code(c) or c.upper() for c in body.skipped]
    unknown = [c for c in approved + skipped if c not in index]
    if unknown:
        raise HTTPException(422, f"Unknown test code(s): {', '.join(unknown)}")
    cost = sum(index[c]["price_sar"] for c in approved)
    full = cost + sum(index[c]["price_sar"] for c in skipped)
    visit = records.add_visit(body.mrn, {"date": body.visit_date, "reason": body.reason, "summary": body.summary,
                                         "ordered": approved, "skipped": skipped, "full_cost": full, "cost": cost, "saved": full - cost})
    updated = records.get_patient(body.mrn)
    return {"kind": "visit", "mrn": body.mrn, "patient": record["name"], "visit": visit,
            "ordered": [{"code": c, "name": index[c]["name"], "price_sar": index[c]["price_sar"]} for c in approved],
            "skipped": [{"code": c, "name": index[c]["name"], "price_sar": index[c]["price_sar"]} for c in skipped],
            "saved_total_sar": updated["saved_total"], "spent_total_sar": updated["spent_total"], "visit_count": len(updated["visits"])}


class ImportResult(BaseModel):
    code: str
    value: str = Field(max_length=200)
    date: str
    source: str = Field(default="External laboratory", max_length=120)


class ImportResults(BaseModel):
    mrn: str
    results: list[ImportResult] = Field(min_length=1, max_length=30)


@app.post("/results/import")
def import_results(body: ImportResults):
    index = rules.catalog_index()
    resolved = []
    for r in body.results:
        code = rules.resolve_code(r.code) or r.code.upper()
        if code not in index:
            raise HTTPException(422, f"Unknown test code: {r.code}")
        date.fromisoformat(r.date)
        resolved.append({"code": code, "value": r.value, "date": r.date, "source": r.source})
    try:
        outcome = records.add_results(body.mrn, resolved)
    except KeyError:
        raise HTTPException(404, f"No patient with MRN {body.mrn}.") from None
    return {"kind": "import", **outcome, "added": [{**a, "name": index[a["code"]]["name"]} for a in outcome["added"]]}


@app.post("/reset")
def reset():
    documents.clear()
    return {"reset": True, "patients": records.reset()}


# -- external lab reports (vision) --------------------------------------------
def vision_text(image_bytes: bytes, media_type: str = "image/png") -> str:
    prompt = ("This is a laboratory report. Transcribe it faithfully as Markdown: the laboratory name, patient identifiers, "
              "report date, and a table with columns Test, Result, Unit, Reference range. Keep Arabic text as is. "
              "Do not invent values. Output only the transcription.")
    response = client.chat(m.ChatDetails(compartment_id=COMPARTMENT_ID, serving_mode=m.DedicatedServingMode(endpoint_id=ENDPOINT_ID),
        chat_request=m.GenericChatRequest(messages=[m.UserMessage(content=[m.TextContent(text=prompt),
            m.ImageContent(image_url=m.ImageUrl(url=f"data:{media_type};base64," + base64.b64encode(image_bytes).decode()))])],
            max_tokens=4000, temperature=0.1)))
    return "".join(c.text or "" for c in response.data.chat_response.choices[0].message.content or [])


@app.post("/documents")
def upload(file: UploadFile = File(...)):
    raw = file.file.read(12 * 1024 * 1024 + 1)
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 12 MB.")
    name = file.filename or "report"
    suffix = Path(name).suffix.lower()
    pages, method = [], "Text extraction"
    try:
        if suffix == ".pdf":
            pdf = pymupdf.open(stream=raw, filetype="pdf")
            if len(pdf) > 10:
                raise HTTPException(422, "Please upload a report of at most 10 pages.")
            scans = 0
            for i, page in enumerate(pdf):
                text = page.get_text().strip()
                if len(text) < 30:
                    scans += 1
                    text = vision_text(page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).tobytes("png"))
                pages.append({"page": i + 1, "text": text})
            method = "PDF text + model vision" if scans else "PDF text extraction"
        elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
            img = Image.open(io.BytesIO(raw)); img.thumbnail((2000, 2000))
            buffer = io.BytesIO(); img.convert("RGB").save(buffer, format="PNG")
            pages = [{"page": 1, "text": vision_text(buffer.getvalue())}]; method = "Model vision"
        elif suffix in (".txt", ".md", ".csv"):
            pages = [{"page": 1, "text": raw.decode("utf-8-sig")}]
        else:
            raise HTTPException(415, "Supported: PDF, PNG, JPG, WEBP, TXT, CSV.")
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(422, f"Could not read this report: {str(error)[:180]}") from None
    total = sum(len(p["text"]) for p in pages)
    if not total:
        raise HTTPException(422, "No readable content was found in this file.")
    import time, uuid
    doc_id = uuid.uuid4().hex
    for key in list(documents):
        if time.time() - documents[key]["created"] > 7200:
            documents.pop(key)
    documents[doc_id] = {"id": doc_id, "name": name, "pages": pages, "method": method, "characters": total, "created": time.time()}
    return documents[doc_id]


@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    if doc_id not in documents:
        raise HTTPException(404, "Report expired. Please upload it again.")
    return documents[doc_id]
