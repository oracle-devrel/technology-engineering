"""
Shared MCP code

mcp_utils
"""

import argparse
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp import FastMCP

from config import (
    ENABLE_JWT_TOKEN,
    IAM_BASE_URL,
    ISSUER,
    AUDIENCE,
    TRANSPORT,
    PORT,
    HOST,
)


def create_server(name: str):
    """
    Create and return the MCP server instance.

    To handle JWT tokens it use OCI IAM as the provider.
    """
    # using JWT for security
    #
    # if you don't need to add security simply set ENABLE_JWT_TOKEN = False
    #
    auth = None

    if ENABLE_JWT_TOKEN:
        # check that a valid JWT token is provided
        auth = JWTVerifier(
            # this is the url to get the public key from IAM
            # the PK is used to check the JWT
            jwks_uri=f"{IAM_BASE_URL}/admin/v1/SigningCert/jwk",
            issuer=ISSUER,
            audience=AUDIENCE,
        )

    mcp = FastMCP(name, auth=auth)

    return mcp


def run_server(mcp):
    """
    Run the MCP server, with optional command line overrides
    for port (defaults to config.PORT).

    mcp is the server instance created with FastMCP()
    """
    if TRANSPORT not in {"stdio", "streamable-http"}:
        raise RuntimeError(f"Unsupported TRANSPORT: {TRANSPORT}")

    # parse CLI arguments to eventually get the port
    parser = argparse.ArgumentParser(description="Run the Select AI MCP server")
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Port to run the MCP server on (default: {PORT} from config.py)",
    )
    args = parser.parse_args()

    # run the MCP server
    if TRANSPORT == "stdio":
        mcp.run(transport=TRANSPORT)
    else:
        mcp.run(
            transport=TRANSPORT,
            host=HOST,
            port=args.port,
        )
