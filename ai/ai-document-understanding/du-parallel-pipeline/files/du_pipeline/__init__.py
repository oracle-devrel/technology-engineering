"""Parallel processing pipeline for OCI Document Understanding.

Splits documents larger than the 5-page synchronous limit into chunks,
analyzes all chunks concurrently, and merges the results back into a
single response with document-level page numbering.
"""

from du_pipeline.splitter import split_pdf, Chunk
from du_pipeline.executor import ParallelDocumentAnalyzer, SUPPORTED_FEATURES
from du_pipeline.merger import merge_results, export_tables_csv
from du_pipeline.config import Settings

__all__ = [
    "split_pdf",
    "Chunk",
    "ParallelDocumentAnalyzer",
    "SUPPORTED_FEATURES",
    "merge_results",
    "export_tables_csv",
    "Settings",
]
