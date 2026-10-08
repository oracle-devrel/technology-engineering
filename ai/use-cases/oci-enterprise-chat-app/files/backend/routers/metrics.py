"""Platform metrics and benchmarking data for performance dashboards."""

import json
import logging
import time
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)

_start_time = time.time()

# Storage service reference (set by main.py)
_storage_service = None


def set_services(storage=None):
    global _storage_service
    if storage:
        _storage_service = storage


def _load_all_documents():
    """Load all document metadata from the storage service."""
    if not _storage_service:
        return []
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                docs = pool.submit(_sync_list_documents).result()
            return docs
        else:
            return loop.run_until_complete(_storage_service.list_documents())
    except Exception as e:
        logger.warning(f"Failed to load documents: {e}")
        return []


def _sync_list_documents():
    """Synchronously list documents by reading metadata files directly."""
    if not _storage_service:
        return []
    docs = []
    metadata_dir = _storage_service.metadata_dir
    if not metadata_dir.exists():
        return []
    for meta_file in metadata_dir.glob("*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                docs.append(data)
        except Exception:
            continue
    return docs


@router.get("/overview")
async def get_overview():
    """Platform overview metrics derived from file-based storage."""
    docs = _sync_list_documents()

    total_docs = len(docs)
    completed = sum(1 for d in docs if d.get("status") == "completed")
    processing = sum(1 for d in docs if d.get("status") in ("processing", "extracting", "indexing"))
    errors = sum(1 for d in docs if d.get("status") == "error")

    total_pages = sum((d.get("metadata", {}).get("page_count") or 0) for d in docs)
    total_size = sum((d.get("metadata", {}).get("file_size") or 0) for d in docs)
    total_size_mb = round(total_size / 1024 / 1024, 1) if total_size else 0

    # Count extractions (documents with extraction_result)
    total_extractions = sum(1 for d in docs if d.get("extraction_result"))
    total_fields = 0
    total_filled = 0
    total_edits = 0
    for d in docs:
        er = d.get("extraction_result")
        if er and er.get("parameters"):
            params = er["parameters"]
            total_fields += len(params)
            total_filled += sum(1 for p in params if p.get("value"))

    # Estimate chunks from extraction results
    total_chunks = sum(
        len(d.get("extraction_result", {}).get("parameters", []))
        for d in docs if d.get("extraction_result")
    )

    uptime_sec = time.time() - _start_time

    return {
        "documents": {
            "total": total_docs,
            "completed": completed,
            "processing": processing,
            "errors": errors,
            "total_pages": total_pages,
            "total_size_mb": total_size_mb,
        },
        "extraction": {
            "total_extractions": total_extractions,
            "total_chunks": total_chunks,
            "total_edits": total_edits,
            "avg_chunks_per_doc": round(total_chunks / max(completed, 1), 1),
        },
        "chat": {
            "total_sessions": 0,
            "total_messages": 0,
            "avg_messages_per_session": 0,
        },
        "system": {
            "uptime_seconds": round(uptime_sec),
            "uptime_human": f"{int(uptime_sec // 3600)}h {int((uptime_sec % 3600) // 60)}m",
            "llm_model": "meta.llama-4-maverick-17b-128e-instruct-fp8",
            "embedding_model": "cohere.embed-multilingual-v3.0",
        },
    }


@router.get("/compliance-summary")
async def compliance_summary():
    """Aggregated compliance data across all documents."""
    docs = _sync_list_documents()

    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    per_doc = []

    for doc in docs:
        if doc.get("status") != "completed":
            continue
        er = doc.get("extraction_result")
        if not er:
            continue

        assessment = er.get("compliance_assessment") or {}
        # Support assessments written by older versions while preferring the
        # evidence-backed, versioned assessment introduced by the compliance API.
        compliance_data = assessment.get("findings", er.get("compliance", []))
        fields = er.get("parameters", [])

        passes = sum(1 for f in compliance_data if f.get("status") == "pass")
        warnings = sum(1 for f in compliance_data if f.get("status") == "warning")
        reviews = sum(1 for f in compliance_data if f.get("status") == "review")
        filled = sum(1 for f in fields if f.get("value"))

        per_doc.append({
            "filename": (doc.get("metadata", {}).get("filename") or "")[:30],
            "domain": assessment.get("industry", doc.get("domain")),
            "ruleset_version": assessment.get("ruleset_version"),
            "assessment_status": assessment.get("assessment_status"),
            "total_checks": len(compliance_data),
            "passes": passes,
            "warnings": warnings,
            "reviews": reviews,
            "pass_rate": round(passes / max(len(compliance_data), 1) * 100),
            "fields_total": len(fields),
            "fields_filled": filled,
            "fill_rate": round(filled / max(len(fields), 1) * 100),
        })

        for f in compliance_data:
            sev = f.get("severity", "medium")
            status = f.get("status", "review")
            if status != "pass":
                by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "per_document": per_doc,
        "by_severity": by_severity,
    }


