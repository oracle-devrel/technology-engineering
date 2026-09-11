# Parallel Processing Pipeline for Long Documents

A Python pipeline that lets OCI Document Understanding process documents **larger than the 5-page synchronous limit** — at synchronous speed — by splitting the PDF into chunks, running the chunks as **parallel synchronous requests**, and merging the results into one coherent response.

_This asset is a reference implementation: review error handling, authentication, and logging against your own production standards before deploying._

Reviewed: 25.08.2026

## When to use this asset?

Use this pipeline when your documents are longer than 5 pages **and** you need results in seconds, not minutes:

| Path | Max pages | Typical latency | Best for |
|---|---|---|---|
| Synchronous request | 5 | seconds | short documents |
| **This pipeline (parallel sync)** | any (chunked) | **seconds** | **long documents, interactive apps** |
| Asynchronous Object Storage job | 2,000 | minutes (queue + poll) | huge batches, no latency requirement |

The Document Understanding service is **stateless** — there is no "send the next 5 pages" continuation mechanism. This pipeline keeps track on the client side instead: each chunk remembers its position in the original document, and the merger restores true page numbers, so the output looks as if one call had processed the whole document.

```
              ┌──────────────┐    ┌─── chunk 1 (p. 1-5)  ──► analyze_document ───┐
 long PDF ───►│   splitter   │────┼─── chunk 2 (p. 6-10) ──► analyze_document ───┼───► merger ───► one JSON
              │ (pypdf, ≤5p, │    └─── chunk N (...)     ──► analyze_document ───┘     (true page   + CSV
              │  ≤8 MB each) │           ThreadPoolExecutor, N parallel calls          numbers)      tables
              └──────────────┘
```

### Features

- **Table extraction** (headline feature): tables from all chunks are re-indexed to document-level page numbers and can be exported as one CSV per table.
- **Text extraction (OCR)**: full per-page text, merged the same way.
- **Key-value extraction**: supported per chunk; note that document-level fields (e.g. `InvoiceTotal`) are answered once per chunk, so downstream logic must pick the right candidate.
- **Rate-limit aware**: bounded worker pool (default 4) plus the OCI SDK default retry strategy (exponential backoff on HTTP 429/5xx), keeping the pipeline polite against the per-tenancy transaction limit.
- **Adaptive splitting**: chunks that exceed the 8 MB synchronous request limit are automatically halved until they fit.

## Setup

1. Install Python 3.10+ and the requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure OCI API-key authentication (`~/.oci/config`) for a region where Document Understanding is available ([documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm)).
3. Set your compartment OCID (never hardcode it):
   ```bash
   export OCI_COMPARTMENT_ID=<compartment_ocid>
   # optional overrides:
   export OCI_CONFIG_PROFILE=DEFAULT
   export OCI_CONFIG_FILE=~/.oci/config
   ```
4. Make sure you have the appropriate IAM policies for Document Understanding ([documentation](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/about_document-understanding_policies.htm)).

## Usage

Analyze a long PDF with table + text extraction, 4 parallel workers:

```bash
python -m du_pipeline.cli report_40_pages.pdf \
    --features table,text \
    --workers 4 \
    --output result.json \
    --tables-dir tables/
```

Output:

```
report_40_pages.pdf: 40 pages -> 8 chunk(s), 4 worker(s), features: table, text
  chunk 2/8 (pages 6-10) done in 4.2s
  chunk 1/8 (pages 1-5) done in 4.9s
  ...
Done in 11.3s wall time (sum of individual requests: 38.1s).
Extracted 12 table(s) across 40 page(s).
Merged result written to result.json
8 CSV file(s) written to tables/
```

Useful flags:

| Flag | Meaning |
|---|---|
| `--workers 1` | sequential baseline (for comparison) |
| `--features table` | table extraction only |
| `--language ARA` | use the multilingual models instead of English-only |
| `--doc-type INVOICE` | document type hint for `key_value` extraction |
| `--profile LONDON` | use a specific profile from your OCI config file |

Or use it as a library:

```python
from du_pipeline import Settings, ParallelDocumentAnalyzer, split_pdf, merge_results

settings = Settings.from_env()
chunks = split_pdf(open("report.pdf", "rb").read())
results, _ = ParallelDocumentAnalyzer(settings).analyze(chunks, features=["table"])
merged = merge_results(results)
```

## Benchmarks

Two scripts under `benchmarks/` measure the speedup on your own tenancy and documents:

```bash
# sequential vs parallel synchronous processing (same document, same chunks)
python benchmarks/run_benchmark.py report_40_pages.pdf --workers 4

# the async Object Storage job path, for comparison (needs a bucket)
export DU_BUCKET_NAME=<bucket_in_a_DU_region>
python benchmarks/run_async_job.py report_40_pages.pdf
```

Results measured on a 22-page text+table PDF (Frankfurt region, default limits, table + text features) — run the scripts to reproduce on your tenancy:

| Mode | Wall time | vs parallel |
|---|---|---|
| **Parallel synchronous (4 workers)** | **18.2s** | — |
| Sequential synchronous (1 worker) | 48.2s | 2.6x slower |
| Asynchronous Object Storage job | 65.6s (upload + queue + processing + polling) | 3.6x slower |

## Notes and limits

- Service limits ([documentation](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/limits.htm)): 5 pages / 8 MB per synchronous request; 2,000 pages / 500 MB per asynchronous job; asynchronous throughput is limited per tenancy.
- The worker pool is deliberately bounded and every request uses the OCI SDK default retry strategy, so HTTP 429 throttling degrades throughput gracefully instead of failing the run.
- Document-level features (document classification, language detection) return one answer **per chunk**; the merger keeps the first chunk's answer. For per-page features (text, tables) the merge is lossless.
- Only PDFs are split; single images (JPEG/PNG/TIFF) fit in one request anyway.

## Project structure

```
files/
├── requirements.txt          # oci, pypdf
├── du_pipeline/
│   ├── splitter.py           # PDF -> ≤5-page / ≤8 MB base64 chunks
│   ├── executor.py           # parallel synchronous analyze_document calls
│   ├── merger.py             # chunk results -> one JSON + CSV table export
│   ├── config.py             # env-based settings (no hardcoded OCIDs)
│   └── cli.py                # command-line entry point
└── benchmarks/
    ├── run_benchmark.py      # sequential vs parallel comparison
    └── run_async_job.py      # async Object Storage job, timed
```

## Authors

- Brona Nilsson

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
