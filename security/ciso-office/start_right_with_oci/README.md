# Start Right With OCI

Last updated: 20 May 2025

## A Five-Step Approach to Deploying on Oracle Cloud Infrastructure (OCI)

Properly setting up your Oracle Cloud Infrastructure (OCI) environment from the beginning is crucial for ensuring security, governance, and operational efficiency. This page outlines a clear, step-by-step method for configuring your tenancy, helping you implement all foundational components in line with best practices.

The steps outlined here will guide you: 

- **Step 1: Identity and Access Management (IAM):** Implementing strong security controls to protect administrative access.  
- **Step 2: Resource Management and Governance:** Applying governance frameworks to maintain compliance, track costs, and enforce policies.  
- **Step 3: Create Your Landing Zone:** Establishing a secure and scalable foundation for OCI workloads.  
- **Step 4: Setup Your Observability:** Setting up logging, monitoring, and alerting to maintain visibility over cloud resources and their usage. 
- **Step 5: Provision Your Workloads :** Using Landing Zone Workload Extensions and Market Place solutions to streamline application deployment.  

Each step in this guide includes links to **essential OCI documentation and video tutorials** to help you successfully configure your environment. If you encounter any challenges, refer to these resources for step-by-step guidance.  

&nbsp;

## Step 1: Identity and Access Management (IAM)

Securing OCI Administrators in the Default identity domain is crucial because these accounts have full control over your tenancy and are prime targets for attacks. Enforcing strong Multi Factor Authentication (MFA), least privilege access, and continuous monitoring for all administrative users within OCI from the start helps prevent unauthorized access and strengthens your cloud security posture. 

Secure access to your OCI resources by implementing strict IAM controls:

