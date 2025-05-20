"""
Factory for Chat models
"""

from langchain_community.chat_models import ChatOCIGenAI

from config import MODEL_ID, SERVICE_ENDPOINT
from config_private import COMPARTMENT_OCID


def get_chat_model(
    model_id: str = MODEL_ID,
    service_endpoint: str = SERVICE_ENDPOINT,
    temperature=0,
    max_tokens=2048,
) -> ChatOCIGenAI:
    """
    Factory function to create and return a ChatOCIGenAI model instance.

    Returns:
        ChatOCIGenAI: Configured chat model instance.
    """
    # Create and return the chat model
    return ChatOCIGenAI(
        model_id=model_id,
        service_endpoint=service_endpoint,
        model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
        compartment_id=COMPARTMENT_OCID,
    )
