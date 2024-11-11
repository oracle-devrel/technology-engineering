

## Version Control
<!-- GUIDANCE -->
<!--
A section describing the versions of this document and its changes.
-->

| Version | Author       | Date                 | Comment         |
|:--------|:-------------|:---------------------|:----------------|
| 1.0     | Vaibhav Tiwari | March 14th, 2024 | Initial version |


## Team
<!-- GUIDANCE -->
<!--
A section describing the versions of these documents and their changes.
-->

| Name         | E-Mail              | Role                              | Company |
|:-------------|:--------------------|:----------------------------------|:--------|
| Vaibhav Tiwari | vaibhav.t.tiwari@oracle.com | Cloud VMware Solutions Specialist | Oracle  |


## Abbreviations and Acronyms
<!-- Guidance -->
<!--
Abbreviation: a shortened form of a word or phrase.
Acronyms: an abbreviation formed from the initial letters of other words and pronounced as a word (e.g. ASCII, NASA ).
Maintain a list of terms, if needed. Use this internal page to find and translate abbreviations and acronyms: https://apex.oraclecorp.com/pls/apex/f?p=15295:1:8900541624336:::::
-->


| Term  | Meaning                               |
|:------|:--------------------------------------|
| SD   | Secure Desktop Service        |
| OCI   | Oracle Cloud Infrastructure           |
| VCN   | Virtual Cloud Network                 |
| IAM   | Identity and Access Management        |
| AD  | Availbility Domain   |       |
| FD   | Fault Domain     |
| IGW  | Internet Gateway      |
| RT    | Route Table                 |
| OSS   | Object Storage Service                |
| SL | Security List |
| BV   | Block Volume Service
| RMS   | Resource Manager Stack

## Document Purpose

This document does provide the highlevel overview of the Oracle Cloud Secure Desktop service.

Oracle Cloud Infrastructure Secure Desktops elevates virtual desktops in the cloud by offering centralized management of large, identically configured pools.  This saves administrators time and ensures consistency. Flexibility is key, with options to leverage pre-existing virtual machine shapes or craft custom desktop images equipped with your organization's specific software. Security is prioritized through strict access controls that safeguard both cloud resources and data. 

Users benefit from a simple experience, securely accessing desktops from various devices with downloadable clients or even web browsers.  And as your needs change, Secure Desktops easily scales by adding or removing desktops from the pool, keeping pace with your evolving workforce while optimizing costs.  Overall, it provides a secure, manageable, and adaptable solution for delivering virtual desktops to your organization.




# Business Context
<!-- GUIDANCE -->
<!--
Describe the customer's business and background. What is the context of the customer's industry and Line of Business (LOB)? What are the business needs and goals which this Workload is an enabler for? How does this technical solution impact and support the customer's business goals? Does this solution support a specific customer strategy, or maybe certain customer values? How does this solution help our customers to either generate more revenue or save costs?

Mandatory Chapter

| Role  | RACI |
|:------|:-----|
| ACE   | R/A  |
| Impl. | None |
| PPM   | None |
-->

*Example:*

${doc.customer.name} is located in Frankfurt, Germany, and is the largest consumer electronics company. ${doc.customer.name} has 2500 employees at this location, generating
millions of dollars in sales. There are subsidiaries under ${doc.customer.name} corporate family which contribute to overall sales for the parent organization.

${doc.customer.name} is an existing Oracle Cloud customer and currently consuming various OCI services such as network, compute, storage, and databases in OCI Frankfurt Region. The current Production, Test, Dev & DMZ environments are hosted in an on-premises infrastructure with physical servers. The customer has a cloud and digital transformation strategy and would like to exit the data center by moving the on-premises workloads to the cloud.

The mission-critical application workloads are hosted primarily in VMware.  The customer is looking for quick and seamless migration to the cloud with minimal interruption to the services. They have decided to use the Oracle Cloud Infrastructure using the Oracle cloud Migration for quick migration of the VMware workloads before their current data center contract expires. The Oracle Cloud Infrastructure offers flexible, highly scalable, and cost-effective solutions to host critical workloads without disrupting their core business.

## Executive Summary

## Workload Business Value

