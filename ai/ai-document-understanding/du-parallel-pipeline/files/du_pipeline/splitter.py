"""Split a PDF into chunks that fit the synchronous analyze_document limits.

OCI Document Understanding accepts at most 5 pages and 8 MB per synchronous
request. The service keeps no state between requests, so the pipeline tracks
each chunk's position in the original document and restores it when merging.
"""

import base64
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader, PdfWriter

MAX_PAGES_PER_CHUNK = 5
MAX_CHUNK_BYTES = 8 * 1024 * 1024


@dataclass
class Chunk:
    index: int
    first_page: int  # 1-based page number in the original document
    page_count: int
    data: str  # base64-encoded PDF bytes, ready for InlineDocumentDetails


def _write_range(reader, start, count):
    writer = PdfWriter()
    for page in reader.pages[start:start + count]:
        writer.add_page(page)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf(pdf_bytes, max_pages=MAX_PAGES_PER_CHUNK):
    """Split raw PDF bytes into base64 chunks of at most max_pages pages.

    A chunk that exceeds the 8 MB request limit is halved until it fits,
    so image-heavy documents degrade to smaller chunks instead of failing.
    """
    if not 1 <= max_pages <= MAX_PAGES_PER_CHUNK:
        raise ValueError(f"max_pages must be between 1 and {MAX_PAGES_PER_CHUNK}")

    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    chunks = []
    start = 0
    while start < total_pages:
        count = min(max_pages, total_pages - start)
        chunk_bytes = _write_range(reader, start, count)
        while len(chunk_bytes) > MAX_CHUNK_BYTES and count > 1:
            count = max(1, count // 2)
            chunk_bytes = _write_range(reader, start, count)
        if len(chunk_bytes) > MAX_CHUNK_BYTES:
            raise ValueError(
                f"Page {start + 1} alone exceeds the 8 MB synchronous request limit; "
                "use the asynchronous Object Storage path for this document."
            )
        chunks.append(
            Chunk(
                index=len(chunks),
                first_page=start + 1,
                page_count=count,
                data=base64.b64encode(chunk_bytes).decode("ascii"),
            )
        )
        start += count
    return chunks
