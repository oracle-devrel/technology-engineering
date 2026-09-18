"""Research report generation — query documents and produce structured reports."""

import logging
import re
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.storage import StorageService, DocumentNotFoundError
from services.rag_service import RAGService
from routers.documents import get_storage_service, get_rag_service, StorageDep, RAGDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])


# ── Schemas ──────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    """Request schema for generating a research report."""
    query: str = Field(..., min_length=1, max_length=5000)
    document_ids: list[str] = Field(..., min_length=1)
    report_type: str = Field(default="summary")  # summary, compliance, comparison, timeline


class ResearchSource(BaseModel):
    page: Optional[int] = None
    relevance: float = 0.0
    snippet: str = ""
    document_id: str = ""
    document_name: str = ""


class TimelineEvent(BaseModel):
    date: str = ""
    type: str = "event"
    description: str = ""
    page: str = ""


class ResearchResponse(BaseModel):
    report: str
    query: str
    report_type: str
    sources: list[ResearchSource] = []
    timeline: list[TimelineEvent] = []
    chunks_searched: int = 0
    chunks_used: int = 0


# ── Helpers ──────────────────────────────────────────────────────────────

def _score_chunk(text: str, query: str) -> float:
    """Score a chunk by keyword overlap with the query."""
    terms = set(re.findall(r'\w{3,}', query.lower()))
    if not terms:
        return 0
    return sum(1 for t in terms if t in text.lower()) / len(terms)


# ── Report instructions by type ─────────────────────────────────────────

