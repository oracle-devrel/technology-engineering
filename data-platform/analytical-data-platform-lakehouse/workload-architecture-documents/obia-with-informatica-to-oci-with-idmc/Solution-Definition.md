---
doc:
  author: Wilbert Poeliejoe                    #Mandatory
  version: 0.7                                   #Mandatory
  cover:                                         #Mandatory
    title:                              #Mandatory
      - ${doc.customer.name}            #Mandatory
      - BI Applications migration to OCI       #Mandatory
    subtitle:                           #Mandatory
      - Solution Definition             #Mandatory
  customer:                             #Mandatory
    name: CustomerA                     #Mandatory
    alias: CustomerA                    #Mandatory
  config:
    impl:
      type: \<Service Provider\>             #Mandatory: Can be 'Oracle Lift', 'Oracle Fast Start', 'Partner' etc. Use with ${doc.config.impl.type}     
      handover: ${doc.customer.name}    #Mandatory: Please specify to whom to hand over the project after implementation. eg.: The Customer, a 3rd party implementation or operations partner, etc.           
  draft: true
  history:
    - version: 0.6
      date: 20 June 2023
      authors: 
        - ${doc.author}
      comments:
        - This is the old WAD version
    - version: 0.7
      date: 01 January 2023
      authors: ${doc.author}
      comments:
        - New Solution Definition template
  team:
    - name: ${doc.author}
      email: wilbert.poeliejoe@oracle.com
      role: Tech Solution Specialist
      company: Oracle
    - name: Alex Hodicke
      email: alexander.hodicke@oracle.com
      role: Template reviewer
      company: Oracle
  acronyms:
      ADW: Autonomous Data Warehouse
      CIDR: Classless Inter-Domain Routing
      DNS: Domain Name System
      DRG: Dynamic Routing Gateway
      ETL: Extract Transform Load
      IAM: Identity and Access Management
      IGW: Internet Gateway
      NSG: Network Security Groups
      OAC: Oracle Analytics Cloud
      OCPU: Oracle Compute Unit
      OBIA: Oracle Business Intelligence Applications
      OBIEE: Oracle Business Intelligence Enterprise Edition
      ODI: Oracle Data Integrator
      OSN: Oracle Service Network
      PVO: Public View Object
      SGW: Service Gateway
      VCN: Virtual Cloud Network
      VNIC: Virtual Network Interface Card
---

<!--
    Last Change: 18th May 2022
    Review Status: Development
    Review Notes: see https://confluence.oraclecorp.com/confluence/x/9Vyyvw
    How to use this template: https://confluence.oraclecorp.com/confluence/x/LBRBvg
-->

# Document Control
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

## Version Control
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

```{#history}
```

## Team
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

```{#team}
```

## Abbreviations and Acronyms
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None

Use this internal page to find and translate abbreviations and acronyms:
- https://apex.oraclecorp.com/pls/apex/f?p=15295:1:10987292473630:::::
- https://apex.oraclecorp.com/pls/apex/f?p=11069:1:15017803279221
-->
<!-- Please use doc.acronyms for adding custom acronyms, or include other acronyms modules -->

```{#acronyms}
```

## Document Purpose
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

```{.snippet}
uc-document-purpose
```

<!--                            -->
<!-- End of 1) Document Control -->
<!--                            -->

# Business Context
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

${doc.customer.name} is using OBIA version 7.9.6.4 which is in sustaining support and modernisation of it is an important step to take. Customer is having Oracle eBS as source environment. 

Success criteria:

| Description                                                  | Success criteria                                             | Owner | Notes |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ----- | ----- |
| Migration of Data Warehouse Database to Autonomous Data Warehouse Database | Successful migration of the database                         |       |       |
| Migration of OBIEE to OAC                                    | Successful migration of the OBIEE content to OAC, connected to ADW and analytics tested to be working |       |       |
| Migration of Informatica Powercenter to Informatica IDMC     | Successful migration of Powercenter content to IDMC and a execution of the data loads rseuling in data in the new ADW |       |       |
| New Solution for DAC                                         | A replacement solution for DAC will be able to run the Informatica mappings in the right sequence and load data in the Data warehouse tables and store the parameters required for the data load |       |       |

## Executive Summary
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*A section describing the Oracle differentiator and key values of the solution of our solution for the customer, allowing the customer to make decisions quickly.*

