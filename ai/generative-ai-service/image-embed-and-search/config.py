

DB_TYPE = "chroma"  # Options: "oracle", "chroma"

# Oracle Vector Store
VECTOR_DB_USER = "######" 
VECTOR_DB_PWD = "######" 
VECTOR_WALLET_PWD = "######" 
VECTOR_DSN = "######" 
VECTOR_WALLET_DIR = "######" 


CONNECT_ARGS = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,
}


# OracleDB Configuration
ORACLE_DB_USER = "######"   #Enter your oracle vector Db username
ORACLE_DB_PWD = "######"  #Enter your oracle vector Db password
ORACLE_DB_HOST_IP = "######"  #Enter your oracle vector Db host ip
ORACLE_DB_PORT = "######"   #Enter your oracle vector Db host port
ORACLE_DB_SERVICE = "######" 

ORACLE_USERNAME = ORACLE_DB_USER
ORACLE_PASSWORD = ORACLE_DB_PWD
ORACLE_DSN = f"{ORACLE_DB_HOST_IP}:{ORACLE_DB_PORT}/{ORACLE_DB_SERVICE}"
ORACLE_TABLE_NAME = "policyTable" #name of table where you want to store the embeddings in oracle DB

# ChromaDB Configuration
CHROMA_PERSIST_DIR = "./chroma_db"

# # Common Configuration
COMPARTMENT_ID = "######" 
# OBJECT_STORAGE_LINK = "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/##############/b/##########/o/"
DIRECTORY = 'data'  # directory to store the pdf's from where the RAG model should take the documents from
ENDPOINT= "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com" #change in case you want to select a diff region
EMBEDDING_MODEL = "cohere.embed-v4.0"
EMBEDDING_MODEL_CHOICES = [
    "cohere.embed-v4.0",
    "cohere.embed-english-image-v3.0",
    "cohere.embed-english-light-image-v3.0"
]
GENERATE_MODEL = "meta.llama-3.3-70b-instruct"
#GENERATE_MODEL = "cohere.command-a-03-2025"  # cohere.command-r-16k or cohere.command-r-plus
