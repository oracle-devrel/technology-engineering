# TAILORED LANDING ZONES

&nbsp; 

<img src="../images/lzf_tailored.png" alt= “” width="400" height="value">

&nbsp; 

## 1. What are Tailored Landing Zones 

A tailored landing zone is a solution to fit specific requirements - normally applicable when the [standard landing zones](/standard_landing_zones/standard_landing_zones.md) are not enough. This approach can involve the design of these OCI views:
- **Security View**: covering the seggregation of duties, with Tenancy Structure, IAM, and Posture Management.
- **Network View**: covering the Network Structure, Network Isolation, Connectivity, Most-Significant Traffic Scenarios, and DNS.
- Optionally, the **Operations View** can include the cloud operating model, monitoring, and possible ITSM integrations. This view highly depends on the existing IT systems context and day-two running objectives.

&nbsp; 

The tailored approach is normally used in these cases, but not limited to:
- **Mirroring**: create an OCI design similar to existing landing zones** on other CSPs.
- **Organization-wide**: Onboarding and reflecting your organization structure & business units.
- **Security**: Fine-grained segregation of duties and responsibilities across resources and teams.
- **Network**: Highly tuned network design, strong isolation and network security posture.
- **Workloads**: Heterogeneous and/or large workloads landscape.
- **Operations**: Adopting a highly scalable operating model, such as control versioned operations.


&nbsp; 


## 2. What Are The Assets Available

## 2.1 Landing Zone Blueprint
To tailor your landing zone we recommend using the **[OCI Open LZ Blueprint](https://github.com/oracle-quickstart/terraform-oci-open-lz)**, which is itself a reference solution design process. It presents an end-to-end coherent solution - with the **security, network, and operations views** - of what an organization-wide landing zone looks like, with fine-grained segregation of duties, strong isolation of resources, and a scaleable operating model.

The blueprint is a solution that can be completely adjusted and easily simplified into any other type of landing zone, by following the design steps as best-practices.  Using this reference blueprint will help you create a day-two operational model ready to scale - using the **configurable IaC solution** presented in the next section.


&nbsp; 

## 2.2 Configurable Infrastructure as Code
For this type of approach **we recommend the use of the CIS LZ v3 Terraform modules**, to configure your resources with json/hcl terraform native interfaces. The outcome of using this approach is that you will: 
- **Focus on Value**: Focus on configuring your design and resources, instead of coding it. This means shorter time-to-value, lower effort, and lower risk.
- **Best Practices**: Use existing top-quality terraform modules that are open and full of best practices. You can leverage this to evolve your OCI terraform skills and apply future IaC best practices. This also means lower risk and lower efforts.
- **Scale Day Two**: You will be able to split operational configurations from code, which will simplify drastically your day-two operations, opening the path for a GitOps operating model and potentially simpler automation. Your cloud operators will only work with configurations, not code.

&nbsp; 

The CIS LZ v3 Terraform modules are distributed into five repositories, as described in the table below. 

&nbsp; 

| MODULES  |  OCI RESOURCES COVERED | DESIGN VIEW MATCH |  USE|
|---|---|---|---|
| [IAM](https://github.com/oracle-quickstart/terraform-oci-cis-landing-zone-iam) | Compartments, Groups, Policies, Dynamic Groups | Security View (Tenancy Structure, IAM) | Mandatory |
| [Network](https://github.com/oracle-quickstart/terraform-oci-cis-landing-zone-networking) | VCNs, Subnets, DGR, Gateways, Load Balancers, etc. | Network View | Mandatory |
| [Security](https://github.com/oracle-quickstart/terraform-oci-cis-landing-zone-security) | Cloud guard, Security Zones, Vaults, VSS | Security View (Posture) | Optional |
| [Observability](https://github.com/oracle-quickstart/terraform-oci-cis-landing-zone-observability) | Alarms, Events, Notifications, Service Connectors, Streams | Operations View | Optional |
| [Governance](https://github.com/oracle-quickstart/terraform-oci-cis-landing-zone-governance) | Tags | Operations View | Optional |

&nbsp; 






&nbsp; 

## 3. How Do You Start 
   

&nbsp; 


| STEP  |   DESCRIPTION | GUIDANCE  |  
|:---:|---|---|
| 1 | **Understand OCI core resources**, such as compartments, groups, policies, and network elements. They are the foundations of any OCI landing zone. | [OCI Foundations](https://mylearn.oracle.com/learning-path/become-an-oci-foundations-associate/108448)<br> [OCI Architect Associate](https://mylearn.oracle.com/learning-path/become-an-oci-architect-associate/108703) <br>[OCI Architect Professional](https://mylearn.oracle.com/learning-path/become-an-oci-architect-professional/108709) |
| 2| **Identify your requirements** in terms of workloads, security, network, and operations. | N/A |
| 3 | **Review an example of a tailored landing zone**: With the **OCI Open LZ Blueprint**, you can review coherent end-to-end landing zone design and considerations for each decision. The **OCI Open LZ** is a reference design to show you what it looks like, and it's not prescriptive. It contains several useful resources and recordings to help you on the next steps. | [OCI Open LZ Blueprint](https://github.com/oracle-quickstart/terraform-oci-open-lz) |
| 4 | **Design the Security View first**, with focus on the tenancy structure and IAM, as all resources and access to them will be defined here. | [OCI Open LZ Security View](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/docs/OCI_Open_LZ.pdf)<br> [OCI Open LZ Draw.io](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/docs/OCI_Open_LZ.drawio)
| 5 | **Design the Network View**, with focus on the network structure, connectivity, and network isolation. | [OCI Open LZ Network View](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/docs/OCI_Open_LZ.pdf)<br> [OCI Open LZ Draw.io](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/docs/OCI_Open_LZ.drawio)
| 6 | If applicable, **design the Operations View**, and set up your cloud operating model, with monitoring, and integrating with your IT Systems. | [OCI Open LZ Operations View](https://github.com/oracle-quickstart/terraform-oci-open-lz/blob/master/docs/OCI_Open_LZ.pdf) 

&nbsp; 

## 4. Other Considerations
   
Note that the **alternative for not using the modules on section 2.1 is to code your own solution**, from scratch or reusing existing modules. From experience, we strongly recommend not following this path as it provides little value and high effort. These modules allow any configuration and allow you to focus on your business resources (workloads) instead of investing time coding to create OCI core resources. In summary, complex customizations with a standard landing zone might imply the following:
- **Time-consuming**. Changing or adapting code to create a new landing zone different than the original is complex and time-consuming. This also means that any change to the landing zone will be executed by code and not configurations.
- **Waste & Late Time-to-Value**. The time spent on adapting code, or recoding over and over for the landing/core resources (compartments, groups, policies, network) is time wasted on the workloads, which means late time-to-value.
- **Skills Limitations**. IaC Terraform coding skills are not as common as we should expect, which makes these efforts a high challenge to solve. 
- **Limited Scaling**. Doing the changes manually works for some tactical solutions, but it will always limit the scaling and day-two operations. Note that, for example, CIS LZ creates 100+ OCI resources.

For a comparison between **standard landing zone** solutions and the proposed solution for **tailored landing zones** please review the [OCI landing zone solution landcscape](/commons/select_your_solution.pdf).

&nbsp; 


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-ngineering/blob/folder-structure/LICENSE) for more details.