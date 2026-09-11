"""Merge per-chunk analyze_document results into one document-level result.

Each chunk is analyzed in isolation, so the service numbers its pages 1..5.
The merger restores the original page numbers from the chunk offsets and
returns a single response-shaped dict, as if one call had processed the
whole document. Tables can additionally be exported to CSV files named by
their true page number.
"""

import csv
import os


def merge_results(chunk_results):
    """Merge ordered (chunk, result_dict) pairs into one result dict.

    Page-level content (text lines, words, tables) merges losslessly.
    Document-level classifications (detected_document_types,
    detected_languages) are taken from the first chunk, since chunked
    processing produces one answer per chunk.
    """
    if not chunk_results:
        raise ValueError("No chunk results to merge")

    merged_pages = []
    for chunk, result in chunk_results:
        for page in result.get("pages") or []:
            page = dict(page)
            local_number = page.get("page_number") or 1
            page["page_number"] = chunk.first_page + (local_number - 1)
            merged_pages.append(page)
    merged_pages.sort(key=lambda page: page["page_number"])

    first_result = chunk_results[0][1]
    metadata = dict(first_result.get("document_metadata") or {})
    metadata["page_count"] = len(merged_pages)

    return {
        "document_metadata": metadata,
        "detected_document_types": first_result.get("detected_document_types"),
        "detected_languages": first_result.get("detected_languages"),
        "pages": merged_pages,
    }


def _table_to_grid(table):
    """Convert a DU table dict into a 2D list of cell texts."""
    cells = []
    for section in ("header_rows", "body_rows", "footer_rows"):
        for row in table.get(section) or []:
            for cell in row.get("cells") or []:
                if cell.get("row_index") is not None and cell.get("column_index") is not None:
                    cells.append(cell)
    if not cells:
        return []

    # Normalize indices so both 0- and 1-based numbering produce a full grid.
    min_row = min(cell["row_index"] for cell in cells)
    min_col = min(cell["column_index"] for cell in cells)
    n_rows = max(cell["row_index"] for cell in cells) - min_row + 1
    n_cols = max(cell["column_index"] for cell in cells) - min_col + 1

    grid = [[""] * n_cols for _ in range(n_rows)]
    for cell in cells:
        grid[cell["row_index"] - min_row][cell["column_index"] - min_col] = (
            cell.get("text") or ""
        )
    return grid


def export_tables_csv(merged_result, output_dir):
    """Write every extracted table to output_dir as one CSV per table.

    Files are named page<NNN>_table<N>.csv using document-level page
    numbers. Returns the list of written paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    written = []
    for page in merged_result["pages"]:
        for table_index, table in enumerate(page.get("tables") or [], start=1):
            grid = _table_to_grid(table)
            if not grid:
                continue
            path = os.path.join(
                output_dir,
                f"page{page['page_number']:03d}_table{table_index}.csv",
            )
            with open(path, "w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerows(grid)
            written.append(path)
    return written