<!-- GUIDANCE -->
<!--
A clear statement of specific business value as part of the full workload scope. Try to keep it SMART: Specific, Measurable, Assignable, Realistic, and Time-Related - Agree on the SMART business value with the customer. Keep it business focused, and speak the language of the LOB which benefits from this Workload: "Increase Customer Retention by 3% in the next year" or "Grow Customer Base with Executive Decision-Making from our Sales and Support Data". Avoid technical success criteria such as "Migrate App X to Oracle Cloud" or "Provision 5 Compute Instances". Avoid Oracle success criteria and language "Get Workload Consuming on OCI".

Mandatory Chapter

| Role  | RACI |
|:------|:-----|
| ACE   | R/A  |
| Impl. | None |
| PPM   | None |
-->

*Example:*

${doc.customer.name} is running a strategic program in FY23 called EXAMPLE. As part of their initiative, one pillar is dedicated to their IT cost saving. ${doc.customer.name} is planning to reduce their IT estate spending by 15% in the current FY. Oracle can help ${doc.customer.name} by reducing the VMware deployment complexity and operations while optimizing IT costs. ${doc.customer.name} IT department wants to innovate other LoBs and enable quick-time-to-market for various applications and business needs. This allows ${doc.customer.name} to stay ahead in a competitive market.

Oracle Cloud Infrastructure (OCI) Secure Desktop Service provides a secure and managed virtual desktop solution in the cloud. It enables organizations to securely access their desktop environments from anywhere using a wide range of devices, enhancing mobility and flexibility for end-users. Secure Desktop Service offers features such as centralized management, data encryption, and secure access controls, ensuring the protection of sensitive information and compliance with regulatory requirements. With built-in scalability and high availability, organizations can easily deploy and scale their virtual desktop infrastructure to meet changing business needs while reducing operational overhead and infrastructure costs.


# Overview

Oracle Cloud Infrastructure (OCI) Secure Desktop Service offers secure and managed virtual desktop environments, enabling remote access from any device. It provides centralized management, robust security features, and scalability for uninterrupted productivity. With OCI Secure Desktop Service, organizations can embrace remote work seamlessly and securely. 

The Oracle Secure Desktop service enables you to perform the following tasks:

* Create a custom Image for Secure Desktop

* Prepare the tenancy for Secure Desktop 

* Publish Desktops for end users

- Endusers connect to the Instance


Oracle guides in planning, architecting, prototyping, and managing Secure Desktop. Customers can host and deploy Windows or Linux instances using custom images on Oracle Cloud Infrastructure (OCI). Instances can be launched within a few hours or even less than a day, providing rapid provisioning and deployment capabilities. Secure Desktop service has a minimal price of 5 USD per instance launched (monthly), followed by OCI resource charges.

# Customer's Environment

With Secure Desktop, customers may find themselves in one of three scenarios with their environment. 

The first scenario involves customers who are planning to deploy desktop instances and currently have no existing deployment in place.

In the second scenario, customers may have an On-Premises Datacenter where they host a VDI solution, which could be based on VMware or another hypervisor. Within this environment, applications like VMware Horizon or Citrix manage the desktop instances atop the hypervisor.

The third possibility is that customers are already running desktop instances in the cloud. They may utilize services such as AWS Workspaces or Azure Virtual Desktops for this purpose.



### Current State IT Architecture OnPrem Datacenter

For a customer with an On-Premises Datacenter, managing a hypervisor and running a VDI solution, the following expenses need to be considered:

* Datacenter Location: This refers to the physical location of the data center facility, including any associated costs such as rent or lease expenses.

* Hardware Costs: Expenses related to the purchase and maintenance of servers, storage devices, networking equipment, and other hardware components required for the data center infrastructure.

* Datacenter Charges: These are ongoing expenses associated with operating the data center facility, including electricity, cooling, and facility maintenance costs.

* Hypervisor Charges: Licensing fees for the hypervisor software being used, such as VMware vSphere or Microsoft Hyper-V, along with any associated support and maintenance costs.

* DR (Disaster Recovery) Charges: Costs related to implementing and maintaining a disaster recovery solution, including hardware, software, and off-site storage facilities.

* Maintenance Charges: Expenses for ongoing maintenance and support services, including hardware maintenance contracts, software updates, and infrastructure upgrades.

* Additional Software: Costs associated with other software components required for the data center environment, such as firewall software licenses, along with the specific versions of these software packages.

It's important to identify the specific versions of software being used in the data center environment to ensure compatibility and compliance with licensing agreements.

![Current State Architecture](image/OnPrem-horizon.png)


### Current State IT Architecture Cloud Service

When customers run desktop instances from cloud vendors like AWS WorkSpaces or Azure Virtual Desktop, it's crucial to examine the following pricing details:

