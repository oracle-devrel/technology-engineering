"""
File name: mcp_semantic_search_with_iam.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for semantic search using Oracle Vector Store
    with IAM authentication. It provides tools to list available collections, retrieve documents in a specific collection,
    and perform semantic searches with query embeddings, returning relevant documents and metadata.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_semantic_search_with_iam import search

        results = search("query text", "BOOKS")
        # Or run the server: python mcp_semantic_search_with_iam.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and relies on OCI Vector Store utilities for embeddings and IAM auth.
    Tools return structured dictionaries for easy integration with MCP agents; default collection is "BOOKS" if not specified.

Warnings:
    This module is in development and may change in future versions. Ensure IAM authentication is properly configured
    and handle potential errors related to vector store connections or query limits.
"""

from typing import Annotated
from pydantic import Field

from fastmcp.server.dependencies import get_http_headers

from utils import get_console_logger
from oci_models import get_embedding_model, get_oracle_vs
from db_utils import get_connection, list_collections, list_books_in_collection
from mcp_utils import create_server, run_server
from config import EMBED_MODEL_TYPE, DEFAULT_COLLECTION, TOP_K
from config import DEBUG, ENABLE_JWT_TOKEN

logger = get_console_logger()


# create the app
# cool, the OAUTH 2.1 provider is pluggable
mcp = create_server("Demo Semantic Search as MCP server")


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
def get_collections() -> list:
    """
    Get the list of collections of documents available in the Oracle Vector Store.
    Returns:
        list: A list of collection names.
    """
    if ENABLE_JWT_TOKEN:
        log_headers()

    return list_collections()


@mcp.tool
def get_documents_in_collection(
    collection_name: Annotated[
        str, Field(description="The name of the collection to search in.")
    ] = DEFAULT_COLLECTION,
) -> list:
    """
    Get the list of documents in a specific collection.
    Args:
        collection_name (str): The name of the collection to search in.
    Returns:
        list: A list of documents titles in the specified collection.
    """
    if ENABLE_JWT_TOKEN:
        log_headers()

    try:
        books = list_books_in_collection(collection_name)
        return books
    except Exception as e:
        logger.error("Error getting books in collection: %s", e)
        return []


@mcp.tool
def search(
    query: Annotated[
        str, Field(description="The search query to find relevant documents.")
    ],
    collection_name: Annotated[
        str, Field(description="The name of DB table")
    ] = DEFAULT_COLLECTION,
) -> dict:
    """
    Perform a semantic search based on the provided query.
    Args:
        query (str): The search query.
        collection_name (str): The name of the collection to search in.
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    # removed top_k as param, use config value

    # here only log
    if ENABLE_JWT_TOKEN:
        log_headers()
        # no verification here, delegated to BearerAuthProvider

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
            relevant_docs = v_store.similarity_search(query=query, k=TOP_K)

            # we can add here a reranking step if needed

            if DEBUG:
                logger.info("Result from the similarity search:")
                logger.info(relevant_docs)

    except Exception as e:
        logger.error("Error in MCP similarity search: %s", e)
        error = str(e)
        return {"error": error}

    result = {"relevant_docs": relevant_docs}

    return result


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
