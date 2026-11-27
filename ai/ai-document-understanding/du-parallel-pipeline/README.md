# Parallel Processing Pipeline for Long Documents with OCI Document Understanding

OCI Document Understanding's synchronous API accepts at most 5 pages per request, and the asynchronous Object Storage path adds queueing latency that interactive applications cannot afford. This asset provides a Python pipeline that processes PDFs of any length at synchronous speed: it splits the document into 5-page chunks, analyzes all chunks in parallel synchronous requests, and merges the results back into a single response with correct document-level page numbering. Table extraction (with CSV export) and OCR text extraction are supported, and a benchmark suite compares sequential, parallel, and asynchronous processing on the same document.

Reviewed: 25.08.2026

# When to use this asset?

See the README document in the /files folder.

# How to use this asset?

See the README document in the /files folder.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