- **Set up an identity and access management (IAM) security model:** An initial version of a security model can help your organization to [mitigate risk](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/overview.htm#Example)
- **Principle of Least Privilege:** Grant only the necessary permissions and regularly audit your [IAM policies](https://www.ateam-oracle.com/post/oci-iam-policies-best-practices).
- **Breakglass Administrator:** Do not use the out-of-the-box OCI Adminstrator account for day-to-day operations. Configure additional administrators based on least privileges and secure the OCI Administrator account as a breakglass account, reserved for emergency use only, as defined in the [OCI IAM Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security.htm#Securing_IAM).
- **Multi‑Factor Authentication (MFA):** Enable MFA for all users to protect against unauthorized access. Additional best practices are detailed in the [OCI IAM Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security.htm#Securing_IAM).
- **Federation:** Configure federated identity management (e.g., using [Microsoft Entra ID](https://docs.oracle.com/en-us/iaas/Content/Identity/tutorials/azure_ad/sso_azure/azure_sso.htm) or [Okta](https://docs.oracle.com/en/learn/integrating-identity-domains-with-okta/index.html#introduction)) to streamline user access.
- **Life Cycle Management (LCM):** Configure [LCM between Microsoft Entra ID and OCI IAM Identity Domain](https://docs.oracle.com/en-us/iaas/Content/Identity/tutorials/azure_ad/lifecycle_azure/01-config-azure-template.htm) or [Okta](https://docs.oracle.com/en-us/iaas/Content/Identity/tutorials/okta/lifecycle_okta/okta-lifecycle.htm)
- **Additional Resources:** [Identity and Access Management Resources](https://github.com/oracle-quickstart/oci-self-service-security-guide/tree/main/3-Identity-and-Access-Management).

&nbsp;

## Step 2: Resource Management and Governance

Effective resource management is crucial to maintain control over your OCI environment:

- **Naming Convention:** A [resource naming convention](https://github.com/oracle-devrel/technology-engineering/blob/main/landing-zones/commons/resource_naming_conventions.md) helps to identify resources, their type, and location by the name, quickly.
- **Tagging:** Apply [tags](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm) to all resources for better organization, cost tracking, and compliance.
- **Cost Management:** Enable [budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/managingbudgets.htm) and [alerts](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/managingalertrules.htm) to monitor cloud spending and proactively address cost anomalies.
- **Governance:** Use [cloud governance practices](https://docs.oracle.com/en/solutions/foundational-oci-governance-model/index.html) to enforce policies and maintain regulatory compliance.
- **Compartmentalization:** [Organize resources into compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm#Working) to enforce governance, simplify billing, and separate workloads.

&nbsp;

## Step 3: Create Your Landing Zone

After securing your Default OCI IAM accounts, define a secure and scalable landing zone. An [OCI Landing Zone](https://github.com/oci-landing-zones/) is a pre-configured, secure, and scalable cloud environment that provides a standardized foundation for deploying workloads in Oracle Cloud Infrastructure. It is needed to ensure that best practices for security, governance, and compliance are implemented from the start, reducing misconfigurations and accelerating cloud adoption:

- **Core Landing Zone:** Blueprints ready for various workloads and suitable for centralized operations [within your organization](https://github.com/oci-landing-zones/terraform-oci-core-landingzone)
- **Operating Entities Landing Zone:** Blueprints to onboard your organizations and partners and their workloads [with distributed operations](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities) 

&nbsp;

## Step 4: Setup Your Observability

Establishing robust observability is key to maintaining the health of your environment. Follow these best practices:

- **SIEM Integration Pattern:** A SIEM platform is required to increase responsiveness to [security attacks](https://www.ateam-oracle.com/post/integrating-siem-with-oracle-cloud-applications)
- **Enable Logging and Monitoring:** Utilize OCI’s logging and monitoring services to track your resources and applications. Setting up alerts for operational insights is crucial for maintaining system health. Refer to [OCI Best Practices](https://docs.oracle.com/en/solutions/oci-best-practices/index.html) for strategies.
- **Data Visualization Tools:** Leverage OCI Monitoring and OCI Logging to visualize data in [dashboards and track performance metrics](https://docs.oracle.com/en-us/iaas/Content/Dashboards/Tasks/dashboards.htm). A number of [security dashboards](https://blogs.oracle.com/observability/post/oracle-cloud-infrastructure-security-fundamentals-dashboards-using-oci-logging-analytics) have been published to help you gain rapid visibility into your operational security metrics.
- **Integrate with Third-Party Tools:** Integrate OCI with a [third-party SIEM](https://docs.oracle.com/solutions/?q=SIEM&cType=reference-architectures%2Csolution-playbook%2Cbuilt-deployed&sort=date-desc&lang=en) (if you are using one) to enhance your monitoring capabilities, as suggested in the OCI Architecture Center.
- **Additional Resources**: [Observability and Monitoring Resources](https://github.com/oracle-quickstart/oci-self-service-security-guide/tree/main/1-Logging-Monitoring-and-Alerting)

&nbsp;

## Step 5: Provision Your Workloads 

Once your OCI environment is set up, you can deploy your first workload by leveraging Oracle’s infrastructure and automation tools. OCI provides multiple deployment options, including 
Terraform, Resource Manager, and manual provisioning via the OCI Console, CLI, SDK, or API.

- **Landing Zone Workload Extensions:** A workload extension is a tangible and self-contained set of resources with a clear functional scope, pluggable to a Landing Zone. They have a design and an implementation ready to receive a specific workloads on top of a landing zone. Each of these extensions follows the [tailored landing zone approach and is ready for deployment](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities/tree/master/workload-extensions)
- **Marketplace Solutions:** Explore pre-configured applications and solutions available in the [OCI Marketplace](https://cloudmarketplace.oracle.com/marketplace/en_US/homePage.jspx) to accelerate deployment.
- **Bring Your Own Image (BYOI):** If needed, you can manually provision resources through the [OCI Console](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/launchinginstance.htm) or automate tasks with the [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm), including [Bring Your Own Image](https://docs.oracle.com/en-us/iaas/Content/Compute/References/bringyourownimage.htm)
- **Assess OCI security posture against best practises outlined in the CIS Oracle Cloud Infrastructure Foundations Benchmark:** Available are the [OCI Security Health Check - Standard Edition](https://github.com/oracle-devrel/technology-engineering/tree/main/security/security-design/shared-assets/oci-security-health-check-standard) and the OCI Security Health Check - Advanced Edition. The OCI Security Health Check - Advanced Edition can be requested by raising a service request.  

&nbsp;

For detailed guidance on deploying specific workloads, refer to Oracle's [Reference Architectures](https://www.oracle.com/cloud/architecture-center/) and [Solution Playbooks](https://docs.oracle.com/solutions/).

&nbsp;

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.