# Document Understanding
 
Oracle Cloud Infrastructure (OCI) Document Understanding is an AI service that enables developers to extract text, tables, and other key data from document files through APIs and command-line interface tools. With OCI Document Understanding, you can automate tedious business processing tasks with prebuilt AI models and customize document extraction to fit your industry-specific needs.

Reviewed: 22.09.2025


# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [Reusable Assets Overview](#reusable-assets-overview)

# Team Publications

## LiveLabs and Workshops

- [Introduction to OCI Document Understanding](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3585)
- [Search Documents stored in Object Storage using Opensearch, Generative AI, Semantic Search, RAG](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3762)
- [Develop with Oracle AI and Database Services: Gen, Vision, Speech, Language, OML, Select AI, RAG and Vector](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3874&clear=RR,180&session=10041712875174)
- [Oracle Integration 3 - Build Intelligent Invoice Automation with OCI Document Understanding and OIC Decisions](https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=4193)
- [Automate Invoice handling using Oracle APEX and OCI Document Understanding](https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3948)

## GitHub

- [Enhanced Document Understanding with LLMs](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/generative-ai-service/Document%20Processing%20with%20GenAI/doc-understanding-and-genAI)
    - A Streamlit-based app comparing and expanding on traditional Document Understanding (OCI DU) + LLM approach vs. a multimodal LLM for extracting structured data from documents (PDFs, images). This is is aimed at highlighting the strengths of each of our services and the power GenAI brings in combining these approaches for the best handling of complex documents.
- [Invoice Document Processing from Gmail into ERP systems using OCI Document Understanding & Oracle Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/ai-document-understanding/ai-email-invoice)
    - Explore how we can process invoice documents from Gmail into an ERP System in real-time using OCI Document Understanding and Oracle Integration Cloud (OIC). This solution combines a low-code approach to capture Gmail messages in real-time with Google Cloud Pub/Sub Adapter, extract invoice data with AI Document Understanding and create invoices in ERP systems using Oracle Integration Cloud ERP adapters.
- [Document Evaluation Tool using OCI Generative AI, Document Understanding & Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai/generative-ai-service/doc-evaluation-genai)
    - Explore how to make a handy tool that helps to evaluate documents using Oracle Generative AI, OCI Document Understanding, and Oracle Integration Cloud (OIC). This application combines a low-code approach to orchestrate LLM AI services and applications using Oracle Integration Cloud and Generative AI prompting techniques for tasks like document key criteria extraction, summarization, and evaluation.

## Architecture Center

