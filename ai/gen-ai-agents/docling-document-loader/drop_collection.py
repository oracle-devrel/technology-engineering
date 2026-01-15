"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Utility to drop an existing collection

    beware: check what you're doing
"""

import argparse

from db_utils import get_db_connection
from oraclevs_4_db_loading import OracleVS4DBLoading

from utils import get_console_logger


#
# Main
#

logger = get_console_logger()

# handle input for collection_name from command line
parser = argparse.ArgumentParser(description="Document batch loading.")

parser.add_argument("collection_name", type=str, help="collection name to drop.")

args = parser.parse_args()
collection_name = args.collection_name

logger.info("")
logger.info("Dropping collection: %s", collection_name)
logger.info("")

with get_db_connection() as conn:
    OracleVS4DBLoading.drop_collection(conn, collection_name)

logger.info("Collection dropped !")
logger.info("")
