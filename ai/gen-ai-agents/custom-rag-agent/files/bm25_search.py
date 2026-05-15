"""
BM25 Search Engine with Oracle Database
"""

import re
import oracledb
import numpy as np
from rank_bm25 import BM25Okapi
from utils import get_console_logger
from config_private import CONNECT_ARGS

logger = get_console_logger()


class BM25OracleSearch:
    """
    Implments BM25
    """

    def __init__(self, table_name, text_column, batch_size=40):
        """
        Initializes the BM25 search engine with data from an Oracle database.

        :param table_name: Name of the table containing the text
        :param text_column: Column name that contains the text to index
        """
        self.table_name = table_name
        self.text_column = text_column
        self.batch_size = batch_size
        self.texts = []
        self.tokenized_texts = []
        self.bm25 = None
        self.index_data()

    def connect_db(self):
        """
        Establishes a connection to the Oracle database.
        """
        try:
            connection = oracledb.connect(**CONNECT_ARGS)
            return connection
        except oracledb.DatabaseError as e:
            logger.info("Database connection error: %s", e)
            return None

    def fetch_text_data(self):
        """
        Fetches text data from the specified table and column.
        Used to initialize the index.
        """

        _results = []

        with self.connect_db() as conn:
            with conn.cursor() as cursor:
                query = f"SELECT {self.text_column} FROM {self.table_name}"
                cursor.execute(query)

                while True:
                    # Fetch records in batches
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        # Exit loop when no more data
                        break

                    for row in rows:
                        # This is a CLOB object
                        lob_data = row[0]

                        if isinstance(lob_data, oracledb.LOB):
                            # Read LOB content
                            _results.append(lob_data.read())
                        else:
                            # Fallback for non-LOB data
                            _results.append(str(lob_data))

        return _results

    def simple_tokenize(self, text):
        """
        Tokenizes a string by extracting words (alphanumeric sequences).

        :param text: Input text string
        :return: List of lowercase tokens
        """
        return re.findall(r"\w+", text.lower())

    def index_data(self):
        """
        Reads text from the database and prepares BM25 index.
        """
        logger.info("Creating BM25 index...")

        self.texts = self.fetch_text_data()
        self.tokenized_texts = [self.simple_tokenize(text) for text in self.texts]
        self.bm25 = BM25Okapi(self.tokenized_texts)

        logger.info("BM25 index created successfully!")
        logger.info("")

    def search(self, query, top_n=5):
        """
        Performs a BM25 search on the indexed documents.

        :param query: Search query string
        :param top_n: Number of top results to return
        :return: List of tuples (text, score)
        """
        if not self.bm25:
            print("BM25 index not initialized. Please check data indexing.")
            return []

        query_tokens = self.simple_tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = np.argsort(scores)[::-1][:top_n]  # Get top_n results

        _results = [(self.texts[i], scores[i]) for i in ranked_indices]

        return _results


# Example Usage:
# credential are packed in CONNECT_ARGS


def run_test():
    """
    To run a quick test.
    """
    table_name = "BOOKS"
    text_column = "TEXT"

    # create the index
    bm25_search = BM25OracleSearch(table_name, text_column)

    questions = [
        "Chi è Luigi Saetta?",
        "What are the main innovation produced by GPT-4?",
    ]

    for _question in questions:
        results = bm25_search.search(_question, top_n=2)

        # Print search results
        for text, score in results:
            print(f"Score: {score:.2f} - Text: {text}")
            print("")


#
# Main
#
run_test()
