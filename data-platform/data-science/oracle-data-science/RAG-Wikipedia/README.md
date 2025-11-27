# Overview
This package provides an end-to-end example of performing vector search and Retrieval-Augmented Generation (RAG) from an OCI Data Science Notebook Session using Wikipedia's Artificial Intelligence page.
It uses OCI AI Vector Search with an Oracle AI Database 26ai and includes explanations along with advanced RAG techniques, including:

1. Comparing rule-based and semantic-based text splitters
2. Connecting to the Oracle AI Database 26ai and creating vector-enabled tables
3. Running hybrid search (keyword + vector similarity)
4. Applying rerankers to improve retrieved context

# Prerequisites

To use this package, you need:
- Basic Python knowledge
- Access to an OCI Data Science Notebook Session
- An Oracle AI Database 26ai or 23ai with Vector Search enabled
- Required IAM permissions for Data Science and Database access
- A configured database wallet or secure connection details

# Environment

Run the examples in a Jupyter Notebook inside an OCI Data Science Notebook Session.