* Pricing Model: Understanding the pricing model used by the cloud vendor for their desktop services, including any subscription-based or pay-as-you-go options.

* Infrastructure Charges (Compute, Storage, Networking): Evaluating the costs associated with compute resources (such as virtual machine instances), storage (for user profiles and data), and networking (data transfer and network usage).

* Other Services Used by Desktop Instances: Identifying any additional services utilized by the desktop instances, such as monitoring, security, or backup services offered by the cloud vendor.

* Support Charges: Reviewing the costs associated with technical support and assistance provided by the cloud vendor, including any premium support or managed services options.

By comparing these pricing details with Oracle Cloud Infrastructure (OCI) services, customers can determine the most cost-effective solution for their desktop requirements. It's essential to analyze which services are critical for their desktop infrastructure in the cloud and prioritize accordingly to optimize costs and meet business needs effectively.

![Current State Architecture](image/AWS.png)

![Current State Architecture](image/AVD-1.png)



### Gather inventory details

__VM resource allocations per location:__


| Location      | Type             | Operating System Version | Total vCPU Cores | Total Memory (GB) | Used Storage (GB) | Total Storage (GB) |
|:--------------|:-----------------|:-----------------|:------------------|:------------------|:------------------|:-|
| Location Name | Virtual Machines | Windows or Linux    | 550              | 1800              | 23580             | 30000 |


# Future State


### Future State of VDI on Oracle Secure Desktop Solution

The future setup of VDI on the Oracle Secure Desktop solution will offer a robust, secure, and highly scalable environment designed to meet the evolving needs of modern enterprises. It will leverage Oracle's advanced security features to ensure that data and applications remain protected against emerging threats. The solution will provide seamless integration with cloud services, enabling organizations to easily scale their desktop infrastructure up or down based on demand. Enhanced user experience will be a key focus, with faster access times, high availability, and improved performance through optimized resource allocation. 

Additionally, comprehensive management tools will enable administrators to efficiently oversee and maintain the VDI environment, ensuring maximum uptime and productivity. This future state will empower businesses to achieve greater flexibility, security, and efficiency in their desktop management processes.

![Future State Architecture](image/Futurestate-ocm-Architecture.jpg)


### Licensing Model for Oracle Secure Desktop

The future licensing model for Oracle Secure Desktop will be designed to offer flexibility and scalability for enterprises. It will provide various options to accommodate different organizational needs, including subscription-based and usage-based licensing. This model will allow businesses to efficiently manage costs by scaling licenses according to the number of users or virtual desktops in use. Comprehensive support and regular updates will be included, ensuring that organizations have access to the latest features and security enhancements.

![Current State Architecture](image/license.png)

# Terminology for Setting up Secure Desktop Service.


- **Tenancy Compartment Design** 

Compartment design in Oracle Cloud Infrastructure (OCI) plays a critical role in enhancing security, governance, and resource isolation for OCI Secure Desktop. By logically segregating resources into compartments, organizations can enforce fine-grained access controls, implement governance policies, and optimize resource utilization. This compartmentalization ensures better security against unauthorized access, enables effective cost tracking and compliance monitoring, and minimizes interference between different workloads, ultimately leading to a robust and reliable virtual desktop infrastructure in the cloud.

- **Connection Broker**

The Oracle Cloud Infrastructure (OCI) Secure Desktop Connection Broker is a key component of OCI Secure Desktop, facilitating the management and connectivity of virtual desktop instances for users. Acting as an intermediary, it ensures secure access to virtual desktops from various devices, optimizes resource allocation, and enhances user experience. With features like load balancing and fault tolerance, the connection broker ensures high availability and performance of virtual desktop environments, enabling efficient deployment and management in the Oracle Cloud.

- **Desktop Clients**

OCI Secure Desktop desktop clients are software applications that users install on their local devices to access virtual desktop environments hosted on Oracle Cloud Infrastructure (OCI). These clients offer enhanced performance, smoother graphics rendering, and reduced latency compared to web-based access. They also provide integration with local devices such as printers and USB devices, support offline access, and offer customization options for tailoring the virtual desktop experience. Additionally, desktop clients include security features such as encryption and certificate-based authentication to ensure secure access to virtual desktop environments. Overall, OCI Secure Desktop desktop clients provide users with a more feature-rich and integrated experience for accessing virtual desktops on OCI, offering improved performance, local device integration, customization options, and enhanced security features compared to web-based access methods.

