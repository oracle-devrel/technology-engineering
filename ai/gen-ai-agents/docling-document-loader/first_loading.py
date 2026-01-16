"""
Batch loading

Create a new collection and load a set of pdf
Can be used ONLY for a new collection.

sept 2024: refactored to reduce dependencies
"""

import os
import sys
import re
import argparse
from glob import glob
from langchain_community.vectorstores.utils import DistanceStrategy
from oraclevs_4_db_loading import OracleVS4DBLoading
from docling_utils import pdf_file_to_chunks, chunks_to_langchain_documents
from oci_models import get_embedding_model
from db_utils import get_db_connection
from utils import get_console_logger, compute_stats
from config import CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL_ID


def get_list_collections():
    """
    get the list of existing collections
    """
    with get_db_connection() as _conn:
        _collection_list = OracleVS4DBLoading.list_collections(_conn)

    return _collection_list


_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_$#]*$")


def _assert_safe_identifier(name: str) -> str:
    """
    Validate an Oracle identifier (simple, unquoted).

    This prevents SQL injection since identifiers cannot be bound.
    """
    n = name.strip().upper()
    if not _IDENTIFIER_RE.match(n):
        raise ValueError(f"Unsafe or invalid Oracle identifier: {name!r}")
    return n


def _escape_sql_string_literal(value: str) -> str:
    """
    Escape a Python string for use as a single-quoted Oracle SQL literal.
    """
    return value.replace("'", "''")


def annotate_collection_table(
    conn,
    table_name: str,
    embedding_model: str,
) -> None:
    """
    Annotate an Oracle table with the embedding model used for the collection.

    The annotation is stored as a table COMMENT, e.g.:

        RAG collection metadata: embedding_model=openai.text-embedding-3-large

    Notes:
        - Oracle does NOT allow bind variables in COMMENT statements.
        - The table name must be a safe, unquoted identifier.

    Args:
        conn: An open oracledb connection.
        table_name: Name of the collection table.
        embedding_model: Identifier of the embedding model used.
    """
    safe_table = _assert_safe_identifier(table_name)
    comment = f"RAG collection metadata: embedding_model={embedding_model}"
    comment_sql = _escape_sql_string_literal(comment)

    sql = f"COMMENT ON TABLE {safe_table} IS '{comment_sql}'"

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()


#
# Main
#

# handle input for new_collection_name from command line
parser = argparse.ArgumentParser(description="Document batch loading.")

parser.add_argument("new_collection_name", type=str, help="New collection name.")
parser.add_argument("books_dir", type=str, help="Dir with the books to load.")

args = parser.parse_args()

new_collection_name = args.new_collection_name
BOOKS_DIR = args.books_dir

logger = get_console_logger()

logger.info("")
logger.info("Batch loading books in collection %s ...", new_collection_name)
logger.info("")

# init models
embed_model = get_embedding_model()

# check that the collection doesn't exist yet
collection_list = get_list_collections()

if new_collection_name in collection_list:
    logger.info("")
    logger.error("Error: collection %s already exist!", new_collection_name)
    logger.error("Exiting !")
    logger.info("")

    sys.exit(-1)

logger.info("")

# the list of books to be loaded
books_list = glob(BOOKS_DIR + "/*.pdf")

logger.info("These books will be loaded:")
for book in books_list:
    logger.info(book)

logger.info("")

logger.info("Parameters used for chunking:")
logger.info("Chunk size: %s chars", CHUNK_SIZE)
logger.info("Chunk overlap: %s chars", CHUNK_OVERLAP)
logger.info("")

docs = []

for book in books_list:
    logger.info("Chunking: %s", book)
    # get the file extension
    _, file_ext = os.path.splitext(book)

    if file_ext == ".pdf":
        docs += pdf_file_to_chunks(
            book,
            max_chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP,
            add_chunk_header=True,
        )

# transform in Langchain docs
docs = chunks_to_langchain_documents(docs)

if len(docs) > 0:
    logger.info("")
    logger.info(
        "Embedding and loading documents in collection %s ...", new_collection_name
    )

    with get_db_connection() as conn:
        OracleVS4DBLoading.from_documents(
            client=conn,
            documents=docs,
            embedding=embed_model,
            table_name=new_collection_name,
            distance_strategy=DistanceStrategy.COSINE,
        )

        # add as a comment the name of the embedding model
        annotate_collection_table(conn, new_collection_name, EMBED_MODEL_ID)

    logger.info("Loading completed.")
    logger.info("")

    mean, stdev, perc_75 = compute_stats(docs)

    logger.info("")
    logger.info("Statistics on the distribution of chunks' lengths:")
    logger.info("Total num. of chunks loaded: %s", len(docs))
    logger.info("Avg. length: %s (chars)", mean)
    logger.info("Std dev: %s (chars)", stdev)
    logger.info("75-perc: %s (chars)", perc_75)
    logger.info("")

else:
    logger.info("No document to load!")
    logger.info("")
