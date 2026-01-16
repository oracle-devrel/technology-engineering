"""
Author: Luigi Saetta
Date last modified: 2026-01-15
Python Version: 3.11
License: MIT

Description:
    Load additional docs in an **existing** collection

    Fow now only pdf
"""

import sys
import os
import argparse
from glob import glob

from db_utils import get_db_connection
from oraclevs_4_db_loading import OracleVS4DBLoading
from docling_utils import pdf_file_to_chunks, chunks_to_langchain_documents
from oci_models import get_embedding_model
from utils import get_console_logger
from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = get_console_logger()


def get_list_collections():
    """
    get the list of existing collections
    """
    with get_db_connection() as _conn:
        _collection_list = OracleVS4DBLoading.list_collections(_conn)

    return _collection_list


def get_documents(coll_name: str):
    """
    get the list of already loaded documents in the collection
    """
    with get_db_connection() as _conn:
        _documents_list = OracleVS4DBLoading.list_documents_in_collection(
            _conn, coll_name
        )

    return _documents_list


def get_embeddings_model():
    """
    Return the embedding model to use to generate embeddings
    """
    return get_embedding_model()


# handle input for collection_name from command line
parser = argparse.ArgumentParser(description="Document batch loading.")

parser.add_argument(
    "collection_name", type=str, help="collection name to add documents to."
)
parser.add_argument("docs_dir", type=str, help="Dir with the documents to load.")

args = parser.parse_args()
collection_name = args.collection_name
DOCUMENTS_DIR = args.docs_dir

# check if collection exist
collection_list = get_list_collections()

if collection_name not in collection_list:
    logger.info("")
    logger.error("Collection %s doesn't exist, exiting!", collection_name)
    logger.info("")

    sys.exit(-1)

# check for existing documents in collection
documents_list = get_documents(collection_name)

# for now only pdf
new_documents_list = glob(DOCUMENTS_DIR + "/*.pdf")
logger.info("")

docs = []

for doc_pathname in new_documents_list:
    # check if already loaded

    # strips path
    if os.path.basename(doc_pathname) not in documents_list:
        logger.info("Converting and chunking %s ...", doc_pathname)

        # get the file extension
        _, file_ext = os.path.splitext(doc_pathname)

        if file_ext == ".pdf":
            docs += pdf_file_to_chunks(
                doc_pathname,
                max_chunk_size=CHUNK_SIZE,
                overlap=CHUNK_OVERLAP,
                add_chunk_header=True,
            )
    else:
        logger.info("Document %s already loaded, skipping...", doc_pathname)

# transform in Langchain docs
docs = chunks_to_langchain_documents(docs)

# embed and save to  DB
if len(docs) > 0:
    with get_db_connection() as conn:
        logger.info("Loading documents list...")

        oracle_vs = OracleVS4DBLoading(
            client=conn,
            table_name=collection_name,
            embedding_function=get_embeddings_model(),
        )

        oracle_vs.add_documents(docs)

logger.info("Loading completed!")
