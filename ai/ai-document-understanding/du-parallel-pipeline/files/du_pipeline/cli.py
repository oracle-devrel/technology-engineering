"""Command-line entry point for the parallel Document Understanding pipeline.

Example:
    python -m du_pipeline.cli invoice_40_pages.pdf \
        --features table,text --workers 4 \
        --output result.json --tables-dir tables/
"""

import argparse
import json
import sys
import time

from du_pipeline.config import Settings
from du_pipeline.executor import DEFAULT_WORKERS, SUPPORTED_FEATURES, ParallelDocumentAnalyzer
from du_pipeline.merger import export_tables_csv, merge_results
from du_pipeline.splitter import split_pdf


def build_parser():
    parser = argparse.ArgumentParser(
        prog="du_pipeline",
        description=(
            "Analyze PDFs of any length with OCI Document Understanding by "
            "splitting them into 5-page chunks and processing the chunks in "
            "parallel synchronous requests."
        ),
    )
    parser.add_argument("pdf", help="Path to the PDF document")
    parser.add_argument(
        "--features",
        default="table,text",
        help=f"Comma-separated features to run: {','.join(sorted(SUPPORTED_FEATURES))} "
        "(default: table,text)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Concurrent requests (default: {DEFAULT_WORKERS}; use 1 for sequential)",
    )
    parser.add_argument("--output", help="Write the merged result JSON to this file")
    parser.add_argument(
        "--tables-dir", help="Export every extracted table as CSV into this directory"
    )
    parser.add_argument(
        "--language",
        help="Document language code, e.g. ENG (English models) or ARA (multilingual models)",
    )
    parser.add_argument(
        "--doc-type",
        help="Document type hint for key_value extraction, e.g. INVOICE, RECEIPT",
    )
    parser.add_argument("--compartment-id", help="Compartment OCID (default: $OCI_COMPARTMENT_ID)")
    parser.add_argument("--config-file", help="OCI config file (default: ~/.oci/config)")
    parser.add_argument("--profile", help="OCI config profile (default: DEFAULT)")
    return parser


def run(args):
    settings = Settings.from_env(
        compartment_id=args.compartment_id,
        config_file=args.config_file,
        profile=args.profile,
    )
    features = [name.strip() for name in args.features.split(",") if name.strip()]

    with open(args.pdf, "rb") as handle:
        pdf_bytes = handle.read()

    chunks = split_pdf(pdf_bytes)
    total_pages = sum(chunk.page_count for chunk in chunks)
    print(
        f"{args.pdf}: {total_pages} pages -> {len(chunks)} chunk(s), "
        f"{args.workers} worker(s), features: {', '.join(features)}"
    )

    analyzer = ParallelDocumentAnalyzer(settings)

    def report(chunk, elapsed):
        last_page = chunk.first_page + chunk.page_count - 1
        print(f"  chunk {chunk.index + 1}/{len(chunks)} "
              f"(pages {chunk.first_page}-{last_page}) done in {elapsed:.1f}s")

    started = time.perf_counter()
    results, timings = analyzer.analyze(
        chunks,
        features=features,
        language=args.language,
        document_type=args.doc_type,
        max_workers=args.workers,
        on_chunk_done=report,
    )
    wall_time = time.perf_counter() - started

    merged = merge_results(results)
    table_count = sum(len(page.get("tables") or []) for page in merged["pages"])
    print(
        f"Done in {wall_time:.1f}s wall time "
        f"(sum of individual requests: {sum(timings):.1f}s). "
        f"Extracted {table_count} table(s) across {len(merged['pages'])} page(s)."
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2, default=str)
        print(f"Merged result written to {args.output}")

    if args.tables_dir:
        written = export_tables_csv(merged, args.tables_dir)
        print(f"{len(written)} CSV file(s) written to {args.tables_dir}/")

    return merged


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except (ValueError, FileNotFoundError) as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
