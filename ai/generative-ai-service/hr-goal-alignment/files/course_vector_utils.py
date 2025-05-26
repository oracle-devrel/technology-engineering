# Copyright (c) 2025 Oracle and/or its affiliates.
from typing import List, Dict, Optional
from langchain_community.vectorstores import OracleVS
import os
import logging
import oci
import pandas as pd
from pathlib import Path
from typing import List

from langchain_community.vectorstores import OracleVS
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import DistanceStrategy

# Use the project's config file
import config
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # <- write logs into a file called app.log
        logging.StreamHandler()          # <- also allow printing to the console (terminal)
    ]
)
logger = logging.getLogger(__name__)


# Configuration will be read from the project's config.py


class CourseVectorStore:
    def __init__(self, db_connection):
        """
        Initializes the CourseVectorStore.

        Args:
            db_connection: An active Oracle database connection object.
        """
        logger.info("Initializing CourseVectorStore...")
        self.db_conn = db_connection
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_vector_store()
        logger.info("CourseVectorStore initialized.")

    def _initialize_embeddings(self) -> OCIGenAIEmbeddings:
        # Read config from the project's config module
        oci_config = oci.config.from_file(profile_name=config.OCI_CONFIG_PROFILE)
        return OCIGenAIEmbeddings(
            model_id=config.EMBEDDING_MODEL_ID,
            service_endpoint=config.OCI_SERVICE_ENDPOINT,
            compartment_id=config.OCI_COMPARTMENT_ID,
            auth_type="API_KEY",
            auth_profile=config.OCI_CONFIG_PROFILE # Use config module
        )

    def _initialize_vector_store(self) -> OracleVS:
        # Use the passed-in connection and project config
        return OracleVS(
            client=self.db_conn, # Use the connection passed in __init__
            embedding_function=self.embeddings, # Use the embeddings initialized in __init__
            table_name=config.VECTOR_TABLE_NAME, # Use table name from project config
            distance_strategy=DistanceStrategy.COSINE
        )

    # LLM initialization removed.
    # Retrieval logic specific to reports removed.

    def add_courses_from_excel(self, excel_path: str):
        """
        Loads course data from an Excel file, processes each row,
        and adds it to the Oracle vector store.
        """
        logger.info(f"Loading course data from: {excel_path}")

        if not os.path.exists(excel_path):
            logger.error(f"Excel file '{excel_path}' not found. Skipping document loading.")
            return

        try:
            # Use pandas to read structured Excel data (instead of UnstructuredExcelLoader as it was before)
            df = pd.read_excel(excel_path)
            logger.info(f"Excel file loaded successfully. Number of rows: {len(df)}")
        except Exception as e:
            logger.error(f"Error reading Excel file {excel_path}: {e}", exc_info=True)
            return

        if df.empty:
            logger.warning("Excel file is empty. No data to process.")
            return

        # Define expected Excel columns and their mapping to metadata keys
        column_mapping = {
            "Course_id": "COURSE_ID",
            "Name": "NAME",
            "University": "UNIVERSITY",
            "Difficulty Level": "DIFFICULTYLEVEL",
            "Rating": "RATING",
            "Url": "URL",
            "Syllabus": "SYLLABUS",
            "Description": "DESCRIPTION",
            "Skills": "SKILLS",
        }

        processed_docs = []
        for _, row in df.iterrows():
            # Build page content
            name = row.get("Name", "N/A")
            description = row.get("Description", "N/A")
            page_content = f"Course: {name}\nDescription: {description}"

            # Build metadata dictionary
            metadata = {}
            for excel_col, meta_key in column_mapping.items():
                metadata[meta_key] = row.get(excel_col, "N/A")

            processed_docs.append(Document(page_content=page_content, metadata=metadata))

        logger.info(f"Created {len(processed_docs)} documents from Excel.")

        if not processed_docs:
            logger.warning("No documents processed after row parsing. Check Excel content.")
            return

        logger.info(f"Processing {len(processed_docs)} documents for splitting.")

        # Split documents into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
        splits = text_splitter.split_documents(processed_docs)

        # Remove duplicates based on page content
        unique_chunks = {chunk.page_content: chunk for chunk in splits}
        splits = list(unique_chunks.values())

        if not splits:
            logger.warning("No chunks generated. Check if the documents are empty or unsupported.")
            return

        try:
            self.vector_store.add_documents(splits)
            logger.info("Successfully added document chunks to the vector store.")
        except Exception as e:
            logger.error(f"Error adding document chunks to vector store: {e}", exc_info=True)


    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Performs a similarity search against the vector store.

        Args:
            query: The query string.
            k: The number of results to return.

        Returns:
            A list of matching Langchain Documents.
        """
        logger.info(f"Performing similarity search for query: '{query}' with k={k}")
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {e}", exc_info=True)
            return []
