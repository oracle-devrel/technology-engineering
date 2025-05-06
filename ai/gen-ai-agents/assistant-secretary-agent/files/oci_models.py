Copyright (c) 2025 Oracle and/or its affiliates.
"""
By Omar Salem
oci_models.py - Factory for OCI GenAI models (Cohere)
"""

from langchain_community.chat_models import ChatOCIGenAI

# OCI compartment details
COMPARTMENT_OCID = "ocid1.com...."
SERVICE_ENDPOINT = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

LLM_MODEL_ID = "cohere.command-r-plus-08-2024"
ROUTER_MODEL_ID = "cohere.command-r-plus-08-2024"

def create_model_for_routing(temperature=0, max_tokens=512):
    """
    Create the OCI Model for routing
    """
    return ChatOCIGenAI(
        model_id=ROUTER_MODEL_ID,
        compartment_id=COMPARTMENT_OCID,
        service_endpoint=SERVICE_ENDPOINT,
        model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
    )
