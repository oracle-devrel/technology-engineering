"""
Configuration for the Nemotron 3 Nano Omni compliance audit asset.

Author: Ali Ottoman
"""
import os

from dotenv import load_dotenv

load_dotenv()

# OCI OpenAI-compatible endpoint and auth
OCI_OPENAI_BASE_URL = os.environ["OCI_OPENAI_BASE_URL"]
OCI_CONFIG_PROFILE = os.getenv("OCI_CONFIG_PROFILE", "LONDON")

# Nemotron 3 Nano Omni - DAC endpoint OCID
NEMOTRON_OMNI_OCID = os.environ["NEMOTRON_OMNI_OCID"]

# Inference defaults
TEMPERATURE = 0.2
MAX_TOKENS = 8000

# Upload limits and accepted types
MAX_VIDEO_SIZE_MB = 100
SUPPORTED_VIDEO_TYPES = ["mp4", "webm", "mov", "mkv"]