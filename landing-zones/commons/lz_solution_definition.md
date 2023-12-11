# OCI LANDING ZONE SOLUTION DEFINITION

## **Table of Contents**

[1. Introduction](#1-introduction) </br>
[2. Design Considerations](#1-design-considerations--decisions)</br>
[3. Landing Zone Approach](#3-landing-zone-zone-approach) </br>
[4. Standard Landing Zones](#4-standard-landing-zones) </br>
[5. Tailored Landing Zones](#5-tailored-landing-zones)

&nbsp; 

## **1. Introduction**

Welcome to the [Landing Zone Framework (LZF)](/landing-zones/README.md) Solution Definition.

This asset provides guidance on the **landing zone design considerations**, and helps select the best **approach** and **solution** to setup and run your OCI Landing Zone.

An OCI Landing Zone sets the foundations for a **secure tenancy**, providing design **best practices** and **operational control** over OCI resources. A Landing Zone also simplifies the **onboarding** of **workloads** and **teams**, with clear patterns for **network isolation** and **segregation of duties** in the organization, which sets the cloud operating model for **day two operations**.

&nbsp; 

## **2. Design Considerations**

Before choosing the approach and solution, it's important to understand a set of security, network, and operational considerations to successfully run OCI - or any cloud provider. It is recommended to iterate over these elements as they will guide the design process, simplify the understanding of OCI core resources, and clarify the day-two operations. For tangibles examples, find [**here**](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/design/OCI_Open_LZ.pdf) an OCI landing zone design document matching these topics.

&nbsp; 

## 2.1 Security 

The following table presents the recommended security topics to review in the landing zone design.

| ID  |  TOPIC | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **SD.01** | **Tenancy Structure** |  Compartment structure to support resource grouping, separation of duties, budget control and billing, and workloads. | Compartments | 
| **SD.02**| **Identity and Access Management** | The groups, dynamic groups, and policies for the related duties and compartments. | Identity Domains, Groups, and Policies | 
| **SD.03**| **Security Posture** |  Additional configurations for OCI native security tooling. | Cloud Guard, Security Zones, Vulnerability Scanning, etc. | 

&nbsp; 

## 2.2 Network 

The following table presents the recommended network topics to review in the landing zone design. The first two topics are highly recommended while the last two can be optional depending on requirements.


| ID  |  TOPIC | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **ND.01** | **Network Structure** | Network elements to support the workloads and network segregation. | VCNs, Subnets, DRG, Gateways | 
| **ND.02**| **Network Security** |  Network areas and their security posture. | NSGs, Security Lists, Gateways, Firewalls | 
| **ND.03**| **Network Connectivity** | Connection to on-premises or other cloud providers with network traffic scenarios. | FastConnec, Site-to-site VPN. </br> ND.01, ND.02 Resources. | 
| **ND.04**| **DNS** | Naming resolution and how DNS zones and records are solved to handle domain DNS queries. |  VCNs, Subnets, Resolvers, and Endpoints. | 

&nbsp; 

## 2.3 Operations 

The following table presents the recommended operational topics to review in the landing zone design.

| ID  |  TOPIC | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **OD.01** | **Teams** | Cloud operations teams responsible for running (provisioning and changing) OCI landing zone and OCI workloads. | Relates to SD01 and SD.02 | 
| **OD.02** | **Tooling** |  Tools to run OCI, used for provisioning and changing of resources. | OCI Console, ORM, CLI, Terraform, SDK, Pipelines, Git, etc. | 
| **OD.03**| **Operating Model** |  The modus operandi to provision and change resources with the tooling by the cloud operations teams. | Relates to OD.01, OD.02 | 
| **OD.04**| **Operatinal Integrations** |  Integrate OCI Landing Zone with external systems, such as SIEM or Monitoring. | Relates to SD.01, SD.02, SD.03, ND.01, ND.03 | 

&nbsp; 


## **3. Landing Zone Zone Approach**

There are two types of landing zone approaches to consider:


| APPROACH  |  DESCRIPTION | 
|---|---|
| [**Standard Landing Zones**](/landing-zones/standard_landing_zones/standard_landing_zones.md) | **Prescribed** and **ready to use** solutions with a **guided setup** and  **IaC**. This is the recommended approach for initial landing zone deployments covering the most common workload scenarios.  | 
| [**Tailored Landing Zones**](/landing-zones/tailored_landing_zones/tailored_landing_zones.md) | An approach to solve **specific requirements** when the standard is not enough. These LZs run with **configuration-as-code** and are used to scale/bridge with existing **operating models**, complying with fine-grained **segregations of duties**, strong **network isolation**, and heterogeneous **workloads**.  | 

&nbsp; 

The **guidance** we recommend to follow is very simple:

- If you're **starting** with OCI landing zones use a **standard landing zone** as they're full of best practices. If it needs adjustments or **extensions** on top of the prescribed design, customize it by code or manually. This approach is described in [next section](#4-standard-landing-zones).
- If your [**requirements** are very **specific/detailed**](/landing-zones/tailored_landing_zones/tailored_landing_zones.md#1-what-are-tailored-landing-zones), or they imply structural changes to a standard landing zone, and/or you need a highly scalable operating model, **use the tailored approach** described in   [section 5](#5-tailored-landing-zones). 

&nbsp; 


## **4. Standard Landing Zones**


| TOPIC  |  DESCRIPTION | 
|---|---|
| **APPROACH** | [Standard Landing Zones](/landing-zones/standard_landing_zones/standard_landing_zones.md) |
| **SOLUTION** | [CIS Landing Zone](/landing-zones/standard_landing_zones/cis_lz_v2/cis_landing_zone_v2.md). CIS 1.2 [certified](https://www.cisecurity.org/partner/oracle) since september 2023. |
| **SECURITY SCOPE** | Covers all topics in [section 2.1](#21-security).
| **NETWORK SCOPE** | Covers all topics in [section 2.2](#22-network) exept ND.04 DNS.
| **OPERATIONS SCOPE** | Covers OD.02 Tooling in [section 2.3](#23-operations). Note that standards landing zones normally have very simple and centralized operating models, and might not require the remaining elements. 
| **RUNTIME** | Use the solution link for complete guidance on the **configuration** and **deployment** of this solution.
| **EXTENSIONS** | **- Design**: For guidande on **extending** this **solution design** with OCI resources on top of the standard model review the [section 4](/landing-zones/standard_landing_zones/cis_lz_v2/cis_landing_zone_v2.md#4-extend-the-solution) of the CIS LZ solution. </br>**- Deployment/Run with IaC**: An alternative to add-ons on the solution v2 code base is using of the [CIS Landing Zone Enhanced Modules](https://www.ateam-oracle.com/post/cis-landing-zone-enhanced-modules), to **configure** the resources templates with *json/hcl* terraform native interfaces. | 

&nbsp; 

## **5. Tailored Landing Zones**


| TOPIC  |  DESCRIPTION | 
|---|---|
| **APPROACH** | [Tailored Landing Zones](/landing-zones/tailored_landing_zones/tailored_landing_zones.md)  |
| **SOLUTION** | Use the [OCI Open LZ Blueprint](https://github.com/oracle-quickstart/terraform-oci-open-lz) to tailor your landing zone. There are also complementar [models](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/design/models/readme.md) for initial discussions. This solution uses CIS 1.2 compliant Terraform modules.|
| **SECURITY SCOPE** | Covers all topics in [section 2.1](#21-security).
| **NETWORK SCOPE** | Covers all topics in [section 2.2](#22-network).
| **OPERATIONS SCOPE** | Covers all topics in [section 2.3](#23-operations) except OD.04 Integrations.
| **RUNTIME** | - In terms of **deployment** and **running** your landing zone design, we recommend the use of the **[CIS Landing Zone Enhanced Modules](https://www.ateam-oracle.com/post/cis-landing-zone-enhanced-modules)**, to **configure** the resources with *json/hcl* terraform native interfaces. </br> - Note the [**OCI Open LZ Blueprint**](https://github.com/oracle-quickstart/terraform-oci-open-lz) also presents the **Runtime View** of the design, with IaC configurations for each operation scenario, using these same [modules](https://www.ateam-oracle.com/post/cis-landing-zone-enhanced-modules).
| **EXTENSIONS** | Any extension is a new operation scenario and follows the same process and cloud operating model of all other scenarios. Refer to the **OCI Open LZ** [**Runtime View**](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/examples/oci-open-lz/readme.md) for examples and the [**Operations View**](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/design/OCI_Open_LZ.pdf) for more details on the cloud operating model.| 


&nbsp; 

&nbsp; 


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
