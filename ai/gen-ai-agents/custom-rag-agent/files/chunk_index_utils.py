"""
Author: Luigi Saetta
Date created: 2024-04-27
Date last modified: 2024-04-30
Python Version: 3.11

Usage: contains the functions to split in chunks and create the index
"""

from collections import defaultdict
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_unstructured import UnstructuredLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter


from utils import get_console_logger, remove_path_from_ref
from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

logger = get_console_logger()


def get_chunk_header(file_path):
    """
    Generate an header for the chunk.
    """
    doc_name = remove_path_from_ref(file_path)
    # split to remove the extension
    doc_title = doc_name.split(".")[0]

    return f"# Doc. title: {doc_title}\n", doc_name


def get_recursive_text_splitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    return a recursive text splitter
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter


def load_and_split_pdf(book_path, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Loads and splits a PDF document into chunks using a recursive character text splitter.

    Args:
        book_path (str): The file path of the PDF document.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between chunks.

    Returns:
        List[Document]: A list of LangChain Document objects with metadata.
    """
    text_splitter = get_recursive_text_splitter(chunk_size, chunk_overlap)

    loader = PyPDFLoader(file_path=book_path)

    docs = loader.load_and_split(text_splitter=text_splitter)

    chunk_header = ""

    if len(docs) > 0:
        chunk_header, _ = get_chunk_header(book_path)

    # remove path from source and reduce the metadata (16/03/2025)
    for doc in docs:
        # add more context to the chunk
        doc.page_content = chunk_header + doc.page_content
        doc.metadata = {
            "source": remove_path_from_ref(book_path),
            "page_label": doc.metadata.get("page_label", ""),
        }

    logger.info("Successfully loaded and split %d chunks from %s", len(docs), book_path)

    return docs


def load_and_split_docx(file_path, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Loads and splits a docx document into chunks using a recursive character text splitter.

    Args:
        file_path (str): The file path of the document.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between chunks.

    Returns:
        List[Document]: A list of LangChain Document objects with metadata.
    """
    loader = UnstructuredLoader(file_path)
    docs = loader.load()

    # Raggruppa per numero di pagina (o altro metadato)
    grouped_text = defaultdict(list)

    chunk_header = ""
    doc_name = ""

    if len(docs) > 0:
        chunk_header, doc_name = get_chunk_header(file_path)

    for doc in docs:
        # fallback to 0 if not available
        page = doc.metadata.get("page_number", 0)
        grouped_text[page].append(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    final_chunks = []

    # Per ogni pagina (o gruppo), unisci il testo e splitta
    for page, texts in grouped_text.items():
        full_text = "\n".join(texts)
        splits = splitter.split_text(full_text)

        for chunk in splits:
            final_chunks.append(
                Document(
                    # add more context
                    page_content=chunk_header + chunk,
                    metadata={
                        "source": doc_name,
                        "page_label": str(page),
                    },
                )
            )

    logger.info("Successfully loaded and split %d chunks from %s", len(docs), file_path)

    return final_chunks
