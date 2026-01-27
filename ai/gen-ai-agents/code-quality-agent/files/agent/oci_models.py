"""
File name: oci_models.py
Author: Luigi Saetta
Date last modified: 2026-01-13
Python Version: 3.11

Description:
    This module enables easy access to OCI GenAI LLM/Embeddings.


Usage:
    Import this module into other scripts to use its functions.
    Example:
        from oci_models import get_llm

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

    modified to support xAI and OpenAI models through Langchain

Warnings:
    This module is in development, may change in future versions.
"""

# switched to the new OCI langchain integration
from langchain_oci import ChatOCIGenAI

from agent.utils import get_console_logger
from agent.config import (
    DEBUG,
    STREAMING,
    AUTH,
    SERVICE_ENDPOINT,
    # used only for defaults
    LLM_MODEL_ID,
    TEMPERATURE,
    MAX_TOKENS,
)
from agent.config_private import COMPARTMENT_ID

logger = get_console_logger()


# for gpt5, since max tokens is not supported
MODELS_WITHOUT_KWARGS = {
    "openai.gpt-oss-120b",
    "openai.gpt-5",
}


def debug_llm(llm):
    print("LLM class:", type(llm))
    for attr in ("model_name", "model", "openai_api_base", "base_url", "api_base"):
        if hasattr(llm, attr):
            print(f"{attr} =", getattr(llm, attr))
    for attr in ("openai_api_key", "api_key"):
        if hasattr(llm, attr):
            v = getattr(llm, attr)
            print(f"{attr} present =", bool(v))


def get_llm(model_id=LLM_MODEL_ID, temperature=TEMPERATURE, max_tokens=MAX_TOKENS):
    """
    Initialize and return an instance of ChatOCIGenAI with the specified configuration.

    Returns:
        ChatOCIGenAI: An instance of the OCI GenAI language model.
    """
    if model_id not in MODELS_WITHOUT_KWARGS:
        _model_kwargs = {"temperature": temperature, "max_tokens": max_tokens}
    else:
        # for some models (OpenAI search) you cannot set those params
        _model_kwargs = None

    # old langchain fashion but based on langchain-oci
    llm = ChatOCIGenAI(
        auth_type=AUTH,
        model_id=model_id,
        service_endpoint=SERVICE_ENDPOINT,
        compartment_id=COMPARTMENT_ID,
        is_stream=STREAMING,
        model_kwargs=_model_kwargs,
    )

    if DEBUG:
        debug_llm(llm)

    return llm
