"""
Semantic Search exposed as an MCP tool
This verion use stdio (local) as transport

Author: L. Saetta
License: MIT

This one requires, if enabled, that a token is generated using the libray PyJWT.
See the associated client
"""

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

from utils import get_console_logger
from oci_models import get_embedding_model, get_oracle_vs
from db_utils import get_connection, list_collections, list_books_in_collection

from config import DEBUG, EMBED_MODEL_TYPE

logger = get_console_logger()

# local, stdio, to test Claude integration
TRANSPORT = "stdio"

mcp = FastMCP("Demo Semantic Search as MCP server")


#
# Helper functions
#


#
# MCP tools definition
#
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

            # (L.S.) we could additionally plug a reranker here

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

    try:
        books = list_books_in_collection(collection_name)
        return books
    except Exception as e:
        logger.error("Error getting books in collection: %s", e)
        return []


if __name__ == "__main__":
    mcp.run(
        transport=TRANSPORT,
    )