- **IAM Policies**

IAM (Identity and Access Management) policies in Oracle Cloud Infrastructure (OCI) regulate access to resources, including Secure Desktop Service components like virtual desktop instances and networking elements. These policies enable administrators to define permissions for users and groups, ensuring appropriate access levels based on roles and responsibilities. By enforcing least privilege access, IAM policies bolster security and governance, reducing the risk of unauthorized access and data breaches within the Secure Desktop environment. Overall, IAM policies in OCI are instrumental in maintaining tight control over resource access, aligning with organizational policies and enhancing overall security posture.


- **Custom Image**

In OCI Secure Desktop, a custom image is a pre-configured template of a virtual desktop environment tailored to organizational needs. These images streamline deployment by providing standardized configurations, saving time and ensuring consistency. By including security measures and software updates, custom images enhance security and mitigate risks. They offer flexibility to create specialized desktop environments and can be modified to adapt to changing requirements. Overall, custom images are essential for efficient, secure, and customizable virtual desktop deployments in OCI Secure Desktop.

Below images are suppoted by Oracle Secure Desktop Service

>  Oracle Linux 7

>  Oracle Linux 8

> Windows 10

> Windows 11

- **Dynamic Group**

Dynamic groups in Oracle Cloud Infrastructure (OCI) are a feature that allows administrators to define groups based on matching rules, rather than manually assigning users. In the context of OCI Secure Desktop, dynamic groups can be used to automatically assign users or devices to specific roles or permissions within the Secure Desktop environment. For example, administrators can create dynamic groups based on user attributes such as department, location, or job title, and then apply IAM policies to these groups to grant access to Secure Desktop resources accordingly. This simplifies management and ensures that users have the appropriate permissions based on their attributes, streamlining access control within the Secure Desktop environment.

- **Tenant Admin Group**

In Oracle Cloud Infrastructure (OCI), the tenant admin group refers to a user group that has administrative privileges and access to manage resources within a specific tenancy. With reference to OCI Secure Desktop, the tenant admin group would typically include users responsible for overseeing and administering the Secure Desktop environment, such as configuring virtual desktop instances, managing user access, and monitoring overall performance. Members of the tenant admin group have the authority to perform administrative tasks related to Secure Desktop, ensuring effective management and governance of the virtual desktop infrastructure within the OCI environment.

- **Desktop User Group**

In Oracle Cloud Infrastructure (OCI), the tenant user group refers to a group of users who have access to resources within a specific tenancy. With reference to OCI Secure Desktop, the tenant user group would include individuals authorized to access and use virtual desktop instances hosted in the OCI environment. These users typically comprise employees or stakeholders who require access to virtual desktops for their daily work activities. The tenant user group is granted appropriate permissions and access rights to securely utilize the Secure Desktop service, enabling them to access their virtual desktop environments from any compatible device and location.

PICTURE .... SHOWING SEGREGATION 
USER REQUIREMENT 


## Secure Desktop Pre-requisites & Steps

* Access to an active OCI Tenancy

- Compartment in the tenancy where the Secure Desktop Service will be made available

- VCN against against instances will be provisioned

- Tenancy administrator who will execute the tasks

- Valid region where the Secure Desktop Service is available

- Create a Valid Image that will be used by Secure Desktop Service

- Create Endusers group on OCI that will request instances

- Secure Desktop Administrator will run the ORM stack.

- Create a Desktop Pool with the required details

- End user will login on the specified OCI portal and will request instances.

- Oracle Secure Desktop service is being offered as SAAS and is deployed at tenancy level within the OCI region.  

