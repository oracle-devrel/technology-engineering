import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".config")

# config, compartments and endpoints
CONFIG_FILE_PATH = os.getenv("CONFIG_FILE_PATH")
COMPARTMENT_ID = os.getenv("COMPARTMENT_ID")
PROFILE_NAME= os.getenv("PROFILE_NAME")
ENDPOINT = os.getenv("ENDPOINT")

## Vision Bucket:
BUCKET_NAMESPACE = os.getenv("BUCKET_NAMESPACE")
BUCKET_NAME = os.getenv("BUCKET_NAME")
BUCKET_FILE_PREFIX = "uploads"
SPEECH_BUCKET_OUTPUT_PREFIX = "speech_output"

## Other config params
ORACLE_LOGO = "frontend/Oracle logo.png"
UPLOAD_PATH = "uploaded_files"
GENAI_MODELS = {
    "OpenAI GPT-OSS 120b": "openai.gpt-oss-120b",
    "OpenAI GPT-OSS 20b": "openai.gpt-oss-20b",
    # Grok models (xAI)
    "Grok Non Reasoning": "xai.grok-4-fast-non-reasoning",
    # Meta models
    "Meta Llama 3.3 70B": "meta.llama-3.3-70b-instruct",
    # Add more models as needed - check OCI documentation for exact model IDs
}
LIST_GENAI_MODELS = list(GENAI_MODELS.keys())
