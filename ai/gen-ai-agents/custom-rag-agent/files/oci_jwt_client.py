"""
Client to get the JWT token from OCI IAM

Author: L. Saetta
License: MIT

for now it assumes API_KEY auth, can be changed for INSTANCE_PRINCIPAL
"""

import base64
import oci
import requests
from utils import get_console_logger
from config import DEBUG

# this is the cliend_id defined in the config of the
# confidential application in OCI IAM
from config_private import OCI_CLIENT_ID

logger = get_console_logger()


class OCIJWTClient:
    """
    Client for obtaining JWT access tokens from Oracle Identity Cloud Service (IDCS)
    via the OAuth2 client credentials grant.

    Attributes:
        base_url (str): Base URL for the IDCS tenant.
        scope (str): OAuth2 scope to include in the token request.
        client_id (str): OCI client ID (from config).
        client_secret (str): OCI client secret (from config).
        token_url (str): Full URL for the token endpoint.

    Methods:
        get_token() -> Tuple[str, str, int]:
            Requests a token and returns (access_token, token_type, expires_in).
    """

    def __init__(self, base_url, scope, secret_ocid):
        """
        Initializes the token client.

        Args:
            base_url: The base URL of the IDCS tenant.
            scope: The requested OAuth2 scope.
            secret_ocid: the ocid of the secret in the vault containing client_secret
        """
        self.base_url = base_url
        self.scope = scope
        # this is the endpoint to request a JWT token
        self.token_url = f"{self.base_url}/oauth2/v1/token"
        self.client_id = OCI_CLIENT_ID
        self.client_secret = self.get_client_secret(secret_ocid)
        self.timeout = 60

    def get_client_secret(self, secret_ocid: str):
        """
        Read the client secret from OCI vault
        """
        oci_config = oci.config.from_file()
        secrets_client = oci.secrets.SecretsClient(oci_config)

        # Retrieve the current secret bundle
        response = secrets_client.get_secret_bundle(secret_id=secret_ocid)
        b64 = response.data.secret_bundle_content.content

        # Decode and use
        return base64.b64decode(b64).decode("utf-8")

    def get_token(self):
        """
        Requests a client_credentials access token from IDCS.

        Returns:
            Tuple of access token (str), token type (str), and expiration (int seconds).

        Raises:
            HTTPError if the request fails.
        """
        data = {"grant_type": "client_credentials", "scope": self.scope}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            self.token_url,
            data=data,
            headers=headers,
            # auth is like basic auth
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )

        if DEBUG:
            logger.info("-------------------------------------------")
            logger.info("---- HTTP response text with JWT token ----")
            logger.info("-------------------------------------------")
            logger.info(response.text)

        # check for any error
        response.raise_for_status()

        token_data = response.json()

        return (
            token_data["access_token"],
            token_data["token_type"],
            token_data["expires_in"],
        )
