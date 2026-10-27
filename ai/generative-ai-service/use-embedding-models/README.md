# Use Embedding Models on OCI Generative AI

*The absolute simplest code examples for generating text embeddings with the OCI Generative AI Service — embed a sentence or a whole file in about 20 lines of Python.*

Author: Brona Nilsson

Reviewed: 04.08.2026

# When to use this asset?

Use this asset when you need a minimal, copy-paste starting point for calling OCI Generative AI embedding models with the OCI Python SDK.

### Who
- Developers making their first embedding call on OCI
- Solution architects preparing demos or proofs of concept
- Anyone building semantic search, RAG, or clustering on OCI

### When
- You want to verify your tenancy, policies, and API key setup with the shortest possible script
- You need a reference snippet to embed either a single sentence or the contents of a text file

# How to use this asset?

### Prerequisites

1. An OCI tenancy with access to the Generative AI Service in a supported region (the examples use `eu-frankfurt-1` — change the `service_endpoint` if you use another region).
2. An API key configured in `~/.oci/config` ([setup guide](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm)).
3. Python 3.9+ with the OCI SDK installed:

```bash
pip install -r files/requirements.txt
```

### Run the examples

Copy `files/.env.example` to `files/.env` and set `OCI_COMPARTMENT_ID` to your compartment OCID (the `.env` file is git-ignored, so your OCID stays out of version control). Then:

```bash
# Embed a single sentence
python files/embed_sentence.py

# Embed a text file (one vector per paragraph)
python files/embed_file.py files/sample.txt
```

Both scripts call the `cohere.embed-v4.0` model on demand and print the resulting embedding vectors.

### The embedding model

The scripts use `cohere.embed-v4.0`, the current embedding model on OCI Generative AI ([official model page](https://docs.oracle.com/en-us/iaas/Content/generative-ai/cohere-embed-4.htm)):

| Model | Dimensions | Max tokens per input | Languages | Notes |
|---|---|---|---|---|
| `cohere.embed-v4.0` | 1536 (also 256 / 512 / 1024) | 512 per text input; up to 128,000 total per API call | Multilingual | Multimodal: can also embed one image per request (API only); Matryoshka embeddings — dimensions are truncatable; output types: float, int8, uint8, binary |

The entire Cohere `embed-*-v3.0` family (English, Multilingual, Light, and Image variants) is **deprecated** — do not use it for new projects.

The scripts call the model **on demand** (pay per request). If you host the model on a **dedicated AI cluster** instead, swap the `OnDemandServingMode` for the `DedicatedServingMode` shown commented out in each script, filling in your endpoint OCID ([dedicated AI clusters documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/ai-cluster.htm)).

Practical guidance:

- `cohere.embed-v4.0` accepts `input_type` hints (`search_document` when indexing, `search_query` when querying) that improve retrieval quality.
- Vectors are only comparable when produced by the same model at the same dimensions — use identical settings for both indexing and querying.
- When storing vectors in a database (e.g. Oracle Database 26ai `VECTOR` columns), the column dimension must match the model output (1536 by default here). Note the service limits: at most 96 inputs per request, and each input must stay under 512 tokens — for large documents, split the text into chunks first (as `embed_file.py` does with paragraphs).

### Repository structure

```
use-embedding-models/
├── README.md
├── LICENSE
└── files/
    ├── embed_sentence.py   # Embed one sentence
    ├── embed_file.py       # Embed a text file, paragraph by paragraph
    ├── sample.txt          # Demo file: 4 topic pairs to showcase semantic similarity
    ├── .env.example        # Copy to .env and set your compartment OCID
    └── requirements.txt
```

# Useful Links

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Generative AI — Embedding Models](https://docs.oracle.com/en-us/iaas/Content/generative-ai/embed-models.htm)
- [OCI API Key Authentication Setup](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm)

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
