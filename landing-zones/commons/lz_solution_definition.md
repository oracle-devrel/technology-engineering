# OCI LANDING ZONE SOLUTION DEFINITION

## **Table of Contents**

[1. Introduction](#1-introduction) </br>
[2. Design Considerations](#1-design-considerations--decisions)</br>
[3. How to Start](#3-landing-zone-zone-approach) </br>


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


## **3. How to Start**


Find in the table below a summary of the two approaches for OCI Landing Zones.



| APPROACH  |  OBJECTIVE | DESCRIPTION | 
|---|---|---|
|  [**Standard Landing Zones**](/landing-zones/standard_landing_zones/readme.md) | **Best Practices</br>3 Shapes** | **Three standard shapes/models** for different organization scopes, **ready to use** with **design blueprints** and  **IaC configurations**. Use these models directly or tailor them to your needs.  | 
| [**Tailored Landing Zones**](/landing-zones/tailored_landing_zones/readme.md)  | **Tailored Design </br> Any Shape** | An approach to solve **specific requirements** when the standard models are not enough. A tailored model has **dedicated design views** to match requirements and an IaC runtime. This approach is commonly used to bridge **existing customer practices** in other CSPs. |  


&nbsp; 

The general recommendation when **starting with OCI landing zones** is:
1. Start with [**Standard Landing Zones**](/landing-zones/standard_landing_zones/readme.md) as they're full of best practices. There are [**three models/shapes**](/landing-zones/standard_landing_zones/readme.md#2-what-are-the-models-available) available for different scopes, we'll help you find the best fit [**here**](/landing-zones/standard_landing_zones/readme.md#3-decide-on-the-model-to-use).
2. If your design is very **customized**, requiring **structural changes** to a standard landing zone (IAM or Network), and/or you need a **highly scalable operating model**, use the [**Tailored Landing Zones**](/landing-zones/tailored_landing_zones/readme.md) approach to create your solution.
3. Complementary, if you have a **specific target workload** that is available as [**Workload Extensions**](/landing-zones/workload_extensions/readme.md), use it directly on top of your landing zone. If it's not available, be free to reach out to us or use the tailored approach to set up your extensions.

&nbsp; 


&nbsp; 


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
