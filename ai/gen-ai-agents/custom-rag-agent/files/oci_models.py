"""
File name: oci_models.py
Author: Luigi Saetta
Date last modified: 2025-06-30
Python Version: 3.11

Description:
    This module enables easy access to OCI GenAI LLM.


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

from langchain_community.chat_models import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.vectorstores.oraclevs import OracleVS

from custom_rest_embeddings import CustomRESTEmbeddings
from utils import get_console_logger
from config import (
    AUTH,
    SERVICE_ENDPOINT,
    COMPARTMENT_ID,
    # used only for defaults
    LLM_MODEL_ID,
    TEMPERATURE,
    MAX_TOKENS,
    EMBED_MODEL_ID,
    NVIDIA_EMBED_MODEL_URL,
)


logger = get_console_logger()

ALLOWED_EMBED_MODELS_TYPE = {"OCI", "NVIDIA"}

# for gpt5, since max tokens is not supported
MODELS_WITHOUT_KWARGS = {
    "openai.gpt-5",
    "openai.gpt-4o-search-preview",
    "openai.gpt-4o-search-preview-2025-03-11",
}


def normalize_provider(model_id: str) -> str:
    """
    apply an hack to handle new models:
    use meta as provider for these new models
    """
    _provider = model_id.split(".")[0]

    if _provider in {"xai", "openai"}:
        # Known LangChain limitation workaround
        _provider = "meta"
    return _provider


def get_llm(model_id=LLM_MODEL_ID, temperature=TEMPERATURE, max_tokens=MAX_TOKENS):
    """
    Initialize and return an instance of ChatOCIGenAI with the specified configuration.

    Returns:
        ChatOCIGenAI: An instance of the OCI GenAI language model.
    """
    # try to identify the provider
    _provider = normalize_provider(model_id)

    if model_id not in MODELS_WITHOUT_KWARGS:
        _model_kwargs = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    else:
        # for some models (OpenAI search) you cannot set those params
        _model_kwargs = None

    llm = ChatOCIGenAI(
        auth_type=AUTH,
        model_id=model_id,
        service_endpoint=SERVICE_ENDPOINT,
        compartment_id=COMPARTMENT_ID,
        is_stream=True,
        model_kwargs=_model_kwargs,
        provider=_provider,
    )
    return llm


def get_embedding_model(model_type="OCI"):
    """
    Initialize and return an instance of OCIGenAIEmbeddings with the specified configuration.
    Returns:
        OCIGenAIEmbeddings: An instance of the OCI GenAI embeddings model.
    """
    # check model type
    if model_type not in ALLOWED_EMBED_MODELS_TYPE:
        raise ValueError(
            f"Invalid value for model_type: must be one of {ALLOWED_EMBED_MODELS_TYPE}"
        )

    embed_model = None

    if model_type == "OCI":
        embed_model = OCIGenAIEmbeddings(
            auth_type=AUTH,
            model_id=EMBED_MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            compartment_id=COMPARTMENT_ID,
        )
    elif model_type == "NVIDIA":
        embed_model = CustomRESTEmbeddings(
            api_url=NVIDIA_EMBED_MODEL_URL, model=EMBED_MODEL_ID
        )

    logger.info("Embedding model is: %s", EMBED_MODEL_ID)
    
    return embed_model


def get_oracle_vs(conn, collection_name, embed_model):
    """
    Initialize and return an instance of OracleVS for vector search.

    Args:
        conn: The database connection object.
        collection_name (str): The name of the collection (DB table) to search in.
        embed_model: The embedding model to use for vector search.
    """
    oracle_vs = OracleVS(
        client=conn,
        table_name=collection_name,
        distance_strategy=DistanceStrategy.COSINE,
        embedding_function=embed_model,
    )

    return oracle_vs
