"""
Minimal MCP server

This should be the starting point for any MCP server built with FastMCP.
This is the version with new FastMCP library.
Biggest difference: the class used to verify JWT.
"""

from fastmcp import FastMCP

# to verify the JWT token
# if you don't need to add security, you can remove this
# uses the new verifier from latest FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

from config import (
    # first four needed only to manage JWT
    ENABLE_JWT_TOKEN,
    IAM_BASE_URL,
    ISSUER,
    AUDIENCE,
    TRANSPORT,
    # needed only if transport is streamable-http
    HOST,
    PORT,
)

AUTH = None

#
# if you don't need to add security, you can remove this part and set
# AUTH = None, or simply set ENABLE_JWT_TOKEN = False
#
if ENABLE_JWT_TOKEN:
    # check that a valid JWT token is provided
    AUTH = JWTVerifier(
        # this is the url to get the public key from IAM
        # the PK is used to check the JWT
        jwks_uri=f"{IAM_BASE_URL}/admin/v1/SigningCert/jwk",
        issuer=ISSUER,
        audience=AUDIENCE,
    )

mcp = FastMCP("OCI MCP server with few lines of code", auth=AUTH)


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
@mcp.tool
def say_the_truth(user: str) -> str:
    """
    Return a secret truth message addressed to the specified user.

    Args:
        user (str): The name or identifier of the user to whom the truth is addressed.

    Returns:
        str: A message containing a secret truth about the user.

    Examples:
        >>> say_the_truth("Luigi")
        "Luigi: Less is more!"
    """
    # here you'll put the code that reads and return the info requested
    # it is important to provide a good description of the tool in the docstring
    return f"{user}: Less is more!"


@mcp.tool
def get_weather(location: str) -> str:
    """
    Provide a human-readable description of the current weather in the given location.

    Args:
        location (str): The name of the city or area for which to fetch weather information.

    Returns:
        str: A description of current weather conditions in `location`.

    Examples:
        >>> get_weather("Rome")
        "In Rome: weather is fine!"
    """
    return f"In {location}: weather is fine!"


#
# Run the MCP server
#
if __name__ == "__main__":
    if TRANSPORT not in {"stdio", "streamable-http"}:
        raise RuntimeError(f"Unsupported TRANSPORT: {TRANSPORT}")

    # don't use sse! it is deprecated!
    if TRANSPORT == "stdio":
        # stdio doesn’t support host/port args
        mcp.run(transport=TRANSPORT)
    else:
        # For streamable-http transport, host/port are valid
        mcp.run(
            transport=TRANSPORT,
            host=HOST,
            port=PORT,
        )
