# Start Right With OCI

A five-step approach to deploy on Oracle Cloud Infrastructure (OCI)

- [Start Right With OCI](#start-right-with-oci)
  - [Introduction](#introduction)
  - [Establishing Your OCI Environment](#establishing-your-oci-environment)
    - [Step 1: Identity and Access Management (IAM)](#step-1-identity-and-access-management-iam)
    - [Step 2: Deploying a Landing Zone](#step-2-deploying-a-landing-zone)
    - [Step 3: Deploying a solution](#step-3-deploying-a-solution)
    - [Step 4: Observability: Logging, Monitoring and Alerting](#step-4-observability-logging-monitoring-and-alerting)
    - [Step 5: Resource Management and Governance](#step-5-resource-management-and-governance)
- [License](#license)

Last updated: 7 March 2025

## Introduction

This document serves as a guide for first-time OCI users. It outlines foundational security best practices from establishing secure landing zones and a well‑architected environment to enabling observability, managing identity and access, and enforcing robust security measures. The guidance below is aligned with the [CIS OCI Foundations Benchmark](https://www.cisecurity.org/benchmark/oracle_cloud) and Oracle’s [OCI Well-Architected Framework](https://docs.oracle.com/en/solutions/oci-best-practices/index.html). It includes curated resources, GitHub repositories, and additional reference links to help you get started.  

After reading the introduction, follow the steps outlined in **Establishing Your OCI Environment** to set up a secure and well-architected OCI deployment. These steps provide a structured approach to configuring identity and access management, setting up a landing zone, deploying solutions in OCI, and enabling logging and monitoring.  

Each step in the **Establishing Your OCI Environment** section contains links to essential OCI documentation. If you encounter any difficulties whilst following the documentation, additional video resources are available. This guide includes links to instructional videos that offer step-by-step explanations of key OCI concepts. Reviewing these videos can help clarify complex topics and provide practical demonstrations of best practices.  

To ensure a further **structured and successful** cloud adoption journey, Oracle provides two key frameworks:  

- The **[Cloud Adoption Framework for OCI (CAF)](https://www.oracle.com/cloud/cloud-adoption-framework/)** helps organizations transition to OCI by providing best practices for governance, security, operations, and financial management. It ensures that cloud strategies align with business goals and regulatory requirements.  
- The **[OCI Well-Architected Framework (WAF)](https://docs.oracle.com/en/solutions/oci-best-practices/index.html)** focuses on the **technical implementation** of cloud workloads, ensuring they are secure, reliable, and optimized for performance and cost.  

These frameworks work together with the **CAF** establishing the foundation and governance model, and the **WAF** ensuring workloads are designed according to best practices. By following both, organizations can create a cloud environment that is scalable, secure, and operationally efficient.  

The entry point for all Oracle Cloud Infrastructure Services is the official [Oracle OCI Documentation](https://docs.oracle.com/en-us/iaas/Content/home.htm).
For an overview of the OCI security services you can review this [Security in OCI](https://videohub.oracle.com/media/Kick+off+your+Oracle+Cloud+Journey+-+Part+3/1_om5n1tll) video. You can also review other topics using this [video dashboard](https://www.oracle.com/uk/cloud/architecture-center/oci-in-5/).

## Establishing Your OCI Environment  

Setting up your Oracle Cloud Infrastructure (OCI) environment correctly from the start is essential for security, governance, and operational efficiency. This section provides a structured approach to configuring your tenancy, ensuring that all foundational components are implemented according to best practices.  

The steps outlined here will guide you through:  

- **Step 1: Identity and Access Management (IAM):** Implementing strong security controls to protect administrative access.  
- **Step 2: Landing Zone Deployment:** Establishing a secure and scalable foundation for OCI workloads.  
- **Step 3: Solution Deployment:** Using automation tools like Terraform and OCI Resource Manager to streamline application deployment.  
- **Step 4: Observability and Monitoring:** Setting up logging, monitoring, and alerting to maintain visibility over cloud resources and their usage. 
- **Step 5: Resource Management and Governance:** Applying governance frameworks to maintain compliance, track costs, and enforce policies.  

Each step in this guide includes links to **essential OCI documentation and video tutorials** to help you successfully configure your environment. If you encounter any challenges, refer to these resources for step-by-step guidance.  

### Step 1: Identity and Access Management (IAM)

Securing OCI Administrators in the Default identity domain is crucial because these accounts have full control over your tenancy and are prime targets for attacks. Enforcing strong Multi Factor Authentication (MFA), least privilege access, and continuous monitoring for all administrative users within OCI from the start helps prevent unauthorized access and strengthens your cloud security posture. 

Secure access to your OCI resources by implementing strict IAM controls:


- **Set up an identity and access management (IAM) security model:** An initial version of a security model can help your organization [mitigate risk](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/iam-security-structure.htm)
- **Principle of Least Privilege:** Grant only the necessary permissions and regularly audit your [IAM policies](https://www.ateam-oracle.com/post/oci-iam-policies-best-practices).
- **Breakglass Administrator:** Do not use the out-of-the-box OCI Adminstrator account for day-to-day operations. Configure additional administrators based on least privileges and secure the OCI Administrator account as a breakglass account, reserved for emergency use only, as defined in the [OCI IAM Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security.htm#Securing_IAM).
- **Multi‑Factor Authentication (MFA):** Enable MFA for all users to protect against unauthorized access. Additional best practices are detailed in the [OCI IAM Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security.htm#Securing_IAM).
- **Federation:** Configure federated identity management (e.g., using [MS EntraID](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/federation.htm)) to streamline user access.
- **Additional Resources:** [Identity and Access Management Resources](https://github.com/oracle-quickstart/oci-self-service-security-guide/tree/main/3-Identity-and-Access-Management).

### Step 2: Deploying a Landing Zone

After securing your Default OCI IAM accounts, define a secure and scalable landing zone. An [OCI Landing Zone](https://github.com/oci-landing-zones/) is a pre-configured, secure, and scalable cloud environment that provides a standardized foundation for deploying workloads in Oracle Cloud Infrastructure. It is needed to ensure that best practices for security, governance, and compliance are implemented from the start, reducing misconfigurations and accelerating cloud adoption:

- **Secure Onboarding:** Leverage resources to rapidly deploy a secure environment, including:
  - [Core Landing Zone](https://github.com/oci-landing-zones/terraform-oci-core-landingzone), which contains blueprints ready for various workloads and is suitable for centralized operations within your organization.
  - [Operating Entities Landing Zone](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities), which contains blueprints to onboard your organizations and partners and their workloads with distributed operations.
- **Compartmentalization:** [Organize resources into compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm#Working) to enforce governance, simplify billing, and separate workloads.

### Step 3: Deploying a solution 

Once your OCI environment is set up, you can deploy your first workload by leveraging Oracle’s infrastructure and automation tools. OCI provides multiple deployment options, including Terraform, Resource Manager, and manual provisioning via the OCI Console, CLI, SDK, or API.

- **Using Terraform:** Automate deployments with Terraform by using the official [Oracle OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs). This provider includes modules for networking, compute, databases, security, and other OCI resources.
- **Resource Manager:** Use OCI [Resource Manager](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Concepts/resourcemanager.htm) to run Terraform templates directly within the OCI Console, simplifying deployment and lifecycle management.
- **Marketplace Solutions:** Explore pre-configured applications and solutions available in the [OCI Marketplace](https://cloudmarketplace.oracle.com/marketplace/en_US/homePage.jspx) to accelerate deployment.
- **Manual Deployment:** If needed, you can manually provision resources through the [OCI Console](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/launchinginstance.htm) or automate tasks with the [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm), including [Bring Your Own Image](https://docs.oracle.com/en-us/iaas/Content/Compute/References/bringyourownimage.htm).

For detailed guidance on deploying specific workloads, refer to Oracle's [Reference Architectures](https://www.oracle.com/cloud/architecture-center/) and [Solution Playbooks](https://docs.oracle.com/solutions/).

### Step 4: Observability: Logging, Monitoring and Alerting

Establishing robust observability is key to maintaining the health of your environment. Follow these best practices:

- **SIEM Integration Pattern:** A SIEM platform is required to increase responsiveness to [security attacks](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/siem-integration.htm)
- **Enable Logging and Monitoring:** Utilize OCI’s logging and monitoring services to track your resources and applications. Setting up alerts for operational insights is crucial for maintaining system health. Refer to [OCI Best Practices](https://docs.oracle.com/en/solutions/oci-best-practices/index.html) for strategies.
- **Data Visualization Tools:** Leverage OCI Monitoring and OCI Logging to visualize data in [dashboards and track performance metrics](https://docs.oracle.com/en-us/iaas/Content/Dashboards/Tasks/dashboards.htm). A number of [security dashboards](https://blogs.oracle.com/observability/post/oracle-cloud-infrastructure-security-fundamentals-dashboards-using-oci-logging-analytics) have been published to help you gain rapid visibility into your operational security metrics.
- **Integrate with Third-Party Tools:** Integrate OCI with a [third-party SIEM](https://docs.oracle.com/solutions/?q=SIEM&cType=reference-architectures%2Csolution-playbook%2Cbuilt-deployed&sort=date-desc&lang=en) (if you are using one) to enhance your monitoring capabilities, as suggested in the OCI Architecture Center.
- **Additional Resources**: [Observability and Monitoring Resources](https://github.com/oracle-quickstart/oci-self-service-security-guide/tree/main/1-Logging-Monitoring-and-Alerting#logging-monitoring-and-alerting).

### Step 5: Resource Management and Governance

Effective resource management is crucial to maintain control over your OCI environment:

- **Tagging:** Apply [tags](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm) to all resources for better organization, cost tracking, and compliance.
- **Cost Management:** Enable [budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/managingbudgets.htm) and [alerts](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/managingalertrules.htm) to monitor cloud spending and proactively address cost anomalies.
- **Governance:** Use [cloud governance practices](https://docs.oracle.com/en/solutions/foundational-oci-governance-model/index.html) to enforce policies and maintain regulatory compliance.

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

