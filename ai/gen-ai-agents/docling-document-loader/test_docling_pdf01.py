"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Test script to convert PDFs in a directory to text chunks using docling_utils
"""

import random
from docling_utils import pdf_dir_to_chunks
from utils import get_console_logger

logger = get_console_logger()


# -----------------------------
# Example usage
# -----------------------------
PDF_DIR = "./pdfs"
MAX_CHUNK_SIZE = 1000
OVERLAP = 100
ARTIFACTS_PATH = "~/docling_models"
# <--- turn on/off
ADD_CHUNK_HEADER = True

if __name__ == "__main__":
    chunks = pdf_dir_to_chunks(
        pdf_dir=PDF_DIR,
        max_chunk_size=MAX_CHUNK_SIZE,
        overlap=OVERLAP,
        artifacts_path=ARTIFACTS_PATH,
        fail_fast=False,
        add_chunk_header=ADD_CHUNK_HEADER,
    )

    # quick preview of N_ITER random samples
    N_ITER = 10
    for c in random.sample(chunks, k=min(N_ITER, len(chunks))):
        print(f"--- chunk {c.chunk_index + 1} " f"({len(c.text)} chars) ---")
        print(c.text[:250].replace("\n", " "), "...")
        print(c.metadata)
        print("")

    print(f"Total chunks (all PDFs): {len(chunks)}")
