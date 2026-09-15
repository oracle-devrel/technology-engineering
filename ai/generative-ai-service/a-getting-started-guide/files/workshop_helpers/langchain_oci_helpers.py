# Copyright (c) 2026 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/.

from __future__ import annotations

import os
import warnings
from typing import Any

from langchain_oci import ChatOCIGenAI, OCIGenAIEmbeddings


warnings.filterwarnings(
    "ignore",
    message="The 'strict' parameter is no longer needed*",
    category=FutureWarning,
    module="urllib3.poolmanager",
)


def infer_provider(model_id: str | None) -> str | None:
    """Infer the LangChain OCI provider name from a common OCI model ID prefix."""
    if not model_id:
        return None
    if model_id.startswith("google."):
        return "google"
    if model_id.startswith("cohere."):
        return "cohere"
    if model_id.startswith("meta."):
        return "meta"
    if model_id.startswith("xai."):
        return "xai"
    return None


def oci_auth_kwargs() -> dict[str, str]:
    """Build the shared OCI API-key auth settings used by langchain-oci."""
    return {
        "auth_type": "API_KEY",
        "auth_profile": os.getenv("OCI_PROFILE", "DEFAULT"),
        "auth_file_location": os.path.expanduser(
            os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
        ),
    }


def create_langchain_chat_model(**overrides: Any) -> ChatOCIGenAI:
    """Create a ChatOCIGenAI model from the workshop .env settings."""
    model_id = os.environ["CHAT_MODEL_ID"]
    model_kwargs = {
        "temperature": 0.2,
        "top_p": 0.75,
        "max_tokens": int(os.getenv("CHAT_MAX_TOKENS", "1024")),
        "max_completion_tokens": int(os.getenv("CHAT_MAX_COMPLETION_TOKENS", "8192")),
        "reasoning_effort": os.getenv("CHAT_REASONING_EFFORT", "LOW"),
    }
    model_kwargs.update(overrides.pop("model_kwargs", {}) or {})

    return ChatOCIGenAI(
        model_id=model_id,
        provider=infer_provider(model_id),
        service_endpoint=os.environ["GENAI_ENDPOINT"],
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        model_kwargs=model_kwargs,
        **oci_auth_kwargs(),
        **overrides,
    )


def create_langchain_embeddings(input_type: str = "SEARCH_DOCUMENT") -> OCIGenAIEmbeddings:
    """Create an OCIGenAIEmbeddings model from the workshop .env settings."""
    return OCIGenAIEmbeddings(
        model_id=os.environ["EMBED_MODEL_ID"],
        service_endpoint=os.environ["GENAI_ENDPOINT"],
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        input_type=input_type,
        **oci_auth_kwargs(),
    )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for small in-notebook retrieval examples."""
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    return numerator / (left_norm * right_norm)


def top_matches(
    query_vector: list[float],
    document_vectors: list[list[float]],
    documents: list[dict],
    k: int = 2,
) -> list[dict]:
    """Return the top in-memory matches for a query vector."""
    scored = []
    for document, vector in zip(documents, document_vectors, strict=True):
        scored.append(
            {
                **document,
                "score": cosine_similarity(query_vector, vector),
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:k]
