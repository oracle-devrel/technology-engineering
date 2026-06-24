"""
Semantic Search exposed as an MCP tool

Author: L. Saetta
License: MIT

This one requires, if enabled, that a token is generated using the libray PyJWT.
See the associated client
"""

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from utils import get_console_logger
from jwt_utils import get_token_from_headers, verify_jwt_token
from oci_models import get_embedding_model, get_oracle_vs
from db_utils import get_connection, list_collections, list_books_in_collection

from config import DEBUG, EMBED_MODEL_TYPE
from config import TRANSPORT, HOST, PORT, ENABLE_JWT_TOKEN

logger = get_console_logger()

mcp = FastMCP("Demo Semantic Search as MCP server")


#
# Helper functions
#
def validate_token():
    """
    Validate the JWT token if enabled
    """
    headers = get_http_headers(include_all=True)

    # check that a valid JWT is provided
    if ENABLE_JWT_TOKEN:
        if DEBUG:
            logger.info("Headers: %s", headers)

        # the header has the format: Bearer <token>
        token = get_token_from_headers(headers)
        logger.info("Received auth header: %s", token)

        verify_jwt_token(token)


@mcp.tool
def semantic_search(
    query: Annotated[
        str, Field(description="The search query to find relevant documents.")
    ],
    top_k: Annotated[int, Field(description="TOP_K parameter for search")] = 5,
    collection_name: Annotated[
        str, Field(description="The name of DB table")
    ] = "BOOKS",
) -> dict:
    """
    Perform a semantic search based on the provided query.
    Args:
        query (str): The search query.
        top_k (int): The number of top results to return.
        collection_name (str): The name of the collection (DB table) to search in.
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    # to handle auth using JWT tokens
    validate_token()

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
        logger.error("Error in MCP similarity search: %s", e)
        error = str(e)
        return {"error": error}

    result = {"relevant_docs": relevant_docs}

    return result


@mcp.tool
def get_collections() -> list:
    """
    Get the list of collections (DB tables) available in the Oracle Vector Store.
    Returns:
        list: A list of collection names.
    """
    # to handle auth using JWT tokens
    validate_token()

    return list_collections()


@mcp.tool
def get_books_in_collection(
    collection_name: Annotated[
        str, Field(description="The name of the collection (DB table) to search in.")
    ] = "BOOKS",
) -> list:
    """
    Get the list of books in a specific collection.
    Args:
        collection_name (str): The name of the collection (DB table) to search in.
    Returns:
        list: A list of book titles in the specified collection.
    """
    # check that a valid JWT is provided
    validate_token()

    try:
        books = list_books_in_collection(collection_name)
        return books
    except Exception as e:
        logger.error("Error getting books in collection: %s", e)
        return []


if __name__ == "__main__":
    mcp.run(
        transport=TRANSPORT,
        # Bind to all interfaces
        host=HOST,
        port=PORT,
        log_level="INFO",
    )