## Workload Business Value
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree on the business value with the customer. Keep it business-focused, and speak the language of the LoB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".*

${doc.customer.name} is running an outdated and unsupported installation of OBIA with support and security risks. Modernising this Data Warehouse and Analytics solution will help ${doc.customer.name} to be ready for the future again. Migrating to OCI and using ADW, OAC and Informatica IDMC creates a cloud native solution and leverage existing OBIEE, Informatica and Database knowledge in a modern setting while preserving previously made investments in Data Warehouse, extractions and analytics. 

After the migration the OBIA installation will continue as a custom data warehouse and analytics solution based on the cloud native successors of the migrated stack.

<!--                            -->
<!-- End of 2) Business Context -->
<!--                            -->

# Workload Requirements and Architecture

## Overview
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*Describe the Workload: What applications and environments are part of this Workload, and what are their names? The implementation will be scoped later and is typically a subset of the Workload. For example, a Workload could exist of two applications, but the implementer would only include one environment of one application. The workload chapter is about the whole Workload and the implementation scope will be described late in the chapter [Scope](#scope).*

Oracle Business Intelligence Applications version 7.9.6.4 with OBIEE + Database + Informatica Powercenter + DAC will be migrated to a new modern cloud based stack of OAC + ADW + Informatica IDMC + a solution for scheduling and parameter repository.

Main components will be migrated to OCI. The Source Database can stay in its current place and the Informatica control plane will be hosted by Informatica. 

## Non-Functional Requirements
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*Describe the high-level technical requirements for the Workload. Consider all sub-chapters, but decide and choose which Non-Functional Requirements are necessary for your engagement. You might not need to capture all requirements for all sub-chapters.*

*This chapter is for describing customer-specific requirements (needs), not to explain Oracle solutions or capabilities.*

Run the OBIA installation in a supported stack of components

### Regulations and Compliances Requirements

*Guide:*

*This section captures specific regulatory or compliance requirements for the Workload. These may limit the types of technologies that can be used and may drive some architectural decisions.*

*The Oracle Cloud Infrastructure Compliance Documents service lets you view and download compliance documents:
https://docs.oracle.com/en-us/iaas/Content/ComplianceDocuments/Concepts/compliancedocsoverview.htm*

*If there are none, then please state it. Leave the second sentance as a default in the document.*

*Example:*

At the time of this document creation, no Regulatory and Compliance requirements have been specified.

In addition to these requirements, the [CIS Oracle Cloud Infrastructure Foundation Benchmark, v1.2](https://www.cisecurity.org/benchmark/Oracle_Cloud) will be applied to the Customer tenancy.

### Environments

*Guide:*

*A diagram or list detailing all the required environments (e.g. development, text, live, production, etc).*

Example:

Name         | Size of Prod  | Location  | Scope
:---       |:---    |:---    |:---
DEV | 100% | Xxxxxxxx |Yes
TST | 100% | Xxxxxxxx |No
PRD | 100% | Xxxxxxxx |No

### High Availability and Disaster Recovery Requirements

*Guide:*

*This section captures the resilience and recovery requirements for the Workload. Note that these may be different from the current system.*

*The Recovery Point Objective (RPO) and Recovery Time Objective (RTO) requirement of each environment should be captured in the environments section above, and wherever possible.*

- *What are the RTO and RPO requirements of the Application?*
- *What are the SLAs of the application?*
- *What are the backup requirements*

*Note that if needed, this section may also include an overview of the proposed backup and disaster recovery proposed architectures.*

*This chapter is mandatory, while there could be no requirements on HA/DR, please mention that in a short single sentence.*

*Example:*

For the Development environment no additional measures are put in place for resilience and recovery.  For OAC the regular functionality of creating snapshots can be used to backup the RPD and Presentation Catalog. For ADW the automatic Backup mechanism is sufficient for the Pilot.

Once the Development environment is concluded and decision is taken to move ahead with this solution, Availability and and Distaster/Recovery architecture can be put in place depending on ${doc.customer.name}s requirements and needs 

### Security Requirements

*Guide:*

*Capture the Non-Functional Requirements for security-related topics. Security is a mandatory subsection that is to be reviewed by the x-workload security team. The requirements can be separated into:*
- *Identity and Access Management*
- *Data Security*

*Other security topics, such as network security, application security, or others can be added if needed.*

*Example:*

At the time of this document creation, no Security requirements have been specified.

### Integration and Interfaces

*Guide:*

*A list of all the interfaces into and out of the defined Workload. The list should detail the type of integration, the type of connectivity required (e.g. VPN, VPC, etc) the volumes, and the frequency.*
- *list of integrations*
- *list of user interfaces*

*Example:*

Name	                    | Source    	| Target	  | Protocol  | Function
:---		                |:---		    |:---		  |:---		  |:---
Data Integration  | EBS           | ADW   | Batch     | Batch extraction

## Current State Architecture
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*Provide a high-level logical description of the Workload's current state. Stay in the Workload scope, and show potential integrations, but do not try to create a full customer landscape. Use architecture diagrams to visualize the current state. I recommend not putting lists of technical resources or dependencies here. Refer to the attachments instead.*

## Future State Architecture
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*The Workload Future State Architecture can be described in various forms. In the easiest case, we describe a Logical Architecture, possibly with a System Context Diagram. A high-level physical architecture is mandatory as a description of your solution.*

*Additional architectures, in the subsections, can be used to describe needs for specific workloads.*

![Logical Architecture](images/Logical-Architecture.jpg)

The architecture focuses on the following logical divisions:

In general, the architecture includes the following logical  divisions. This reference architecture focuses on the data refinery and  data persistence architecture components:

- Data refinery

  Ingests and refines the data for use in each of the data layers in the  architecture. The shape is intended to illustrate the differences in  processing costs for storing and refining data at each level and for  moving data between them. The narrower the shape, the less refinery  effort; as the shape gets wider, the refinery effort also increases.

- Data persistence platform (curated information layer)

  Facilitates access and navigation of the data to show the current and historical  business view. It contains both raw data as well as granular and  aggregated curated data. For relational technologies, data may be  logical or physically structured in simple relational, longitudinal,  dimensional or OLAP forms. For non-relational data, this layer contains  one or more pools of data, either output from an analytical process or  data optimised for a specific analytical task.

  Oracle Autonomous Data Warehouse is a self-driving, self-securing, self-repairing database service that  is optimised for data warehousing workloads. You do not need to  configure or manage any hardware, or install any software. Oracle Cloud                                Infrastructure handles creating the database, as well as backing up, patching, upgrading, and tuning the database.                        

- Access and interpretation

  Abstracts the logical business view of the data for the consumers. This  abstraction facilitates agile approaches to development, migration to  the target architecture, and the provision of a single reporting layer  from multiple federated sources. The narrower the shape, the less access and interpretation effort; as the shape gets wider, the access and  interpretation effort also increases.

### Security

The proposed solution consists of OAC in OCI which is fully managed by Oracle. The authentication and authorisation of users is done by Oracle IAM Identity Domains. Protecting the communication between the on-premises and cloud services over the Internet is achieved by leveraging a VPN IP-Sec connection.

OAC and ADW instances are placed into private subnets which can't be accessed over the Internet. The users can access OAC via the corporate network, the VPN IP-Sec connection will be leveraged for that.

The OCI Bastion Service will allow temporary access by the development team during the project. Only during the implementation phase the OCI Bastion Service will be used by the Oracle Implementation team to access the ADW and OAC instances. The Bastion Service allows the implementation team to access ADW and OAC via the internet with an SSH tunnel.

Once the Implementation team has finished their work the Bastion Service can be deactivated or removed.

### Identity and Access Management

To facilitate the identity and access management the solution will make use of the standard Oracle OCI Identity and Access Management (IAM) with the IDCS Foundation integration. IDCS will be used to create the users and to configure access and roles for OAC. When going forward Identity and Access management can be setup to use an Active Directory or Identity Provider. 

OAC will require a separate Identity Domain

### Resilience & Recovery Requirements

  **ADW Backups**  By default the Automatic Backup feature for the Autonomous Data Warehouse is enabled. The service creates the following on an on-going basis: One weekly level 0 backup, generally created on a specified weekend day. A level 0 backup is the equivalent of a full backup. A daily level 1 backups, which are incremental backups created on each day for the six days following the level 0 backup day and an ongoing archived redo log backups (with a minimum frequency of every 60 minutes). The automatic backup process used to create level 0 and level 1 backups can run at any time within the daily backup window (between midnight and 6:00 AM). Automatic incremental backups (level 0 and level 1) are retained in Object Storage for 30 days by default. Level 0 and level 1 backups are stored in Object Storage and have an assigned OCID.

  **Autonomous Dataguard** In addition to the automatic backup and manual backups that can be created from the Autonomous Data Warehouse database it is possible to enable Autonomous Data Guard. When you enable Autonomous Data Guard the system creates a standby database that is continuously updated with the changes from the primary database. You can enable Autonomous Data Guard with a standby in the current region, a local standby, or with a standby in a different region, a cross-region standby. You can also enable Autonomous Data Guard with both a local standby and a cross-region standby.  

  **OAC Snapshots** will be used to perform full and partial backups of the OAC content. The data can be either restored on the same or a different OAC instance. OAC automatically takes a snapshot when changes are made to the data model. Those automatically created snapshots will be used by Oracle for recovery. It keeps up to 5 most recent snapshots taken in 1-hour intervals at most, if you need to revert to an earlier model version. Up to 40 snapshots can be stored. For manual recovery, manual snapshots have to be created.

  Please check this [link](https://docs.oracle.com/en/cloud/paas/analytics-cloud/acabi/snapshots.html#GUID-FAE709DE-3370-457C-9015-2E088ACA6181) for more details about OAC Snapshots.

### Mandatory Security Best Practices

*Guide:*

*Use this text for every engagament. Do not change. Aligned with the Cloud Adoption Framework*

```{.snippet}
sec-best-practices
```

### Hub and Spoke

For this deployment architecture a Hub and Spoke topology is designed. A hub-and-spoke network, often called a star network, has a central component that's connected to multiple networks around it. 

The dynamic routing gateway (DRG) is a virtual router that provides a path for private network traffic between a virtual cloud networks (VCN) inside and outside the region, such as a VCN in another Oracle Cloud Infrastructure region, an on-premises network, or a network from another cloud provider.

The DRG connects to multiple VCNs, adding flexibility to how you design your cloud network.

The hub VCN has an internet gateway for network traffic to and from the public internet. It also has a dynamic routing gateway (DRG) to  enable private connectivity with your on-premises network, which you can implement by using Oracle Cloud Infrastructure FastConnect, or Site-to-Site VPN, or both.

You can use a OCI Bastion service to provide secure access to your resources. This architecture  uses Bastion Service.

### VCN and Subnets

For security reasons the the Data Warehouse and Analytics components are positioned in a separate VCN. Spoke VCNs are not accessible from the internet. All components are placed in private subnets. The subnets where OAC, ADW and the Linux developer instance are in can be configured to be accessible from customers network or accessed through the Bastion Service in the Hub VCN. VCN's require to have CIDR ranges that are not overlapping with other VCN's and are also not overlapping with IP ranges used in ${doc.customer.name} network.

### Network Firewall

Optionally a managed Network Firewall can be leveraged to increase security posture of the workload.

OCI Network Firewall is a next-generation managed network firewall and intrusion detection and prevention service for VCNs, powered by Palo Alto Networks®. The Network Firewall service offers simple setup and deployment and gives visibility into traffic entering the cloud environment (North-south network traffic) as well traffic between subnets (East-west network traffic).

Use network firewall and its advanced features together with other Oracle Cloud Infrastructure security services to create a layered network security solution.

A network firewall is a highly available and scalable instance that you create in the subnet of your choice. The firewall applies business logic to traffic that is specified in an attached firewall policy. Routing in the VCN is used to direct network traffic to and from the firewall.

![Network Firewall deployment example](images/network-firewall-drg.png)

Above a simple example is presented where a Network Firewall is deployed in a DMZ subnet and for which all incoming traffic via the DRG as well as all the outgoing traffic from the private subnet is routed to the Network Firewall so that policies are enforced to secure traffic. 

#### Bill of materials

Environment | Description | Metric | Size | Monthly Cost | Annual Cost| Hours p/m
----------- | ----------- |----------- |----------- |----------- |----------- |-----------
Prod | Network Firewall (optional) | Instance per Hour | 1 |  |  | 744


| Part Number | Component                                                                                     | Unit of Measure  | Units    |
| :---------- | :-------------------------------------------------------------------------------------------- | :-------         | ----:    |
| B95403      | Oracle Cloud Infrastructure - Network Firewall Instance                                    | Instance per Hour              | 744    |

Further details can be found [here](https://docs.oracle.com/en-us/iaas/Content/network-firewall/overview.htm)

### Informatica Secure Agent

The Informatica Secure Agent requires a connection with the Informatica Control plane. This connection is established with a Network address translation (NAT) gateway. A NAT gateway enables private resources in a VCN to access hosts on the  internet, without exposing those resources to incoming internet  connections.

### Architecture Decisions (Optional)
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*List the architecture decisions for the previous future state architecture(s). The decisions can be based upon the previously defined requirements or can be based on common architecture best practices or architecture design patterns.*

### Requirements Evaluation (Optional)

*Guide:*

*List architecture decisions and how they impact previous functional, non-function, or other requirements. Do a realist evaluation and also highlight lowlights where an architecture decision might not fully comply with a previous requirement. Discuss with your customer and get feedback from your colleagues if some requirements are not fully satisfied.*

## Solution Considerations
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*Describe certain aspects of your solution in detail. What are the security, resilience, networking, and operations decisions you have taken that are important for your customer?*

### High Availability and Disaster Recovery 

*Reference:*

[HA Reference for EBS](https://confluence.oraclecorp.com/confluence/x/jy_9cgE) <!-- TODO: Public link needed -->

### Security
<!-- [Security Snippets](https://orahub.oci.oraclecorp.com/emea-workloadarchitecture/wad-snippets/-/tree/main/snippets/security/security-design/sec) -->

*Guide:*

*Please describe your solution from a security point of view. Generic security guidelines are in the Annex chapter.*

*Example:*

Please see our security guidelines in the [Annex](#security-guidelines).

### Networking

*Reference:*

[Networking Confluence](https://confluence.oraclecorp.com/confluence/x/jDxJBQE) <!-- TODO: Public link needed -->

### Operations (Optional)
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*In this chapter, we provide a high-level introduction to various operations-related topics around OCI. We do not design, plan or execute any detailed operations for our customers. We can provide some best practices and workload-specific recommendations.*

*Please visit our Operations Catalogue for more information, best practices, and examples: https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=3403322163* <!-- TODO: Public link needed -->

*The below example text represents the first asset from this catalog PCO#01. Please consider including other assets as well. You can find MD text snippets within each asset.*

*Example:*

```{.snippet}
uc-oci-cloud-operations
```

## Sizing and Bill of Materials
<!--
Price Lists and SKUs / Part Numbers: https://esource.oraclecorp.com/sites/eSource/ESRCHome
-->

*Guide:*

*Estimate and size the physically needed resources of the Workload. The information can be collected and is based upon previously gathered capacities, business user numbers, integration points, or translated existing on-premises resources. The sizing is possibly done with or even without a Physical Architecture. It is ok to make assumptions and to clearly state them!*

*Clarify with sales your assumptions and your sizing. Get your sales to finalize the BoM with discounts or other sales calculations. Review the final BoM and ensure the sales are using the correct product SKUs / Part Number.*

*Even if the BoM and sizing were done with the help of Excel between the different teams, ensure that this chapter includes or links to the final BoM as well.*

*WIP*
- *Revision of existing discovery templates*
- *Consolidated data gathering sheet (sizing focused)*
- *Workload-specific sizing process/methodology*

Example for a small workload, but to be adjusted for ${doc.customer.name}s situation

| Environment | Component              | Quantity                | Metric    |
| ----------- | ---------------------- | ----------------------- | --------- |
| Pilot       | OAC Enterprise Edition | 2 | OCPU      |
| Pilot       | ADW-S                  | 2 | OCPU      |
| Pilot       | Object Storage         | 5 | Terrabyte |
| Pilot       | Compute Cloud - Oracle Free Linux Cloud Develop | 1 | OCPU |
| Pilot       | Compute Cloud for Informatica Secure Agent | 8 | OCPU |
| Pilot       | Exadata Storage        | 5 | Terrabyte |
| Pilot       | Block Volume           | 500 | Gb |

Next section is included in this document as an example covering the activities required for such migration and needs to be agreed with the migration partner (Lift, Oracle Consulting, 3rd party partner) to reflect the activities and effort required.

<!--                                                 -->
<!-- End of 3) Workload Requirements and Architecture -->
<!--                                                 -->

<!-- Use the below chapter only for Oracle Implementations such as Lift and FastStart. do not describe the work plan for 3rd Party implementation partners --> 

## OCI Secure Landing Zone Architecture

*Guide:*

*This chapter describes landing zone best practices and usually does not require any changes. If changes are required please refer to [landing zone confluence](https://confluence.oraclecorp.com/confluence/x/GZ-VHQE). The full landing zone needs to be described in the Solution Design by the service provider.*

*Use this template ONLY for new cloud deployments and remove for brown field deployments.*

```{.snippet}
ar-landingzone
```
## Physical Architecture
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*The Workload Architecture is typically described in a physical form. This should include all solution components. You do not have to provide solution build or deployment details such as IP addresses.*

*[The Oracle Cloud Notation, OCI Architecture Diagram Toolkits](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)*

*Reference:*

[StarterPacks](https://orahub.oci.oraclecorp.com/emea-workloadarchitecture/wad-snippets/-/tree/main/starter-packs) <!-- TODO: Change to public link -->

![Deployment Architecture](images/Deployment-Architecture.jpg)The white subnets are in scope for this architecture

# Project Implementation (Only for Oracle Implementations!)

## Solution Scope

### Disclaimer
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | None
PPM   | None
-->

*Guide:*

*A scope disclaimer should limit scope changes and create awareness that a change of scope needs to be agreed upon by both parties.*

*Example:*

```{.snippet}
uc-disclaimer
```
* OBIEE 11.1.1.9 will be migrated to OAC (in a private subnet). All data will be migrated, but testing will be done on a limited number of reports.
* Oracle Database will be migrated to ADW
* informatica Powercenter will be migrated to Informatica IDMC (IDMC)
* Solution for DAC to be defined and not in scope of this solution pack

### Overview
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | R
PPM   | C
-->

*Guide:*

*Describe the scope of the implementation as a sub-set of the Workload scope. For example one environment from one application.*

### Business Value
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | C
PPM   | C
-->

*Guide:*

*What's the value for the customer to do an Oracle implementation? For example, speed of deployment and the resulting impact on time to market, and free service. Do not describe Oracle's value or consumption.*

*Example:*

```{.snippet}
uc-business-value
```

### Success Criteria
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | R
PPM   | C
-->

*Guide:*

*Technical success criteria for the implementation. As always be S.M.A.R.T: Specific, Measurable, Achievable, Relevant, Timebound. Example: 'Deployment of all OCI resources for the scoped environments in 3 months'.*

*Example:*

The below-listed success criteria are for the ${doc.config.impl.type} implementation only. Partner activities and success criteria are not listed in this documentation.

- Finish provisioning of all OCI resources
- Establish all required network connectivity
- Successfully pass all test cases
- Finished handover with documentation
- Complete the Implementation Security Checklist


### Specific Requirements and Constraints (Optional)
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | C
PPM   | None
-->

*Guide:*

*If the implementation scope has special or different requirements as otherwise explained in the Workload.*

## Workplan

### Deliverables
<!--
Role  | RACI
------|-----
ACE   | A
Impl. | R
PPM   | None
-->

*Guide:*

*Describe deliverables within the implementation scope. Including this documentation as Solution Definition and the later following Solution Design. This should be a generic reusable text, provided by the implementers.*

A Solution Defintion Document which includes:

- Solution Definition

### Included Activities and Implementation RACI
<!--
Role  | RACI
------|-----
ACE   | A
Impl. | R
PPM   | None
-->

*Guide:*

*Describe the implementation activities. It does need to include a detailed list of cloud services or OCI capabilities, but rather includes activities such as 'Provisioning of Infrastructure Components'. This should be a generic reusable text, provided by the implementers.*

*Describe for all activities the RACI (Responsible, Accountable, Consultant, Informed) matrix*

*Example:*

#### Infrastructure and Landingzone

- OCI Infrastructure and landingzone setup
  - Compartments
  - VCN
  - Subnets
  - IAM, users, groups, identity domains, SL, RT, NSG
  - Connections with customer Network
    - VPN or Fastconnect IP Sec connection
    - Source system
  - Connection with Informatica control plane
- Provisioning of Services
  - ADW
  - Compute for IDMC agent migration tool
  - OAC +PAC
  - IAM and Users
  - Compute for Bastion
  - Compute for DB Migration (Developer cloud service)
  - Object Store bucket

#### Migration of On-premise DB to Oracle Autonomous Database

- Pre-migration tasks in source database:
   - Collect and analysis previous information related to the source database (Review space used by schemas, registry state, invalid objects, execution and analysis CPAT tool).
   - Support to export and copy Datapump files to OCI Object Storage which will be done by customer.

- Configure Working Migration Development (Developer cloud service, oracle client, OCI CLI, etc.)
- Database Migration using Oracle Datapump. Sample parameter might be used on certain tables if data volume is too big in size.
- Postmigration tasks:
   - Fix warning detected in the migration to ADW
   - Fix privileges not imported with Datapump
   - Support customer with validations after the database migration

#### OBIEE to Oracle Analytics Cloud

- Establishing the connectivity between ADW and OAC (Private Access Channel will be used)
- RPD is cleansed from Errors and Warnings during migration by customer with help from Oracle team
- Configuration of IAM Roles to Application Roles in OAC (limit to 5 users and 10 groups to Application Role mapping)
- Migration of the existing reports and dashboards
- Testing for a limited number of reports (up to 10 reports)

#### Informatica Powercenter to IDMC (Wilbert reached out to Infa Team)

- Deployment of IDMC agent on OCI (IDMC Market place)
- Export of Informatica Powercenter Repository (customer activity)
- Assessment step to check on possible issues to be covered
- Installation of IDMC + its new Repository
- Other preparation steps?????.........
- Use Migration tool from Informatica to migrate repository.
- Change or create connections to new ADW database
- Unit test for a limited number of mappings

#### DAC to ?????? (Manual Activity - solution definition still to be made and checked with Infa Team)

- Export of DAC repository content or access to running DAC environment at On-Premise
- Creation of new parameter storage solution
- Manually create schedule for migrated mappings                                                    | Something                  | Partner | Customer | Partner | Oracle

### Recommended Activities
<!--
Role  | RACI
------|-----
ACE   | A
Impl. | R
PPM   | None
-->

*Guide:*

*All activities not stated in the [Included Activities](#included-activities) are out of scope, as described in the [Disclaimer](#disclaimer). We do not provide a list of excluded activities to not create expectations based on a grey area between included and excluded activities. Here we only recommend further activities which happen to not be included but are not a full list of excluded activities.*

This workload is designed to assist Customer to rapidly start utilizing Oracle Cloud Infrastructure and allow them to explore the benefits of the solution to them for further rollout. Once the Lift team finishes the work, the customer can leverage the knowledge acquired from this project to create additional environments themselves or with the help of ${doc.config.impl.type}.

### Timeline
<!--
Role  | RACI
------|-----
ACE   | A
Impl. | R
PPM   | C/I
-->

*Guide:*

*Provide a high-level implementation plan. Use phases to communicate an iterative implementation if needed.*

#### Phase 1: Development Environment

This high-level project timeline shows a representative timeline and is intended for planning purposes only.

| Step                                        | Description | Effort |
| ------------------------------------------- | ----------- | ------ |
| Initiation, INfrastructure and Connectivity |             | 6.5    |
| Migration of DB and OBIEE to ADW and OAC    |             | 25     |
| Migration of Powercenter to IDMC            |             | xx     |
| Documentation, Security, QA and handover    |             | 4      |
| TPM and PPM                                 |             | 7      |
| DAC replacement design                      |             | xx     |
| Total                                       |             | 42.5   |

#### Phase n: <name>

### Assumptions
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | R
PPM   | None
-->

*Guide:*

*List any assumptions, if any, which could impact the solution architecture or the implementation.*

*Example:*

#### Infrastructure and Landingzone

- Predefined Reference Architecture can be used
- No implementation of AD and SSO integration
- VPN IP-Sec tunnel
- Creation of maximum 5 users and 5 groups
- creation of 2 identity domains

#### On premise DB to Oracle Autonomous Database

- Oracle Database
- Database minimum version of 10.2.0.5
- Size of DB maximum 2 TB
- CPAT tool outcome reveals no blocking errors
- One time migration of database content. Later adjustments and new data will not be taken in account.  

#### OBIEE to Oracle Analytics Cloud

- OBIEE is on minimum version 11.1.1.9
- RPD is in a consistent state
- Usage tracking will not be re-configured
- Customer will send us the RPD and the export of the migration tool from OBIEE
- Agents and schedulers will not be tested
- SMTP server will not be configured
- BI Publisher reports will not be tested
- No JS and/or CSS customisation of the reports
- No special characters (including spaces) are used in the names of the reports and entities in the catalog
- Unsupported functionality such as "Act As" is not used
- Reporting performance will remain as found (no performance improvement activities will be carried out)
- No setup/configuration of write-back functionality
- No security integration setup based on ICX-Session cookies. Data level security will not be tested and validated.

#### Informatica Powercenter to IDMC

*Guidance*
*This section probably will be part of a 3rd party/customer to provide input or create a plan for it.*

#### DAC to ??????

*Guidance*
*No replacing technolgy for this is availble yet. Could be an IDMC solution or 3rd party, or custom solution*

### Generic Assumptions

All work will be done remotely and within either local time or India standard time within normal office working hours.
The following assumptions have been made about the project, which will impact delivery:

- Disaster Recovery is not in scope
- Tenancy is provisioned as new with availability of Identity and Access Management Identity Domains
- Customer will have the export datapump prepared and he will copy datapump files to the Oracle Object Storage
- For the pilot customer accepts to pass warnings and errors when loading the data in the database.

### Out of scope

The following components and activities are out of scope:

- Provisioning and configuration of a second instance (only a NONPROD instance will be provisioned).
- Any third party or Customer on-premises integration.
- Third Party products, Backup tools, Firewall implementation, Security tools, monitoring tools implementation.
- Load Testing, Performance benchmarking testing, Functional/code change & tuning of any component in the solution.
- Any Vulnerability Assessment and Penetration Testing.
- Trainings on deployed products and cloud services.
- Any other activity not listed under “In Scope” section.
- Migration Apex workspaces in case of use.


### Obligations
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | R
PPM   | None
-->

*Guide:*

*List any obligations required by the customer to perform or have available, if any, which could impact the architecture or the implementation. Please always include this chapter to capture the obligation that we have admin access to the customer's tenancy.*

*Example:*

- You will have purchased the appropriate Universal Credits for the services required for the project.
- The implementation team will have admin access to the customer's tenancy for implementation.
- You will ensure the appropriate product training has been obtained to maintain and support the implementation
- Your business team will be available for the Testing phase, which will be completed within the agreed testing window.
- You will provide project management for the project and will manage any third-party suppliers or vendors.
- Complete the OCI Site-to-Site VPN Request Form as supplied by the Oracle Workload Architect
- Complete the OCI Fast Connect Request Form as supplied by the Oracle Workload Architect
- Test cases to be defined and provided by the customer

### Interdependencies (Optional)
<!--
Role  | RACI
------|-----
ACE   | R/A
Impl. | R
PPM   | None
-->

*Guide:*

*Describe dependencies between implementation or service providers. These can be inbound or outbound dependencies.*

## Other

# Annex

```{.snippet}
annex-common-security
```

<!-- 
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠸⣷⣦⣀⠀⠀⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⣿⣦⠀⠠⠾⠿⣿⣷⠀⠀⠀⠀⠀⣠⣤⣄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠟⢉⣠⣤⣶⡆⠀⣠⣈⠀⢀⣠⣴⣿⣿⠋⠀⠀⠀⠀
⠀⢀⡀⢀⣀⣀⣠⣤⡄⢀⣀⡘⣿⣿⣿⣷⣼⣿⣿⣷⡄⠹⣿⡿⠁⠀⠀⠀⠀⠀
⠀⠀⠻⠿⢿⣿⣿⣿⠁⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣁⠀⠋⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠻⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⢰⣄⣀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⡀⠀⣴⣿⣿⣿⣿⣿⣿⣿⡿⢿⡿⠀⣾⣿⣿⣿⣿⣶⡄⠀
⠀⠀⠀⠀⠀⢀⣾⣿⣷⡀⠻⣿⣿⡿⠻⣿⣿⣿⣿⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣠⣾⡿⠟⠉⠉⠀⢀⡉⠁⠀⠛⠛⢉⣠⣴⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⢸⣿⣿⡿⠉⠀⠙⠿⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⠁⠀⠀⠀⠀⠀⠙⠿⣷⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠃⠀⠀⠀⠀⠀⠀⠀
        
        Have a great summer 2023!⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
-->
