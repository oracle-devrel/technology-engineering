# OCI LANDING ZONE SOLUTION DEFINITION

## **Table of Contents**

[1. Introduction](#1-introduction) </br>
[2. Design Considerations / Decisions](#1-design-considerations--decisions)</br>
[3. Landing Zone Approach](#3-landing-zone-zone-approach) </br>
[4. Standard Landing Zones](#4-standard-landing-zones) </br>
[5. Tailored Landing Zones](#5-tailored-landing-zones)

&nbsp; 

## **1. Introduction**

Welcome to the Landing Zone Framework (LZF) Solution Definition Asset.

Using an OCI Landing Zone will enable a **secured OCI Tenancy**, with operational control and governance, ready to **onboard** and **run**  workloads with **network isolation** and with the right **segregation of duties** in the organization.

The content of this asset will guide you through the **landing zone design decisions**, and help select the best **approach** and **solution** to setup and run an OCI Landing Zone.


&nbsp; 

## **2. Design Considerations / Decisions**

Before choosing the approach and solution, it's important to understand the design decisions to be made - their scope, objective, and related OCI resources - to successfully run OCI. It's recommended to iterate over these elements as they will guide and simplify the understanding of OCI core resources and day-two operations.


&nbsp; 

## 2.1 Security 

The following table presents the recommended security decision to review.

&nbsp; 

| ID  |  DECISION | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **SD.01** | **Tenancy Structure** |  Compartment structure to support resource grouping, separation of duties, budget control and billing, and workloads. | Compartments | 
| **SD.02**| **Identity and Access Management** | The groups, dynamic groups, and policies for the related duties and compartments. | Groups & Policies | 
| **SD.03**| **Security Posture** |  Additional configurations for OCI native security tooling. | Cloud Guard, Security Zones, Vulnerability Scanning, etc. | 

&nbsp; 

## 2.2 Network 

The following table presents the recommended network decision to review. The first two decisions are highly recommended while the last two can be optional depending on requirements.

&nbsp; 


| ID  |  DECISION | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **ND.01** | **Network Structure** | Network elements to support the workloads and network segregation. | VCNs, Subnets, DRG, Gateways | 
| **ND.02**| **Network Security** |  Network areas and their security posture. | NSGs, Security Lists, Gateways, Firewalls | 
| **ND.03**| **Network Connectivity** | Connection to on-premises or other cloud providers with network traffic scenarios. | FastConnec, Site-to-site VPN. </br> ND.01, ND.02 Resources. | 
| **ND.04**| **DNS** | Naming resolution and how DNS zones and records are solved to handle domain DNS queries. |  VCNs, Subnets, Resolvers, and Endpoints. | 

&nbsp; 

## 2.3 Operations 

The following table presents the recommended operational decision to review.

| ID  |  DECISION | DESCRIPTION | OCI RESOURCES
|---|---|---|---|
| **OD.01** | **Teams** | Cloud operations teams responsible for running (provisioning and changing) OCI landing zone and OCI workloads. | Relates to SD01 and SD.02 | 
| **OD.02** | **Tooling** |  Tools to run OCI, used for provisioning and changing of resources. | OCI Console, ORM, CLI, Terraform, SDK, Pipelines, Git, etc. | 
| **OD.03**| **Operating Model** |  The modus operandi to provision and change resources with the tooling by the cloud operations teams. | OD.01, OD.02 | 

&nbsp; 


## **3. Landing Zone Zone Approach**


There are two types of landing zone approaches to consider:

&nbsp; 

| APPROACH  |  DESCRIPTION | 
|---|---|
| [**Standard Landing Zones**](/landing-zones/standard_landing_zones/standard_landing_zones.md) | **Prescribed** and **ready to use** solutions with a **guided setup** and  **IaC**. This is the recommended approach for initial landing zone deployments covering the most common workload scenarios.  | 
| [**Tailored Landing Zones**](/tailored_landing_zones/tailored_landing_zones.md) | An approach to solve **specific requirements** when the standard is not enough. These LZs run with **configuration-as-code** and are used to scale/bridge with existing **operating models**, complying with fine-grained **segregations of duties**, strong **network isolation**, and heterogeneous **workloads**.  |  

&nbsp; 

The guidance we recommend to follow is very simple:

- If you're **starting** with OCI landing zones use a **standard landing zone** as they're full of best practices. If it needs adjustments or extensions on top of the prescribed design, customize it by code or manually. This approach is described in [section 4](#4-standard-landing-zones).
- If your **requirements are very specific/detailed**, or they imply structural changes to a standard landing zone, and/or you need a highly scalable operating model, **use the tailored approach** described in   [section 5](#5-tailored-landing-zones).

&nbsp; 


## **4. Standard Landing Zones**

The **CIS Landing Zone** is the recommended solution to start with standard landing zones. It proposes a design that covers:
- Security Design Decisions (SD.01, SD.02, and SD.03) covered in [section 2.1](#21-security).
- Network Design Decisions (ND.01, ND.02, and ND.03) covered in [section 2.2](#22-network).
- Operations Design Decision (OD.02) covered in [section 2.3](#23-operations).


For complete guidance on the **configuration** and **deployment** of this solution refer to this [**LZF asset dedicated to the CIS Landing Zone**](/landing-zones/standard_landing_zones/cis_lz_v2/cis_landing_zone_v2.md).

For guidande on **extending** this solution with OCI resources on top of the standard model review the [section 4](/landing-zones/standard_landing_zones/cis_lz_v2/cis_landing_zone_v2.md#4-extend-the-solution) of the same asset.



&nbsp; 

## **5. Tailored Landing Zones**



For guiding you on the tailoring of your landing zone use the [**LZF asset dedicated to this approach**](/tailored_landing_zones/tailored_landing_zones.md):
- This asset  will describe all the **recommended steps** for **designing** and **running** your landing zone. 
- In terms of **design**, to tailor a landing zone we recommend using the [**OCI Open LZ Blueprint**](https://github.com/oracle-quickstart/terraform-oci-open-lz).
- In terms of **deployment** and **running** your landing zone design, we recommend the use of the **[CIS Landing Zone Enhanced Modules](https://www.ateam-oracle.com/post/cis-landing-zone-enhanced-modules)**, to **configure** the resources with *json/hcl* terraform native interfaces. 


&nbsp; 

&nbsp; 


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
