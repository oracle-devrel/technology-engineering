"""
Semantic Search exposed as an MCP tool
with added security with OCI IAM and JWT tokens

Author: L. Saetta
License: MIT
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
        str, Field(description="The name of the collection to search in.")
    ] = DEFAULT_COLLECTION,
) -> list:
    """
    Get the list of books in a specific collection.
    Args:
        collection_name (str): The name of the collection to search in.
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
