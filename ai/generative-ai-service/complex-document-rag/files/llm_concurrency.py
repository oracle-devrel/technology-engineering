"""
Global LLM concurrency limiter.

All outbound LLM calls should be wrapped with this semaphore to prevent
overwhelming the inference endpoint with too many concurrent requests.

Usage:
    from llm_concurrency import llm_semaphore

    with llm_semaphore:
        result = llm.invoke(messages)
"""

import os
import threading

_MAX_CONCURRENT_LLM_CALLS = int(os.environ.get("MAX_LLM_CONCURRENCY", "6"))

llm_semaphore = threading.Semaphore(value=_MAX_CONCURRENT_LLM_CALLS)
