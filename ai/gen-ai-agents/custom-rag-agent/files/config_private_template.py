"""
File name: config_private.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    All the security and private configs here.

Usage:
    Import this module into other scripts to use its functions.
    Example:
      from config_private import ...


License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

# Oracle Vector Store
VECTOR_DB_USER = "XXXXX"
VECTOR_DB_PWD = "YYYY"
VECTOR_WALLET_PWD = "welcome1"
VECTOR_DSN = "aidb_medium"
VECTOR_WALLET_DIR = "/Users/xxxx/Progetti/yyyyy/WALLET_VECTOR"


CONNECT_ARGS = {
    # check that settings are correct for your environment
    "user": "XXXXX",
    "password": "YYYY",
    "dsn": "aidb_medium",
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": "xxxxxx",
}

# integration with APM
APM_PUBLIC_KEY = "123456789PM"

# to add JWT to MCP
JWT_SECRET = "your-secret"
JWT_ALGORITHM = "HS256"

# if using IAM to generate JWT token
OCI_CLIENT_ID = "your-client-id"
# th ocid of the secret in the vault
SECRET_OCID = "secret-ocid"
