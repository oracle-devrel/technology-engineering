"""
File name: mcp_internet_search.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for internet search capabilities.
    It provides a tool to perform searches using an LLM (e.g., OpenAI GPT-4o-search-preview) with a prompt template,
    returning key points, summaries, and references from credible sources based on the query.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_internet_search import internet_search

        search_results = internet_search("latest AI advancements")
        # Or run the server: python mcp_internet_search.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and relies on LangChain for prompt handling and OCI models.
    The tool returns a dictionary with 'search_result' containing the formatted output for easy integration with MCP agents.

Warnings:
    This module is in development and may change in future versions. It depends on external LLM services, so ensure API keys
    are configured and handle potential rate limits or availability issues in production.
"""

from typing import Dict, Any

try:
    # LangChain 1.x
    from langchain_core.prompts import PromptTemplate
except ImportError:
    # Pre-1.x
    from langchain.prompts import PromptTemplate

from langchain_core.messages import HumanMessage

from oci_models import get_llm
from mcp_utils import create_server, run_server

# using OpenAI for Internet Search
MODEL_4_SEARCH = "openai.gpt-4o-search-preview"

PROMPT_TEMPLATE_SEARCH = """
You're an expert researcher.

Provide key points and summaries from credible sources about: {topic}.
"""

mcp = create_server("OCI MCP Internet Search")


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
@mcp.tool
def internet_search(query: str) -> Dict[str, Any]:
    """
    Return the result of Internet Search for
    the provided query.

    Args:
        query (str): the request for Internet Search.

    Returns:
        str: text + the references.

    """
    llm = get_llm(model_id=MODEL_4_SEARCH)

    prompt_search = PromptTemplate(
        input_variables=["topic"], template=PROMPT_TEMPLATE_SEARCH
    ).format(topic=query)

    result = llm.invoke([HumanMessage(content=prompt_search)]).content

    return {"search_result": result}


#
# Run the MCP server
#
if __name__ == "__main__":
    run_server(mcp)
