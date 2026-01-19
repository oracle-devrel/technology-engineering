"""
File name: docling_utils.py
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Utilities to convert PDF documents to Docling's internal representation (DoclingDocument),
    extract content while preserving provenance (page numbers), and produce chunks suitable
    for RAG ingestion.

    Key features:
    - Scans a directory for *.pdf files
    - Converts each PDF using Docling
    - Extracts blocks in reading order:
        * Text blocks (page-scoped, then chunked by size)
        * Table blocks (kept atomic; never chunked)
    - Attaches per-chunk metadata:
        {
            "source": "<pdf file name>",
            "page_label": "<page number or range>"
        }
    - Optional flag to prepend a clearly separated header to each chunk text
    - Fallback to markdown chunking if item/provenance extraction yields no blocks

New:
    - Exposes a function to process a single PDF file: pdf_file_to_chunks()

Notes:
    - Page labels are derived from Docling provenance (page_no). For tables spanning
      multiple pages, page_label can be a range like "12-13".
    - Table detection/rendering is conservative and somewhat heuristic to cope with
      Docling version differences. If you know the exact table item class in your
      Docling version, replacing is_table_item() with an isinstance() check is recommended.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils import get_console_logger, remove_path_from_ref

logger = get_console_logger()


def iter_doc_items(doc) -> Iterator[Any]:
    """
    Iterate over DoclingDocument items robustly across Docling versions.

    Some Docling versions yield:
      - item
    Others yield:
      - (item, level) tuples
    And some support iterate_items(with_groups=False).

    Args:
        doc: A DoclingDocument-like object (typically result.document).

    Yields:
        Docling "item" objects (DocItem instances) only.
    """
    if not hasattr(doc, "iterate_items"):
        # fix for pylint added
        return

    # Try with_groups=False if supported (newer versions / recommended usage)
    try:
        it = doc.iterate_items(with_groups=False)
    except TypeError:
        it = doc.iterate_items()

    for elem in it:
        # If elem is (item, level) or similar, take the first entry
        if isinstance(elem, tuple) and elem:
            yield elem[0]
        else:
            yield elem


def item_page_nos(item) -> Set[int]:
    """
    Extract page numbers from a Docling item provenance.

    In many Docling versions, item.prov can be:
      - None / missing
      - a single ProvenanceItem
      - a list/tuple of ProvenanceItem objects

    This function normalizes all these cases and returns a set of integer page numbers.

    Args:
        item: A Docling item (DocItem).

    Returns:
        A set of page numbers (ints). Empty set if no provenance info is available.
    """
    prov = getattr(item, "prov", None)
    if not prov:
        return set()

    prov_list = prov if isinstance(prov, (list, tuple)) else [prov]

    pages: Set[int] = set()
    for p in prov_list:
        page_no = getattr(p, "page_no", None)
        if page_no is None:
            continue
        try:
            pages.add(int(page_no))
        except (TypeError, ValueError):
            continue

    return pages


def normalize_spaces_keep_newlines(text: str) -> str:
    """
    Normalize whitespace without removing newlines.

    Replaces sequences of two or more spaces/tabs with a single space,
    while preserving newlines.

    Args:
        text: Input text.

    Returns:
        Normalized text.
    """
    return re.sub(r"[ \t]{2,}", " ", text)


def build_docling_converter(
    artifacts_path: str = "~/docling_models",
) -> DocumentConverter:
    """
    Build a Docling DocumentConverter configured for PDF conversion.

    Args:
        artifacts_path: Path where Docling stores/downloads model artifacts.

    Returns:
        A configured DocumentConverter instance.
    """
    opts = PdfPipelineOptions(
        artifacts_path=artifacts_path,
        allow_external_plugins=True,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )


def pdf_to_docling_document(converter: DocumentConverter, pdf_path: str | Path):
    """
    Convert a PDF into a DoclingDocument (preserving provenance).

    Args:
        converter: A DocumentConverter instance.
        pdf_path: Path to the PDF file.

    Returns:
        DoclingDocument instance (result.document).
    """
    pdf_path = str(pdf_path)
    logger.info("Converting PDF to DoclingDocument: %s", pdf_path)
    result = converter.convert(pdf_path)
    return result.document


def pdf_to_markdown(converter: DocumentConverter, pdf_path: str | Path) -> str:
    """
    Convert a PDF to markdown using Docling.

    Warning:
        Markdown export can be lossy with respect to provenance (page numbers), so it is used
        only as a fallback when item-based extraction yields no blocks.

    Args:
        converter: A DocumentConverter instance.
        pdf_path: Path to the PDF file.

    Returns:
        Markdown string.
    """
    pdf_path = str(pdf_path)
    logger.info("Converting PDF to markdown: %s", pdf_path)
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()


def chunk_text(text: str, max_chunk_size: int, overlap: int = 0) -> list[str]:
    """
    Chunk text into approximate character-sized parts.

    Uses LangChain's RecursiveCharacterTextSplitter to generate chunks.

    Args:
        text: Input text to chunk.
        max_chunk_size: Target maximum chunk size in characters.
        overlap: Overlap between chunks in characters.

    Returns:
        List of chunk strings.
    """
    normalized = normalize_spaces_keep_newlines(text)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=overlap,
    )
    return splitter.split_text(normalized)


def make_chunk_header(file_name: str) -> str:
    """
    Build a clearly separated header string to prefix chunk text.

    Args:
        file_name: The source file name (or path).

    Returns:
        A markdown-friendly header string.
    """
    file_name = remove_path_from_ref(file_name)
    return f"---\nsource_file: {file_name}\n---\n\n"


def maybe_prepend_header(text: str, file_name: str, add_header: bool) -> str:
    """
    Conditionally prepend a header to the given text.

    Args:
        text: Chunk body.
        file_name: Source file name.
        add_header: If True, prepend the header.

    Returns:
        Possibly header-prefixed text.
    """
    return (make_chunk_header(file_name) + text) if add_header else text


def build_chunk_metadata(source_file_name: str, page_label: str) -> Dict[str, str]:
    """
    Build the metadata dict attached to each chunk.

    Structure:
        {
            "source": "<pdf file name>",
            "page_label": "<page number or range>"
        }

    Args:
        source_file_name: Source PDF file name (or path).
        page_label: Page number label (e.g., "12") or range (e.g., "12-13"). Can be "".

    Returns:
        Metadata dict.
    """
    source_file_name = remove_path_from_ref(source_file_name)
    return {"source": source_file_name, "page_label": page_label}


def page_label_from_pages(pages: Set[int]) -> str:
    """
    Convert a set of page numbers to a compact label string.

    Examples:
        {12} -> "12"
        {12, 13} -> "12-13"
        empty set -> ""

    Args:
        pages: Set of page numbers.

    Returns:
        A page label string.
    """
    if not pages:
        return ""
    lo, hi = min(pages), max(pages)
    return str(lo) if lo == hi else f"{lo}-{hi}"


@dataclass(frozen=True)
class Chunk:
    """
    A chunk of extracted content, suitable for vectorization / RAG.

    Attributes:
        text: The chunk content (text or table serialization).
        source_path: Full path to the source PDF file.
        chunk_index: Global index within the returned list.
        metadata: Dict containing source and page_label.
    """

    text: str
    source_path: str
    chunk_index: int
    metadata: Dict[str, str]


def is_table_item(item) -> bool:
    """
    Heuristically detect if a Docling item represents a table.

    This is conservative and version-tolerant but not perfect.

    Args:
        item: A Docling item.

    Returns:
        True if the item looks like a table, otherwise False.
    """
    name = item.__class__.__name__.lower()
    return "table" in name or hasattr(item, "table")


def render_table_item(item, doc) -> str:
    """
    Render a table item into a stable textual representation.

    Args:
        item: A Docling table-like item.
        doc: The parent DoclingDocument (required by recent Docling versions).

    Returns:
        A string representing the table.
    """
    # Preferred: Markdown export WITH doc
    if hasattr(item, "export_to_markdown"):
        try:
            md = item.export_to_markdown(doc=doc)
            md = str(md).strip()
            if md:
                return md
        except TypeError:
            # older Docling version without doc parameter
            try:
                md = str(item.export_to_markdown()).strip()
                if md:
                    return md
            except Exception:
                pass
        except Exception:
            pass

    # TSV fallback
    tbl = getattr(item, "table", None)
    if tbl is not None:
        rows = getattr(tbl, "rows", None)
        if rows:
            lines: List[str] = []
            for r in rows:
                cells = getattr(r, "cells", None)
                if not cells:
                    continue
                vals: List[str] = []
                for c in cells:
                    v = getattr(c, "text", None) or getattr(c, "value", None) or ""
                    v = str(v).replace("\t", " ").replace("\n", " ").strip()
                    vals.append(v)
                lines.append("\t".join(vals))
            if lines:
                return "```tsv\n" + "\n".join(lines) + "\n```"

    # last resort
    txt = getattr(item, "text", "") or ""
    return str(txt).strip()


def iter_blocks(doc) -> Iterable[Tuple[str, Set[int], str]]:
    """
    Yield blocks from doc in order:
      - "table" blocks are atomic (never chunked)
      - "text" blocks are page-scoped (flushed on page change)

    Returns:
        Tuples (block_text, pages_set, block_type)
    """
    pending_text: List[str] = []
    pending_pages: Set[int] = set()
    current_text_page: Optional[int] = None

    def flush_text() -> Optional[Tuple[str, Set[int], str]]:
        nonlocal pending_text, pending_pages, current_text_page
        if not pending_text:
            return None

        text = "\n\n".join(pending_text).strip()
        pages = set(pending_pages)

        pending_text = []
        pending_pages = set()
        current_text_page = None

        if text:
            return (text, pages, "text")
        return None

    table_mode = False
    table_parts: List[str] = []
    table_pages: Set[int] = set()

    for item in iter_doc_items(doc):
        pages = item_page_nos(item)

        # ---- TABLE PATH (atomic, may span pages) ----
        if is_table_item(item):
            flushed = flush_text()
            if flushed:
                yield flushed

            table_mode = True
            table_pages |= pages

            rendered = render_table_item(item, doc)
            if rendered:
                table_parts.append(rendered)
            continue

        # leaving table mode
        if table_mode:
            table_text = "\n\n".join(table_parts).strip()
            if table_text:
                yield (table_text, set(table_pages), "table")
            table_mode = False
            table_parts, table_pages = [], set()

        # ---- TEXT PATH (page-scoped) ----
        txt = getattr(item, "text", None)
        if not txt or not str(txt).strip():
            continue

        item_page = min(pages) if pages else None

        if (
            current_text_page is not None
            and item_page is not None
            and item_page != current_text_page
        ):
            flushed = flush_text()
            if flushed:
                yield flushed

        if current_text_page is None:
            current_text_page = item_page

        pending_text.append(str(txt).strip())

        if item_page is not None:
            pending_pages.add(item_page)
        else:
            pending_pages |= pages

    # flush remaining table
    if table_mode:
        table_text = "\n\n".join(table_parts).strip()
        if table_text:
            yield (table_text, set(table_pages), "table")

    # flush remaining text
    flushed = flush_text()
    if flushed:
        yield flushed


def iter_pdf_files(pdf_dir: str | Path) -> Iterable[Path]:
    """
    Yield all PDF files found in a directory (sorted, deterministic).

    Args:
        pdf_dir: Directory path containing PDFs.

    Yields:
        Paths to PDF files.
    """
    pdf_dir = Path(pdf_dir).expanduser().resolve()
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        raise ValueError(f"pdf_dir must be an existing directory. Got: {pdf_dir}")
    yield from sorted(pdf_dir.glob("*.pdf"))


def pdf_file_to_chunks(
    pdf_path: str | Path,
    max_chunk_size: int,
    overlap: int,
    converter: Optional[DocumentConverter] = None,
    artifacts_path: str = "~/docling_models",
    fail_fast: bool = False,
    add_chunk_header: bool = False,
) -> List[Chunk]:
    """
    Convert a single PDF file into a list of chunks.

    Behavior:
      - Text blocks are chunked using RecursiveCharacterTextSplitter.
      - Table blocks are kept atomic (NOT chunked).
      - metadata.page_label is derived from provenance pages:
          * "12" for single page
          * "12-13" for a range
          * "" if provenance is missing
      - If item/provenance extraction yields no blocks, fallback to markdown chunking
        (page labels will be empty).

    Args:
        pdf_path: Path to the PDF file.
        max_chunk_size: Chunk size in characters for text blocks.
        overlap: Overlap in characters for text chunks.
        converter: Optional pre-built DocumentConverter (recommended when processing many PDFs).
        artifacts_path: Docling artifacts/model directory used if converter is not provided.
        fail_fast: If True, raise exceptions on failures; otherwise log and return what is possible.
        add_chunk_header: If True, prepend a header containing the source file name.

    Returns:
        List of Chunk objects for this PDF. chunk_index is local to this PDF (0..n-1).
    """
    pdf_path = Path(pdf_path).expanduser().resolve()

    local_converter = converter or build_docling_converter(
        artifacts_path=artifacts_path
    )
    file_name = remove_path_from_ref(pdf_path.name)

    chunks: List[Chunk] = []
    try:
        doc = pdf_to_docling_document(local_converter, pdf_path)

        produced = 0
        for block_text, pages_set, block_type in iter_blocks(doc):
            page_label = page_label_from_pages(pages_set)

            if block_type == "table":
                text_out = maybe_prepend_header(block_text, file_name, add_chunk_header)
                chunks.append(
                    Chunk(
                        text=text_out,
                        source_path=str(pdf_path),
                        chunk_index=len(chunks),
                        metadata=build_chunk_metadata(file_name, page_label),
                    )
                )
                produced += 1
            else:
                parts = chunk_text(
                    block_text, max_chunk_size=max_chunk_size, overlap=overlap
                )
                for part in parts:
                    text_out = maybe_prepend_header(part, file_name, add_chunk_header)
                    chunks.append(
                        Chunk(
                            text=text_out,
                            source_path=str(pdf_path),
                            chunk_index=len(chunks),
                            metadata=build_chunk_metadata(file_name, page_label),
                        )
                    )
                    produced += 1

        if produced == 0:
            logger.warning(
                "No blocks produced via iterate_items() for %s."
                " Falling back to markdown chunking (no page labels).",
                pdf_path.name,
            )
            md = pdf_to_markdown(local_converter, pdf_path)
            for part in chunk_text(md, max_chunk_size=max_chunk_size, overlap=overlap):
                text_out = maybe_prepend_header(part, file_name, add_chunk_header)
                chunks.append(
                    Chunk(
                        text=text_out,
                        source_path=str(pdf_path),
                        chunk_index=len(chunks),
                        metadata=build_chunk_metadata(file_name, ""),
                    )
                )

    except Exception as e:
        logger.exception("Failed processing %s: %s", str(pdf_path), str(e))
        if fail_fast:
            raise

    return chunks


def pdf_dir_to_chunks(
    pdf_dir: str | Path,
    max_chunk_size: int,
    overlap: int,
    artifacts_path: str = "~/docling_models",
    fail_fast: bool = False,
    add_chunk_header: bool = False,
) -> List[Chunk]:
    """
    Convert all PDFs in a directory into a single flattened list of chunks.

    This function reuses a single Docling converter for performance and calls
    pdf_file_to_chunks() for each PDF.

    Args:
        pdf_dir: Directory containing PDF files.
        max_chunk_size: Chunk size in characters for text blocks.
        overlap: Overlap in characters for text chunks.
        artifacts_path: Docling artifacts/model directory.
        fail_fast: If True, raise exceptions on failures; otherwise log and continue.
        add_chunk_header: If True, prepend a header containing the source file name.

    Returns:
        A single list of Chunk objects across all PDFs. chunk_index is global across the list.
    """
    converter = build_docling_converter(artifacts_path=artifacts_path)

    pdf_files = list(iter_pdf_files(pdf_dir))
    logger.info("Found %d PDF(s) in %s", len(pdf_files), str(Path(pdf_dir).resolve()))

    all_chunks: List[Chunk] = []

    for pdf_path in pdf_files:
        doc_chunks = pdf_file_to_chunks(
            pdf_path=pdf_path,
            max_chunk_size=max_chunk_size,
            overlap=overlap,
            converter=converter,  # reuse
            artifacts_path=artifacts_path,
            fail_fast=fail_fast,
            add_chunk_header=add_chunk_header,
        )

        # Reindex chunks globally (keep the per-pdf metadata untouched)
        for ch in doc_chunks:
            all_chunks.append(
                Chunk(
                    text=ch.text,
                    source_path=ch.source_path,
                    chunk_index=len(all_chunks),
                    metadata=ch.metadata,
                )
            )

        logger.info(
            "Processed %s. Total chunks so far: %d",
            Path(pdf_path).name,
            len(all_chunks),
        )

    return all_chunks


#
# Transform to Langchain docs
#
def chunks_to_langchain_documents(chunks: List[Chunk]) -> List[Document]:
    """
    Convert a list of Chunk objects into a list of LangChain Document objects.

    Each Chunk becomes:
      - Document.page_content = chunk.text
      - Document.metadata = chunk.metadata + extra fields for traceability:
            {
                "source": "<pdf file name>",
                "page_label": "<page number or range>",
                "source_path": "<full path to pdf>",
                "chunk_index": <int>
            }

    Args:
        chunks: List of Chunk objects.

    Returns:
        List of langchain_core.documents.Document objects.
    """
    docs: List[Document] = []
    for ch in chunks:
        # changed to align to already established format
        # removed path
        md = {
            "source": remove_path_from_ref(ch.source_path),
            "page_label": ch.metadata["page_label"],
        }
        docs.append(Document(page_content=ch.text, metadata=md))

    return docs
