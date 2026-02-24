# How to start developing an MCP server
The code provided in [minimal_mcp_server](./minimal_mcp_server.py) is a good starting point.

But, in reality, for a super-minimal MCP server you need less code.
For example, you can remove support for JWT, if you don't need it.

Therefore:

```
from fastmcp import FastMCP

from config import (
    TRANSPORT,
    # needed only if transport is streamable-http
    HOST,
    PORT,
)

mcp = FastMCP("MCP server with few lines of code", auth=None)

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
```

## Discoverability and internal documentation
One of the key features in MCP is **discoverability**. 
They provide an endpoint where any AI assistant can discover the list of available tools and the way these tools can be called (params, return value).

But, to make it works, you need to put in place **clear documentation**.
If you implement it using FastMCP, the documntation for each tool is automatically generated from the docstring. 
So, it is mandatory to **write a complete and clear docstring** (Google style).