"""
File name: config.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module provides general configurations


Usage:
    Import this module into other scripts to use its functions.
    Example:
        import config

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

DEBUG = False

# type of auth
AUTH = "API_KEY"

# embeddings
EMBED_MODEL_ID = "cohere.embed-multilingual-v3.0"

# LLM
# this is the default model
LLM_MODEL_ID = "meta.llama-3.3-70b-instruct"
TEMPERATURE = 0.1
MAX_TOKENS = 1024

# for the UI
LANGUAGE_LIST = ["same as the question", "en", "fr", "it", "es"]
MODEL_LIST = ["meta.llama-3.3-70b-instruct", "cohere.command-r-plus-08-2024"]

ENABLE_USER_FEEDBACK = True

# semantic search
TOP_K = 6
COLLECTION_LIST = ["BOOKS", "CNAF"]

# OCI general
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaaushuwb2evpuf7rcpl4r7ugmqoe7ekmaiik3ra3m7gec3d234eknq"
SERVICE_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

# history management (put -1 if you want to disable trimming)
# consider that we have pair (human, ai) so use an even (ex: 6) value
MAX_MSGS_IN_HISTORY = 6

# reranking enabled or disabled from UI

# Integration with APM
ENABLE_TRACING = False
AGENT_NAME = "OCI_CUSTOM_RAG_AGENT"

# lsaetta-apm compartment
APM_BASE_URL = "https://aaaadec2jjn3maaaaaaaaach4e.apm-agt.eu-frankfurt-1.oci.oraclecloud.com/20200101"
APM_CONTENT_TYPE = "application/json"

# for loading
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 100
