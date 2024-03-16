# Shared Assets

This section contains various examples related to Application Integration: demo videos and code examples, articles, blogs, presentations, and reference architectures. Links to public content are listed below, while the assets can be found in subfolders.

# Team Publications

## Architecture Center

- [Enable a Low Code Modular LLM App Engine using Oracle Integration and OCI Generative AI](https://docs.oracle.com/en/solutions/oci-generative-ai-integration/index.html)
    - This reference architecture lets you understand the necessary considerations and recommendations to enable an AI-based, modular and event-driven  LLM App Engine using a low-code approach with Oracle Integration as the LLM orchestrator, OCI Generative AI and other OCI services
    - Build enterprise-grade, modular, scalable, secure & maintainable LLM Apps

- [Enable multicloud integrations from Oracle Cloud ERP to Microsoft Azure SQL Database](https://docs.oracle.com/en/solutions/oci-multicloud-erp-azure/index.html)
    - Reference Architecture on the Oracle Architecture Center, which provides the necessary considerations and recommendations to enable a multicloud, event-driven, and no-code integration solution to receive real-time feeds from Oracle Cloud ERP and send those to a private Microsoft Azure SQL Database, leveraging a component Oracle Integration provides called the connectivity agent, to facilitate on-premises/multicloud integrations
- [Implement message-level encryption in Oracle Integration Cloud using OCI Vault](https://docs.oracle.com/en/solutions/oic-message-level-encryption/index.html#GUID-5C843938-A470-4584-9048-4361025358C6)
    - Message-level encryption (MLE) is a security technique used to protect the confidentiality and integrity of a message during transmission. It involves using encryption algorithms to scramble the contents of a message so that only the intended recipient, with the decryption keys, can read it. This reference architecture shows how you can implement message-level encryption in OIC using OCI Vault Service.

## Demos

- [Oracle Integration - Realtime File Processing from Object Storage](https://www.youtube.com/watch?v=HnpYrussmWw)

    - Discover a hands-on approach to processing real-time files from OCI Object Storage using Oracle Integration Cloud, OCI Events and OCI Streaming Service.No need for you to run scheduled jobs and checking the OCI Object Bucket for new files, by enabling Events in OCI Object Storage you can transmit Events like OCI Object Create, OCI Object Update, OCI Object Delete etc. to an OCI Stream in Real-time and configure OCI Stream Adapter in Oracle Integration as a trigger to receive the data in real time and process the file.
    - This video will show you step by step guide to achieve this.   

- [Cloud Coaching Webinar: Real-Time Outlook Email Analysis with Oracle Integration & AI](https://youtu.be/qzyzdAZjUU0?si=moC-O47m7L1nrhqx)
    - Through a Live Demo you will see how Oracle Integration Cloud work seamlessly with Oracle Cloud Streaming & API Gateway for instant Outlook Messages capture via Microsoft Graph Webhooks

    - Explore Email Sentiment Analysis & Categorization with Oracle Cloud AI Language Service

    - Explore Email "Quick Replies" Generation with Oracle Cloud Generative AI Service (in Beta Program, limited availability)

    - Explore No-Code Integration flow into Oracle Autonomous Database & Automatic Creation of Service Tickets into Customer Service Apps, all orchestrated by Oracle Integration Cloud

    - Finally, watch live Email Classification & Analysis Dashboard with Oracle Analytics Cloud

- [Cloud Coaching On-Demand: Oracle Integration (OIC3) Provisioning and User Access with Identity Domains](https://youtu.be/osuCdujq6-A)
  - This video shows how to provision OIC and how to setup user access to OIC in a cloud account with Identity Domains.

- [Cloud Coaching On-Demand: Enabling a WhatsApp Customer HelpMate using OCI Generative AI, AI Language & Integration](https://youtu.be/ryo3wVB_69E)
    - Learn how Oracle Integration Cloud and Oracle Cloud Infrastructure (OCI) Streaming allow real-time capture of WhatsApp messages.

    - Use OCI Generative AI (in pre-availability) for "Customer Service Quick Replies" Generation for Whatsapp Neutral Messages (customer questions, queries, etc.), sentence-level sentiment analysis from OCI AI Language to uncover overall sentiment and set service ticket severity for negative Whatsapp messages, automatically classify Customer Service tickets through OCI AI Language custom text classification and aspect-based sentiment analysis (ABSA) services.

    - All this automation using OCI AI Services APIs orchestrated by Oracle Integration Cloud (using no-code integration approach).

- [Cloud Coaching Webinar: AI Based & Real Time Gmail Invoice Documents Processing into Oracle Fusion ERP Cloud](https://youtu.be/wq7HH-WYslU)
    - How can you speed up your Account Payable Invoice Processing Cycle? Document Understanding and OCI Intelligent Automation Engine running on top of Oracle Fusion ERP Cloud can help.

    - Through a live demo, we show how to use it to enable an AI-based, Event-Driven and Real-Time Invoice Processing Solution into Oracle Fusion ERP Cloud on top of Gmail Invoices as Attachments.

    - Learn how Oracle Integration Cloud combined with OCI Streaming and API Gateway allow real-time capture of Gmail Messages (leveraging Gmail Push Notifications via Google Cloud Pub/Sub).

    - Then, using AI Document Understanding, uncover Invoice Documents Data using the Key-Value Extraction and automatically load it into Oracle Fusion ERP Cloud using Oracle Integration Cloud's native connectors.

- [Usecase - Fusion HCM Payslips to FTP](https://www.youtube.com/watch?v=KxKfnmfHPc8)
    - This video will demonstrate a common use case, how you can extract data from Fusion HCM using Oracle Integration. You will learn how to download Payslips from Fusion HCM and send it to FTP Server using Oracle Integration
        Demonstration includes:
        - Understanding Fusion HCM APIs
        - Creating Integration using HCM, Rest and FTP Adapters
        - Passing Absolute path at run time for a Rest invoke
        - Switch Action to create multiple paths based on data
        - For Action to traverse through multiple records

- [Cloud Coaching Webinar: Multi-Cloud Employee New Hire Delta Feeds from Oracle HCM Cloud into Azure Data Lake](https://youtu.be/sn0qLz4jJ38)
    - Demo Video where we show how to quickly and easily enable a multi-cloud integration solution to feed a private Microsoft Azure Data Lake (Azure Blob Storage) with Employee New Hire Delta Feeds coming from Oracle Fusion HCM Cloud. Learn how to use a no-code approach with Oracle Integration Cloud's prebuilt connectors and connectivity agent (key enabler for multicloud integrations) and Oracle Cloud Infrastructure Streaming (Kafka-based)

- [Oracle Integration Cloud - Feature - Recipes](https://youtu.be/Yfim7S11gU8)
    -This video will explain Oracle Integration Cloud Feature Recipes. Recipes are pre-built integrations covering a certain use case scenario. A recipe contains all the resources required for a specific integration use case. The resources include integration flows, connections, lookups, and certificates. Use a recipe to quickly get started on your integration journey.
    Demonstration includes:
    - Overview of Recipes
    - How to find and install recipes
    - Run and Test Recipes
    - The following Recipes demonstrated end-to-end
        - Oracle Fusion PopUp Notification
        - Oracle ERP Cloud FTP Server Business Event
        - SOAP Calculator Multiple Operations

- [Oracle Integration Cloud - Feature - Projects](https://youtu.be/CxNDbBnWWYU)
    -This video will explain Oracle Integration Cloud Feature Projects, and how you can use it. Enterprises often have hundreds of integrations to manage and monitor. Developers want to focus on specific integration components involved with an automated business process. With OIC Project, all related integrations and their components are in a single unified workspace. Additionally, projects provide robust life cycle management and risk-free updates to prebuilt integrations.

    Demonstration includes:
    - Creating Project & setting Role Based Access
    - Creating Connections (FTP, Rest, Autonomous Database(ATP) using JDBC With OCI Signature Security Policy)
    - Creating Lookup
    - Creating App Driven Integration (Bulk Load Data to ATP)
    - Creating Schedule Integration
    - Run, Observe and monitor the Integrations
    - Create Deployments and Migrate to another instance
    - Creating a new version of Integration, Deployment, and Migrate to another Instance
    - Add Schedule and see Future Runs
    - Check Design Time Audit

- [Oracle Integration Cloud - Feature - Publish & Subscribe Events](https://youtu.be/3gZcHnPJtuk)

    -This video will explain Oracle Integration Cloud Feature Events, and how Events can be used to create publish and subscribe integration patterns.

    Demonstration includes:
    - Creating an Event in Oracle Integration Cloud
    - Creating an Integration that publishes the Event
    - Creating an integration that subscribes to the Event and adds data in ServiceNow
    - Creating an integration that subscribes to the Event and appends data in a file stored in an FTP Server

- [Oracle Integration Cloud - Feature - Parallel Action](https://youtu.be/BTtPsDyiVLo)
    -This video demonstrates how you can use parallel action in Oracle Integration.
    Parallel action is used to process tasks in parallel to improve integration performance and response times.

    The demonstration includes Rest Based App Driven Integration that takes Supplier Data and Creates the Supplier in parallel in two systems:
    - Oracle ERP Cloud
    - Autonomous Database
- [Red Hot Webinar: Event-Driven and Low-Code Document Approval Process and Lifecycle Automation](https://youtu.be/kQuF2XOYKOc)
    - Demo Video about enabling Document Lifecycle Automation using a Low-Code Approach with OCI Integration (ProcessAutomation, Integration & Visual App Builder), Content Management (embedded document mgmt & Microsoft O365 online editor plugin), Streaming (kafka-based) and Autonomous Database (document business data store).
- [Cloud Coaching - Automating Invoice Handling using OIC and AI Document Understanding Service](https://www.youtube.com/watch?v=pjdQzFscOrk)
    - In this session, we demonstrate how you can use OCI AI Document Understanding service's pre-trained models to extract key information from invoices and use Oracle Integration Cloud to automate the whole process. It also includes kick-starting process workflows where human intervention is required.
- [Smarter Apps with AI, OIC partner community webcast June 2023](https://videohub.oracle.com/media/Smarter+AI+Apps+with+OIC+partner+community+webcast+June+2023-1080p30/1_m2yjnvf9)
    - OCI Language and Document Understanding are cloud-based AI services for performing sophisticated text analysis and extracting data from all kinds of documents e.g. Passport, Driving License, Invoices, Receipts, etc. You can use these services to build intelligent applications by leveraging REST APIs. You can use these services to build intelligent applications by leveraging REST APIs and automating using Oracle Integration Cloud. This allows you to process unstructured text for use cases such as sentiment analysis, service ticket classification, document extraction, and more using pre-trained models or your own custom models leveraging OCI Data Labelling.
- [Cloud World Session: LRN1261 - Building a Multicloud, Event-Driven PO Feed Solution with Low-Code Integration](https://youtu.be/eGnbWn9btYA)
    - Demo Video showed during Oracle Cloud World 2022, where we show how to quickly and easily enable a real-time and event-driven solution to feed a Microsoft Azure SQL database with purchase order data coming from Oracle Enterprise Resource Planning (ERP). Learn how to use a low-code approach with Oracle Integration Cloud's prebuilt connectors and connectivity agent and Oracle Cloud Infrastructure Streaming (Kafka-based)
- [Cloud World Session: LRN3620 - Enabling an Event-Driven, Real-Time Twitter Sentiment Analysis Dashboard](https://youtu.be/9hvUxLSE3Vg)
    - Demo Video showed during Oracle Cloud World 2022, where we show how to enable an event-driven, real-time Twitter analysis dashboard, using an Oracle Cloud Infrastructure (OCI) Python Twitter Stream Listener, OCI Streaming (Kafka-like service), OCI AI Language Bulk Sentiment Analysis, Oracle Integration Cloud, Oracle Autonomous Database, and Oracle Analytics Cloud. See how this can keep retention and referrals high. Take part by tweeting positively and/or negatively about a specific hashtag and see how OCI AI Language Sentiment Analysis services work in real-time
- [Red Hot Webinar: Multi-cloud & No Code GL Journal Integration](https://youtu.be/S6dMBqJRngw)
    - Demo Video about a Multi-Cloud & No-Code Integration Approach for GL Journal Bulk Data Loads from AWS S3 into Oracle Fusion Cloud ERP, using Oracle Integration Cloud native adapters and the connectivity agent as a key enabler for multi-cloud integration use cases
- [Red Hot Webinar: Event-Driven & Real-Time Order Feeds from Shopify to MSFT SQLServerDB with No-Code Integration](https://youtu.be/IFrFI-feWQU)
    - Demo Video about enabling Real-Time and Event-Driven Order feeds from Shopify to an On-Prem Microsoft SQLServer DB, using No-Code Integration with Oracle Cloud Integration and Streaming (Kafka-based)
- [Cloud Coaching Webinar: Building a Multi-Cloud, Event-Driven Service Request Feeds Solution using No-Code Integration](https://youtu.be/gvENaT6fcYY)
    - Demo Video where we show how to quickly and easily enable a real-time and event-driven solution to feed a Microsoft Azure SQL database with service request data coming from Oracle Fusion CX Service. Learn how to use a no-code approach with Oracle Integration Cloud's prebuilt connectors and connectivity agent (key enabler for multicloud integrations) and Oracle Cloud Infrastructure Streaming (Kafka-based)
- [OIC - Recipes and Accelerators - Exploit Reuse](https://www.youtube.com/watch?v=qt_vX5CpRL4)
    - Demo Video (part of Red Hot Webinars) where we show how to use a Recipe (HCM Employee sync) and how to enhance it through an available accelerator.
- [Cloud Integration is not only for SaaS: an EBS modernization ](https://www.youtube.com/watch?v=E_Kz-r26La4)
    - Demo Video (part of Red Hot Webinars) where we show an initiative to enhance and modernize the EBS platform for better reach and ease of users. No change to existing workflow approvals in EBS and standard EBS Self Service Submissions has been required. From a mobile VBCS app employees are able to submit their IQAMA Renewal (Residence renewal) or Overtime Work Requests and their managers (up to 2 management chains up) are able to check the request and perform their approval. It uses EBS Integrated SOA Gateway which exposes custom and standard EBS APIs reached through OIC REST adapter.
- [Oracle Process Automation - BPM Structured Process - Travel Request Demo](https://www.youtube.com/watch?v=MAVZzBX8nQY)
    - Demo video showing how to create and run a BPM structured process. Shows how to manage a Travel request through automatic decisiona and Human Task approval steps. This demo implements [Oracle Live Lab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=3362&p210_wec=&session=17064424204924), Lab 1
- [Oracle Process Automation - BPM Dynamic (Case Management) Process - Car Rental Demo](https://www.youtube.com/watch?v=JcB4FDIEzPo)
    - Demo video showing how to create and run a BPM Dynamic (Case Management) Process. Shows how to manage Car Rental Process through Case Management stages, Global activities and combination of Human Tasks, Structured BPM processes and Milestones in Case Management stages. This demo implements [Oracle Live Lab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=3362&p210_wec=&session=17064424204924), Lab 2

## Blogs

- [Practical Guide to using HCM Data Loader with Oracle Integration](https://blogs.oracle.com/integration/post/practical-guide-to-use-hcm-data-loader-with-oracle-integration)
    - This blog addresses some key practical steps and prerequisites needed to use HCM Data Loader with Oracle Integration Cloud. Steps like generating Business Object Mapping file in Fusion HCM. How to work with nxsd in Oracle Integration Cloud and more.

- [OCI Signature in Oracle Integration Rest Adapter for OCI Rest APIs](https://blogs.oracle.com/integration/post/oci-signature-in-rest-adapter-for-oci-rest-apis)
    - This blog provides step by step guide on configuring OCI Signature Version 1 security policy in OIC Rest Adapter to call any OCI Rest APIs.


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