REPORT_INSTRUCTIONS = {
    "summary": (
        "Generate a comprehensive summary report. Include:\n"
        "1. Executive Summary (3-5 sentences)\n"
        "2. Key Findings (bulleted list with page references)\n"
        "3. Important Details (structured by topic)\n"
        "4. Recommendations or Action Items\n"
        "5. References (list of cited pages/sections)"
    ),
    "compliance": (
        "Generate a compliance assessment report. Include:\n"
        "1. Compliance Summary (pass/fail/review status)\n"
        "2. Required Elements Check (what's present, what's missing)\n"
        "3. Standards Referenced (list all, flag any outdated)\n"
        "4. Signatures & Approvals Status\n"
        "5. Risk Findings\n"
        "6. Recommendations"
    ),
    "comparison": (
        "Generate a comparison report across the selected documents. Include:\n"
        "1. Overview of each document\n"
        "2. Common elements\n"
        "3. Differences and discrepancies\n"
        "4. Conflicting information\n"
        "5. Recommendations"
    ),
    "timeline": (
        "Extract a chronological timeline from the documents. Include:\n"
        "1. All dates mentioned with their context\n"
        "2. Project phases in order\n"
        "3. Milestones and deadlines\n"
        "4. Event type (milestone, decision, deadline, deliverable)\n"
        "Format each event as: DATE | EVENT TYPE | DESCRIPTION | PAGE REF"
    ),
}


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/report", response_model=ResearchResponse)
async def generate_report(req: ResearchRequest, storage: StorageDep, rag: RAGDep):
    """Generate a structured research report from selected documents."""
    start = time.time()

    # Collect document texts
    doc_texts: list[dict] = []
    for doc_id in req.document_ids:
        try:
            document = await storage.get_document(doc_id)
            text = storage.extract_text_from_pdf(doc_id)
            if text.strip():
                doc_texts.append({
                    "id": doc_id,
                    "filename": document.metadata.filename,
                    "text": text,
                })
        except DocumentNotFoundError:
            logger.warning(f"Document not found for research: {doc_id}")
            continue
        except Exception as e:
            logger.warning(f"Failed to read document {doc_id}: {e}")
            continue

    if not doc_texts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid documents found for the provided IDs",
        )

    # Split each document into page-level chunks for scoring
    all_chunks = []
    for doc in doc_texts:
        pages = re.split(r'---\s*page\s*(\d+)\s*---', doc["text"], flags=re.IGNORECASE)
        # pages alternates: [pre-text, page_num, page_text, page_num, page_text, ...]
        if len(pages) <= 1:
            # No page markers — treat whole text as one chunk
            all_chunks.append({
                "content": doc["text"][:3000],
                "page_number": 1,
                "document_id": doc["id"],
                "doc_name": doc["filename"],
            })
        else:
            for i in range(1, len(pages) - 1, 2):
                page_num = int(pages[i])
                page_text = pages[i + 1].strip()
                if page_text:
                    all_chunks.append({
                        "content": page_text,
                        "page_number": page_num,
                        "document_id": doc["id"],
                        "doc_name": doc["filename"],
                    })

    # Score chunks
    for c in all_chunks:
        c["score"] = _score_chunk(c["content"], req.query)

    # Select top chunks
    if req.report_type == "comparison" and len(req.document_ids) > 1:
        top = []
        per_doc = max(5, 25 // len(req.document_ids))
        for doc_id in req.document_ids:
            doc_chunks = sorted(
                [c for c in all_chunks if c["document_id"] == doc_id],
                key=lambda x: -x["score"],
            )
            top.extend(doc_chunks[:per_doc])
    else:
        ranked = sorted(all_chunks, key=lambda c: -c["score"])
        top = [c for c in ranked if c["score"] > 0][:25]
        if len(top) < 5:
            top = ranked[:15]

    # Build context
    context = "\n\n---\n\n".join(
        f"[{c['doc_name']} — Page {c['page_number']}] {c['content']}"
        for c in top
    )

    # Build LLM prompt
    instruction = REPORT_INSTRUCTIONS.get(req.report_type, REPORT_INSTRUCTIONS["summary"])

    system_prompt = (
        "You are an expert document analyst. Generate detailed, structured reports "
        "based on the provided document excerpts. Always cite specific pages."
    )

    user_prompt = (
        f"DOCUMENT CONTENT:\n{context}\n\n"
        f"---\n\n"
        f"RESEARCH QUERY: {req.query}\n\n"
        f"REPORT TYPE: {req.report_type}\n\n"
        f"INSTRUCTIONS:\n{instruction}\n\n"
        f"Use ONLY information from the documents above. "
        f"Quote exact text and include [Page N] references. "
        f"Format the report using markdown headings and bullet points."
    )

    # Call LLM via RAG service's OpenAI client
    try:
        response = rag._client.chat.completions.create(
            model=rag.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        report_content = response.choices[0].message.content if response.choices else ""
    except Exception as e:
        logger.error(f"LLM call failed for research report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )

    # Build sources
    sources = []
    seen_keys = set()
    for c in top:
        pg = c.get("page_number")
        doc_id = c.get("document_id", "")
        key = f"{doc_id}:{pg}"
        if key not in seen_keys:
            seen_keys.add(key)
            snippet = re.sub(r'^\d+\s+---\s*', '', c["content"]).strip()[:150]
            sources.append(ResearchSource(
                page=pg,
                relevance=round(c["score"], 2),
                snippet=snippet,
                document_id=doc_id,
                document_name=c.get("doc_name", "Unknown"),
            ))

    # Parse timeline events if report type is timeline
    timeline = []
    if req.report_type == "timeline" and report_content:
        for line in report_content.split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                timeline.append(TimelineEvent(
                    date=parts[0],
                    type=parts[1] if len(parts) > 1 else "event",
                    description=parts[2] if len(parts) > 2 else "",
                    page=parts[3] if len(parts) > 3 else "",
                ))

    return ResearchResponse(
        report=report_content,
        query=req.query,
        report_type=req.report_type,
        sources=sorted(sources, key=lambda s: (s.document_name, s.page or 0))[:20],
        timeline=timeline,
        chunks_searched=len(all_chunks),
        chunks_used=len(top),
    )


@router.get("/templates")
async def get_report_templates():
    """Get available report templates."""
    return {
        "templates": [
            {"id": "summary", "name": "Summary Report", "description": "Comprehensive document summary with key findings"},
            {"id": "compliance", "name": "Compliance Assessment", "description": "Check document completeness and standards compliance"},
            {"id": "comparison", "name": "Document Comparison", "description": "Compare information across multiple documents"},
            {"id": "timeline", "name": "Timeline Extraction", "description": "Extract chronological events and milestones"},
        ]
    }
