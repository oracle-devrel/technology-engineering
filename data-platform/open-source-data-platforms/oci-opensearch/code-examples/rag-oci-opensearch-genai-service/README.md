# Create a full RAG pipeline using OCI OpenSearch and the GenAI service

Reviewed: 05.06.2024

# When to use this asset?

When you are looking to use build a full RAG pipeline using OCI OpenSearch (as vector database and as in-memory engine) and the GenAI service, using the OCI Data Science service. Largely, the steps are documented and automated to help you create the pipeline. The notebook includes a small interactive chatbot you can use to interact with in a conversation.

# How to use this asset?

Upload the notebook to an OCI Data Science session, which will:
- Create and store a custom embedding model in the OCI OpenSearch cluster
- Create a full RAG pipeline (OCI OpenSearch as Vector database and in-memory engine and the GenAI service (cohere) as LLM)

# Pre-requisites:

- Create a VCN with a private subnet. Make sure there is NAT gateway attached.
- Add ingress rules to the security list: ports 9200 and 5601 ports on source 0.0.0.0/0, TCP
- Create the OpenSearch cluster in the public subnet
- Create the OCI Data Science notebook session in the private subnet
- Add the config file (API Key) and private key to this notebook in the .oci directory
- Install any of the latest pre-defined conda environments with latest version of OCI
- Create an object storage bucket

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
