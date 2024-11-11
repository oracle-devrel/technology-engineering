# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Utility Function to get secrets from OCI Vault
import logging
import oci
import base64

def getSecret(ocid):
    signer = oci.auth.signers.get_resource_principals_signer()
    try:
        client = oci.secrets.SecretsClient({}, signer=signer)
        secret_content = client.get_secret_bundle(ocid).data.secret_bundle_content.content.encode('utf-8')
        decrypted_secret_content = base64.b64decode(secret_content).decode('utf-8')
    except Exception as ex:
        logging.getLogger().error("getSecret: Failed to get Secret" + ex)
        print("Error [getSecret]: failed to retrieve", ex, flush=True)
        raise
    return decrypted_secret_content

