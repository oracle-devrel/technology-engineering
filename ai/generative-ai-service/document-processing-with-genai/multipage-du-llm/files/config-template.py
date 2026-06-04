# config.py - Centralized configuration for all OCI and LLM settings
import os

# ============================================================================
# OCI Compartment Configuration
# ============================================================================
COMPARTMENT_ID = "<your_compartment_id>"
OCI_CONFIG_PROFILE = "PAUL"
OCI_CONFIG_PATH = "~/.oci/config"

# ============================================================================
# OCI Generative AI Service Configuration
# ============================================================================
OCI_SERVICE_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

# ============================================================================
# Model IDs
# ============================================================================
# Meta Llama 3.3 70B Instruct
OCI_LLAMA_3_3_MODEL_ID = "<your_model_ocid>"

# Default model alias
DEFAULT_MODEL_ID = OCI_LLAMA_3_3_MODEL_ID

# ============================================================================
# File Paths
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# ============================================================================
# LLM Default Parameters
# ============================================================================
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0
DEFAULT_PRESENCE_PENALTY = 0
