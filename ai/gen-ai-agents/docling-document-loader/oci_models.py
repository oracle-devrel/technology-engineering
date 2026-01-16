"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Contains utility functions to get access to Models
    in OCI GenAI service
"""

from langchain_oci import OCIGenAIEmbeddings

from config import AUTH, EMBED_MODEL_ID, DEBUG, SERVICE_ENDPOINT
from config_private import COMPARTMENT_ID
from utils import get_console_logger

logger = get_console_logger()


def get_embedding_model():
    """
    Initialize and return an instance of OCIGenAIEmbeddings with the specified configuration.
    Returns:
        OCIGenAIEmbeddings: An instance of the OCI GenAI embeddings model.
    """
    embed_model = None

    embed_model = OCIGenAIEmbeddings(
        auth_type=AUTH,
        model_id=EMBED_MODEL_ID,
        service_endpoint=SERVICE_ENDPOINT,
        compartment_id=COMPARTMENT_ID,
    )

    if DEBUG:
        logger.info("Embedding model is: %s", EMBED_MODEL_ID)

    return embed_model
