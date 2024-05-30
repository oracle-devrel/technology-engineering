# Low Code Modular RAG-based Knowledge Search Engine using OCI Generative AI, OCI Vector Search, and Oracle Integration Cloud

Reviewed: 30.05.2024

# Introduction

In this article, we'll explore how to enable an enterprise-grade RAG-based Knowledge Search Engine with a low-code approach.

You’ll learn how to use Oracle Integration Cloud to integrate and orchestrate business chanels like a Web Application built in Oracle Visual Builder, productivity channels like OCI Object Storage, local large and small language models (LLMs), and vector databases to ingest live data into the RAG-based Knowledge Search Engine store. 

You'll use Oracle Cloud Infrastructure (OCI) Document Understanding to extract information from different document types. Leverage OCI Generative AI for document summarization, generation and synthesis of answers to questions on documents. Use OCI DB Cloud Service 23AI for Document Extraction, Vector Search and Embedding (using ONNX local models to the DB) capabilities , and apply local OCI Data Science models for better answers from advanced RAG.

# Prerequisites

Before getting started, make sure you have access to the following Oracle Cloud Infrastructure (OCI) services:

- OCI Generative AI Service (GenAI)
- OCI Document Understanding Service 
- Oracle Integration Cloud (OIC) with Visual Builder(VBCS) enabled
- OCI Object Storage 
- OCI Base Database Cloud Service (23ai) 
- OCI Data Science

And also, make sure you have access to the following Meta services:

- Whats App Business Account

# Solution Architecture

In this section, we'll dive into the building blocks of the solution architecture.
<img src="./images/5_low-code-modular-rag-knowledge-search-engine-arch.png"></img>

We've built the application using Oracle Visual Builder (as part of OIC), and it smoothly runs through Oracle Integration Cloud  as the main, low-code orchestration tool. OCI Document Understanding is there to handle the document extraction, OCI Base Database Cloud Service 23ai for document extraction, local embeddings using onnx models within Oracle 23ai, Generative AI for answer synthesis and OCI Data Science as the Reranker model for advance RAG:

1. Document Evaluation Tool App interface built using VBCS:

- A low-code or no-code approach for the Data Loader and Query Engine flows of your LLM Application with Oracle Integration visual orchestration tools and native adapters for different Social, Productivity and Business Data Channels (users input to the LLM App Engine, either documents, images, business data or queries) and Sources (source of the data used by the LLM App Engine), as well as native adapters to the different OCI Services used by the LLM App Engine (OCI Generative AI REST APIs, Vector Databases or Stores, Oracle Cloud Infrastructure Language REST APIs, Oracle Cloud Infrastructure Data Science Custom Model REST Endpoints and more). This helps to quickly set up your LLM Application Business Flows 

2. An event-driven pattern to decouple the Document, Image and Business Data Channels and Sources as well as the Query Channels from the Data Loader and Query Engine modules of the LLM App Engine using the OCI Streaming Service (Oracle managed Kafka Service) and the native adapter we have for this OCI Service in Oracle Integration. This helps to enable a scalable and performant LLM application.

3. A private connection to 3rd party cloud, on-premises apps, systems, and so on, using the Oracle Integration Connectivity Agent, which is the key enabler for hybrid and multicloud integration architectures, specially in an LLM Application where documents, images, business data, query from users can come from those systems and you want to keep the transit for documents and data private and secured. This helps to improve the security of the end-to-end LLM Flow, keeping the traffic within private networks.

4. The possibility to use local LLM models within Oracle 23ai in OCI Base Database Cloud service and dedicate cluster for OCI Generative AI service (orchestrating OCI Base Database Cloud service 23ai ONNX models, OCI Generative AI Model Endpoints or OCI Data Science Model Endpoints using Oracle Integration cloud native adapters and with the connectivity agent for private models).

5. A flexible approach to plug or unplug your own User Interface (UI) for your LLM Application with the LLM APP Engine (in this case whatsapp for uploading documents), or a low-code approach to build the UI either using Visual App Builder under Oracle Integration (using Visual Builder Web App for the Q&A UI)



# Application Flow in Detail

In this application:

**Step1.** 

# Code



# Conclusion


### Authors

<a href="https://github.com/jcgocol">@jcgocol</a>, <a href="https://github.com/bobpeulen">@bobpeulen</a>


# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
	
