"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Script to analyze a collection (table with VECTOR type columns)
    in the connected database schema.
    For now, it is useful to check that we don't mix different vector
    dimensions or formats in the same collection.
"""

import argparse

from db_utils import get_db_connection
from oraclevs_4_db_loading import OracleVS4DBLoading

from utils import get_console_logger

# handle input for collection_name from command line
logger = get_console_logger()

parser = argparse.ArgumentParser(description="Analyzew a collection.")

parser.add_argument("collection_name", type=str, help="collection name.")

args = parser.parse_args()
collection_name = args.collection_name

with get_db_connection() as conn:
    REPORT = OracleVS4DBLoading.analyze_collection(conn, collection_name)

logger.info("")
print("")
print(REPORT)
logger.info("")
