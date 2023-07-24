---
doc:
  author: Ismael Hassane                #Mandatory
  version: 1.3                          #Mandatory
  cover:                                #Mandatory
    title:                              #Mandatory
      - ${doc.customer.name}            #Mandatory
      - Autonomous DB ML Project        #Mandatory
      - Oracle Machine Learning
    subtitle:                           #Mandatory
      - Workload Architecture Document  #Mandatory
      - Solution Definition and Design  #Mandatory
  customer:                             #Mandatory
    name: A Company Making Everything   #Mandatory
    alias: ACME                         #Mandatory
  config:
    impl:
      type: Lift                        #Mandatory: Either 'Lift' or 'Fast Start'. Use with ${doc.config.impl.type}     
      handover: ${doc.customer.name}    #Mandatory: Please specify to whom to hand over the project after implementation. eg.: The Customer, a 3rd party implementation or operations partner, etc.           
  draft: false
  history:
    - version: 1.3
      date: 24 July 2023
      authors: 
        - ${doc.author}
      comments:
        - adding more use-cases and details on OML
    - version: 1.2
      date: 17 February 2023
      authors: 
        - ${doc.author}
      comments:
        - adding the Network Firewall
    - version: 1.1
      date: 12 January 2023
      authors: 
        - ${doc.author}
      comments:
        - Version update
        - Removed reference to OCI Data Science
    - version: 1.0
      date: 13 October 2022
      authors: ${doc.team.2.name}
      comments:
        - Initial version
  team:
    - name: ${doc.author}
      email: ismael.hassane@oracle.com
      role: Cloud Solution Specialist - Analytics & Lakehouse
      company: Oracle
    - name: ACE
      email: ace@oracle.com
      role: Account Cloud Engineer
      company: Oracle
  acronyms:
    ADB: Autonomous Database including ATP, ADW, AJD, etc.
    ADW: Autonomous Data Warehouse                            
  	ATP: Autonomous Transaction Processing                    
  	DEV: Development Environment                              
  	DI : Data Integration                
  	DLH: Data Lakehouse                                       
  	DWH: Data Warehouse                                       
  	ELT: Extract-Load-Transform                               
  	ETA: Estimated Time of Arrival                            
  	OCI: Oracle Cloud Infrastructure                       
  	PROD: Production Environment
  	SLA: Service Level Agreement                              
  	UAT: User Acceptance Test Environment
---



# Document Control
<!-- GUIDANCE -->
<!--
First Chapter of the document, describes meta data for the document. Such as versioning and team members.
 -->

## Version Control

```{#history}
This is the document history. Please use doc.history metadata for compiling the table
```

## Team

<!-- EXAMPLE / TEMPLATE -->

```{#team}
This is the team that is delivering the WAD. Please use doc.team metadata for compiling the table
```

## Table of Acronyms
<!-- Please use doc.acronyms for adding custom acronyms, or include other acronyms modules -->
```{#acronyms}
common
data-lake
```

## Document Purpose
<!-- GUIDANCE -->
<!--
Describe the purpose of this document and the Oracle specific terminology, specifically around 'Workload' and 'Lift'.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
This document provides a high-level solution definition for the Oracle solution and aims at describing the current state, to-be state as well as a potential implementation project scope and timeline. The implementation project will be described as a physical implementable solution. The intended purpose is to provide all parties involved a clear and well-defined insight into the scope of work and intention of the project.

