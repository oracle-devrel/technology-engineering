"""
File name: minimal_mcp_server.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module provides a minimal example of an MCP (Model Context Protocol) server built with FastMCP.
    It defines basic tools (e.g., say_the_truth and get_weather) and demonstrates server creation and execution,
    including JWT verification using the updated FastMCP library.

Usage:
    Use this as a template for custom MCP servers or run it directly as a standalone server.
    Example:
        # Run the server: python minimal_mcp_server.py
        # Or extend it by adding custom tools decorated with @mcp.tool

License:
    This code is released under the MIT License.

Notes:
    This is a starting point for building MCP servers in the MCP-OCI integration framework.
    It uses mcp_utils for server creation and focuses on simplicity for quick prototyping.

Warnings:
    This module is in development and may change in future versions. It includes placeholder tools for demonstration;
    replace them with real implementations and ensure proper security for production use.
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
