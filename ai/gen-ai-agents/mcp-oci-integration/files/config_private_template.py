"""
Private config
"""

#
VECTOR_DB_USER = "your-db-user"
VECTOR_DB_PWD = "your-db-pwd"

VECTOR_WALLET_PWD = "wallet-pwd"
VECTOR_DSN = "db-psn"
VECTOR_WALLET_DIR = "/Users/xxx/yyy"

CONNECT_ARGS = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,
}

COMPARTMENT_ID = "ocid1.compartment.oc1.your-compartment-ocid"

# to add JWT to MCP server
JWT_SECRET = "secret"
# using this in the demo, make it simpler.
# In production should switch to RS256 and use a key-pair
JWT_ALGORITHM = "HS256"

# if using IAM to generate JWT token
OCI_CLIENT_ID = "client-id"
# th ocid of the secret in the vault
SECRET_OCID = "ocid1.vaultsecret.oc1.eu-frankfurt-1.secret-ocid"
