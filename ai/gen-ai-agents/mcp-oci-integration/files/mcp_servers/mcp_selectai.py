"""
File name: mcp_selectai.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for Text2SQL capabilities using ADB Select AI.
    It provides tools to generate SQL queries from natural language requests and execute them, requiring a pre-configured
    Select AI profile in the database schema for integration with OCI (Oracle Cloud Infrastructure) databases.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_selectai import generate_sql

        sql_query = generate_sql("List top 5 customers by sales")
        # Or run the server: python mcp_selectai.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and relies on db_utils for SQL handling.
    Tools return dictionaries with results or error messages for easy integration with MCP agents.

Warnings:
    This module is in development and may change in future versions. Ensure a Select AI profile is created in the DB schema
    prior to use, and handle potential exceptions related to database connections or query generation.
"""

from typing import Any, Dict

# here is the function that calls Select AI
from db_utils import generate_sql_from_prompt, execute_generated_sql
from mcp_utils import create_server, run_server
from utils import get_console_logger

from config import (
    DEBUG,
    # select ai
    SELECT_AI_PROFILE,
)


logger = get_console_logger()

mcp = create_server("OCI Select AI MCP server")


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
# results are wrapped
#
@mcp.tool
def generate_sql(user_request: str) -> Dict[str, Any]:
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
    if DEBUG:
        logger.info("Called generate_sql...")

    try:
        results = generate_sql_from_prompt(SELECT_AI_PROFILE, user_request)
    except Exception as e:
        logger.error("Error generating SQL for request %s: %s", user_request, e)
        results = {"error": str(e)}

    return results


@mcp.tool
def execute_sql(sql: str) -> Dict[str, Any]:
    """
    Execute the SQL statement generated
    """
    if DEBUG:
        logger.info("Called execute_sql...")
    try:
        results = execute_generated_sql(sql)
    except Exception as e:
        logger.error("Error executing SQL %s: %s", sql, e)
        results = {"error": str(e)}

    return results


#
# Run the Select AI MCP server
#
if __name__ == "__main__":
    run_server(mcp)
