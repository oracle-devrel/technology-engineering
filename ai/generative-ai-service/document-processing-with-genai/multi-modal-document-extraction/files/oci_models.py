"""
    This module provides a function to initialize LLM
    
    Return an instance of the OCI GenAI language model.

    Author: Ali Ottoman
"""
# ─── Imports ────────────────────────────────────────────────────────────────────
import oci
from config import service_endpoint


# ─── Configuration ─────────────────────────────────────────────────────────────
config = oci.config.from_file("~/.oci/config", "DEFAULT")

def get_llm():
    """
    Initialize and return an instance of ChatOCIGenAI with the specified configuration.

    Returns:
        ChatOCIGenAI: An instance of the OCI GenAI language model.
    """
    llm = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,
        service_endpoint=service_endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )
    return llm
