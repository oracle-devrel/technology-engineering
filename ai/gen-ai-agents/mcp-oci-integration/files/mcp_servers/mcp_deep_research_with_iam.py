"""
File name: mcp_deep_research_with_iam.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for deep research capabilities using IAM authentication.
    It likely provides tools for advanced searches, combining semantic vector store queries, internet research, or RAG pipelines
    with OCI integration, returning structured results with references and summaries.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_deep_research_with_iam import deep_research  # Assuming a primary tool name

        results = deep_research("in-depth query on AI ethics")
        # Or run the server: python mcp_deep_research_with_iam.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and relies on IAM-authenticated services like Oracle Vector Store or search utilities.
    Tools return dictionaries with research outputs for easy integration with MCP agents.

Warnings:
    This module is in development and may change in future versions. Ensure IAM authentication is properly configured
    and handle potential errors related to external services, rate limits, or complex query processing.
"""

from typing import Annotated, Dict, Any
from pydantic import Field


# to verify the JWT token
from fastmcp.server.dependencies import get_http_headers

from utils import get_console_logger
from oci_models import get_embedding_model, get_oracle_vs
from db_utils import (
    get_connection,
    list_collections,
    list_books_in_collection,
    fetch_text_by_id,
)
from mcp_utils import create_server, run_server
from config import EMBED_MODEL_TYPE, DEFAULT_COLLECTION
from config import DEBUG, ENABLE_JWT_TOKEN

logger = get_console_logger()

# create the app
# cool, the OAUTH 2.1 provider is pluggable
mcp = create_server("Demo Deep Search as MCP server")


#
# Helper functions
#
def log_headers():
    """
    if DEBUG log the headers in the HTTP request
    """
    if DEBUG:
        headers = get_http_headers(include_all=True)
        logger.info("Headers: %s", headers)


#
# MCP tools definition
#
@mcp.tool
def search(
    query: Annotated[
        str, Field(description="The deep search query to find relevant documents.")
    ],
    top_k: Annotated[int, Field(description="TOP_K parameter for search")] = 10,
    collection_name: Annotated[
        str, Field(description="The name of DB table")
    ] = DEFAULT_COLLECTION,
) -> dict:
    """
    Perform a deep search based on the provided query.
    Args:
        query (str): The search query.
        top_k (int): The number of top results to return.
        collection_name (str): The name of the collection (DB table) to search in.
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    # here only log, no verification here, delegated to AuthProvider
    if ENABLE_JWT_TOKEN:
        log_headers()

    try:
        # must be the same embedding model used during load in the Vector Store
        embed_model = get_embedding_model(EMBED_MODEL_TYPE)

        # get a connection to the DB and init VS
        with get_connection() as conn:
            v_store = get_oracle_vs(
                conn=conn,
                collection_name=collection_name,
                embed_model=embed_model,
            )
            relevant_docs = v_store.similarity_search(query=query, k=top_k)

            if DEBUG:
                logger.info("Result from the similarity search:")
                logger.info(relevant_docs)

    except Exception as e:
        logger.error("Error in MCP deep search: %s", e)
        error = str(e)
        return {"error": error}

    # process relevant docs to be OpenAI compliant
    results = []
    for doc in relevant_docs:
        result = {
            "id": doc.metadata["ID"],
            "title": doc.metadata["source"],
            # here we return a snippet of text
            "text": doc.page_content,
            "url": "",
        }
        results.append(result)

        if DEBUG:
            logger.info(result)

    return {"results": results}


@mcp.tool
def fetch(
    id: Annotated[
        str, Field(description="The ID of the document as returned by search call.")
    ],
    collection_name: str = DEFAULT_COLLECTION,
) -> Dict[str, Any]:
    """
    Retrieve complete document content by ID for detailed
    analysis and citation. This tool fetches the full document
    content from Oracle 23AI. Use this after finding
    relevant documents with the search tool to get complete
    information for analysis and proper citation.

    Args:
        id: doc ID from Vector Store. It is the value retrieved by search, NOT the document name.

    Returns:
        Complete document with id, title, full text content,
        optional URL, and metadata

    Raises:
        ValueError: If the specified ID is not found
    """
    if not id:
        raise ValueError("Document ID is required")

    # execute the query on the DB
    result = fetch_text_by_id(id=id, collection_name=collection_name)

    # formatting result as required by OpenAI specs
    # see: https://platform.openai.com/docs/mcp#create-an-mcp-server
    # we could add metadata
    result = {
        "id": id,
        "title": result["source"],
        "text": result["text_value"],
        "url": "",
        "metadata": None,
    }

    if DEBUG:
        logger.info(result)

    return result


@mcp.tool
def get_collections() -> list:
    """
    Get the list of collections (DB tables) available in the Oracle Vector Store.
    Returns:
        list: A list of collection names.
    """
    # check that a valid JWT is provided
    if ENABLE_JWT_TOKEN:
        log_headers()

    return list_collections()


@mcp.tool
def get_books_in_collection(
    collection_name: Annotated[
        str, Field(description="The name of the collection (DB table) to search in.")
    ] = DEFAULT_COLLECTION,
) -> list:
    """
    Get the list of books in a specific collection.
    Args:
        collection_name (str): The name of the collection (DB table) to search in.
    Returns:
        list: A list of book titles in the specified collection.
    """
    # check that a valid JWT is provided
    if ENABLE_JWT_TOKEN:
        log_headers()

    try:
        books = list_books_in_collection(collection_name)
        return books
    except Exception as e:
        logger.error("Error getting books in collection: %s", e)
        return []


#
# Run the MCP server
#
if __name__ == "__main__":
    if DEBUG:
        LOG_LEVEL = "DEBUG"
    else:
        LOG_LEVEL = "INFO"

    # this one takes care of HOST, PORT settings
    run_server(mcp)
