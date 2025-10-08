"""
Minimal MCP server

This should be the starting point for any MCP server built with FastMCP.
This is the version with new FastMCP library.
Biggest difference: the class used to verify JWT.
"""

from mcp_utils import create_server, run_server


mcp = create_server("OCI MCP server with few lines of code")


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
    run_server(mcp)
