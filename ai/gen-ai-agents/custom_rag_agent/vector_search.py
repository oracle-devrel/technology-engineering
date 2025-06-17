"""
File name: vector_search.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module implements the Semantic Sesarch in the agent
    using 23Ai Vector Search


Usage:
    Import this module into other scripts to use its functions.
    Example:
        import config

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

import oracledb
from langchain_core.runnables import Runnable
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS

# integration with APM
from py_zipkin.zipkin import zipkin_span

from agent_state import State
from utils import get_console_logger

from config import (
    AGENT_NAME,
    DEBUG,
    AUTH,
    EMBED_MODEL_ID,
    SERVICE_ENDPOINT,
    COMPARTMENT_ID,
    TOP_K,
)

from config_private import CONNECT_ARGS

logger = get_console_logger()


class SemanticSearch(Runnable):
    """
    Implements Semantic Search for the Agent
    """

    def __init__(self):
        """
        Init
        """

    def get_connection(self):
        """
        get a connection to the DB
        """
        return oracledb.connect(**CONNECT_ARGS)

    def get_embedding_model(self):
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

    @zipkin_span(service_name=AGENT_NAME, span_name="similarity_search")
    def invoke(self, input: State, config=None, **kwargs):
        """
        This method invokes the vector search

        input: the agent state
        """
        collection_name = config["configurable"]["collection_name"]

        relevant_docs = []
        error = None

        standalone_question = input["standalone_question"]

        if DEBUG:
            logger.info("Search question: %s", standalone_question)

        try:
            embed_model = self.get_embedding_model()

            # get a connection to the DB and init VS
            with self.get_connection() as conn:
                v_store = OracleVS(
                    client=conn,
                    table_name=collection_name,
                    distance_strategy=DistanceStrategy.COSINE,
                    embedding_function=embed_model,
                )

                relevant_docs = v_store.similarity_search(
                    query=standalone_question, k=TOP_K
                )

            if DEBUG:
                logger.info("Result from similarity search:")
                logger.info(relevant_docs)

        except Exception as e:
            logger.error("Error in vector_store.invoke: %s", e)
            error = str(e)

        return {"retriever_docs": relevant_docs, "error": error}

    #
    #  Helper functions
    #
    def list_books_in_collection(self, collection_name: str) -> list:
        """
        get the list of books/documents names in the collection
        taken from metadata
        expect metadata contains the field source

        modified to return also the numb. of chunks
        """
        query = f"""
                SELECT DISTINCT json_value(METADATA, '$.source') AS books, 
                count(*) as n_chunks 
                FROM {collection_name}
                group by books
                ORDER by books ASC
                """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

                rows = cursor.fetchall()

                list_books = []
                for row in rows:
                    list_books.append((row[0], row[1]))

        return list_books

    def add_documents(self, docs: list, collection_name: str):
        """
        Add the chunks to an existing collection

        docs is a list of Langchain documents
        """
        try:
            embed_model = self.get_embedding_model()

            with self.get_connection() as conn:
                v_store = OracleVS(
                    client=conn,
                    table_name=collection_name,
                    distance_strategy=DistanceStrategy.COSINE,
                    embedding_function=embed_model,
                )
                v_store.add_documents(docs)
                logger.info("Added docs to collection %s", collection_name)

        except Exception as e:
            logger.error("Error in vector_store.add_documents: %s", e)
            raise e
