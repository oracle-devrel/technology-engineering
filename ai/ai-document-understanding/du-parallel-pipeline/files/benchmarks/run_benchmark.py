"""Benchmark sequential vs parallel synchronous processing of one PDF.

Runs the identical chunk set twice — once with 1 worker, once with N —
and prints a comparison table for the README.

Usage:
    python benchmarks/run_benchmark.py document.pdf --workers 4
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from du_pipeline.config import Settings
from du_pipeline.executor import ParallelDocumentAnalyzer
from du_pipeline.merger import merge_results
from du_pipeline.splitter import split_pdf


def timed_run(analyzer, chunks, features, workers):
    started = time.perf_counter()
    results, timings = analyzer.analyze(chunks, features=features, max_workers=workers)
    wall_time = time.perf_counter() - started
    merge_results(results)  # include merge cost in the measurement
    return wall_time, timings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="Path to a multi-page PDF")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--features", default="table,text")
    parser.add_argument("--profile", help="OCI config profile (default: DEFAULT)")
    args = parser.parse_args()

    settings = Settings.from_env(profile=args.profile)
    features = [name.strip() for name in args.features.split(",")]

    with open(args.pdf, "rb") as handle:
        chunks = split_pdf(handle.read())
    total_pages = sum(chunk.page_count for chunk in chunks)
    print(f"{args.pdf}: {total_pages} pages, {len(chunks)} chunks, features: {args.features}\n")

    analyzer = ParallelDocumentAnalyzer(settings)

    print("Sequential run (1 worker)...")
    seq_wall, seq_timings = timed_run(analyzer, chunks, features, workers=1)

    print(f"Parallel run ({args.workers} workers)...")
    par_wall, par_timings = timed_run(analyzer, chunks, features, workers=args.workers)

    speedup = seq_wall / par_wall if par_wall else float("inf")
    print()
    print(f"| Mode | Wall time | Avg per chunk |")
    print(f"|---|---|---|")
    print(f"| Sequential (1 worker) | {seq_wall:.1f}s | {sum(seq_timings)/len(seq_timings):.1f}s |")
    print(f"| Parallel ({args.workers} workers) | {par_wall:.1f}s | {sum(par_timings)/len(par_timings):.1f}s |")
    print(f"\nSpeedup: {speedup:.1f}x")


if __name__ == "__main__":
    main()
