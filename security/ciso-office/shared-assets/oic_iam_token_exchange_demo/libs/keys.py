import jwt
import requests
import json
import oci
import base64
import os

import constants
import environment as env

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from requests.models import HTTPBasicAuth

#Initialise OCI SDK
config = config = oci.config.from_file(
    "~/.oci/config",
    env.oci_profile)

#Load private key from Vault
def __read_secret_value(secret_client, secret_id):
    response = secret_client.get_secret_bundle(secret_id)

    base64_Secret_content = response.data.secret_bundle_content.content
    base64_secret_bytes = base64_Secret_content.encode('ascii')
    base64_message_bytes = base64.b64decode(base64_secret_bytes)
    secret_content = base64_message_bytes.decode('ascii')

    return secret_content

#Load local public key from file
def load_public_key():
    try:
        with open(env.public_key, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
            return public_key
    except Exception as e:
        print('ERROR: Cannot read public key')
        raise

#Load the private key from either Vault or local file
def load_private_key(location):
    if location == "local":
        try:
            with open(env.private_key, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            return private_key
        except Exception as e:
            print('ERROR: Cannot read private key from local file')
            raise
    if location == "vault":
        try:
            secret_client = oci.secrets.SecretsClient(config)
            secret_content = __read_secret_value(secret_client, env.secret_id)
            return secret_content
        except Exception as e:
            print('ERROR: Cannot read private key from Vault')
        raise