"""
Private config
"""

# Oracle Vector Store
# VECTOR_DB_USER = "TEST_VECTOR"
# VECTOR_DB_PWD = "LuigiLuigi2025##"
# VECTOR_WALLET_PWD = "welcome1"
# VECTOR_DSN = "aidb_medium"
# VECTOR_WALLET_DIR = "/Users/lsaetta/Progetti/ai_assistant3/WALLET_VECTOR"

# switched to ATP to avoid invalid LOB locator
VECTOR_DB_USER = "AIUSER"
VECTOR_DB_PWD = "Pennolina23ai&"

# point to the environment to test NVIDIA llama3.2 embed model
# VECTOR_DB_USER = "NVIDIAUSER"
# VECTOR_DB_PWD = "Pennolina2025&"
VECTOR_WALLET_PWD = "welcome1"
VECTOR_DSN = "aiatp01_medium"
VECTOR_WALLET_DIR = "/Users/lsaetta/Progetti/custom_rag_agent/wallet_atp"

CONNECT_ARGS = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,
}

# integration with APM
APM_PUBLIC_KEY = "6OXZ45BTT5AHD5KYICGOMLXXAZYTTLGT"

# to add JWT to MCP server
JWT_SECRET = "oracle-ai"
# using this in the demo, make it simpler.
# In production should switch to RS256 and use a key-pair
JWT_ALGORITHM = "HS256"

# if using IAM to generate JWT token
OCI_CLIENT_ID = "b51225fce0374a759f615ed264ddd268"
# th ocid of the secret in the vault
SECRET_OCID = "ocid1.vaultsecret.oc1.eu-frankfurt-1.amaaaaaa2xxap7yalre4qru4asevgtxlmn7hwh27awnzmdcrnmsfqu7cia7a"