The details of the Oracle Cloud Infrastructure SLAs are found in the link below.
[OCI Service SLA](https://www.oracle.com/ae/cloud/sla/).


# Workload Architecture of On-prem and OCM Environement.

Below is the current high-level architecture of the customer's on-premises VMware environment and OCM in Oracle cloud Infrastructure.



### Current Virtual Desktop Inventory On-premises

========================================================================= 

__Resource allocations per location:__

| Location      | Type             | Operating System | Total vCPU Cores | Total Memory (GB) | Used Storage (GB) | Total Storage (GB) |
|:--------------|:-----------------|:-----------------|:-----------------|:------------------|:------------------|:-------------------|
| Location Name | Virtual Machines | Windows/Linux              | XXX              | XXX               | XXX               | XXX                |
| Location Name | Physical Machines | Windows/Linux              | XXX              | XXX               | XXX               | XXX                |


&nbsp;

# Work flow of Secure Desktop Service



![Future State Architecture](image/Picture1.png)

### High Level steps


R- Responsible, I- Informed, A- Accountable, C- Consulted

| Task                                           | Responsible (R) | Accountable (A) | Consulted (C) | Informed (I) |
|------------------------------------------------|------------------|------------------|----------------|---------------|
| Define project scope and objectives            | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
|Identify Image requirements            | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Analyze current infrastructure and applications| Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Select appropriate Oracle cloud services       | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Develop Desktop Pool plan            | Consultant       | Account Cloud Engineer  | Team Members   | Stakeholders |
| Allocate resources for Secure Desktop Administrator                | Account Cloud Engineer | Account Cloud Engineer | Consultant     | Stakeholders |
| Execute Desktop Pool plan                         | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Monitor Image and Desktop Pool progress                     | Account Cloud Engineer | Account Cloud Engineer | Consultant     | Stakeholders |
| Resolve Image and Desktop Pool progress issues and escalations       | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Validate successful connection for the enduser                  | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Document  process and outcomes       | Team Members     | Account Cloud Engineer | Consultant     | Stakeholders |
| Conduct review post enduser login                 | Consultant       | Account Cloud Engineer | Team Members   | Stakeholders |




Responsible (R): Individuals or roles responsible for completing the task.
Accountable (A): Individuals ultimately answerable for the task's completion or outcome.
Consulted (C): Individuals or roles to be consulted for their input or expertise.
Informed (I): Individuals or roles to be kept informed about the task's progress or outcome.





R- Responsible, I- Informed, A- Accountable, C- Consulted

The participation of the following Customer stakeholders is required for the Service to be performed:

* Enterprise Architect
* Infrastructure Architect
* Backup/Recovery team leads
* Windows/Linux Administrator
* Network Operations team leads

### Assumptions

* Secure Desktop Administrators have relevant permissions.
* The Secure Desktop end-users have been created on the OCI tenancy
* Dedicated Compartment has been setup for the Secure Desktop Pools
* Appropriate Pool settings have been applied to make the solution cost-effective
* Selected region has OCI Secure Desktop Service
* Golden Image has the required softwares installed for the end-user.
* The CIDR which will be used for Secure Desktop does not overlap with the Customer's existing environment.
* Supported Images are used for Secure Desktop.
* Required traffic is allowed from the Secure Desktop Images.
* Required storage is mapped with the Secure Desktop instances.
* There are no licensing constraints from Microsoft or any other software vendors. 
* The Secure Desktop instances have sufficient CPU cores and RAM to address application requirement.
* Customer has flexibility to edit VPU for the Block Volume.
* Customer will have the necessary Oracle Support (MoS) contract for all the products that may/will be used during this project.
* Customer will be managing any other 3rd party vendors or suppliers.
* Customer will have adequate licenses for all the products that may/will be used during this project.
* It is assumed that all work will be done remotely and within either central European time or Indian standard time normal office working hours.
* Any problems, issues, errors, and anomalies to be addressed through MOS SRs & will continue to be owned by the Customer.
* Details and Naming convention will be provided for OCI resources.
* Any additional effort outside of the scope of this proposal will be managed by change control and mutually agreed upon by both Oracle and Customer.

## Windows Licensing 

Oracle Secure Desktop (OCM) supports Bring Your Own License (BYOL) for Windows virtual machines, it's likely that the support may vary depending on the specific version of Windows being migrated and the licensing agreements in place. OCI Windows Server Images can be used with OCI Secure Desktop as custom images however charges will be applicable. 

For certain versions of Windows, customers may be able to migrate to dedicated virtual machine hosts on Oracle Cloud Infrastructure (OCI) to enable BYOL. Dedicated VM hosts provide physical servers dedicated to a single customer's use, offering enhanced control and security.

Customers should review their licensing agreements and consult with Oracle support or their Oracle account representative to determine the specific options available for migrating Windows virtual machines to OCI with BYOL. Additionally, they should ensure compliance with licensing requirements to avoid any potential issues.

&nbsp;

**Note:** 

For more information regarding the Secure Desktop Service, please refer to [Official Documentation.](https://docs.oracle.com/en-us/iaas/secure-desktops/home.htm)



#### Acknowledgments

•	Author - Vaibhav Tiwari (Cloud VMware Solutions Specialist)