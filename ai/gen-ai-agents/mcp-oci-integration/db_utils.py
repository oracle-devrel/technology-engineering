"""
File name: db_utils.py
Author: Luigi Saetta
Date last modified: 2025-07-30
Python Version: 3.11

Description:
    This module contains utility functions for database operations,


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

import re
from typing import List, Tuple, Optional, Any, Dict
import decimal
import datetime
import oracledb

from utils import get_console_logger
from config import DEBUG
from config_private import CONNECT_ARGS

logger = get_console_logger()


#
# Helpers
#
def get_connection():
    """
    get a connection to the DB
    """
    return oracledb.connect(**CONNECT_ARGS)


def read_lob(value: Any) -> Optional[str]:
    """
    Return a Python string from an oracledb LOB (CLOB) or a plain value.
    If value is None, returns None.
    """
    if value is None:
        return None
    # oracledb returns CLOBs as LOB objects; read() -> str
    if isinstance(value, oracledb.LOB):
        return value.read()
    # Sometimes drivers may already return a str
    return str(value)


def normalize_sql(sql_text: str) -> str:
    """
    Strip trailing semicolons and whitespace to avoid ORA-00911 in driver.
    """
    return sql_text.strip().rstrip(";\n\r\t ")


def is_safe_select(sql_text: str) -> bool:
    """
    Minimal safety check: only allow pure SELECTs (no DML/DDL/PLSQL).
    """
    s = sql_text.strip().upper()
    if not s.startswith("SELECT "):
        return False
    forbidden = r"\b(INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|CREATE|GRANT|REVOKE|TRUNCATE|BEGIN|EXEC|CALL)\b"
    return not re.search(forbidden, s)


def _to_jsonable(value: Any):
    # Convert DB/native types → JSON-safe
    if value is None:
        return None
    if isinstance(value, oracledb.LOB):
        return value.read()  # CLOB/BLOB → str/bytes; CLOB becomes str
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()  # or base64 if you prefer
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        # choose float or str; str preserves precision
        return float(value)
    # Tuples/lists/sets inside cells (rare) → list
    if isinstance(value, (tuple, set)):
        return list(value)
    return value


def list_collections():
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
    _collections = []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            for row in rows:
                _collections.append(row[0])

    return sorted(_collections)


def list_books_in_collection(collection_name: str) -> list:
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
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            list_books = []
            for row in rows:
                list_books.append((row[0], row[1]))

    return sorted(list_books)


def fetch_text_by_id(id: str, collection_name: str) -> str:
    """
    Given the ID of a chunk return the text
    """
    sql = """
    SELECT TEXT, json_value(METADATA, '$.source')
    FROM {collection_name}
    WHERE ID = :id
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.format(collection_name=collection_name),
                {"id": id},
            )

            # we expect 0 or 1 rows
            row = cursor.fetchone()
            if row:
                clob = row[0]
                text_value = clob.read() if clob is not None else None
                source = row[1]
            else:
                source = None
                text_value = None

    return {"text_value": text_value, "source": source}


# ---------------------------
# Select AI utilities
# ---------------------------
def generate_sql_from_prompt(profile_name: str, prompt: str) -> str:
    """
    Use DBMS_CLOUD_AI.GENERATE to get the SQL for a natural language prompt.
    Returns the SQL as a Python string (CLOB -> .read()).
    """
    stmt = """
        SELECT DBMS_CLOUD_AI.GENERATE(
                 prompt       => :p,
                 profile_name => :prof,
                 action       => 'showsql'
               )
        FROM dual
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(stmt, {"p": prompt, "prof": profile_name})
            # CLOB (LOB) or str
            raw = cursor.fetchone()[0]
            sql_text = read_lob(raw) or ""
            return normalize_sql(sql_text)


def execute_generated_sql(
    generated_sql: str, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute the SQL and return a JSON-serializable dict:
      {
        "columns": [ ... ],
        "rows": [ [ ... ], ... ],
        "sql": "..."
      }
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(generated_sql)

            columns: List[str] = [d[0] for d in cursor.description]

            # Fetch
            raw_rows = cursor.fetchmany(limit) if limit else cursor.fetchall()

            # Normalize every cell to JSON-safe
            rows: List[List[Any]] = [
                [_to_jsonable(cell) for cell in row] for row in raw_rows
            ]

            return {
                "columns": columns,
                "rows": rows,  # list of lists (JSON arrays)
                "sql": generated_sql,  # useful for logging/debug
            }


def run_select_ai(
    prompt: str, profile_name: str, limit: Optional[int] = None
) -> Tuple[List[str], List[tuple], str]:
    """
    Generate SQL via Select AI for the given prompt, execute it, and return:
      (columns, rows, generated_sql)

    If 'limit' is provided, fetch at most that many rows.
    """
    generated_sql = generate_sql_from_prompt(profile_name, prompt)

    if DEBUG:
        logger.info(generated_sql)

    # if not is_safe_select(generated_sql):
    # raise ValueError("Refusing to execute non-SELECT SQL generated by Select AI.")

    return execute_generated_sql(prompt, limit)
