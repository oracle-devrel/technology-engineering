# Oracle Vector Store – Ingestion Utilities

**Author** L. Saetta
**Last update:** 15.10.2026 
**License:** MIT  
**Python:** 3.11+

This project provides a set of utilities to ingest PDF documents into an Oracle Vector Store using [Docling](https://github.com/docling-project/docling) for document parsing and **OCI LangChain-compatible embeddings**, with a strong focus on:

- deterministic, reproducible ingestion
- clear separation between *collection creation* and *incremental loading*
- traceability of documents and metadata

The code is designed for **RAG pipelines targeting Oracle Database / Autonomous Database (ADB)**.

---

## High-level architecture

PDF files
↓
Docling (structure-aware parsing)
↓
Chunking (text + tables, provenance preserved)
↓
LangChain Documents
↓
Embedding model (OCI Generative AI)
↓
Oracle Vector Store (one table = one collection)


---

## Main scripts

### 1. first_loading.py
**Create a new collection and load PDFs (one-shot).**

- Creates a new Oracle Vector Store table
- Loads all PDFs from a directory
- chunks and embed documents
- Annotates the table with the embedding model used
- Computes basic chunk statistics

**Important:**  
This script must be used **only for new collections**.  
It will fail if the collection already exists.

```bash
python first_loading.py <new_collection_name> <pdf_directory>
```

### 2. add_documents.py

Incrementally add PDFs to an existing collection.

* Checks if the collection exists
* Skips documents already loaded
* Loads only new PDFs
* Uses the same chunking and embedding strategy

```bash
python add_documents.py <existing_collection_name> <pdf_directory>
```

### 3. list_collection_info.py

* Inspect a collection.
* Displays:
    * embedding model used (from table comment)
    * list of documents in the collection

```bash
python list_collection_info.py <collection_name>
```

### 4. list_collections.py

* Displays the list of collections (tables) loaded in the Vector Store

```bash
python list_collections.py
```

---

## Core modules
```docling_utils.py```

Document processing backbone.

Key features:
* Structure-aware PDF parsing via Docling
* Page provenance preservation
* Atomic table handling (tables are never chunked)
* Configurable chunk size and overlap
* Optional per-chunk headers
* Fallback to markdown chunking when needed
* Conversion to LangChain Document objects

This module is intentionally verbose and defensive.
Silent failures are avoided by design.

```db_utils.py```

Oracle database utilities.

Responsibilities:
* Open connections (ADB or non-ADB)
* Retrieve table comments
* Provide safe, logged access to the database

```config.py```

Centralized configuration:
* Embedding model selection
* OCI region and endpoint
* Chunk size and overlap
* Debug flags

Sensitive values (credentials, wallets) are intentionally excluded and expected
in a separate config_private.py.

---

## Chunking strategy (important)

* Text blocks
    * Page-scoped
    * Chunked using RecursiveCharacterTextSplitter
* Tables
    * Detected heuristically
    * Kept atomic
    * Never split
* Metadata
``{
  "source": "<pdf file name>",
  "page_label": "12-13"
}``

---

## License

This project is released under the **MIT License**.

You are free to:
* use
* modify
* distribute
* embed in commercial systems

---

## Setup

1. You need to have proper access to a schema in an Autonomous DB (ADB)
2. Create a file config_private.py with connection's info
3. Load in the machine Docling models (see Docling docs)
4. Clone the repository
5. install all the packages from **requirements.txt** 

