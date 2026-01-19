# oci_utils.py - Shared OCI client utilities and common functions
"""
Centralized OCI client initialization and utility functions.
This module provides a single source of truth for OCI client setup,
eliminating redundant initialization code across the codebase.
"""

import json
import oci
from typing import Tuple, List, Optional

from config import (
    COMPARTMENT_ID,
    OCI_CONFIG_PROFILE,
    OCI_CONFIG_PATH,
    OCI_SERVICE_ENDPOINT,
    DEFAULT_MODEL_ID,
    CATEGORIES_FILE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_PRESENCE_PENALTY,
)


# ============================================================================
# OCI Client Initialization
# ============================================================================

def get_oci_config() -> dict:
    """Load OCI configuration from the config file."""
    return oci.config.from_file(OCI_CONFIG_PATH, OCI_CONFIG_PROFILE)


def init_generative_ai_client() -> Tuple[oci.generative_ai_inference.GenerativeAiInferenceClient, str]:
    """
    Initialize the OCI Generative AI Inference client.
    
    Returns:
        Tuple containing (client, compartment_id)
    """
    config = get_oci_config()
    client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,
        service_endpoint=OCI_SERVICE_ENDPOINT,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240),
    )
    return client, COMPARTMENT_ID


def init_document_client() -> oci.ai_document.AIServiceDocumentClient:
    """Initialize OCI Document Understanding client."""
    config = get_oci_config()
    return oci.ai_document.AIServiceDocumentClient(config)


# ============================================================================
# Chat Request Helpers
# ============================================================================

def create_chat_request(
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    frequency_penalty: float = DEFAULT_FREQUENCY_PENALTY,
    presence_penalty: float = DEFAULT_PRESENCE_PENALTY,
) -> oci.generative_ai_inference.models.GenericChatRequest:
    """
    Create a standardized chat request with the given prompt.
    
    Args:
        prompt: The text prompt to send to the model
        max_tokens: Maximum tokens in response (default from config)
        temperature: Model temperature (default from config)
        top_p: Top-p sampling parameter (default from config)
        frequency_penalty: Frequency penalty (default from config)
        presence_penalty: Presence penalty (default from config)
    
    Returns:
        Configured GenericChatRequest object
    """
    content = oci.generative_ai_inference.models.TextContent()
    content.text = prompt

    message = oci.generative_ai_inference.models.Message()
    message.role = "USER"
    message.content = [content]

    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.api_format = (
        oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    )
    chat_request.messages = [message]
    chat_request.max_tokens = max_tokens
    chat_request.temperature = temperature
    chat_request.top_p = top_p
    chat_request.frequency_penalty = frequency_penalty
    chat_request.presence_penalty = presence_penalty

    return chat_request


def create_chat_details(
    chat_request: oci.generative_ai_inference.models.GenericChatRequest,
    model_id: str = DEFAULT_MODEL_ID,
    compartment_id: str = COMPARTMENT_ID,
) -> oci.generative_ai_inference.models.ChatDetails:
    """
    Create ChatDetails with the specified model and compartment.
    
    Args:
        chat_request: The chat request to wrap
        model_id: OCI model ID (default: Llama 3.3)
        compartment_id: OCI compartment ID (default from config)
    
    Returns:
        Configured ChatDetails object
    """
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
        model_id=model_id
    )
    chat_detail.chat_request = chat_request
    chat_detail.compartment_id = compartment_id
    return chat_detail


def send_chat_request(
    client: oci.generative_ai_inference.GenerativeAiInferenceClient,
    prompt: str,
    model_id: str = DEFAULT_MODEL_ID,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """
    Convenience function to send a chat request and get the response text.
    
    Args:
        client: Initialized GenerativeAiInferenceClient
        prompt: The text prompt to send
        model_id: OCI model ID (default: Llama 3.3)
        max_tokens: Maximum tokens in response
        temperature: Model temperature
    
    Returns:
        Response text from the model
    """
    chat_request = create_chat_request(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    chat_details = create_chat_details(chat_request, model_id=model_id)
    
    response = client.chat(chat_details)
    return (
        response.data.chat_response.choices[0]
        .message.content[0]
        .text.strip()
    )


# ============================================================================
# Categories Loading
# ============================================================================

def load_categories(categories_file: str = CATEGORIES_FILE) -> List[str]:
    """
    Load document categories from the JSON file.
    
    Args:
        categories_file: Path to categories JSON file (default from config)
    
    Returns:
        List of category strings
    """
    with open(categories_file, 'r') as f:
        data = json.load(f)
    return data.get('categories', [])


# ============================================================================
# LangChain Integration (for Streamlit app)
# ============================================================================

def get_langchain_llm(
    model_id: str = DEFAULT_MODEL_ID,
    compartment_id: str = COMPARTMENT_ID,
    max_tokens: int = 2000,
    temperature: float = 0,
):
    """
    Initialize a LangChain ChatOCIGenAI client for Meta Llama 3.3.
    
    Args:
        model_id: OCI model ID (default: Llama 3.3)
        compartment_id: OCI compartment ID
        max_tokens: Maximum tokens in response
        temperature: Model temperature
    
    Returns:
        ChatOCIGenAI instance
    """
    try:
        from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
    except ImportError:
        raise ImportError(
            "langchain_community is required for LangChain integration. "
            "Install it with: pip install langchain-community"
        )
    
    return ChatOCIGenAI(
        model_id=model_id,
        compartment_id=compartment_id,
        provider="meta",
        model_kwargs={"max_tokens": max_tokens, "temperature": temperature},
    )
