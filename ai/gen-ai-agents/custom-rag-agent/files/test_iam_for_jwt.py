"""
Module for requesting and verifying OAuth2 JWT tokens from Oracle IDCS.

Classes:
    OCIJWTClient: Fetches access tokens using client credentials flow.
    OCIJWTServer: Decodes and verifies JWT signatures using IDCS JWKS.
"""

import jwt
from jwt import PyJWKClient
from oci_jwt_client import OCIJWTClient
from utils import get_console_logger
from config_private import SECRET_OCID

logger = get_console_logger()


class OCIJWTServer:
    """
    Server-side utility for decoding and verifying JWT tokens using
    the JWKS endpoint of Oracle IDCS.

    Attributes:
        jwks_url (str): URL to fetch JWKS (JSON Web Key Set).
        audience (str): Expected audience claim in the token.
        issuer (str): Expected issuer claim in the token.

    Methods:
        decode_unverified(token: str) -> dict:
            Returns unverified claims for inspection/debug.
        verify_token(token: str) -> dict:
            Fully validates the token signature and claims.
    """

    def __init__(self, base_url, audience, issuer):
        """
        Initializes the verifier.

        Args:
            base_url: Base URL for the IDCS tenant.
            audience: Expected 'aud' claim in JWT.
            issuer: Expected 'iss' claim in JWT.
        """
        self.jwks_url = f"{base_url}/admin/v1/SigningCert/jwk"
        self.audience = audience
        self.issuer = issuer

    def decode_unverified(self, _token):
        """
        Decodes a JWT without verifying the signature.

        Args:
            token: The JWT string.

        Returns:
            Dictionary of JWT claims.
        """
        return jwt.decode(_token, options={"verify_signature": False})

    def verify_token(self, _token):
        """
        Verifies a JWT's signature and standard claims using JWKS.

        Args:
            token: The JWT string.

        Returns:
            Dictionary of verified JWT claims.

        Raises:
            jwt.exceptions.PyJWKClientError, jwt.PyJWTError if verification fails.
        """
        logger.info("Getting public key from OCI IAM...")
        jwks_client = PyJWKClient(self.jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(_token).key

        logger.info("Verifying token...")
        return jwt.decode(
            _token,
            signing_key,
            # this is the default for OCI iam
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            verify=True,
        )


#
# Main
#
BASE_URL = "https://idcs-930d7b2ea2cb46049963ecba3049f509.identity.oraclecloud.com"
# this is the scope for which the token is issued
SCOPE = "urn:opc:idm:__myscopes__"
# these are used in verification
# these is depending from the tenant

AUDIENCE = "urn:opc:lbaas:logicalguid=idcs-930d7b2ea2cb46049963ecba3049f509"
ISSUER = "https://identity.oraclecloud.com/"

client = OCIJWTClient(BASE_URL, SCOPE, SECRET_OCID)
print("")
print("Getting token from OCI IAM...")
token, token_type, expires_in = client.get_token()
print(token)
print("Token type:", token_type)

server = OCIJWTServer(BASE_URL, AUDIENCE, ISSUER)
claims = server.decode_unverified(token)
print("")
print("Unverified claims:", claims)
print("")

verified = server.verify_token(token)
print("")
print("Token Verification OK:", verified)
