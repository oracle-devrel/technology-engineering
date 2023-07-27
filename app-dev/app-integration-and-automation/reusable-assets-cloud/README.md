# Reusable Assets: Cloud

This section contains various examples related to Application Integration: demo videos and code examples, articles, blogs, presentations, and reference architectures. Links to public content are listed below, while the assets can be found in subfolders.

## Architecture Center

- [Enable multicloud integrations from Oracle Cloud ERP to Microsoft Azure SQL Database](https://docs.oracle.com/en/solutions/oci-multicloud-erp-azure/index.html)
    - Reference Architecture on the Oracle Architecture Center, which provides the necessary considerations and recommendations to enable a multicloud, event-driven, and no-code integration solution to receive real-time feeds from Oracle Cloud ERP and send those to a private Microsoft Azure SQL Database, leveraging a component Oracle Integration provides called the connectivity agent, to facilitate on-premises/multicloud integrations
- [Implement message-level encryption in Oracle Integration Cloud using OCI Vault](https://docs.oracle.com/en/solutions/oic-message-level-encryption/index.html#GUID-5C843938-A470-4584-9048-4361025358C6)
    - Message-Level Encryption (MLE) is a security technique used to protect the confidentiality and integrity of a message during transmission. It involves using encryption algorithms to scramble the contents of a message so that only the intended recipient, with the decryption keys, can read it. This reference architecture shows how you can implement message level encryption in OIC using OCI Vault Service.

## Demos

- [Oracle Integration Cloud - Feature - Publish & Subscribe Events](https://youtu.be/3gZcHnPJtuk)

    -This video will explain Oracle Integration Cloud Feature Events, how Events can be used to create publish and subscribe integration pattern.
    
    Demonstration includes.
        - Creating an Event in Oracle Integration Cloud
        - Creating an Integration that publishes the Event
        - Creating an integration that subscribes to the Event and add data in ServiceNow
        - Creating an integration that subscribes to the Event and append data in a file stored in an FTP Server

- [Oracle Integration Cloud - Feature - Parallel Action](https://youtu.be/BTtPsDyiVLo)
    -This video demonstrate how you can use parallel action in Oracle Integration.
    Parallel action is used to process tasks in parallel to improve integration performance and response times. 
    
    Demonstration includes: Rest Based App Driven Integration that takes Supplier Data and Creates the Supplier in parallel in two systems:
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
    - Demo Video where we show to quickly and easily enable a real-time and event-driven solution to feed a Microsoft Azure SQL database with service request data coming from Oracle Fusion CX Service. Learn how to use a no-code approach with Oracle Integration Cloud's prebuilt connectors and connectivity agent (key enabler for multicloud integrations) and Oracle Cloud Infrastructure Streaming (Kafka-based)
- [OIC - Recipes and Accelerators - Exploit Reuse](https://www.youtube.com/watch?v=qt_vX5CpRL4)
    - Demo Video (part of Red Hot Webinars) where we show how to use a Recipe (HCM Employee sync) and how to enhance it through an available accelerator.
- [Cloud Integration is not only for SaaS: an EBS modernization ](https://www.youtube.com/watch?v=E_Kz-r26La4)
    - Demo Video (part of Red Hot Webinars) where we show an initiative to enhance and modernize the EBS platform for better reach and ease of users. No change to existing workflow approvals in EBS and standard EBS Self Service Submissions has been required. From a mobile VBCS app employees are able to submit their IQAMA Renewal (Residence renewal) or Overtime Work Requests and their managers (up to 2 management chains up) are able to check the request and perform their approval. It uses EBS Integrated SOA Gateway which exposes custom and standard EBS APIs reached through OIC REST adapter.

## Blogs

- [Practical Guide to use HCM Data Loader with Oracle Integration](https://blogs.oracle.com/integration/post/practical-guide-to-use-hcm-data-loader-with-oracle-integration)
    - This blog addresses some key practical steps and pre-requisites needed to use HCM Data Loader with Oracle Integration Cloud. Steps like generating Business Object Mapping file in Fusion HCM. How to work with nxsd in Oracle Integration Cloud and more.

- [OCI Signature in Oracle Integration Rest Adapter for OCI Rest APIs](https://blogs.oracle.com/integration/post/oci-signature-in-rest-adapter-for-oci-rest-apis)
    - This blog provides step by step guide on configuring OCI Signature Version 1 security policy in OIC Rest Adapter to call any OCI Rest APIs.


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