The document may refer to a 'Workload', which summarizes the full technical solution for a customer (You) during a single engagement. The Workload is described in chapter [Workload Requirements and Architecture](#workload-requirements-and-architecture). 

\newpage

# Business Context
<!-- GUIDANCE -->
<!--
Describe the customers business and background. What is the context of the customers industry and LOB. What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customers business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->

## Executive Summary
<!-- GUIDANCE -->
<!--
A section describing the Oracle differentiator and key values of the solution of our solution for the customer, allowing the customer to make decisions quickly.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->

## Workload Business Value
<!-- GUIDANCE -->
<!--
A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree the SMART business value with the customer. Keep it business focused, and speak the language of the LOB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
ACE   | R
-->


The client is developing a new line of business where they will provide credit financing to importers and exporters. The approval process for the credit solution will be quicker than with banks. At the time of booking a consignment, the booking agent can offer it in real-time, saving a great deal of time on paperwork and approval procedures.

A precise credit risk scoring algorithm is crucial for this new service. Machine learning and data science can use historical trade information and make classifications and predictions about importer or exporter credit worthiness. Machine learning models will use 3rd party data and Fusion ERP data since this data is based on factual audited trade information that provides high confidence in data quality.  

\newpage

# Workload Requirements and Architecture

## Overview
<!-- GUIDANCE -->
<!--
Describe the Workload: What applications and environments are part of this Workload, what are their names? Lift will be scoped later and is typically a subset of the Workload. For example a Workload could exists of two applications, but Lift would only include one environment of one application. This Workload chapter is about the whole Workload and Lift will be described late in chapter [Scope](#scope).

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

## Machine Learning Model steps

The below schema lists the necessary tasks in the lifecycle of a machine learning model ranging from data collection to model retraining when performance decays. 

![Ml Lifecycle](assets/MLAI_WAD_v.0.3-492cb605.png)


## Functional Requirements
<!-- GUIDANCE -->
<!--
Provide a brief overview of the functional requirements, the functional area they belong to, the impacted business processes, etc.

Provide a formal description of the requirements as 1. a set of Use Cases or 2. a description of Functional Capabilities or 3. a Requirement Matrix. The three descriptions are not mutually exclusive.

Some Workload team, especially the Analytics and Merging Tech teams, will create new application based on functional requirements, some Workload team will not touch the functional requirements at all and just change the platform under an application. But it is important to understand who is using the system and for what reason.

Recommended Chapter (Mandatory for Analytics and Emerging Tech)

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

In-database machine learning refers to the integration of machine learning algorithms and models directly into a database system. This approach offers several advantages, including reduced data movement, faster predictions, and enhanced security. Here are some use cases for in-database machine learning:

### Use Cases

#### Real-time Credit Risk Assessment

Credit scoring is a crucial process in the banking industry that assesses the creditworthiness of individuals or businesses applying for loans or credit. In-database machine learning can significantly improve the efficiency and accuracy of credit scoring models. 

When customers apply for credit, banks need to make quick and informed decisions about their creditworthiness. Traditional credit scoring models may involve transferring large volumes of data to external systems for analysis, leading to delays in processing applications and potential security risks. In-database machine learning can address these challenges by building credit scoring models directly within the banking database.

By integrating machine learning algorithms into the database, banks can analyze a customer's historical financial data, credit history, transaction behavior, and other relevant factors in real-time. This enables immediate credit risk assessment and decision-making during the application process. In-database machine learning models can quickly evaluate a customer's credit risk profile and provide an instant credit score, facilitating faster approvals for credit products like loans, credit cards, and overdrafts.

Moreover, in-database machine learning allows banks to continuously update and fine-tune their credit scoring models as new data becomes available, ensuring that the models stay relevant and accurate over time. This adaptability is especially important in the dynamic and ever-changing financial landscape.

By leveraging in-database machine learning for credit scoring, banks can streamline their lending processes, improve customer experiences, and mitigate credit risks effectively. Additionally, it helps in maintaining data privacy and security, as sensitive customer information remains within the secure confines of the database.

#### Fraud Detection

In the financial industry, fraud detection is a critical application. By leveraging in-database machine learning, financial institutions can develop and deploy fraud detection models directly within their databases. This enables real-time analysis of transactions and customer behavior, reducing the time between data collection and prediction. With in-database machine learning, suspicious activities can be quickly flagged and appropriate actions taken to prevent fraudulent transactions, leading to enhanced security and reduced financial losses.

#### Customer Churn Prediction

For businesses with large customer bases, understanding and predicting customer churn (i.e., when customers stop using their services) is vital. By employing in-database machine learning, companies can build churn prediction models directly within their databases. These models can analyze historical customer data, such as transaction history, customer interactions, and usage patterns, to identify potential churners. The in-database approach allows businesses to make real-time predictions and take proactive measures, such as personalized retention offers, to retain valuable customers.

#### Personalized Recommendations

E-commerce platforms and content providers often rely on recommendation systems to offer personalized suggestions to their users. In-database machine learning can be used to develop recommendation models within the database itself. By analyzing user behavior, purchase history, and preferences in real-time, the database can generate personalized recommendations without the need to transfer vast amounts of data to external systems. This not only ensures faster response times but also protects the privacy and security of user data.

In all these use cases, the integration of machine learning directly within the database optimizes data processing, minimizes data movement, and enhances overall system performance. It also simplifies model deployment and maintenance, making it an attractive solution for various data-intensive applications.

### Data Dictionary

<!-- GUIDANCE -->
<!--
Show how data is acquired, transported, store, queried, and secured as in scope of this Workload. This could include Data Ecosystem Reference Architectures, Master Data Management models or any other data centric model.

The Data ecosystem: https://apex.oraclecorp.com/pls/apex/patterns/r/patternlibrary/view-pattern?p118_id=604&session=17457054591654

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->


### Data Flow
<!-- GUIDANCE -->
<!--
A Use Case (UC) can be represented in a table as the following one. See https://www.visual-paradigm.com/guide/use-case/what-is-use-case-specification/ for quick introduction to the concept of UC. See https://www.gatherspace.com/use-caseexamples/ for more examples and detailed instructions.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

<!-- EXAMPLE / TEMPLATE -->
Element                         | Description
:---                            |:---
Use Case 1                      | Preparing near real-time Credit Risk solution by using AutoML in Autonomous Data Warehouse
Stakeholder                     | Customer name
Use Case Overview               | This use case will create a new business line for the company.
Precondition 1                  | Business requirements will be defined by the customer
Trigger                         | Whenever there is new data in the 3rd party application database, it will be loaded into Autonomous Data Warehouse by OCI GG. Fusion ERP data will be integrated daily.
Basic Flow                      | The data from 3rd party applications and Fusion ERP will be integrated to Autonomous Data Warehouse daily and AutoML will provide the best ML model over historical data. Applications will access the results through OML Services and the Business users will access through Oracle Analytics Cloud.
Alternative Flow 1              | If the customer would like to use Jupyter Environment and they can also use OCI Data Science Cloud
Alternative Flow 2              | If the customer would like to integrate new data sources, they can be integrated with OCI Data Integration


### Functional Capabilities
<!-- GUIDANCE -->
<!--
In specific cases, a set of Functional Capabilities can be represented in a Functional Decomposition Diagram. This is typical of Functional Analysis in System Engineering domain. For more information on Functional Analysis see, e.g. https://spacese.spacegrant.org/functional-analysis/.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

### Requirement Matrix
<!-- GUIDANCE -->
<!--
A Requirement Matrix can be used when the solution will be based on software capabilities already available in existing components (either custom or vendor provided). The Requirements Matrix is a matrix that is used to capture client requirements for software selection and to evaluate the initial functional “fit” of a vendor’s software solution to the business needs
of the client.

For example, rows can list required functional capabilities and columns can list available software components. Cells can contain a simple Y/N or provide more detail. The Requirements Matrix also is used to identify initial functional gaps or special software enhancements needed to enable each vendor’s software to fulfill the client’s desired system capabilities.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

|Requirements                                       | OAC[^1] | ADW |  OCI DI  |  OCI GG|
|--------                                           |--       |--              |--      |--|
| Access report and advanced visualization          |   Y     |         |       |       |
| Self-Service reporting and advanced visualization |   Y     |         |       |       |
| Profile and analyze data and KPIs                 |   Y     |   Y     |       |        |
| Data loading                 |        |       |    Y   |      Y  |
| Data processing                       |         |         |      Y   |      |
| Data persistence (storage) | | Y |  | |


[^1]: **OAC**:Oracle Analytics Cloud, **ADW**: Autonomous Data Warehouse, **OCI DI**: OCI Data Integration, **OCI GG**: OCI Golden Gate


## Non Functional Requirements
<!-- GUIDANCE -->
<!--
Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non Functional Requirements are actually necessary for your engagement. You might not need to capture all requirements for all sub-chapters.

This chapter is for describing customer specific requirements (needs), not to explain Oracle solutions or capabilities.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

### Integration and Interfaces
<!-- GUIDANCE -->
<!--
A list of all the interfaces into and out of the defined Workload. The list should detail the type of integration, the type connectivity required (e.g. VPN, VPC etc) the volumes and the frequency
- list of integrations
- list of user interfaces

Recommended Chapter
-->

<!-- EXAMPLE / TEMPLATE -->

Name	                      | Source    		| Target	  	| Mode	| Function
:---		                    |:---		      	|:---		    	|:---		   	|:---
OCI Data Integration     | Oracle Fusion Maintenance Cloud	| ADW	| Batch			| Batch extraction
OCI Golden Gate	                       	| 3rd party Application DB	      	| ADW 	| realtime	| Change data capture


### Regulations and Compliances
<!-- GUIDANCE -->
<!--
This section captures and specific regulatory of compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.

If there are none, then please state None.

Mandatory Chapter
-->

At the time of this document creation, no Regulatory and Compliance requirements have been specified.

### Environments
<!-- GUIDANCE -->
<!--
A diagram or list detailing all the required environments (e.g. development, text, live, production etc).
- list each environment included in the scope
- map each environment to bronze/silver/gold MAA

Mandatory Chapter
-->

Name	          | Size of Prod  | Location	  | MAA   | Scope
:---		        |:---		      	|:---		    	|:---   |:---
Production      | 100%        	| Madrid	| Gold  | Not in Scope / On-prem
Disaster Recovery              | 50%           | Marseille | None  | Implementation Partner 
Dev & Test      | 25%           | Madrid | None  | Lift Project 

### System Configuration Control Lifecycle
<!-- GUIDANCE -->
<!--
This section should detail the requirements for the development and deployment lifecycle across the Workload. This details how code will be deployed and how consistency across the environments will be maintained over future software deployment. This may include a need for CI/CD.

- will a CI/CD tool need access to deploy to the target environment
- does the customer require software to be delivered to a repository
- how will configuration and software be promoted through the environments

Optional Chapter
-->

### Resilience and Recovery
<!-- GUIDANCE -->
<!--
This section captures the resilience and recovery requirements for the Workload. Note that these may be different from the current system.

The Recovery Point Objective (RPO) and Recovery Time Objective (RTO) requirement of each environment should be captured in the environments section above, and wherever possible, these should be mapped to the standard Bronze, Silver and Gold levels of Oracle's MAA.

- What are RTO and RPO requirements of the Application?
- What are SLA's of the application?
- What are the backup requirements

Note that if needed, this section may also include an overview of the proposed backup and disaster recovery proposed architectures.

This chapter is mandatory, while there could be no requirements on HA/DR, please mention that in a short single sentence.

Mandatory Chapter
-->

At the time of this document creation, no Resilience or Recovery requirements have been specified.

Workload resilience is achieved by the intrinsic capabilities of ExaCS and OAC and providing Service Level Objectives as described in ["Oracle PaaS and IaaS Public Cloud Services Pillar Document"](https://www.oracle.com/assets/paas-iaas-pub-cld-srvs-pillar-4021422.pdf).

**Recovery** can be achieved by leveraging:

- __OAC__ :
  - __OAC system-generated backups :__ Oracle regularly do system-generated backups (daily, and also when a change is done on the data model and keep them for 30 days) of the entire Oracle Analytics Cloud environment, including system configuration and user content. Oracle Support Services use these system-generated backups to restore an environment that becomes corrupt, but these system-generated backups aren't accessible to customers and they’re not intended to provide customer-requested recovery points. Customer must use the snapshot feature (described below) to back up and restore user content.

  - __OAC Snapshots__ : Customer should regularly back up the content that users create to a file called a snapshot. User content includes catalog content such as reports, dashboards, data visualization workbooks, and pixel perfect reports, datasets, data flows, data models, security roles, service settings, and so on. If something goes wrong with your content or service, you can revert to the content you saved in a snapshot. Snapshots are also useful if there is a requirement to move or share content from one service to another. Oracle Analytics Cloud Snapshot is described [here](https://docs.oracle.com/en/cloud/paas/analytics-cloud/acabi/snapshots.html#GUID-FAE709DE-3370-457C-9015-2E088ACA6181)

    Oracle recommends to take snapshots at significant checkpoints, for example, before making a major change to the content or environment. In addition, Oracle recommends taking regular weekly snapshots or at defined frequency based on the rate of change of the environment and rollback requirements. These Snapshots are can be downloaded to in order to store them locally.

  - To implement a disaster recovery, a well-architected business continuity plan should be designed in order to recover as quickly as possible and continue to provide services to Oracle Analytics Cloud users. Oracle recommends to do snapshots regularly and restore the content to a redundant Oracle Analytics Cloud environment (that can be only powered on during restore process) in another region if possible to mitigate the risk of region-wide events.

- __OCI DI__ :

   - __Applications in ODI Data Integration__ : In order to achieve disaster recovery, version upgrade and cross environment code promotion, we use the notion of Applications in OCI Data Integration. An Application in Data Integration is a container at the workspace level that holds runtime objects such as published tasks and task runs. You have the flexibility to [create a new Application](https://docs.oracle.com/en-us/iaas/data-integration/using/applications.htm#creating-applications) from scratch or make a copy of an existing one. Disaster Recovery will be achieve by automating backup creation and trigger restauration in the event of a disaster. 
   
- __ADW__ :

   - __ADW automated backups__ : that have a retention period of 60 days and that allow to restore and recover the ADW database to any point-in-time in this retention period. Manual backups can also be performed and stored in an Object Storage bucket, if needed, for instance to have a higher retention period.
   - __Oracle Database Autonomous Recovery Service__ You can select Recovery Service as the backup destination for automatic backups.
   - __Autonomous Data Guard__ you can add an Autonomous Data Guard standby database, the system creates a standby database that continuously gets updated with the changes from the primary database
   - __OML__  backup and recovery are also immediate as part of ADW. 


### Management and Monitoring
<!-- GUIDANCE -->
<!--
This subsection captures any requirements for integrations into the customer's existing management and monitoring systems - e.g. system monitoring, systems management etc. Also, if the customer requires new management or monitor capabilities, these should also be recorded.

Optional Chapter
-->

Type|Tool		              | Task				                                | Target		        | Location   	    | Notes|
|:---		|:---			            |:---					                             |:---		          |:---		          |:---		          |
Monitoring | OAC console	|  monitor user sessions and cache status   | OAC	| OCI	  |
Monitoring |Performance Hub	|  monitor performance, CPU utilization, consumed storage, running SQL statements and sessions amongst other metrics exposed   | ADW    | OCI        |   
Management | Identity Domain console	| manage users and perform role assignment for those users   | Identity Domain	| OCI	  |
Management | OCI Console	|  database management tasks for Autonomous Databases    | ADW	| OCI	  |
Management | Using the API	|  database management tasks for Autonomous Databases    | ADW	| OCI	  |
Management | OAC console| manage OAC settings, create and restore snapshots   | OAC	| OCI	  |

### Security
<!-- GUIDANCE -->
<!--
Capture the non functional requirements for security related topics. Security is a mandatory subsection which is to be reviewed by the x-workload security team. The requirements can be separated into:
- Identity and Access Management
- Data Security

Other security topics, such as network security, application security or other can be added if needed.

Mandatory Chapter
-->

At the time of this document creation, no Security requirements have been specified.

#### Identity and Access Management
<!-- GUIDANCE -->
<!--
The requirements for identity and access control. This section describes any requirements for
authentication, identity management, single-sign-on and necessary integrations to retained customer systems
(e.g. corporate directories)
- Is there any Single Sign On or Active Directory Integration Requirement?
- Is the OS hardened if so please share the hardening guide line?

Recommended Chapter
-->

The proposed solution consists of ADW, Oracle Analytics Cloud (OAC) and OCI Golden Gate which are fully managed by Oracle (OCI PaaS), and therefore have very small attack surface. Authentication and authorization of users is done with the enterprise-grade Identity and Access Management (IAM) services of OCI.

#### Data Security
<!-- GUIDANCE -->
<!--
Capture any specific or special requirements for data security. This section should also describe any additional constraints such as a requirement for data to be held in a specific locations or for data export restrictions

Recommended Chapter
-->

## Constraints and Risks
<!-- GUIDANCE -->
<!--
Constraints are limitations which will impact the resulting project or Solution Architecture. It is a technology- or project-related condition or event that prevents the project from fully delivering the ideal solution to customers and end-users. Constraints can be identified on our customer, partner or even Oracle's side.

A project risk is an uncertain event that may or may not occur during a project.

Describe constraints and risks affecting the Workload and possible Logical Solution Architecture. These can be of technical nature, but might also be non-technical. Consider: budgets, timing, preferred technologies, skills in the customer organization, location, etc.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->
Name                | Description                                    | Type           | Impact                         | Mitigation Approach
:---                |:---                                            |:---            |:---                              |:---
OCI skills          | Limited OCI skills in customers organization   | Risk     | No Operating Model                | Involve Ops partner, for example Oracle ACS
Team Availability  | A certain person is only available on Friday CET time zone  | Constraint  | | Arrange meetings to fit that persons availability
Access Restriction  | We are not allowed to access a certain tenancy without customer presence  | Constraint   | | Invite customer key person to implementation sessions

## Current State Architecture
<!-- GUIDANCE -->
<!--
Provide a high-level logical description of the Workload current state. Stay in the Workload scope, show potential integrations, but do not try to create a full customer landscape. Use architecture diagrams to visualize the current state. I recommend not putting lists of technical resources or dependencies here. Refer to attachments instead.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

## Future State Architecture
<!-- GUIDANCE -->
<!--
The Workload Future State Architecture can be described in various forms. In the easiest case we  just describe a Logical Architecture, possibly with a System Context Diagram.

Additional architectures, in the subsections, can be used to describe needs for specific workloads or for non Lift engagements.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->|



![Future State Architecture](assets/MLAI_WAD_v.0.2-99d6b896.png)



**Main Components:**

### Data Ingestion & Data Refinery
- **Oracle Cloud Infrastructure Data Integration** will be used to process and transform data that is coming from Fusion ERP and ingest it into Autonomous Database.

- **OCI Golden Gate** will be used to replicate the data from the database of 3rd Party Application Database to Autonomous Database.

### Serving/Data Persistance

- **Oracle Autonomous Data Warehouse** will serve as the source of the curated data that will be used to create the AutoML data preparation and feature engineering. By leveraging Autonomous Oracle Database and the power of Exadata in the cloud, data preparation over historical data will perform better.

- **Object Storage** - is an internet-scale, high-performance storage platform that offers reliable and cost-efficient data durability. Object Storage can also be used as a cold storage layer for the Autonomous Databases by storing data that is used infrequently and then joining it seamlessly with the most recent data by using hybrid tables in the Oracle Database.

### Data Access & Interpretation

**Data Science & Machine Learning**

- **Predict**

**Oracle Machine Learning Services** extend Oracle Machine Learning (OML) functionality to support model deployment and model lifecycle management for both in-database Oracle Machine Learning models and third-party Open Neural Networks Exchange (**ONNX**) machine learning models via REST APIs. Oracle Machine Learning Services supports real-time and small-batch scoring for applications and dashboards. 

The REST API for Oracle Machine Learning Services provides REST endpoints with authentication via Autonomous Data Warehouse. These endpoints enable the storage and management of machine learning models and their metadata. These endpoints also allow for the creation of scoring endpoints for models.

Oracle Machine Learning Services supports third-party classification or regression models that can be built using packages like Scikit-learn and TensorFlow, among others and then exported in ONNX format. Oracle Machine Learning Services supports integrated cognitive text analytics for topic discovery, keywords, summary, sentiment, and similarity. Oracle Machine Learning Services also supports image classification via third-party ONNX format model deployment, and supports scoring using images or tensors.

Users can also predict directly in the database using in-database models from SQL, R, and Python for singleton, small batch, and large-scale batch scoring. Users can leverage OML4Py embedded Python execution to invoke user-defined Python function with models produced from third-party packages and make predictions from Python and REST interfaces. 

- **Learn**

Oracle Machine Learning **Notebooks** provide a collaborative user interface for data scientists and business and data analysts to work with SQL and Python interpreters while also performing machine learning in Oracle Autonomous Database—which includes Autonomous Data Warehouse (ADW), Autonomous Transaction Processing (ATP), and Autonomous JSON Database (AJD). Oracle Machine Learning Notebooks enable the broader data science team (data scientists, citizen data scientists, data analysts, data engineers, DBAs) to work together to explore their data visually and to develop analytical methodologies using OML4SQL and OML4Py. The Notebooks interface provides access to Oracle's high-performance, parallel, and scalable in-database implementations of machine learning algorithms via Python, SQL, and PL/SQL. In-database functionality can also be accessed through connection to Autonomous Database via external interfaces, such as SQL Developer, open source notebook environments, and third-party IDEs. 

**OML4Py** also provides a Python API for automated machine learning (AutoML) for automated algorithm and feature selection, and for automated model tuning and selection. 

Oracle Machine Learning **AutoML** User Interface (OML AutoML UI) is a no-code user interface that provides automated machine learning with ease of deployment to Oracle Machine Learning Services. Business users without extensive data science background can use OML AutoML UI to create and deploy machine learning models as well as generate an OML notebook containing the corresponding OML4Py code to rebuild the model and score data programmatically. 

Expert data scientists may use OML AutoML UI as a productivity accelerator for faster model exploration, for ease of deployment, and for starter notebook generation.

**Visualize and Learn**

**Oracle Analytics Cloud** Business users will have access to the customer's final data/variables and the evaluation of their credit score results in Oracle Analytics Dashboards.  It is scalable and secure public self-service & enterprise Visualization service that provides a full set of capabilities to explore and perform collaborative analytics.

OAC supports **Oracle Machine Learning** models deployments along with OCI AI services such as **OCI Vision** for image detection. 

**Governance**

- **OCI Data Catalog** - is a crucial component in governing the data and information landscape providing visibility to where technical assets such as metadata and respective attributes reside as well as offering the ability to maintain a business glossary that is mapped to that technical metadata. Data Catalog can also serve metadata to be consumed by ADB in order to facilitate external tables creation in those autonomous databases.

- **Data Safe** - is a unified control center for Oracle Databases which helps you understand the sensitivity of your data, evaluate risks to data, mask sensitive data, implement and monitor security controls, assess user security, monitor user activity, and address data security compliance requirements. Data Safe will be used to 1) audit and implement security controls namely on the production database as well as 2) sensitive data discovery and masking of non prod environments that might originate from production copies/replicas.


**CI/CD**

- **OCI DevOps Service** Oracle Cloud Infrastructure DevOps service is a complete continuous integration/continuous delivery (CI/CD) platform for developers to simplify and automate their software development lifecycle. The OCI DevOps service enables developers and operators to collaboratively develop, build, test, and deploy software. Developers and operators get visibility across the full development lifecycle with a history of source commit through build, test, and deploy phases.

**Security & IAM**

- **IAM** - OCI Identity and Access Management allows controlling who has access to cloud resources. 

  OCI IAM provides identity and access management features such as authentication, single sign-on (SSO), and identity lifecycle management for Oracle Cloud as well as Oracle and non-Oracle applications, whether SaaS, cloud-hosted, or on-premises. Employees, business partners, and customers can access applications at any time, from anywhere, and on any device in a secure manner.

  IAM integrates with existing identity stores, external identity providers, and applications across cloud and on-premises to facilitate easy access for end users. It provides the security platform for Oracle Cloud, which allows users to securely and easily access, develop, and deploy business applications such as Oracle Human Capital Management (HCM) and Oracle Sales Cloud, and platform services such as Oracle Java Cloud Service, Oracle Analytics Cloud, and others.

  It can control what type of access a group of users have and to which specific cloud resources. It is a key component of segregating resources and restricting access only to authorised groups and users. OCI IAM, and in fact, OCI as a whole implements a [Zero Trust Security](https://www.oracle.com/security/what-is-zero-trust/#link1) model of which one of the guiding principles is least privilege access; in fact, a user by default doesn't have access to any resources and policies need to be created explicitly to grant groups of users access to cloud resources.


### Physical Architecture
<!-- GUIDANCE -->
<!--

The Workload Architecture is typically not described in a physical form. If we deliver a Lift project, the scoped Lift Project in chapter 4 includes the physical architecture.

Nevertheless, an architect might want to describe the full physical Workload here, if this is a non-Lift project or if 3rd party implementation partner implement the non Lift environments.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This section's physical future state architecture serves as the first iteration of the Credit Risk system that might be provisioned in OCI. As a result, the physical future state architecture will be refined in accordance with the customer's low level requirements, and those refinements and the final solution will be detailed in WAD in the future.

![Physical Architecture](assets/MLAI_WAD_v.0.3-1bbe09ab.png)



- **Oracle Analytics Cloud (OAC)** will be provisioned in a private subnet.
- **Oracle Cloud Analytics Private Access Channel (OAC PAC)** will be used to connect the OAC to the ADW residing
in the private subnet.
- **ADW** will be provisioned in the private subnet.
- **OCI Data integration** will be prepared in the private subnet.
- **Data Catalog** will be ready to use when the tenancy is created.
- **Object storage** will be ready to use when the tenancy is created.
- **Monitoring/Logging**  tools ready to use to monitor OCI Services and related Logs.
- **OCI IAM Identity Domains** is automatically provided and ready to use at the tenancy level.
- **OCI VCN and Subnets** Lift team will check the existing VCN and subnets and create new ones if needed.
- **Bastion Service**  will be used by the Oracle Lift team to have external access to VCNs
- **NAT Gateway** -A NAT gateway enables private resources in a VCN to access hosts on the internet, without exposing those resources to incoming internet connections. It will be used for OCI Data integration and BICC.
- **Dynamic Routing Gateway (DRG)** is the virtual router that secures and manages traffic between on-premises networks and Virtual Cloud Networks (VCN) in Oracle Cloud.
- **Service Gateways** allow private access to Oracle managed services with public IP addresses from on-premises and from VCNs, without exposing the traffic to the public Internet.
- **Virtual Cloud Networks (VCN) and Subnets** will contain private resources like computing instances, database systems, and private endpoints for Oracle managed resources like Autonomous Data Warehouse and Oracle Analytics Cloud.

#### Network Firewall

Optionally a managed Network Firewall can be leveraged to increase security posture of the workload.

OCI Network Firewall is a next-generation managed network firewall and intrusion detection and prevention service for VCNs, powered by Palo Alto Networks. The Network Firewall service offers simple setup and deployment and gives visibility into traffic entering the cloud environment (North-south network traffic) as well traffic between subnets (East-west network traffic).

Use network firewall and its advanced features together with other Oracle Cloud Infrastructure security services to create a layered network security solution.

A network firewall is a highly available and scalable instance that you create in the subnet of your choice. The firewall applies business logic to traffic that is specified in an attached firewall policy. Routing in the VCN is used to direct network traffic to and from the firewall.

![Network Firewall deployment example](assets/network-firewall-drg.png)

Above a simple example is presented where a Network Firewall is deployed in a DMZ subnet and for which all incoming traffic via the DRG as well as all the outgoing traffic from the private subnet is routed to the Network Firewall so that policies are enforced to secure traffic. 




## OCI Cloud Landing Zone Architecture
<!-- GUIDANCE -->
<!--

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with customer specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc). An OCI Cloud Landing zone involves a variety of fundamental aspects that have a broad level of sophistication. A good summary of a Cloud Landing Zone has been published by [Cap Gemini](https://www.capgemini.com/2019/06/cloud-landing-zone-the-best-practices-for-every-cloud/).

### Resource Naming Convention
<!-- GUIDANCE -->
<!--
If the customer provides a resource naming convention use it. They should have it already for their on-premises compute resources.
-->

Oracle recommends the following Resource Naming Convention:

- The name segments are separated by “-“
- Within a name segment avoid using <space> and “.”
- Where possible intuitive/standard abbreviations should be considered (e.g. “shared“ compared to "shared.cloud.team”)
- When referring to the compartment full path, use “:” as separator, e.g. cmp-shared:cmp-security

Some examples of naming are given below:

- cmp-shared
- cmp-\<workload>
- cmp-networking

The patterns used are these:

- \<resource-type>-\<environment>-\<location>-\<purpose>
- \<resource-type>-\<environment>-\<source-location>-\<destination-location>-\<purpose>
- \<resource-type>-\<entity/sub-entity>-\<environment>-\<function/department>-\<project>-\<custom>
- \<resource-type>-\<environment>-\<location>-\<purpose>

Abbreviation per resource type are listed below. This list may not be complete.

| Resource type | Abbreviation | Example |
|---|---|---|
| Bastion Service | bst | bst-\<location>-\<network> |
| Block Volume | blk | blk-\<location>-\<project>-\<purpose>
| Compartment | cmp | cmp-shared, cmp-shared-security |
| Customer Premise Equipment | cpe | cpe-\<location>-\<destination> |
| DNS Endpoint Forwarder | dnsepf | dnsepf-\<location> |
| DNS Endpoint Listener | dnsepl | dnsepl-\<location> |
| Dynamic Group | dgp | dpg-security-functions |
| Dynamic Routing Gateway | drg | drg-prod-\<location>
| Dynamic Routing Gateway Attachment | drgatt | drgatt-prod-\<location>-\<source_vcn>-\<destination_vcn> |
| Fast Connect | fc# <# := 1...n> | fc0-\<location>-\<destination> |
| File Storage | fss | fss-prod-\<location>-\<project> |
| Internet Gateway | igw | igw-dev-\<location>-\<project> |
| Jump Server | js | js-\<location>-xxxxx |
| Load Balancer | lb | lb-prod-\<location>-\<project> |
| Local Peering Gateway | lpg | lpg-prod-\<source_vcn>-\<destination_vcn> |
| NAT Gateway | nat | nat-prod-\<location>-\<project> |
| Network Security Group | nsg | nsg-prod-\<location>-waf |
| Managed key | key | key-prod-\<location>-\<project>-database01 |
| OCI Function Application | fn | fn-security-logs |
| Object Storage Bucket | bkt | bkt-audit-logs |
| Policy | pcy | pcy-services, pcy-tc-security-administration |
| Region Code, Location | xxx | fra, ams, zch # three letter region code |
| Routing Table | rt | rt-prod-\<location>-network |
| Secret | sec | sec-prod-wls-admin |
| Security List | sl | sl-\<location> |
| Service Connector Hub | sch | sch-\<location> |
| Service Gateway | sgw | sgw-\<location> |
| Subnet | sn | sn-\<location> |
| Tenancy | tc | tc |
| Vault | vlt | vlt-\<location> |
| Virtual Cloud Network | vcn | vcn-\<location> |
| Virtual Machine | vm | vm-xxxx |
| | | |

**Note:** Resource names are limited to 100 characters.

#### Group Names

OCI Group Names should follow the naming scheme of the Enterprise Identity Management system for Groups or Roles.

Examples for global groups are:

- \<prefix>-\<purpose>-admins
- \<prefix>-\<purpose>-users

For departmental groups:

- \<prefix>-\<compartment>-\<purpose>-admins
- \<prefix>-\<compartment>-\<purpose>-users

The value for \<prefix> or the full names **must be agreed** with customer.

### Security and Identity Management

This chapter covers the Security and Identity Management definitions and resources which will be implemented for customer.

#### Universal Security and Identity and Access Management Principles

- Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
- Any new project deployment in OCI will start with the creation of a new compartment. Compartments follow a hierarchy, and the compartment structure will be decided as per the application requirements.
- It is also proposed to keep any shared resources, such as Object Storage, Networks etc. in a shared services compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific resource types and user roles.
- Policies will be configured in OCI to maintain the level of access / control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy.
- The tenancy will include a pre-provisioned Identity Cloud Service (IDCS) instance (the primary IDCS instance) or, where applicable, the Default Identity Domain. Both provide access management across all Oracle cloud services for IaaS, PaaS and SaaS cloud offerings.
- The primary IDCS or the Default Identity Domain will be used as the access management system for all users administrating (OCI Administrators) the OCI tenant.

#### Authentication and Authorization for OCI

Provisioning of respective OCI administration users will be handled by the customer.

##### User Management

Only OCI Administrators are granted access to the OCI Infrastructure. As a good practice, these users are managed within the pre-provisioned and pre-integrated Oracle Identity Cloud Service (primary IDCS) or, where applicable, the OCI Default Identity Domain, of OCI tenancy. These users are members of groups. IDCS Groups can be mapped to OCI groups while Identity Domains groups do not require any mapping. Each mapped group membership will be considered during login.

**Local Users**

The usage of OCI Local Users is not recommended for the majority of users and is restricted to a few users only. These users include the initial OCI Administrator created during the tenancy setup, and additional emergency administrators.

**Local Users are considered as Emergency Administrators and should not be used for daily administration activities!**

**No additional users are to be, nor should be, configured as local users.**

**The customer is responsible to manage and maintain local users for emergency use cases.**

**Federated Users**

Unlike Local Users, Federated Users are managed in the Federated or Enterprise User Management system. In the OCI User list Federated Users may be distinguished by a prefix which consists of the name of the federated service in lower case, a '/' character followed by the user name of the federated user, for example:

`oracleidentityservicecloud/user@example.com`

In order to provide the same attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials) for Local and *Federated Users* federation with third-party Identity Providers should only be done in the pre-configured primary IDCS or the Default Identity Domain where applicable.

All users have the same OCI-specific attributes (OCI API Keys, Auth Tokens, Customer Secret Keys, OAuth 2.0 Client Credentials, and SMTP Credentials).

OCI Administration user should only be configured in the pre-configured primary IDCS or the Default Identity Domain where applicable.

**Note:** Any federated user can be a member of 100 groups only. The OCI Console limits the number of groups in a SAML assertion to 100 groups. User Management in the Enterprise Identity Management system will be handled by the customer.

**Authorization**

In general, policies hold permissions granted to groups. Policy and Group naming follows the Resource Naming Conventions.

**Tenant Level Authorization**

The policies and groups defined at the tenant level will provide access to administrators and authorized users, to manage or view resources across the entire tenancy. Tenant level authorization will be granted to tenant administrators only.

These policies follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.1.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Service Policy**

A Service Policy is used to enable services at the tenancy level. It is not assigned to any group.

**Shared Compartment Authorization**

Compartment level authorization for the cmp-shared compartment structure uses the following specific policies and groups.

Apart from tenant level authorization, authorization for the cmp-shared compartment provides specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

Policies for the cmp-shared compartment follow the recommendations of the [CIS Oracle Cloud Infrastructure Foundations Benchmark v1.1.0, recommendations 1.1, 1.2, 1.3](https://www.cisecurity.org/cis-benchmarks).

**Compartment Level Authorization**

Apart from tenant level authorization, compartment level authorization provides compartment structure specific policies and groups. In general, policies will be designed that lower-level compartments are not able to modify resources of higher-level compartments.

**Authentication and Authorization for Applications and Databases**

Application (including Compute Instances) and Database User management is completely separate of and done outside of the primary IDCS or Default Identity Domain. The management of these users is the sole responsibility of the customer using the application, compute instance and database specific authorization.

#### Security Posture Management

**Oracle Cloud Guard**

Oracle Cloud Guard Service will be enabled using the pcy-service policy and with the following default configuration. Customization of the Detector and Responder Recipes will result in clones of the default (Oracle Managed) recipes.

Cloud Guard default configuration provides a number of good settings. It is expected that these settings may not match with the customer's requirements.

**Targets**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.15](https://www.cisecurity.org/cis-benchmarks), Cloud Guard will be enabled in the root compartment.

**Detectors**

The Oracle Default Configuration Detector Recipes and Oracle Default Activity Detector Recipes are implemented. To better meet the requirements, the default detectors must be cloned and configured by the customer.

**Responder Rules**

The default Cloud Guard Responders will be implemented. To better meet the requirements, the default detectors must be cloned and configured by the customer.

**Vulnerability Scanning Service**

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, OCI Vulnerability Scanning](https://www.cisecurity.org/cis-benchmarks) will be enabled using the pcy-service policy.

Compute instances which should be scanned *must* implement the *Oracle Cloud Agent* and enable the *Vulnerability Scanning plugin*.

**OCI OS Management Service**

Required policy statements for OCI OS Management Service are included in the pcy-service policy.

By default, the *OS Management Service Agent plugin* of the *Oracle Cloud Agent* is enabled and running on current Oracle Linux 6 and Oracle Linux 7 platform images.

#### Monitoring, Auditing and Logging

In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3 Logging and Monitoring](https://www.cisecurity.org/cis-benchmarks) the following configurations will be made:

- OCI Audit log retention period set to 365 days. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.1](https://www.cisecurity.org/cis-benchmarks)
- At least one notification topic and subscription to receive monitoring alerts. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.3](https://www.cisecurity.org/cis-benchmarks)
- Notification for Identity Provider changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.4](https://www.cisecurity.org/cis-benchmarks)
- Notification for IdP group mapping changes. [See CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.5](https://www.cisecurity.org/cis-benchmarks)
- Notification for IAM policy changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.6](https://www.cisecurity.org/cis-benchmarks)
- Notification for IAM group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.7](https://www.cisecurity.org/cis-benchmarks)
- Notification for user changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.8](https://www.cisecurity.org/cis-benchmarks)
- Notification for VCN changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.9](https://www.cisecurity.org/cis-benchmarks)
- Notification for changes to route tables. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.10](https://www.cisecurity.org/cis-benchmarks)
- Notification for security list changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.11](https://www.cisecurity.org/cis-benchmarks)
- Notification for network security group changes. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.12](https://www.cisecurity.org/cis-benchmarks)
- Notification for changes to network gateways. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.13](https://www.cisecurity.org/cis-benchmarks)
- VCN flow logging for all subnets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.14](https://www.cisecurity.org/cis-benchmarks)
- Write level logging for all Object Storage Buckets. See [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.1.0, Chapter 3.17](https://www.cisecurity.org/cis-benchmarks)
- Notification for Cloud Guard detected problems.
- Notification for Cloud Guard remedied problems.

For IDCS or OCI Identity Domain Auditing events, the respective Auditing API can be used to retrieve all required information.

#### Data Encryption

All data will be encrypted at rest and in transit. Encryption keys can be managed by Oracle or the customer and will be implemented for identified resources.

##### Key Management
<!--
Make sure that the correct type of the vault is used:
shared - cheap to moderate pricing
private - expensive pricing
-->

All keys for **OCI Block Volume**, **OCI Container Engine for Kubernetes**, **OCI Database**, **OCI File Storage**, **OCI Object Storage**, and **OCI Streaming** are centrally managed in a shared or a private virtual vault will be implemented and placed in the compartment cmp-security.

**Object Storage Security**

For Object Storage security the following guidelines are considered.

- **Access to Buckets** -- Assign least privileged access for IAM users and groups to resource types in the object-family (Object Storage Buckets & Object)
- **Encryption at rest** -- All data in the Object Storage is encrypted at rest using AES-256 and is on by default. This cannot be turned off and objects are encrypted with a master encryption key.

**Data Residency**

It is expected that data will be held in the respective region and additional steps will be taken when exporting the data to other regions to comply with the applicable laws and regulations. This should be review for every project onboard into the tenancy.

#### Operational Security

**Security Zones**

Whenever possible OCI Security Zones will be used to implement a security compartment for Compute instances or Database resources. For more information on Security Zones refer to the in the *Oracle Cloud Infrastructure User Guide* chapter on [Security Zones](https://docs.oracle.com/en-us/iaas/security-zone/using/security-zones.htm).

**Remote Access to Compute Instances or Private Database Endpoints**

To allow remote access to Compute Instances or Private Database Endpoints, the OCI Bastion will be implemented for defined compartments.

To be able to use OCI services to for OS management, Vulnerability Scanning, Bastion Service, etc. it is highly recommended to implement the Oracle Cloud Agent as documented in the *Oracle Cloud Infrastructure User Guide* chapter [Managing Plugins with Oracle Cloud Agent](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/manage-plugins.htm).

#### Network Time Protocol Configuration for Compute Instance

Synchronized clocks are a necessity for securely operating environments. OCI provides a Network Time Protocol (NTP) server using the OCI global IP number 169.254.169.254. All compute instances should be configured to use this NTP service.

#### Regulations and Compliance

The customer is responsible for setting the access rules to services and environments that require stakeholders’ integration to the tenancy to comply with all applicable regulations. Oracle will support in accomplishing this task.

## Operations
<!-- GUIDANCE -->
<!--
In this chapter we provide a high-level introduction to various operations related topics around OCI. We do not design, plan or execute any detailed operations for our customers. We can provide some best practices and workload specific recommendations.

Please visit our Operations Catalogue for more information, best practices, and examples: https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=3403322163

The below example text represents the first asset from this catalogue PCO#01. Please consider including other assets as well. You can find MD text snippets within each asset.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

This chapter provides an introduction and collection of useful resources, to relevant topics to operate the solution on Oracle Infrastructure Cloud.

Cloud Operations Topic                       | Short Summary      | References
:---                                         |:------             |:---
Cloud Shared Responsibility Model            | The shared responsibility model conveys how a cloud service provider is responsible for managing the security of the public cloud while the subscriber of the service is responsible for securing what is in the cloud.	                |  [Shared Services Link](https://www.oracle.com/a/ocom/docs/cloud/oracle-ctr-2020-shared-responsibility.pdf)
Oracle Support Portal	                       | Search Oracle knowledge base and engage communities to learn about products, services, and to find help resolving issues.	   |  [Oracle Support Link](https://support.oracle.com/portal/)
Support Management API	                     | Use the Support Management API to manage support requests	  |  [API Documentation Link](https://docs.oracle.com/en-us/iaas/api/#/en/incidentmanagement/20181231/) and [Other OCI Support Link](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport.htm)
OCI Status	                                 | Use this link to check the global status of all OCI Cloud Services in all Regions and Availability Domains.	  |  [OCI Status Link](https://ocistatus.oraclecloud.com/)
Oracle Incident Response	                   | Reflecting the recommended practices in prevalent security standards issued by the International Organization for Standardization (ISO), the United States National Institute of Standards and Technology (NIST), and other industry sources, Oracle has implemented a wide variety of preventive, detective, and corrective security controls with the objective of protecting information assets.	  |  [Oracle Incident Response Link](https://ocistatus.oraclecloud.com/)
Oracle Cloud Hosting and Delivery Policies   | Describe the Oracle Cloud hosting and delivery policies in terms of security, continuity, SLAs, change management, support, and termination.	  |  [Oracle Cloud Hosting and Delivery Policies](https://www.oracle.com/us/corporate/contracts/ocloud-hosting-delivery-policies-3089853.pdf)
OCI SLAs                                     | Mission-critical workloads require consistent performance, and the ability to manage, monitor, and modify resources running in the cloud at any time. Only Oracle offers end-to-end SLAs covering performance, availability, manageability of services. This document applies to Oracle PaaS and IaaS Public Cloud Services purchased, and supplements the Oracle Cloud Hosting and Delivery Policies | [OCI SLA's](https://www.oracle.com/cloud/sla/) and [PDF Link](https://www.oracle.com/assets/paas-iaas-pub-cld-srvs-pillar-4021422.pdf)

## Roadmap
<!-- GUIDANCE -->
<!--
Explain a high-level roadmap for this Workload. Include a few easy high-level steps to success (See Business Context). Include Lift services (if possible) as a first fast step. Add other implementation partners and their work as part of your roadmap as well. Does not include details about the Lift scope or any timeline. This is not about product roadmaps.

Recommended Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
-->

## Sizing and Bill of Materials
<!-- GUIDANCE -->
<!--
Estimate and size the physical needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!

Clarify with sales your assumptions and your sizing. Get your sales to finalize the BoM with discounts or other sales calculations. Review the final BoM and ensure the sales is using the correct product SKU's / Part Number.

Even if the BoM and sizing was done with the help of Excel between the different teams, ensure that this chapter includes or links to the final BoM as well.

Price Lists and SKU's / Part Numbers: https://esource.oraclecorp.com/sites/eSource/ESRCHome
-->

### Sizing
<!-- GUIDANCE -->
<!--
Describe the sizes of the complete workload solution and its components.

Mandatory Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
Sales | C
-->
The benefit of Oracle Cloud Infrastructure is that services can be set up with a small footprint and can be easily scaled as more use cases and workloads are migrated over to the new architecture.
<!--
In the scope of this use case, there is no extra charges like egress as the data stays in OCI. Please contact your sales representative if you are planning to use other solutions after this use case.
-->
The following represents a Bill of Materials with an OCPU sizing estimates :

| Phase                      | OCI Service               | Feature Set      | Size        | Comment|
| :-----                     | :-----------              | :-------          | :------     | :------|
| **PROD**           | Autonomous Data Warehouse  | **License Included**|**TBD** |    |
| **PROD**           | Autonomous Data Warehouse-Exadata Storage  | | **TBD** |    |
| **PROD**               | Oracle Analytics Cloud-Enterprise  | **License Included** |**TBD**  |    |
| **PROD**               | OCI Data Integration - Pipeline Operator Execution  |   |**TBD**  |    |
| **PROD**               | OCI Data Integration - GB of Data processed per hour  |   |**TBD**  |    |
| **PROD**               | OCI Golden Gate   | **License Included** |**TBD**  |    |
| **PROD** | Network Firewall (optional) - B95403 |  |**TBD** | |


The sizing defined above is the recommended sizing from Oracle team to accommodate the expected volume of data and meet the scalability of the predicted data processing; since the OCI services can be scaled up and scaled down the customer can always revisit this sizing in the future and adjust it as needed.

* (1) With Autoscaling enabled, ADW will automatically scale to 3x time of base OCPUs. With 1 OCPU, it can scale up to 3 OCPUs. We recommend enabling Autoscaling for production workloads.
* (2) For OAC, 1 OCPU is recommended for Trials only. OAC instances with 1 OCPU are restricted in how many rows they may return (see https://docs.oracle.com/en-us/iaas/analytics-cloud/doc/create-services.html for details.

### Bill of Material
<!-- GUIDANCE -->
<!--
A full Bill of Material can be described in addition.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | None
PPM   | None
Sales | R
-->

<!-- Non Lift Workload End -->

\newpage
\blandscape

## Deployment Build
<!-- GUIDANCE -->
<!--
The Deployment Build is a list of all OCI resources needed for the Lift implementation. It serves two purposes: as a customers documentation; and as a Lift implementer handover. The checklist below defines mandatory requirements as per project scope for the Lift implementation. This table replaces the CD3 file for the architecture team.

Agile Approach: The architect creates and fills in the first version of this table. We work together with our customers to get and confirm the detailed data. Afterwards, the architect and the implementer are working together to iteratively fill these tables. In the meantime some development might already been done by the implementers.

RACI: The architect is Accountable and Responsible for this section. The implementer will actively Consult to provide missing data.

Automatic Parsing: This section is going to be automatically parsed by the implementers. As architects, please try to avoid changing the sub-section names or table structures and attributes. Change only with a strong need, and let me (Alexander Hodicke) know if you need a change here. In addition, please put a comment around each table as seen in the example below - Do not delete them.

For all sub-chapters:

Mandatory Chapter (Partly Optional: If part of your solution / Some subchapters might be mutual exclusive.)

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
-->

### Phase 1: <name>
<!-- Guidance -->
<!--
Please group the Deployment Build into phases depending on the size of the engagement. Each chapter of the Deployment Build belongs to a phase and represents an iterative implementation. First we implement phase 1 and we need to collect data here for that phase. Rearrange the chapters to fit to the right phases. An implementation could have as many phases as needed, and if it has just one, do not group it into just a single phase.

For more information please read a guide here: https://confluence.oraclecorp.com/confluence/display/OCLS/Delivery+Geared+Design%3A+A+Phased+Implementation+Approach
-->

#### Compartments
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Parent Compartment:- Leave it empty or mention 'root' to create under root compartment, mention compartment in compartment1:compartment2 order if not below root compartment.
Region:- Home Region of Tenancy.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Region | Parent Compartment | Description | Tags
:--- |:---    |:---                |:---         |:---
Network | | | Compartment for all network resources
Production   |  |   |  Compartment for production application and database tier
<!--END-->

#### Policies
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Statements:- Policy to create.
Region: Home region of Tenancy
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Statements | Region | Compartment | Description | Tags
:--- |:---        |:---    |:---         |:---         |:---
Network_Admins_Policy | Allow group Network_Admins to manage virtual-network-family in tenancy | | Policy for Network_Admins  | |
Compute_Admins_Policy   | Allow group Compute_Admins to manage instance-family in tenancy | | Policy for Compute_Admins  | |
 | Allow group Compute_Admins to manage compute-management-family in tenancy  | | |
 | Allow group Compute_Admins to use volume-family in tenancy | | |
Database_Admins_Policy  | Allow group Database_Admins to manage database-family in tenancy |  | Policy for Database_Admins | |
 | Allow group Database_Admins to manage buckets in tenancy | | |
 | Allow group Database_Admins to use virtual-network-family in tenancy | | |
<!--END-->

#### Groups
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Matching Rule | Region | Authentication | Description | Tags
:--- |:---           |:---    |:---            |:---         |:---
AdminGroup | | Frankfurt | IAM |Users that have admin access to network, DB, WLS, user management |
<!--END-->

#### Dynamic Group Policies
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Policy | Region | Description | Tags
:--- |:---    |:---    |:---         |:---
examplepolicy | Allow dynamic-group examplegroup to inspect autonomous-database-family in compartment Production | | |
<!--END-->

#### Tags
<!-- GUIDANCE -->
<!--
<!--
All the fields are mandatory.
Tag Namespace: Specify the Tag Namespace.
Namespace Description: Description of Tags Namespace.
Cost Tracking: Specify "Yes" if tag is cost tracking tag else "No".
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Tag Namespace | Namespace Description | Tag Keys | Tag Description | Cost Tracking | Tag Values | Region
:---          |:---                   |:---      |:---             |:---           |:---        |:---
Application | Inventory | Environment | Environments Identification | Yes | Production Development Test | Region
<!--END-->

#### Users
<!-- EXAMPLE / TEMPLATE -->
Name | Email | Group | Description
:--- |:---   |:---   |:---
 |   |   |

#### Virtual Cloud Networks
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags and DNS Label. If DNS Label is left empty, DNS Label will be created with VCN Name.
IGW:- Internet Gateway, mention the name of internet gateway, enter None if not needed, if left empty it will treated as None.
SGW:- Service Gateway, mention the name of Service gateway, enter None if not needed, if left empty it will treated as None.
NGW:- NAT Gateway, mention the name of NAT gateway, enter None if not needed, if left empty it will treated as None.
DRG:- Dynamic Routing Gateway, enter the name of Dynamic Routing gateway, mention None if not needed, if left empty it will treated as None. DRG should be unique in the region. If same DRG to be attached to multiple VCN please mention same in respective VCN's.
Region:- Region under which VCN's to be created
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | VCN Name | CIDR Block | DNS Label | IGW | DRG | NGW | SGW | Region | Tags
:---        |:---      |:---        |:---       |:--- |:--- |:--- |:--- |:---    |:---
Network | examplevcn |  10.0.1.0/24 |  examplevcn | | | | | Region |
<!--END-->

#### Virtual Cloud Network Information
<!-- GUIDANCE -->
<!--
None of the fields are mandatory.
onprem_destinations: Enter on-premise CIDR, separated by comma.
ngw_destination: Enter NAT Gatewat CIDR.
igw_destination: Enter Internet Gatewat CIDR.
subnet_name_attach_cidr: Mention y if you want to attachd AD and CIDR to object's display name; defaults to n.
-->
<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Property | Value
:---     |:---
onprem_destinations | 10.0.0.0/16
ngw_destination | 0.0.0.0/0
igw_destination | 0.0.0.0/0
subnet_name_attach_cidr | n
<!--END-->

#### Subnets
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Security List Name, Route Table Name and Tags.
Subnet Span:- Valid Values are AD1/AD2/AD3/Regional.
Type:- Valid Values are Private/Public
Security List Name:- Specify Security list to be attached to subnet, if left blank security list with name as that of subnet will attached,
specify None if not to attach any custom security list.
Route Table Name:- Specify Route Table Name to be attached to subnet, if left blank route Table with name as that of subnet will attached,
specify None if not to attach any custom route table.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | VCN Name | Subnet Name | CIDR Block | Subnet Span | Type | Security List Name | Route Table Name | Region | Tags
:---        |:---      |:---         |:---        |:---         |:---  |:---                |:---     |:---|:---
Network | examplevcn |  appsubnet |  10.0.1.0/25 | Regional  | Private | | | Region |
Network | examplevcn  | bastionsubnet  | 10.0.1.128/25  | AD1  | Public  | | | Region |
<!--END-->

### Phase 2: <name>
<!-- Guidance -->
<!--
Please group the Deployment Build into phases depending on the size of the engagement. Each chapter of the deployment Build belongs to a phase and represents an iterative implementation. Secondly we implement phase 2 and we need to collect data here for that phase. Rearrange the chapters to fit to the right phases. An implementation could have as many Phases as needed, and if it has just one, do not group it into just a single Phases.

For more information please read a guide here: https://confluence.oraclecorp.com/confluence/display/OCLS/Delivery+Geared+Design%3A+A+Phased+Implementation+Approach
-->

#### DNS Zones
<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Zone Name | Compartment | Region | Zone Type | Domain | TTL | IP Address | View Name | Tags
:---      |:---         |:---    |:---       |:---    |:--- |:---        |:---       |:---
PrivateZone | anand.as.singh | zurich | private/public | example.com | 300 | 10.0.0.0/32 | privateview |
<!--END-->

#### DNS Endpoint
<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Subnet | Endpoint Type | NSG | IPAddress (Listner/Forwarder)
:--- |:---    |:---           |:--- |:---
privateforwarder | subnetname | Listening/Fowarding | nsg | ipaddress
<!--END-->

#### Dynamic Routing Gateways Attachment
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
IPSEC/Virtual Circuit: Ipsec VPN or FastConnect Virtual Circuit Name, Leave empty if not needed.
-->
<!-- WIP: Split IPSEC and Virtual Circuit into two coloumns (By JC, to be reviewed by Impl) -->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | VCN | Compartment | IPSEC/ Virtual Circuit | Region | Tags
:--- |:--- |:---         |:---                    |:---    |:---
exampledrg | examplevcn | examplecompartment | examplevpn | Region |
<!--END-->

#### Route Tables
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Table Compartment: Specify Compartment in which route table is to be created.
Destination CIDR: Specify the destination CIDR.
Target Type: Valid options are CIDR_BLOCK/Service
Target Compartment: Specify the Compartment in which Target Exist.
Target: Valid Targets are Name of the DRG/IGW/SGW/LPG/Private IP/NGW
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Table Compartment | Destination CIDR | Target Type | Target Compartment | Target | Region | Description | Tags | VCN Name
:--- |:---               |:---              |:---         |:---                |:---    |:---    |:---           |:---  |:---
exampleroute | Networks | 0.0.0.0/0 | NAT | Networks | examplenat | Region | | |
<!--END-->

#### Network Security Groups
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | VCN | Compartment | Region | Description | Tags
:--- |:--- |:---         |:---    |:---         |:---
examplensg | examplevcn | examplecompartment | Region | |
<!--END-->

#### NSG Rules (Egress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
Egress Type: Valid options are CIDR_BLOCK/NETWORK_SECURITY_GROUP/SERVICE_CIDR_BLOCK.
protocol: Valid options are TCP/UDP/HTTP.
Destination: Specify the Destination CIDR.
Destination Port: Specify the Destination Port.
Attached Components: Leave it empty as of now
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
NSG Name | Egress Type | Destination | Protocol | Source Port | Dest. Port | Region | Description | Tags
:---     |:---         |:---         |:---      |:---         |:---              |:---      |:---         |:---
examplensg | Stateful/CIDR | 0.0.0.0/0 | TCP | all | 443 | Region | |
<!--END-->

#### NSG Rules (Ingress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
Ingress Type: Valid options are CIDR_BLOCK/NETWORK_SECURITY_GROUP/SERVICE_CIDR_BLOCK.
protocol: Valid options are TCP/UDP/HTTP.
Source: Specify the Source CIDR.
Source Port: Specify the Source Port.
Attached Components: Leave it empty as of now
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
NSG Name | Ingress Type | Source | Protocol | Source Port | Dest. Port | Region | Description | Tags
:---     |:---          |:---    |:---      |:---         |:---        |:---    |:---        |:---
examplensg | Stateful/CIDR | 0.0.0.0/0 | TCP | 443 | all | Region | |
<!--END-->

#### Security Lists (Egress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Destination: Specify Destination CIDR.
Protocol: Specify the protocol For Example: TCP/HTTP/ICMP
Destination Port: Specify egress port to allow.
Egress Type: Valid option is CIDR
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Compartment | Egress Type | Destination | Protocol | Source Port | Dest. Port | VCN Name | Region | Description | Tags
:--- |:---         |:---         |:---         |:---      |:---         |:---        |:---      |:---    |:---          |:---
examplelist | compartment | Stateful/ CIDR | 0.0.0.0/0 | TCP | all | all | | Region | | |
<!--END-->

#### Security Lists (Ingress)
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Destination: Specify Destination CIDR.
Protocol: Specify the protocol For Example: TCP/HTTP/ICMP
Destination Port: Specify ingress port to allow.
Ingress Type: Valid option is CIDR
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | Compartment | Ingress Type | Source | Protocol | Source Port | Dest. Port | VCN Name | Region | Description | Tags
:--- |:---         |:---          |:---    |:---      |:---         |:---        |:---      |:---    |:---           |:---
examplelist | compartment | Stateful/ CIDR | 0.0.0.0/0 | TCP | all | all | | Region | |
<!--END-->

#### Local Peering Gateways
<!-- GUIDANCE -->
<!--
Optional chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Name | LPG Compartment | Source VCN | Target VCN | Region | Description | Tags
:--- |:---             |:---        |:---        |:---    |:---         |:---
examplelpg | Networks | examplevcn | examplevcn2 | Region | |
examplelpg2 | Networks | examplevcn2 | examplevcn | Region | |
<!--END-->

#### Compute Instances
<!-- GUIDANCE -->
<!--
All the fields are mandatory except NSG and Tags.
Availability Domain:- Valid values are AD1/AD2/AD3 which also depend upon Region.
Fault Domain:- Valid values are FD1/FD2/FD3 or FD-1/FD-2/FD-3, if left blank OCI will take it default.
OS Image:- Valid Values are image name with version without period(.) For Example: OracleLinux79 or Windows2012,
to create instance from boot volume bootvolume OCID.
Shape: Valid Values are compute shapes, for Flex shapes specify Flexshape::NoCPU For Example: VM.Standard.E3.Flex::2.
Backup Policy: Valid Values are Gold/Silver/Bronze
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Availability Domain | Name | Fault Domain | Subnet | OS Image | Shape | Backup Policy | Region | NSG | Tags
:---        |:---                 |:---  |:---          |:---    |:---      |:---   |:---           |:---      |:--- |:---
Production | AD1 |  ebsinstance |  FD1 | appsubnet  | Oracle Linux 7.9 | VM.Standard2.2 | | Region | |
Development | AD2  | bastion  | FD3  | bastionsubnet  | Oracle Linux 7.9  | VM.Standard. E3.Flex::2| | Region | |
<!--END-->

#### Block Volumes
<!-- GUIDANCE -->
<!--
All the fields are mandatory except tags.
Size (in GB):- Specify Block Volume size in GB's.
Availability Domain:- Valid values are AD1/AD2/AD3, make sure to specify same AD in which instance is provisioned.
Attached to Instance:- Instance to which Block Volume to be attached.
Backup Policy:- Valid values are Gold/Silver/bronze
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Name | Size (in GB) | Availability Domain | Attached to Instance | Backup Policy | Region | Tags
:---        |:---  |:---          |:---                 |:---                  |:---           |:---    |:---
Production | ebsinstance-blkvol01 |  500 |  AD1 | ebsinstance  | Gold | Region |
Development | bastion-blkvol01  | 100  | AD2  | bastion  | None  | Region |
<!--END-->

#### Object Storage Buckets
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Bucket | Visibility | Region | Description | Tags
:---        |:---    |:---        |:---    |:---         |:---
Development | devebsbucket | Private | Region | |
<!--END-->

#### File Storage
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Availability Domain | Mount Target Name | Mount Target Subnet | FSS Name | Path | IP Whitelist | Region | NSG | Tags
:---        |:---                 |:---               |:---                 |:---      |:---  |:---          |:---   |:--- |:---
Production | AD1 |  prdebsmt |  appsubnet | prodebsfss  | /prodebsfss | 10.0.1.0/25 | Region | |
<!--END-->

#### Load Balancers
<!-- GUIDANCE -->
<!--
All the fields are mandatory except tags
LB Name:- Specify LB Name
Shape:- Specify LB Shapes in 10Mbps/100Mbps/400Mbps/8000Mbps
Visibility:- Valid values are Private/Public
LBR Hostname: Valid values are Name:Hostname
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | LB Name | Shape | Subnet | Visibility | Hostnames | NSG | Region | Tags
:---        |:---     |:---   |:---    |:---        |:---       |:--- |:---    |:---
Network | prdebslb |  100Mbps |  appsubnet | Private  | www.example.com ebs.application.com | Region | |
<!--END-->

##### Backend Sets
<!-- GUIDANCE -->
<!--
All the fields are Mandatory.
LB Name:- Load Balancer Name should exist in Load Balancer Chapter.
Backend Set Name: Specify Backend Set Name.
Backend Server:Port: Specify Backend Server name:Port.Backend server should exist in tenancy.
Backend Policy:- Valid options for backend policy is LEAST_CONNECTIONS/IP_HASH/ROUND_ROBIN.
SSL: Valid option to use SSL is 'yes'/'no'.
HC Protocol: Health Check Protocol valid options are HTTP/TCP.
HC Port: Health Check Port Specify Health Check Port.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
LB Name | Backend Set Name | Backend Server Port | Backend Policy | SSL | Region | Tags | HC Protocol | HC Port
:---    |:---              |:---                 |:---            |:--- |:---    |:---  |:---         |:---
prdebslb | prdebsbs |  ebsinstance1:8005 ebsinstance2:8005 |  Round Robin | No  | Region | | |
<!--END-->

##### Listeners
<!-- GUIDANCE -->
<!--
All the fields are mandatory.
LB Name: Specify Load Balancer Name should exist in Load Balancer Chapter.
Backend Set Name: Specify Backend Set Name should exist in Backend Sets Chapter.
Hostname: Spcify name ( name:hostnames ) hostname fields from Load Balancer Chapter.
SSL: Specify 'yes' if SSL Listener 'no' if non SSL Listener.
Protocol: Valid options are HTTP/TCP.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
LB Name | Backend Set Name | Hostname | SSL | Listener Name | Protocol | Port | Region
:---    |:---              |:---      |:--- |:---           |:---      |:---  |:---
prdebslb | prdebsbs | ebs.application.com | Yes | Listener1  | HTTP | 443 | Region
<!--END-->

#### Databases

##### DBSystem Info
<!-- GUIDANCE -->
<!--
All the Fields are Mandatory Except Tags.
Shape: Specify VM.Standard for VM DBCS BM.DenseIO2 for Bare Metal DBCS and Exadata for Exadata DBCS System.
DB Software Edition: Valid Options are ENTERPRISE_EDITION_EXTREME_PERFORMANCE, STANDARD_EDITION, ENTERPRISE_EDITION, ENTERPROSE_EDITION_HIGH_PERFORMANCE.
DB Size: Specify DB Size in GB's.
DB Disk Redundancy: Valid options are High/Low.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Region | Compartment  | Display Name | Shape | Total Node Count | DB Software Edition | DB Size (TB) | DB Disk Redundancy | Tags
|:---  |:---          |:---          |:---   |:---              |:---                 |:---     |:---          |:---
amsterdam | network | devdb | VMStandard/ BMStandard/ Exa | 1 | Enterprise Edition | 256 | Normal/ High |
<!--END-->

##### DBSystem Network
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in DBSystem Info Chapter.
Availability Domain: Valid Options are AD1/AD2/AD3, AD varies Region to Region.
License Type: Valid options are LICENSE_INCLUDED/BRING_YOUR_OWN_LICENSE, please specify one of them.
Time Zone: Specify the appropriate time zone.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Display Name | Hostname Prefix | Subnet Name | Availability Domain | License Type | Time Zone
:---         |:---             |:---         |:---                 |:---          |:---
devdb | dbhost | db-sl | AD1 | License Included/ Bring your own license | UTC
<!--END-->

##### Database
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in DBSystem Info Chapter.
Workload Type: Valid Options are OLTP/DSS.
Database Version: Valid options are given below. Please specify one from the below.
11.2.0.4 or 11.2.0.4.201020 or 11.2.0.4.210119 or 11.2.0.4.210420 or 12.1.0.2 or 12.1.0.2.201020 or 12.1.0.2.210119 or 12.1.0.2.210420
or 12.2.0.1 or 12.2.0.1.201020 or 12.2.0.1.210119 or 12.2.0.1.210420 or 18.0.0.0 or 18.12.0.0 or 18.13.0.0 or 18.14.0.0 or 19.0.0.0 or 19.10.0.0 or 19.11.0.0
or 19.9.0.0 or 21.0.0.0 or 21.1.0.0
nCharacter Set: Valid Options are AL16UTF16/UTF8.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Display Name | PDB Name | Workload Type | Database Name | Database Version | Character Set | ncharacter Set
:---         |:---      |:---           |:---           |:---              |:---           |:---
devdb | | OLTP/DSS | Testdb | 19c | |
<!--END-->

#### Autonomous Databases

##### Autonomous Database Information
<!-- GUIDANCE -->
<!--
All the fields are mandatory except Tags.
Workload Type: Valid options are ADW/ATP.
Infrastructure Type: Valid Options are Shared/Dedicated.
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Display Name | DB Name | Workload Type | Infra. Type |  DB Version | OCPU Count | Storage (TB) | Region | Tags
:---        |:---          |:---     |:---           |:---         |:---         |:---        |:---         |:---         |:---
compartment | dbsystem | db | ADW/ ATP | Shared/ Dedicated | 19c | 2 | 1 | Region | Tags
<!--END-->

##### Automation Database Network
<!-- GUIDANCE -->
<!--
All the Fields are mandatory
Display Name: Specify the display name should exist in Autonomous Database Information Chapter.
Auto Scaling: Valid Options are Yes/No.
Network Access: Valid options are Shared/Private.
Access Control Rules: Leave it Blank as of now.
License Type: Valid Options BYOL/LICENSE_INCLUDED
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Display Name | Auto Scaling | Network Access | Access Control Rules | Subnet Name | License Type | NSG
:---         |:---          |:---            |:---                  |:---         |:---          |:---
dbsystem | Yes/ No | Shared only | Shared/ Secure Access only | Shared only | network | BYOL/ Included |
<!--END-->

#### Key Management System Vaults
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Name | Type | Region | Description | Tags
:---        |:---  |:---  |:---    |:---         |:---
A | B | Virtual private | Region | |
A | B | Non virtual private | Region | |
<!--END-->

#### Key Management System Keys
<!-- GUIDANCE -->
<!--
Optional Chapter
-->

<!-- EXAMPLE / TEMPLATE -->
<!--START-->
Compartment | Protection Mode | Name | Key Algorithm | Key Length
:---        |:---             |:---  |:---           |:---
A | Software  | X  | AES  | 128 bits
B | HSM  | C  | RSA  | 256 bits
<!--END-->

<!-- Rotate PDF pages, to give tables more space. Please put in comments here and also before the Deployment Build to remove -->
\elandscape
\newpage

# Glossary
<!-- GUIDANCE -->
<!--
A chapter for Product, Technology or Concept descriptions

Please avoid describing products, and link to product documentation at the first occurrence of a product.

Optional Chapter

Role  | RACI
------|-----
WLA   | R/A
Impl. | C
PPM   | None
-->

You can learn about Oracle Cloud Infrastructure terms and concepts in this [glossary](https://docs.oracle.com/en-us/iaas/Content/libraries/glossary/glossary-intro.htm). Further terms, product names or concepts are described below in each subsection.

## 2-Factor Authentication

A second verification factor is required each time that a user signs in. Users can't sign in using just their user name and password.

For more information please visit our documentation for [Administering Oracle identity Cloud](https://docs.oracle.com/en/cloud/paas/identity-cloud/uaids/enable-multi-factor-authentication-security-oracle-cloud.html).

## Other

<!-- End of Solution Design -->

<!--
          ^^                   @@@@@@@@@
     ^^       ^^            @@@@@@@@@@@@@@@
                           @@@@@@@@@@@@@@@@@@              ^^
                          @@@@@@@@@@@@@@@@@@@@

~~~~ ~~ ~~~~~ ~~~~~~~~ ~~ &&&&&&&&&&&&&&&&&&&& ~~~~~~~ ~~~~~~~~~~~ ~~~
~         ~~   ~  ~       ~~~~~~~~~~~~~~~~~~~~ ~       ~~     ~~ ~
  ~      ~~      ~~ ~~ ~~  ~~~~~~~~~~~~~ ~~~~  ~     ~~~    ~ ~~~  ~ ~~
  ~  ~~     ~         ~      ~~~~~~  ~~ ~~~       ~~ ~ ~~  ~~ ~
~  ~       ~ ~      ~           ~~ ~~~~~~  ~      ~~  ~             ~~
      ~             ~        ~      ~      ~~   ~             ~
-->

~~~~





