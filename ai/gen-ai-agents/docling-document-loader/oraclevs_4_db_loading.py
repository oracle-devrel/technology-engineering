"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Extension of OracleVS class to add utility methods for database loading
    and management specific to Oracle Vector Search.
"""

import re
from collections import Counter
from oracledb import Connection, DB_TYPE_VECTOR

# moved to Langchain 1.x compatibility
from langchain_oracledb import OracleVS

from utils import get_console_logger
from config import DEBUG

logger = get_console_logger()

# to avoid SQL injection
_VALID_IDENT = re.compile(r"^[A-Z][A-Z0-9_$#]*$")


def _safe_ident(name: str) -> str:
    """
    Validate and return a safe Oracle identifier
    """
    n = name.strip().upper()
    if not _VALID_IDENT.fullmatch(n):
        raise ValueError(f"Invalid Oracle identifier: {name!r}")
    return n


class OracleVS4DBLoading(OracleVS):
    """
    This class extends OracleVS and has been defined to add utility methods
    """

    @classmethod
    def list_collections(cls, connection: Connection):
        """
        return a list of all collections (tables) with a type vector
        in the schema in use
        """

        query = """
                SELECT DISTINCT table_name
                FROM user_tab_columns
                WHERE data_type = 'VECTOR'
                ORDER by table_name ASC
                """

        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            list_collections = []
            for row in rows:
                list_collections.append(row[0])

        return list_collections

    @classmethod
    def list_documents_in_collection(cls, connection: Connection, collection_name: str):
        """ "
        get the list of documents in the collection
        taken from metadata
        expect metadata contains source
        """
        collection_name = _safe_ident(collection_name)

        query = f"""
                SELECT DISTINCT json_value(METADATA, '$.source') AS books
                FROM {collection_name}
                ORDER by books ASC
                """
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            list_books = []
            for row in rows:
                list_books.append(row[0])

        return list_books

    @classmethod
    def analyze_collection(cls, connection: Connection, collection_name: str) -> str:
        """
        analyze completely a collection and return a text containing a short report
        """
        collection_name = _safe_ident(collection_name)

        sql = f"SELECT * FROM {collection_name}"

        with connection.cursor() as cur:
            cur.execute(sql)

            descs = cur.description  # column metadata

            records = 0
            dim_counter = Counter()
            format_counter = Counter()
            # here we analyse the vector columns
            # we compute the number of records
            # and the number of different dimensions and formats
            for row in cur:
                records += 1
                for idx, _ in enumerate(row):
                    info = descs[idx]
                    if info.type_code == DB_TYPE_VECTOR:
                        dims = info.vector_dimensions
                        fmt = info.vector_format
                        dim_counter[dims] += 1
                        format_counter[fmt] += 1

        # output
        report = f"Analyzed collection: {collection_name}\n"
        report += f"    Total chunks fetched: {records}\n"
        report += f"    Vector dimensions seen (count): {dict(dim_counter)}\n"
        report += f"    Vector formats seen (count): {dict(format_counter)}\n"

        return report

    @classmethod
    def delete_documents(
        cls, connection: Connection, collection_name: str, doc_names: list
    ):
        """
        doc_names: list of names of docs to drop
        """
        for doc_name in doc_names:
            sql = f"""
                  DELETE FROM {collection_name}
                  WHERE json_value(METADATA, '$.source') = :doc
                  """

            if DEBUG:
                logger.info("Drop %s", doc_name)
                logger.info(sql)

            cur = connection.cursor()

            cur.execute(sql, [doc_name])

            cur.close()

        connection.commit()

    @classmethod
    def drop_collection(cls, connection: Connection, collection_name: str):
        """
        drop a collection
        """
        collection_name = _safe_ident(collection_name)

        sql = f"DROP TABLE {collection_name}"

        cur = connection.cursor()

        cur.execute(sql)
