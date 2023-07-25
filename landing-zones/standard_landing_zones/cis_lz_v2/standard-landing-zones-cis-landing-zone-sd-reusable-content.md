# Landing Zones

With Landing Zones, we simplify the OCI onboarding experience and reduce OCI day-one and day-two efforts. We provide Landing Zone assets, best practices, and approaches covering the complete spectrum of OCI landing zones, from the standards ones with the CIS LZ and OELZ to the most strategically tailored design with IaC.

# Future State Architecture

## OCI Cloud Landing Zone Architecture


The design considerations for an OCI Cloud Landing Zone have to do with OCI and industry architecture best practices, along with A Company Making Everything specific architecture requirements that reflect the Cloud Strategy (hybrid, multi-cloud, etc).

These are some characteristics of a Landing Zone:

1. It provides a set of **best practices** and a prescriptive approach to deploying secure landing zones.
2. It creates a **pre-defined** landing zone structure (compartments, networks, groups, policies, etc.)
3. It’s a **configurable** setup, with no design or implementation activities.
4. It provides a **secure footprint** to safely land and use workloads.
5. It has an **automated deployment** with public code.
6. It’s where the **journey starts** to later expand or extend toward specific requirements.

[CIS Landing Zone v2 Architecture](https://docs.oracle.com/en/solutions/cis-oci-benchmark/index.html#GUID-89CA48AA-73E1-4992-A43F-CA5FA5CE21CD) solution provides a Terraform-based landing zone template that meets the security guidance prescribed in [CIS Oracle Cloud Infrastructure Foundations Benchmark](https://www.cisecurity.org/benchmark/oracle_cloud).

All the documentation is public and accessible in the [GitHub Repository](https://github.com/oracle-quickstart/oci-cis-landingzone-quickstart).

### Naming Convention

A naming convention is an important part of any deployment to ensure consistency as well as security within the tenancy. Hence we jointly agree on a naming convention, matching Oracle’s best practices and A Company Making Everything requirements. 

When deploying an OCI Cloud Landing Zone based on the OCI CIS Landing Zone Quick Start, there is one key input parameter that is used in most of the OCI resource names to make them unique for this Landing Zone deployment. This input parameter is called Service Label and is located in the input tfvars file or can be modified during the deployment via the OCI Resource Manager stack. In the below table of used naming convention, this Service Label is referred to as <label>.

The following naming convention is used with a landing zone deployment for resources created by the Quick Start:

**Resource Type**                     | **Abbreviation**   		| **Example / Usage pattern**   |
:---		                    |:------		      |:------     
Bastion Service                   | bst  | bst< timestamp>   
Compartment            	| cmp   | < label >-< purpose>-cmp 
Dynamic Group         	| dynamic-group   | < label >-< purpose >-dynamic-group 
Dynamic Routing Gateway            	| drg   | < label>-drg 
Dynamic Routing Gateway Attachment          	| drg-attachment  | 
Internet Gateway            	| igw  | < vcn>-igw  
NAT Gateway            	| natgw   | < vcn>-natgw 
Network Security Group            	| nsg   | < subnet>-nsg
Managed key            	| key   | < label>-< purpose>-key  
Object Storage Bucket            	| bucket  | < label>-< purpose>-bucket
Policy           	| policy   | < label>-< purpose>-policy 
Routing Table            	| rtable   | < vcn>-rtable 
Security List            	| security-list   | < subnet>-security-list
Service Connector Hub           	| service-connector  | < label>-service-connector
Service Gateway            	| sgw  | < vcn>-sgw
Subnet            	| subnet   | < vcn>-< purpose>-subnet 
Vault            	| vlt   | < label>-vault
Virtual Cloud Network           	| vcn   | < label>-< purpose>-vcn

This naming convention can be extended and agreed upon for the workload-specific resources.

### Compartments
This chapter covers the Compartments definitions and resources which will be implemented for A Company Making Everything.

By default, the Landing Zone deploys these four predefined compartments:

* < label>-security-cmp
* < label>-network-cmp
* < label>-appdev-cmp
* < label>-database-cmp

Two additional compartments can be created optionally, one as the enclosing compartment for all other compartments and one for Exadata cloud service infrastructure:

* < label>-cmp
* < label>-exainfra-cmp


For guidance on how to use these compartments refer to the Security Principles in the next section.

### Security

This chapter covers the specific Security definitions and resources which will be implemented for A Company Making Everything. Tenancy global security requirements are covered in previous chapters (Regulations and Compliance Requirements, and Mandatory Security Best Practices) and form the foundation for this chapter.

### Security Principles

The following security principles should be applied:

* Groups will be configured at the tenancy level and access will be governed by policies configured in OCI.
* A workload (e.g., project) resources can be deployed in the available **appdev** and **database** compartments, and if multiple workloads need to be deployed the compartment design might need to be extended to facilitate this depending on the requirements.
* It is also proposed to keep any shared resources, such as Object Storage, Networks, etc. in compartments for shared resources or services like the **network** or **security** compartment. This will allow the various resources in different compartments to access and use the resources deployed in the shared services compartment and user access can be controlled by policies related to specific re-source types and user roles.
* Policies will be configured in OCI to maintain the level of access/control that should exist between resources in different compartments. These will also control user access to the various resources deployed in the tenancy. It is essential that the default policies included in the landing zone are reviewed and modified accordingly to comply with customer and workload requirements.

### Authorization

In general, policies hold permissions granted to groups. Policy and Group naming follows the Resource Naming Conventions.



### Tenant Level Authorization

The policies and groups defined at the tenant level will provide access to administrators and authorized users, to manage or view resources across the entire tenancy. The tenant-level authorization will be granted to tenant administrators only.

These policies follow the recommendations of the CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3.



### Compartment Level Authorization


Compartment-level authorization for the network and security compartments follow the recommendations of the CIS Oracle Cloud Infrastructure Foundations Benchmark v1.2.0, recommendations 1.1, 1.2, 1.3.

Apart from tenant-level authorization, authorization for the landing zone compartments is provided via specific policies and groups. In general, policies will be designed so that lower-level compartments are not able to modify the resources of higher-level compartments.

### Additional Security Posture Management

In addition to the services enabled in the chapter Mandatory Security Best Practices, additional OCI services are used to complement the Security Posture.



### OCI OS Management Service

Required policy statements for OCI OS Management Service are included in the Service Policy.

By default, the OS Management Service Agent plugin of the Oracle Cloud Agent is enabled and running on current Oracle Linux platform images. The recommendation is to use the default values unless there are other specific requirements.



### Secure Zones

Oracle Security Zones is a preventive control measure, designed to avoid poor implementation choices that weaken the security stance. OCI Security Zones enforce strict and best practices security rules that are locked and can't be modified.

By default, the Landing Zone does not enable the feature of Secure Zones. The recommendation is to use the default values unless there are other specific requirements.


### Monitoring, Auditing, and Logging

For the SIEM Integration mentioned in the chapter Mandatory Security Best Practices, workload-specific Monitoring, Auditing, and Logging definitions and resources will be implemented for A Company Making Everything. In accordance with the [CIS Oracle Cloud Infrastructure Foundations Benchmark, v1.2.0, Chapter 3](https://www.cisecurity.org/cis-benchmarks), the specified Logging and Monitoring configurations will be made.



### Service Connector

A Service connector can be deployed to manage all service log sources and the designated target specified in 'Service Connector Target Kind'.

By default, Landing Zones does not deploy any service connector. The recommendation is to use the default values unless there are other specific requirements.

As outlined in [Design Guidance for SIEM Integration](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/siem-integration.htm) the following OCI services will provide the necessary information to the SIEM.



### Object Storage

By default, the Landing Zone does not deploy any Object Storage. The recommendation is to use the default values unless there are other specific requirements.

Providing an encryption key is optional. If a key is not provided and 'CIS Level' is set to 2, the Landing Zone will manage the key.

### Events

Two event rules are created by default.

1. < label>-notify-on-iam-changes-rule

1.1. Notification for IAM policy changes.

1.2. Notification for IAM group changes.

1.3. Notification for user changes.

2.  < label>-notify-on-network-changes-rule

2.1 Notification for VCN changes.

2.2. Notification for changes to route tables.

2.3. Notification for security list changes.

2.4. Notification for network security group changes.

2.5. Notification for changes to network gateways.

2.6. Notification for Identity Provider changes.

2.7. Notification for IdP group mapping changes.


### Notification (Topics and Subscriptions)

Two topics are created by default.

* < label>-security-topic
* < label>-network-topic

### Alarms

Two alarms are created by default.

* < label>-fast-connect-status-alarm
* < label>-vpn-status-alarm

### VCN Flow Log 

The VCN flow logging for all subnets is enabled by default.

Example naming: < label>-< subnet>-flow-log

### Data Encryption

All data will be encrypted at rest and in transit. Encryption keys can be managed by Oracle or by the Customer and will be implemented for identified resources.

### Network

This chapter covers the Network definitions and resources which will be implemented for A Company Making Everything.

### VCN & Subnets

The stack provides a standard three-tier network architecture for each VCN. The three tiers are divided into:

1. One public subnet for load balancers and bastion services.

2. Two private subnets:

2.1. one for the application tier

2.2. one for the database tier


### Hub & Spoke

The Landing Zone can deploy simple Network configurations with 1-n VCN or more complex structures like Hub & Spoke network topologies.

By default, the Landing Zone does not deploy a Hub & Spoke network topology. It's highly recommended to use this network topology to scale the deployment of multiple workloads with network isolation and central network control.



### Network Appliance Hub

With a Hub & Spoke topology selected, a requirement can be to route all traffic through the Hub VCN (also known as DMZ VCN).

The Hub VCN (DMZ VCN) can also be used for 3rd-Party Firewalls.



### Exadata VCN

In the case ExaCS workload is required, it's necessary to specify the following subnet:

* One private client subnet.
* One private backup subnet.

By default, Landing Zone does not deploy an EXADATA VCN. The recommendation is to use the default values unless there are other specific requirements.



#### On-Premises/Cloud Service Provider Connectivity

When communication to on-premises networks or a cloud service provider is required, with one VCN over a single FastConnect private virtual circuit or Site-to-Site VPN, the stack can deploy a DRG or reuse an existing one.

By default, Landing Zone does not deploy a DRG. The recommendation is to use the default values unless there are other specific requirements.



#### Public Connectivity

The Landing Zone can deploy **Internet Gateway**, **Nat Gateway**, and **Bastions resources**.

To allow remote access to Compute Instances or Private Database Endpoints, the usage of an OCI Bastion is recommended. The default configuration does not include a Bastion service, in order to deploy it proper configuration values need to be provided for the required attributes in the stack.

By default, Landing Zone deploys an Internet Gateway (< vcn>-igw) and a NAT Gateway (< vcn>-natgw). If blocking of any Internet Access is required, a configuration of an OCI Security Zone recipe and a target configuration for the Network compartment is recommended.



#### Governance 

#### Cost Management

The chapter Mandatory Security Best Practices requires the implementation of budget control for the whole tenancy. Additional budget control can be implemented by the Customer to fit the requirements.

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/main/LICENSE) for more details.