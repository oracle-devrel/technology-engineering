# OCI Search with OpenSearch
OCI Search with OpenSearch is a managed service that you can use to build in-application search solutions based on OpenSearch to enable you to search large datasets and return results in milliseconds, without having to focus on managing your infrastructure.

Search with OpenSearch handles all the management and operations of search clusters, including operations such as security updates, upgrades, resizing, and scheduled backups. This allows you to focus your resources on building features for your OpenSearch solutions.

Reviewed: 04.06.2024

# Table of Contents

1. [Team Publications](#team-publications) 
2. [Useful Links](#useful-links)
3. [Reusable Assets](#reusable-assets)

# Team Publications

- [Step-by-step migration guide](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/importingacluster.htm)
- [LiveLabs: Search Documents stored in Object Storage using OpenSearch, Generative AI, Semantic Search, RAG](https://apexapps.oracle.com/pls/apex/f?p=133:180:239256605646::::wid:3762)
- [Retrieval Augmented Generation with OCI OpenSearch and GenAI service](https://github.com/bobpeulen/oci_opensearch/blob/main/oci_opensearch_rag_auto.ipynb)
A notebook describing and performing all steps to create and store a custom embedding model in the OCI OpenSearch cluster and create a full RAG pipeline (OCI OpenSearch as Vector database and in-memory engine and the GenAI service (cohere) as LLM)
- [LiveLabs: Search and visualize data with OCI Search Service with OpenSearch](https://apexapps.oracle.com/pls/apex/f?p=133:180:6071760449919::::wid:3427)

# Useful Links

- [Search and visualize data using OCI Search Service with OpenSearch](https://docs.oracle.com/en/learn/oci-opensearch/index.html)
- [Use OCI Search Service with OpenSearch to build in-application search - architecture pattern](https://docs.oracle.com/en/solutions/oci-opensearch-application-search/#GUID-AEAA600E-BBCC-4102-8E23-ABEC941FE84C)


# Reusable Assets

- [Create a full RAG pipeline using OCI OpenSearch and the GenAI service](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/open-source-data-platforms/oci-opensearch/code-examples/rag-oci-opensearch-genai-service)
When you are looking to use build a full RAG pipeline using OCI OpenSearch (as a vector database and as an in-memory engine) and the GenAI service, using the OCI Data Science service. Largely, the steps are documented and automated to help you create the pipeline. The notebook includes a small interactive chatbot you can use to interact within a conversation.

- [Create a NGINX server to access the OCI OpenSearch Dashboards](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/open-source-data-platforms/oci-opensearch/code-examples/nginx-server)
When many people need access to the OCI OpenSearch dashboards and you want them to use one single point of entry, being the public URL. You can use these steps to install an NGINX server on a compute, providing you access to the OCI OpenSearch dashboard with full control over your security.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
