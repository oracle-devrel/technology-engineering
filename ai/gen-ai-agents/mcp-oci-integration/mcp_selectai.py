"""
Text2SQL MCP server based on ADB Select AI

It requires that a Select AI profile has already been created
in the DB schema used for the DB connection.
"""

from fastmcp import FastMCP

# to verify the JWT token
# if you don't need to add security, you can remove this
# uses the new verifier from latest FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

# here is the function that calls Select AI
from db_utils import generate_sql_from_prompt, execute_generated_sql

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
    # select ai
    SELECT_AI_PROFILE,
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

mcp = FastMCP("OCI Select AI MCP server", auth=AUTH)

# helpers


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
@mcp.tool
def generate_sql(user_request: str) -> str:
    """
    Return the SQL generated for the user request.

    Args:
        user_request (str): the request to be translated in SQL.

    Returns:
        str: the SQL generated.

    Examples:
        >>> generate_sql("List top 5 customers by sales")
        SQL...
    """
    return generate_sql_from_prompt(SELECT_AI_PROFILE, user_request)


@mcp.tool
def execute_sql(sql: str):
    """
    Execute the SQL generated
    """
    return execute_generated_sql(sql)


#
# Run the Select AI MCP server
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
