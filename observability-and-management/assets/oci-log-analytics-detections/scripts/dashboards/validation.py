"""Live OCI Log Analytics query-validation helpers (behavior-preserving extract).

Used by deploy_dashboard's deploy orchestration and by sibling scripts that import
``validate_query_in_oci_isolated`` / ``resolve_validation_namespace``.
"""
import multiprocessing
import os
import re
import signal
import sys
import time
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oci_config import COMPARTMENT_ID, LA_NAMESPACE, get_la_client, get_namespace
from oci_time import build_time_window
from redaction import redact_text
from dashboards.builders import load_query_info, iter_inventory_widgets

import oci


PROGRESS_REDACTIONS = (
    (re.compile(r"\bopc-request-id\s*[:=]\s*[A-Za-z0-9_.:-]+", re.IGNORECASE), "opc-request-id=<redacted>"),
    (re.compile(r"\bocid1\.[A-Za-z0-9_.-]+\b"), "<OCI_OCID>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP_ADDRESS>"),
    (re.compile(r"\bhttps?://[^\s\"']+"), "<URL>"),
    (re.compile(r"\bprofile\s+['\"]?[A-Za-z0-9_.:-]+['\"]?", re.IGNORECASE), "profile <redacted>"),
    (re.compile(r"\bnamespace\s+['\"]?[A-Za-z0-9_.:-]+['\"]?", re.IGNORECASE), "namespace <redacted>"),
)


DEFAULT_QUERY_VALIDATION_LOOKBACK = "24h"


@contextmanager
def query_deadline(seconds):
    """Raise TimeoutError when one live OCI validation query runs too long."""
    if not seconds or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _raise_timeout(_signum, _frame):
        raise TimeoutError(f"query validation exceeded {seconds}s")

    previous_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def validate_query_in_oci(la_client, namespace, query_file, query_string, lookback, timeout=None):
    """Execute a query against OCI Log Analytics to catch parser/runtime errors."""
    time_start, time_end = build_time_window(lookback)
    try:
        with query_deadline(timeout):
            response = la_client.query(
                namespace_name=namespace,
                query_details=oci.log_analytics.models.QueryDetails(
                    compartment_id=COMPARTMENT_ID,
                    compartment_id_in_subtree=True,
                    query_string=query_string,
                    sub_system="LOG",
                    time_filter=oci.log_analytics.models.TimeRange(
                        time_start=time_start,
                        time_end=time_end,
                        time_zone="UTC",
                    ),
                    max_total_count=1,
                ),
            ).data
        rows = len(getattr(response, "items", []) or [])
        return {
            "query_file": query_file,
            "ok": True,
            "rows": rows,
            "empty": rows == 0,
            "error": "",
        }
    except Exception as exc:
        return {
            "query_file": query_file,
            "ok": False,
            "rows": 0,
            "empty": False,
            "error": redact_text(str(exc)),
        }


def _validate_query_worker(queue, namespace, query_file, query_string, lookback, client_timeout):
    """Run one OCI query validation in a child process."""
    la_client = get_la_client(timeout=(10, client_timeout))
    result = validate_query_in_oci(
        la_client=la_client,
        namespace=namespace,
        query_file=query_file,
        query_string=query_string,
        lookback=lookback,
        timeout=None,
    )
    queue.put(result)


def validate_query_in_oci_isolated(namespace, query_file, query_string, lookback, query_timeout):
    """Validate one query in a killable child process."""
    context_name = "fork" if hasattr(os, "fork") else "spawn"
    context = multiprocessing.get_context(context_name)
    queue = context.Queue()
    process = context.Process(
        target=_validate_query_worker,
        args=(queue, namespace, query_file, query_string, lookback, query_timeout),
    )

    process.start()
    process.join(query_timeout + 5)

    if process.is_alive():
        process.terminate()
        process.join(5)
        return {
            "query_file": query_file,
            "ok": False,
            "rows": 0,
            "empty": False,
            "error": f"query validation exceeded {query_timeout}s",
        }

    if process.exitcode != 0 and queue.empty():
        return {
            "query_file": query_file,
            "ok": False,
            "rows": 0,
            "empty": False,
            "error": f"query validation process exited with code {process.exitcode}",
        }

    if queue.empty():
        return {
            "query_file": query_file,
            "ok": False,
            "rows": 0,
            "empty": False,
            "error": "query validation process returned no result",
        }

    return queue.get()


def resolve_validation_namespace(client_timeout):
    """Resolve the Log Analytics namespace for live validation."""
    if LA_NAMESPACE:
        print(f"  Namespace (from env): {LA_NAMESPACE}")
        return LA_NAMESPACE
    la_client = get_la_client(timeout=(10, client_timeout))
    return get_namespace(la_client)


def _redact_progress_text(value):
    redacted = str(value or "")
    for pattern, replacement in PROGRESS_REDACTIONS:
        redacted = pattern.sub(replacement, redacted)
    return " ".join(redacted.split())


def _validation_status(result):
    if not result.get("ok"):
        return "failed"
    if result.get("empty"):
        return "empty"
    return "passed"


def _should_emit_validation_progress(progress, progress_interval, index, total):
    if not progress:
        return False
    interval = int(progress_interval or 1)
    if interval <= 1:
        return True
    return index == 1 or index == total or index % interval == 0


def _format_validation_progress(index, total, result):
    status = _validation_status(result)
    query_file = result.get("query_file", "<unknown>")
    rows = result.get("rows", 0)
    message = f"    [{index:03d}/{total:03d}] {query_file} status={status} rows={rows}"
    if status == "failed" and result.get("error"):
        error = _redact_progress_text(result["error"])
        message = f"{message} error={error[:180]}"
    return message
