# Shared Assets

This section contains various examples related to Application Integration: demo videos and code examples, articles, blogs, presentations, and reference architectures. Links to public content are listed below, while the assets can be found in subfolders.

# Team Publications

## Technical Case Study

- [Careem increases efficiency and cuts invoice process time 70% with Oracle AI](https://www.oracle.com/customers/careem-case-study/)

    - Business Challenge: 
        Careem is a Dubai-based super app with operations in over 70 cities, covering 10 countries across the Middle East, Africa, and South Asia regions. The company was founded with a mission to simplify transportation and create earning opportunities as a ride-hailing marketplace. Careem wanted to enhance aspects of its back-end operations—such as manual invoice management—to enable greater scalability and accuracy. 
    - Results: 
        The adoption of Oracle’s AI-powered invoice automation solution has transformed Careem Groceries’ operations, unlocking new opportunities to innovate.
        - Cut invoice processing time by 70%, from 3 minutes to under 1 minute, freeing over 332 hours monthly
        - Reduced errors while enhancing accuracy and compliance
        - Handle more than 10,000 invoices per month and scale 37% more volume without additional staff
        - Automate workflows and simplify scalability, strengthening Careem’s position in Dubai’s Q-commerce market
    - Oracle Solutions: 
        - Oracle Integration
        - Oracle Cloud Infrastructure Document Understanding
        - Oracle Autonomous Transaction Processing
        - Oracle APEX

## Architecture Center

- [Enable a Low Code Modular LLM App Engine using Oracle Integration and OCI Generative AI](https://docs.oracle.com/en/solutions/oci-generative-ai-integration/index.html)
    - This reference architecture lets you understand the necessary considerations and recommendations to enable an AI-based, modular and event-driven  LLM App Engine using a low-code approach with Oracle Integration as the LLM orchestrator, OCI Generative AI and other OCI services
    - Build enterprise-grade, modular, scalable, secure & maintainable LLM Apps

- [Enable multicloud integrations from Oracle Cloud ERP to Microsoft Azure SQL Database](https://docs.oracle.com/en/solutions/oci-multicloud-erp-azure/index.html)
    - Reference Architecture on the Oracle Architecture Center, which provides the necessary considerations and recommendations to enable a multicloud, event-driven, and no-code integration solution to receive real-time feeds from Oracle Cloud ERP and send those to a private Microsoft Azure SQL Database, leveraging a component Oracle Integration provides called the connectivity agent, to facilitate on-premises/multicloud integrations
- [Implement message-level encryption in Oracle Integration Cloud using OCI Vault](https://docs.oracle.com/en/solutions/oic-message-level-encryption/index.html#GUID-5C843938-A470-4584-9048-4361025358C6)
    - Message-level encryption (MLE) is a security technique used to protect the confidentiality and integrity of a message during transmission. It involves using encryption algorithms to scramble the contents of a message so that only the intended recipient, with the decryption keys, can read it. This reference architecture shows how you can implement message-level encryption in OIC using OCI Vault Service.
- [Set up a landing zone architecture with Oracle Integration](https://docs.oracle.com/en/solutions/set-up-lz-oic/index.html#GUID-E2C6E096-E695-4813-94F1-0C697EEEC8F0)
   - To run integrations in Oracle Cloud, you need a secure environment that you can operate efficiently. Oracle Integration is a Cloud Native service designed to address your security requirements. This reference architecture describes the components and concepts that enable you to build hybrid integrations.These components conform to the landing zone template and concepts that meet the security guidance prescribed for Oracle Cloud Infrastructure's CIS Foundation Benchmark.

## Demos

- [Setting Up OAuth with JWT User Assertion in OIC: Identity Propagation from VBCS, OIC to OPA](https://youtu.be/UdOXA53BQMM?si=YIjvJbNrMblqhczM)

    - In this step-by-step tutorial, you'll learn how to setup OAuth 2.0 using JWT User Assertion in Oracle Integration Cloud (OIC) to enable secure identity propagation between Oracle Integration and Oracle Process Automation (OPA). You will also see how idenity can easily propogate from Visual Builder to OIC to OPA.

    - The video covers:
        - Creating client confidential application
        - Certificate creation and upload
        - Constructing the JWT header and payload
        - Configuring the REST connection in OIC
        - Full OAuth and identity propagation flow


- [Developer Coaching - Unlocking Robotic Process Automation with Oracle Integration](https://youtu.be/Gh33NJfoanU?si=iVIZQ4fgrQVTVdYc)

    - Developer Coaching Session "Unlocking Robotic Process Automation with Oracle Integration for Developers", where we explore the full spectrum of capabilities offered by Oracle Integration Cloud (OIC). 

    This powerful platform seamlessly combines integration, process automation, low-code visual development, and advanced Robotic Process Automation (RPA) to empower developers and streamline business processes. 

    This session will focus on Robotic Process Automation. Learn how to automate repetitive tasks, orchestrate end-to-end workflows, and accelerate productivity using RPA tailored for modern development needs. Whether you're scaling applications, optimizing business operations, or innovating digital solutions, this session will provide you with the expertise and practical insights to harness the full potential of RPA within OIC. Don’t miss this chance to elevate your automation strategy!

- [Developer Coaching Session : Automate Expenses - OCI Document Understanding + Oracle Process Automation](https://youtu.be/orqQoTFrKBc?si=PCCSYWtblxLWCIwn)

    - OCI Process Automation enables businesses to streamline workflows, reduce manual efforts, and ensure consistent decision-making by harnessing intelligent services to automate repetitive processes and integrate seamlessly with other business applications. 
    
    In this session, we explore out of the box recipes, demonstrating how to optimize the expense report creation process using intelligent document processing and decision service capabilities within OCI Process Automation.

    Key Takeaways:
    1. Automated Data Extraction:
        The process starts when users upload receipts as part of their expense reports in OCI Process Automation custom form.
        OCI Document Understanding automatically scans and extracts data, populating the expense report with necessary line items.
    2. Approval Workflow:
        Once the expense report is submitted, the OCI Process Automation decision service evaluates it for automatic approval or manual review.
        Decisions are based on total amount, cost center, expense type, and receipt attachments.
    3. Manual Review and Integration:
        Expense reports flagged for review are sent to line managers for approval.


- [Setting Up OAuth and Calling Oracle Integration APIs: A Step-by-Step Guide](https://youtu.be/UrptzZbycm4?si=opv0_wc5F7SV86nx)

    - In this demo video, we provide a step-by-step guide to setting up OAuth and calling Oracle Integration APIs. We'll walk you through registering your application, obtaining client credentials, and generating OAuth tokens. 

    Using Postman, we'll demonstrate how to make authenticated API calls to Oracle Integration, ensuring secure data retrieval and manipulation.

    Parameters referred in video:

    Grant Type : Client Credentials/Authorization Code
    Access Token URL : https://[idcs url]/oauth2/v1/token
    Client ID: xxxxx
    Client Secret: xxxxxx
    Scope: https://xxxxx:opc:resource:consumer::all
    Auth URL* : https://[idcs url]/oauth2/v1/authorize
    Redirect URL* : https://[oic url]/icsapis/agent/oauth/callback

    "*" parameters are required for Authorization Code flow only.

- [Oracle Process Automation - File Manager Component](https://youtu.be/ZnGPteYE_tA?si=KAFsgffX1ZsRkfer)

    - The File Manager component allows end users to upload one or more documents using a process form to an external system.This video demonstrate the use of the File Manager

    Demonstration Includes

        - Creating a Process in Oracle Process Automation
        - Creating a Web UI with File Manager Component
        - Walk through of Oracle Integration Project and Integrations to Dowload, List, Delete and Upload files in OCI Object Storage
        - Configuring Rest API Connector to Integrate with OIC Integrations
        - Configuring File Manager Component and connecting with the Integrations
        - Validate, Activate, Test the Process

- [Cloud Coaching - Boost Your Oracle AI Services](https://youtu.be/VVWTqqlIEhg)
    - Learn how to Develop a Multi-Chain Document Evaluation Apps with Oracle Generative AI, Document Understanding, and Integration Cloud.
    - Integrate OCI AI Speech Service and Generative AI Summarization with Oracle Integration Cloud and Visual Builder
    - Describe an image using OCI AI Vision, Generative AI Service and Oracle Integration

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

-[A Beginner’s Guide to Using OCI Generative AI with Oracle Integration](https://www.linkedin.com/pulse/beginners-guide-using-oci-generative-ai-oracle-harris-qureshi-wqcof/)

Designed for Oracle Integration developers, this beginner-friendly guide walks you through:

 • Exploring the OCI Generative AI Playground
 • Understanding the OCI Gen AI Inference API
 • Calling OCI Gen AI directly from Oracle Integration

Whether you're experimenting or building real use cases, this step-by-step intro will help you bridge the gap between integration and Gen AI. It also includes a hands on demo.

- [Agentic AI Workflows in Oracle Integration: Unlocking the Power of Generative AI](https://www.linkedin.com/pulse/agentic-ai-workflows-oracle-integration-unlocking-power-qureshi-nxm0f)

    What if your integrations could reason, plan, and act on their own? In this article, I explore how Agentic AI Workflows in OIC, powered by OCI Generative AI, enable dynamic, 𝙨𝙚𝙡𝙛–𝙤𝙥𝙩𝙞𝙢𝙞𝙯𝙞𝙣𝙜 𝙨𝙮𝙨𝙩𝙚𝙢𝙨 𝙩𝙝𝙖𝙩 𝙖𝙙𝙖𝙥𝙩 𝙖𝙣𝙙 𝙧𝙚𝙨𝙥𝙤𝙣𝙙 𝙞𝙣 𝙧𝙚𝙖𝙡 𝙩𝙞𝙢𝙚.

    You’ll learn how to:

    - Replace hard-coded logic with 𝘁𝗼𝗼𝗹-𝗰𝗮𝗹𝗹𝗶𝗻𝗴 LLMs that make decisions
    - Design workflows that 𝗮𝗱𝗮𝗽𝘁 𝗶𝗻 𝗿𝗲𝗮𝗹 𝘁𝗶𝗺𝗲 to changing inputs and context
    - Orchestrate 𝗮𝗰𝘁𝗶𝗼𝗻𝘀 𝗮𝗰𝗿𝗼𝘀𝘀 𝘀𝘆𝘀𝘁𝗲𝗺𝘀 without rigid dependencies
    - Treat 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗶𝘃𝗲 𝗔𝗜 𝗮𝘀 𝗮 𝘁𝗿𝘂𝗲 𝗶𝗻𝘁𝗲𝗴𝗿𝗮𝘁𝗶𝗼𝗻 𝗽𝗮𝗿𝘁𝗻𝗲𝗿—not just a chatbot

    The article also includes 𝗵𝗮𝗻𝗱𝘀-𝗼𝗻 𝗱𝗲𝗺𝗼𝘀 to illustrate these concepts in action.


- [From Prompt to Payload: Using JSON Response Format in OCI Gen AI with Oracle Integration](https://www.linkedin.com/pulse/from-prompt-payload-using-json-response-format-oci-gen-harris-qureshi-4yk9f)

    - Tired of clunky AI integrations? Discover how to seamlessly combine OCI Generative AI’s JSON output with Oracle Integration Cloud (OIC)—unlocking smarter automation and cleaner data pipelines. 
    In this article, I break down:
        - ✅ Step-by-step integration tactics for OIC + OCI Generative AI
        - ✅ How structured JSON responses reduce downstream complexity
        - ✅ Why this duo is a game-changer for enterprise scalability   

- [GenAI-based Procurement Q&A App using Text-to-SQL and Low-Code Integration](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/procurement-qa-genai/files)
    - In this article, we'll explore how to make a handy tool that helps to enable real-time purchase order feeds into a procurement DB store and also to transform procurement queries in natural language to SQL Queries and synthesize the SQL Response using Oracle Generative AI, Oracle Integration Cloud (OIC) and Oracle Autonomous Database (ADB). This application combines a low-code approach to orchestrate LLM AI services and applications using Oracle Integration Cloud and Generative AI prompting techniques for tasks like text-to-SQL transformations.

- [Real-Time Email Categorization, Sentiment Analysis & "Quick Replies" using OCI AI Language, Generative AI & Oracle Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/ai-language/ai-email-analyis/files)
    - In this article, we'll explore how we can process emails from Outlook in real-time with a low-code approach using Oracle Integration Cloud (OIC), OCI API Gateway and Microsoft Graph API Webhooks, perform sentiment analysis, custom email categorization and email body PII masking using OCI AI Language, and generate email "quick replies" using OCI Generative AI. Finally all this Email Analysis data is sent to Oracle Autonomous Database for further visualization in an Oracle Analytics Cloud Dashboard.

- [Invoice Document Processing from Gmail into ERP Systems using OCI Document Understanding & Oracle Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/ai-document-understanding/ai-email-invoice/files)
    - In this article, we'll explore how we can process invoice documents from Gmail into an ERP System in real-time using OCI Document Understanding and Oracle Integration Cloud (OIC). This solution combines a low-code approach to capture Gmail messages in real-time with Google Cloud Pub/Sub Adapter, extract invoice data with AI Document Understanding and create invoices in ERP systems using Oracle Integration Cloud ERP adapters.

- [Document Evaluation Tool using OCI Generative AI, Document Understanding & Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/doc-evaluation-genai)
    - In this article, we'll explore how to make a handy tool that helps to evaluate documents using Oracle Generative AI, OCI Document Understanding, and Oracle Integration Cloud (OIC). This application combines a low-code approach to orchestrate LLM AI services and applications using Oracle Integration Cloud and Generative AI prompting techniques for tasks like document key criteria extraction, summarization, and evaluation.

- [Describe an image using OCI AI Vision, Generative AI & Integration Cloud](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/vision-genai)
    - In this article, we'll explore how to describe an image using OCI AI Vision Service and OCI Generative AI Service. The application is developed using Oracle VBCS, OIC, OCI AI Vision service, and OCI Generative AI Service. This integrated approach combines the strength of OCI AI Vision and OCI Generative AI Service, allowing for efficient and insightful summarization of image content.

- [Integrate OCI AI Speech Service and Generative AI Summarization with Oracle Integration Cloud & Visual Builder](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/speech-genai)
    - OCI Speech is an AI service that applies automatic speech recognition technology to transform audio-based content into text. Generative AI, The Large Language Model (LLM) analyzes the text input and can generate, summarize, transform, and extract information. Using these AI capabilities, we built a low code application- “Integrate OCI AI Speech Service and Generative AI Service for Summarization in Visual Builder " to invoke AI Speech REST API to convert audio files into text and then further invoke the Generative AI REST API to Summarize it.

- [Practical Guide to using HCM Data Loader with Oracle Integration](https://blogs.oracle.com/integration/post/practical-guide-to-use-hcm-data-loader-with-oracle-integration)
    - This blog addresses some key practical steps and prerequisites needed to use HCM Data Loader with Oracle Integration Cloud. Steps like generating Business Object Mapping file in Fusion HCM. How to work with nxsd in Oracle Integration Cloud and more.

- [OCI Signature in Oracle Integration Rest Adapter for OCI Rest APIs](https://blogs.oracle.com/integration/post/oci-signature-in-rest-adapter-for-oci-rest-apis)
    - This blog provides step by step guide on configuring OCI Signature Version 1 security policy in OIC Rest Adapter to call any OCI Rest APIs.


# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
