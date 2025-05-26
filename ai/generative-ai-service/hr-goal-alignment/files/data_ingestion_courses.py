# Copyright (c) 2025 Oracle and/or its affiliates.
import logging
import sys
import oracledb
import config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # <- write logs into a file called app.log
        logging.StreamHandler()          # <- also allow printing to the console (terminal)
    ]
)
logger = logging.getLogger(__name__)

try:
    print("Connecting to the database...")
    oci_db_connection = oracledb.connect(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dsn=config.DB_DSN
    )
    print("Connection successful.")
    cursor = oci_db_connection.cursor()
except ImportError:
    logging.error("Could not import get_db_connection from utils.py. Ensure it exists.")
    sys.exit(1)

from course_vector_utils import CourseVectorStore
import config # Project's config file



def main():
    """
    Connects to the database, initializes the CourseVectorStore,
    and populates it with data from the course catalog Excel file.
    """
    logger.info("Starting course data ingestion...")
    db_connection = None
    try:
        # Get database connection using the project's utility function
        logger.info("Connecting to the database...")
        db_connection = oci_db_connection
        logger.info("Database connection successful.")

        # Initialize the vector store utility
        logger.info("Initializing CourseVectorStore...")
        vector_store_util = CourseVectorStore(db_connection)

        # Define the path to the Excel file
        excel_file_path = "data/Full_Company_Training_Catalog.xlsx"
        logger.info(f"Processing Excel file: {excel_file_path}")

        # Add courses from the Excel file to the vector store
        vector_store_util.add_courses_from_excel(excel_file_path)

        logger.info("Course data ingestion completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during data ingestion: {e}", exc_info=True)
        sys.exit(1) # Exit with error code

    finally:
        # Ensure the database connection is closed
        if db_connection:
            try:
                db_connection.close()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}", exc_info=True)

if __name__ == "__main__":
    main()
