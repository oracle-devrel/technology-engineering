# Copyright (c) 2025 Oracle and/or its affiliates.
# config_template.py

# === OCI Configuration ===
OCI_COMPARTMENT_ID = "ocid1.compartment.oc1..your_compartment_id"
OCI_CONFIG_PROFILE = "DEFAULT"
REGION = "your-region-id"  # e.g., "eu-frankfurt-1"
GEN_AI_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# === Embedding and Generation Models ===
EMBEDDING_MODEL_ID = "cohere.embed-english-v3.0"
GENERATION_MODEL_ID = "cohere.command-r-plus-08-2024"
GENERATION_MODEL_PROVIDER = "cohere"

# === LLM Parameters ===
TEMPERATURE = 0.1
MAX_TOKENS = 4000
TOP_P = 0.9

# === Vector Store Configuration ===
VECTOR_TABLE_NAME = "your_vector_table_name"  # e.g., coursera_vector_store
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# === Oracle Autonomous Database Configuration ===
# Replace these placeholders with your actual DB credentials and connection string
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_DSN = """
(description=
  (retry_count=20)(retry_delay=3)
  (address=(protocol=tcps)(port=1522)(host=your-adb-host.oraclecloud.com))
  (connect_data=(service_name=your_service_name.adb.oraclecloud.com))
  (security=(ssl_server_dn_match=yes))
)
"""

# This dict is used for vector store connections
CONNECT_ARGS_VECTOR = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "dsn": DB_DSN
}

# === Auth Method ===
AUTH_TYPE = "API_KEY"  # or "RESOURCE_PRINCIPAL", depending on deployment
CONFIG_PROFILE = OCI_CONFIG_PROFILE
