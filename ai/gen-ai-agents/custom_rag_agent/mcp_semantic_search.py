"""
Semantic Search exposed as an MCP tool

Author: L. Saetta
License: MIT
"""

from typing import Annotated
from pydantic import Field
import oracledb
from fastmcp import FastMCP
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS
from utils import get_console_logger

from config import DEBUG
from config import AUTH, EMBED_MODEL_ID, SERVICE_ENDPOINT, COMPARTMENT_ID
from config import TRANSPORT, HOST, PORT
from config_private import CONNECT_ARGS

logger = get_console_logger()

mcp = FastMCP("Demo Semantic Search as MCP server")


#
# Helper functions
#
def get_connection():
    """
    get a connection to the DB
    """
    return oracledb.connect(**CONNECT_ARGS)


def get_embedding_model():
    """
    Create the Embedding Model
    """
    embed_model = OCIGenAIEmbeddings(
        auth_type=AUTH,
        model_id=EMBED_MODEL_ID,
        service_endpoint=SERVICE_ENDPOINT,
        compartment_id=COMPARTMENT_ID,
    )
    return embed_model


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
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    try:
        # must be the same embedding model used during load in the Vector Store
        embed_model = get_embedding_model()

        # get a connection to the DB and init VS
        with get_connection() as conn:
            v_store = OracleVS(
                client=conn,
                table_name=collection_name,
                distance_strategy=DistanceStrategy.COSINE,
                embedding_function=embed_model,
            )

            relevant_docs = v_store.similarity_search(query=query, k=top_k)

            if DEBUG:
                logger.info("Result from similarity search:")
                logger.info(relevant_docs)

    except Exception as e:
        logger.error("Error in vector_store.invoke: %s", e)
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
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT DISTINCT utc.table_name
            FROM user_tab_columns utc
            WHERE utc.data_type = 'VECTOR'
            ORDER BY 1 ASC"""
        )
        collections = [row[0] for row in cursor.fetchall()]
        return collections
    
if __name__ == "__main__":
    mcp.run(
        transport=TRANSPORT,
        # Bind to all interfaces
        host=HOST,
        port=PORT,
        log_level="INFO",
    )
