import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "qdrant")

# Oracle Vector Store
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PWD = os.getenv("VECTOR_DB_PWD")
VECTOR_WALLET_PWD = os.getenv("VECTOR_WALLET_PWD")
VECTOR_DSN = os.getenv("VECTOR_DSN")
VECTOR_WALLET_DIR = os.getenv("VECTOR_WALLET_DIR")

CONNECT_ARGS = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,
}

# OracleDB Configuration
ORACLE_DB_USER = os.getenv("ORACLE_DB_USER")
ORACLE_DB_PWD = os.getenv("ORACLE_DB_PWD")
ORACLE_DB_HOST_IP = os.getenv("ORACLE_DB_HOST_IP")
ORACLE_DB_PORT = os.getenv("ORACLE_DB_PORT")
ORACLE_DB_SERVICE = os.getenv("ORACLE_DB_SERVICE")

ORACLE_USERNAME = ORACLE_DB_USER
ORACLE_PASSWORD = ORACLE_DB_PWD
ORACLE_DSN = f"{ORACLE_DB_HOST_IP}:{ORACLE_DB_PORT}/{ORACLE_DB_SERVICE}"
ORACLE_TABLE_NAME = os.getenv("ORACLE_TABLE_NAME", "policyTable")

# Qdrant Configuration
QDRANT_LOCATION = os.getenv("QDRANT_LOCATION", ":memory:")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "my_documents")
QDRANT_DISTANCE_FUNC = os.getenv("QDRANT_DISTANCE_FUNC", "Dot")

# OCI Configuration
COMPARTMENT_ID = os.getenv("COMPARTMENT_ID")
ENDPOINT = os.getenv("ENDPOINT")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
GENERATE_MODEL = os.getenv("GENERATE_MODEL")

# Application Configuration
DIRECTORY = os.getenv("DIRECTORY", "data")
PROMPT_CONTEXT = os.getenv("PROMPT_CONTEXT", "You are an AI Assistant trained to give answers based only on the information provided. Given only the above text provided and not prior knowledge, answer the query. If someone asks you a question and you don't know the answer, don't try to make up a response, simply say: I don't know.")