@router.get("/domain-usage")
async def domain_usage():
    """Document count per domain."""
    docs = _sync_list_documents()

    domain_counts: dict = {}
    for doc in docs:
        if doc.get("status") != "completed":
            continue
        domain = doc.get("domain") or "general"
        if domain not in domain_counts:
            domain_counts[domain] = {"domain": domain, "doc_count": 0, "total_pages": 0, "total_size": 0}
        domain_counts[domain]["doc_count"] += 1
        domain_counts[domain]["total_pages"] += doc.get("metadata", {}).get("page_count") or 0
        domain_counts[domain]["total_size"] += doc.get("metadata", {}).get("file_size") or 0

    return {"domains": list(domain_counts.values())}


@router.get("/baselines")
async def get_baselines():
    """AI-Q PaaS benchmark baselines from production testing on OKE."""
    return {
        "test_date": "2026-03-19",
        "platform": "OCI AI Accelerator on OKE (us-chicago-1)",

        "llm_models": {
            "llama_4_maverick": {
                "name": "Llama 4 Maverick 17B-128E FP8",
                "status": "primary",
                "summary_latency_ms": 1692,
                "timeline_latency_ms": 1712,
                "extraction_latency_ms": 1025,
                "tokens_per_sec": 105.75,
                "context_window": "512K tokens",
            },
            "gpt_4o": {
                "name": "OCI OpenAI GPT-4o",
                "status": "available",
                "summary_latency_ms": 3004,
                "extraction_latency_ms": 2116,
                "tokens_per_sec": 33.50,
            },
            "llama_3_3_70b": {
                "name": "Llama 3.3 70B Instruct",
                "status": "available",
                "summary_latency_ms": 6462,
                "extraction_latency_ms": 4017,
                "tokens_per_sec": 24.73,
            },
        },

        "rag_latency": {
            "short": {
                "label": "Quick Q&A (300 tokens)",
                "c1": {"e2e_p50_ms": 2310, "e2e_p99_ms": 32942, "rps": 0.12, "tps": 12.5},
                "c5": {"e2e_p50_ms": 2540, "e2e_p99_ms": 9338, "rps": 0.75, "tps": 75.2},
                "c10": {"e2e_p50_ms": 4280, "e2e_p99_ms": 4876, "rps": 2.05, "tps": 206.0},
                "c25": {"e2e_p50_ms": 4440, "e2e_p99_ms": 7971, "rps": 0.15, "tps": 15.1, "error_pct": 10},
                "optimal_concurrency": 10,
            },
            "medium": {
                "label": "Detailed Analysis (800 tokens)",
                "c1": {"e2e_p50_ms": 8073, "e2e_p99_ms": 16505, "rps": 0.12, "tps": 39.7},
                "c5": {"e2e_p50_ms": 8419, "e2e_p99_ms": 18476, "rps": 0.42, "tps": 146.9},
                "c10": {"e2e_p50_ms": 10259, "e2e_p99_ms": 23655, "rps": 0.42, "tps": 151.6},
                "optimal_concurrency": 5,
            },
            "long": {
                "label": "Research Report (1500 tokens)",
                "c1": {"e2e_p50_ms": 16840, "e2e_p99_ms": 37118, "rps": 0.06, "tps": 32.4},
                "c5": {"e2e_p50_ms": 19883, "e2e_p99_ms": 50810, "rps": 0.17, "tps": 93.4},
                "c10": {"e2e_p50_ms": 13268, "e2e_p99_ms": 26848, "rps": 0.37, "tps": 202.7},
                "optimal_concurrency": 10,
            },
        },

        "embeddings": {
            "text_embedding_3_small": {"single_p50_ms": 611, "single_p99_ms": 1100, "batch_8_p50_ms": 817, "status": "recommended"},
            "text_embedding_3_large": {"single_p50_ms": 982, "single_p99_ms": 1202, "batch_8_p50_ms": 1118, "status": "available"},
        },

        "reranking": {
            "embedding_similarity_avg_ms": 764,
            "llm_reranking_avg_ms": 955,
        },

        "document_upload": {
            "small_5kb_avg_ms": 147,
            "medium_20kb_avg_ms": 117,
            "large_100kb_avg_ms": 155,
            "success_rate_pct": 100,
        },

        "concurrency_limits": {
            "optimal_users": 10,
            "max_stable_users": 25,
            "error_threshold_users": 50,
            "error_rate_at_50": 12,
        },

        "success_rates": {
            "rag_short_c10": 98,
            "rag_med_c10": 100,
            "document_upload": 100,
            "embedding": 100,
            "reranking": 100,
        },
    }
