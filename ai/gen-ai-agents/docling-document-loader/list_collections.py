"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Script to list all collections (tables with VECTOR type columns)
    in the connected database schema.
"""

from db_utils import get_db_connection
from oraclevs_4_db_loading import OracleVS4DBLoading

from utils import get_console_logger

# handle input for collection_name from command line
logger = get_console_logger()

with get_db_connection() as conn:
    coll_list = OracleVS4DBLoading.list_collections(conn)

logger.info("")
logger.info("List of collections:")
logger.info("")

for coll in coll_list:
    logger.info("* %s", coll)

logger.info("")
