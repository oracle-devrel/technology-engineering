"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Configuration settings
"""

DEBUG = False
ADB = True

# embeddings
AUTH = "API_KEY"
EMBED_MODEL_ID = "cohere.embed-multilingual-v3.0"
REGION = "eu-frankfurt-1"
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# Chunking parameters
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100
