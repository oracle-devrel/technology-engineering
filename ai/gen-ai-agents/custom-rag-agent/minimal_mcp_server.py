"""
Minimal-but-solid MCP server with JWT hardening and sane defaults.

- Safe defaults for transports
"""

from fastmcp import FastMCP

# to verify the JWT token
# if you don't need to add security, you can remove this
# in newer version of FastMCP should be replaced with
# from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth import BearerAuthProvider

from config import (
    # first four needed only to manage JWT
    ENABLE_JWT_TOKEN,
    IAM_BASE_URL,
    ISSUER,
    AUDIENCE,
    TRANSPORT,
    # needed only if transport is stremable-http
    HOST,
    PORT,
)


#
# if you don't need to add security, you can remove this part and set
# AUTH = None, simply set ENABLE_JWT_TOKEN = False
#
AUTH = None

if ENABLE_JWT_TOKEN:
    # check that a valid JWT token is provided
    AUTH = BearerAuthProvider(
        # this is the url to get the public key from IAM
        # the PK is used to check the JWT
        jwks_uri=f"{IAM_BASE_URL}/admin/v1/SigningCert/jwk",
        issuer=ISSUER,
        audience=AUDIENCE,
    )

#
# define the MCP server
#
mcp = FastMCP("MCP server with few lines of code, but secure", auth=AUTH)


#
# MCP tools definition
# add and write the code for the tools here
#
@mcp.tool
def say_the_truth(user: str) -> str:
    """
    This tool, given the name of the user return one of the secret truths.

    Args:
        user: The caller's display name or identifier.

    Returns:
        A short truth string. 
    """
    # here you'll put the code that reads and return the info requested
    # mark each tool with the annotation
    return f"{user}: Less is more!"


#
# Run the MCP server
#
if __name__ == "__main__":
    # Validate transport
    if TRANSPORT not in {"stdio", "streamable-http"}:
        # don't use sse! it is deprecated!
        raise RuntimeError(f"Unsupported TRANSPORT: {TRANSPORT}")

    if TRANSPORT == "stdio":
        # stdio doesn’t support host/port args
        mcp.run(transport=TRANSPORT)
    else:
        # For http/streamable-http transport, host/port are valid
        mcp.run(
            transport=TRANSPORT,
            host=HOST,
            port=PORT,
        )
