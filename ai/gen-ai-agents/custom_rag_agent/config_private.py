"""
Private config
"""

# Oracle Vector Store
VECTOR_DB_USER = "TEST_VECTOR"
VECTOR_DB_PWD = "GenaAiGen2024##"
VECTOR_WALLET_PWD = "welcome1"
VECTOR_DSN = "aidb_medium"
VECTOR_WALLET_DIR = "/Users/lsaetta/Progetti/ai_assistant3/WALLET_VECTOR"


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