- [Enable a Low Code Modular LLM App Engine using Oracle Integration and OCI Generative AI](https://docs.oracle.com/en/solutions/oci-generative-ai-integration/index.html)
- [Process unstructured documents intelligently](https://docs.oracle.com/en/solutions/oracle-integration-process-documents-intelligently/index.html)
- [Implement an API management platform for enterprise AI models and services](https://docs.oracle.com/en/solutions/implement-ai-model-api-management/index.html)
- [Data platform - decentralized data platform](https://docs.oracle.com/en/solutions/data-platform-decentralized/index.html)

# Useful Links

- [AI Solutions Hub](https://www.oracle.com/artificial-intelligence/solutions/)
- [Document Understanding Oracle.com Page](https://www.oracle.com/artificial-intelligence/document-understanding/)
- [Document Understanding Documentation](https://docs.oracle.com/iaas/document-understanding/document-understanding/using/home.htm)
- [Other GitHub Examples](https://github.com/oracle-samples/oci-data-science-ai-samples/tree/master/labs/ai-document-understanding)

## Customer Stories
 
- [Trailcon Leasing: Low-code and AI for Automating Invoice Processing & Approval Workflow](https://www.youtube.com/watch?v=TsbNU6xdQPw)
- [Careem increases efficiency and cuts invoice process time 70% with Oracle AI](https://www.oracle.com/customers/careem-case-study/)
- [DMCC reshapes HR and enterprise operations with Oracle GenAI](https://www.oracle.com/customers/dmcc-case-study/)

# Reusable Assets Overview

## Cloud Coaching
- [Cloud Coaching - Boost Your Oracle AI Services](https://youtu.be/VVWTqqlIEhg)
    - Learn how to Develop a Multi-Chain Document Evaluation Apps with Oracle Generative AI, Document Understanding, and Integration Cloud.
    - Integrate OCI AI Speech Service and Generative AI Summarization with Oracle Integration Cloud and Visual Builder
    - Describe an image using OCI AI Vision, Generative AI Service and Oracle Integration

- [Cloud Coaching - How to code and develop a Web (or Mobile) Application with Visual Builder that uses and leverages OCI Document Understanding Service](https://youtu.be/0oHixpA9JDc?si=3CWh0d2RpuEzzLKU)
    - Learn how to create applications that read, modify, and classify documents with a couple of clicks using our low code development platform and some of the OCI AI services offering

- [Cloud Coaching - AI Based & Real Time Gmail Invoice Documents Processing into Oracle Fusion ERP Cloud](https://youtu.be/wq7HH-WYslU?si=wBqH5eEkcC0hYKqj)
    How can you speed up your Account Payable Invoice Processing Cycle? Document Understanding and OCI Intelligent Automation Engine running on top of Oracle Fusion ERP Cloud can help:
    - Through a live demo, we show how to use it to enable an AI-based, Event-Driven, and Real-Time Invoice Processing Solution into Oracle Fusion ERP Cloud on top of Gmail Invoices as Attachments
    - Learn how Oracle Integration Cloud combined with OCI Streaming allows real-time capture of Gmail Messages (leveraging Gmail Push Notifications via Google Cloud Pub/Sub)
    - Then, using AI Document Understanding, uncover Invoice document data using the Key-Value Extraction and automatically load it into Oracle Fusion ERP Cloud using Oracle Integration Cloud's native connectors

- [Cloud Coaching - Automating Invoice Handling using OIC and AI Document Understanding Service](https://www.youtube.com/watch?v=pjdQzFscOrk)
    - In this session, we demonstrate how you can use OCI AI Document Understanding service's pre-trained models to extract key information from invoices and use Oracle Integration Cloud to automate the whole process. It also includes kick-starting process workflows where human intervention is required.

    - [Oracle AI Invoice Handling Solution](https://github.com/oracle-devrel/oci-ai-invoice-handling)

- [Cloud Coaching - Low Code Modular RAG-based Knowledge Search Engine using Oracle GenAI](https://www.youtube.com/watch?v=KkVomurY_0Q)
    - In this coaching session, you’ll learn how to use low-code integration with Oracle Integration Cloud to integrate and orchestrate social media channels like WhatsApp, Business channels like a Web Application built in Oracle Visual Builder, productivity channels like OCI Object Storage, local large and small language models (LLMs), and vector databases to ingest live data into the RAG-based Knowledge Search Engine store.
    - You'll use Oracle Cloud Infrastructure (OCI) Document Understanding to extract information from different document types. Leverage OCI Generative AI for document summarization, generation, and synthesis of answers to questions on documents.
    - Use OCI DB Cloud Service 23AI for Document Extraction, Vector Search, and Embedding (using ONNX local models to the DB) capabilities, and apply local OCI Data Science re-ranking models for better answers from advanced RAG.

- [Document Processing with Oracle Content Management, Integration Cloud & AI Document Understanding](https://www.youtube.com/watch?v=vNxK7s-W8J0)
    - Ingesting & indexing business documents like Contracts or Invoices into a content repository from various sources and then applying AI Document Understanding's document classification functionality as well as metadata extraction dramatically decreases manual effort for successfully processing documents for your business. Coupled with Oracle Integration Cloud's application integration capabilities that can accommodate integration flows between all services and a customer's application ecosystem, Oracle Cloud Infrastructure provides all the necessary tools to build such solutions in a low code development approach.

- [Integrating Oracle Digital Assistant with Document Understanding Using Oracle Integration Cloud](https://www.youtube.com/watch?v=0S6eSUNDdc8)
    - Join us for an insightful webinar on enhancing Oracle Digital Assistant (ODA) by integrating Oracle Cloud Infrastructure (OCI) Document Understanding Service with the help of Oracle Integration Cloud (OIC).
    - Explore how to:
        - Uploading documents within ODA
        - Extract key-value data using Document Understanding models
        - Leverage OIC for seamless document processing


## Blogs

- [OCI Document Understanding: Using OJET apps with TypeScript](https://blogs.oracle.com/developers/post/oci-document-understanding-using-ojet-apps-with-typescript)

- [Extract key values with Oracle Analytics and OCI Document Understanding](https://blogs.oracle.com/analytics/post/innovate-with-oracle-analytics-and-ai-document-understanding)


## Demos & Events

- [How to Use OCI Document Understanding's AI Service: Demo](https://www.youtube.com/watch?v=F3VUY3Yz324)
    - Basic demo of OCI Document Understanding.
- [Low-Code Modular RAG-Based Knowledge Search Engine](https://www.oracle.com/artificial-intelligence/low-code-modular-rag/)
    - Use Oracle Cloud Infrastructure (OCI) Document Understanding to extract information from different document types. Leverage OCI Generative AI for document summarization, generation, and synthesis of answers. Use Oracle Base Database Service for document extraction, vector search, and embedding into the database using Open Neural Network Exchange local models and apply local OCI Data Science models for better answers from advanced RAG.
- [Automate Invoice Handling with OCI Document Understanding](https://www.oracle.com/artificial-intelligence/automate-invoice-processing/)
    - OCI Document Understanding and Oracle Integration to extract key information from invoices and load them into a system of records in an enterprise resource planning (ERP) system.
- [Processing Invoices in Email Using OCI Document Understanding and Oracle Integration Cloud](https://www.oracle.com/artificial-intelligence/processing-invoices-in-email/)
    - This project will show you how to use Oracle Cloud Infrastructure (OCI) Document Understanding and OCI Integration Services to process invoices in email, freeing up employees to handle more important tasks.
- [Evaluating Documents using OCI Generative AI and OCI Document Understanding](https://www.oracle.com/artificial-intelligence/evaluating-document/)
    - How to make a handy tool that helps evaluate documents using Oracle Cloud Infrastructure (OCI) Generative AI, OCI Document Understanding, and Oracle Integration Cloud. This tool can be useful in many situations: evaluating part specifications, helping check the RFP compliance in a vendor bid, or understanding what’s in a bunch of email attachments without opening each one. These are just a few examples for this powerful technology—it can be applied to any industry and is adaptable to departments including HR, procurement, marketing, customer service, and more.


# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
