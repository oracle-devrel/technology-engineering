# Benefits of the Solution Definition Document for You

## What is a Solution Definition Document?

The Solution Definition Document (SDD) is a high-level technical architecture document focusing on the Oracle Cloud Infrastructure (OCI) architecture for a solution. Low-level design details are created later in the delivery phase of the project by the delivery team typically the Oracle partner.

The SDD is created by Oracle's pre-sales teams as an investment by Oracle for our customers and partners. The SDD should provide just enough architecture to ensure a successful handover of Oracle's best practices to the implementer. 

It has four main sections:

- Context of the solution at hand 
- As-Is on-premises architecture (Optional)
- Logical and physical to-be architecture
- Bill of materials 

## Where Can I Find SDD Templates and Related Resources?

The base templates can be found in the sub-folders of this repository. There are two versions, [Mandatory](./solution-definition-mandatory/) and [Complete](./solution-definition-complete/). The mandatory version contains fewer chapters than the complete version. 

In addition, we provide a range of predefined templates for various different use cases and applications.

- [Oracle Digital Assistant](../../ai/oracle-digital-assistant/solution-definition/)
- [Application Integration (Simple)](../../app-dev/app-integration-and-automation/shared-assets/starter-packs/application-integration-simple/)
- [Application Integration (Complex)](../../app-dev/app-integration-and-automation/shared-assets/starter-packs/application-integration-complex/)
- [Application Integration (Oracle ERP)](../../app-dev/app-integration-and-automation/shared-assets/starter-packs/application-integration-oracle-erp/)
- [ArcGIS](../../cloud-architecture/3rd-party-and-isv-applications/arcgis/arcgis-solution-description/)
- [Microsoft Dynamics365 CRM](../../cloud-architecture/3rd-party-and-isv-applications/d365crm/dynamics-365-solution-description/)
- [MSSQL](../../cloud-architecture/3rd-party-and-isv-applications/mssql/mssql-solution-description/)
- [Outsystems](../../cloud-architecture/3rd-party-and-isv-applications/outsystems/outsystems-solution-description/)
- [MS SQL Server Resources Solution Description](../../cloud-architecture/custom-apps-and-consolidation/3rd-party-databases/ms-sql-always-on-solution-description/)
- [Database Migration Solution Description](../../cloud-architecture/custom-apps-and-consolidation/db-migration/solution-description/)
- [Oracle Database Consolidation to ExaDB-CC Workload Solution Definition](../../cloud-architecture/custom-apps-and-consolidation/oracle-db-consolidation/solution-definition-exadb-cc/)
- [WebLogic For OKE](../../cloud-architecture/custom-apps-and-consolidation/weblogic/weblogic-for-oke/)
- [E-Business Suite](../../cloud-architecture/oracle-apps-erp/e-business-suite/ebs-starterpack/)
- [JD Edwards](../../cloud-architecture/oracle-apps-erp/jd-edwards/jde-starterpack/)
- [PeopleSoft](../../cloud-architecture/oracle-apps-erp/peoplesoft/psft-starterpack/)
- [Primavera](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/gbu/construction-engineering/primavera-solution-definition/)
- [Flexcube](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/gbu/financial-services/flexcube-solution-definition/)
- [Opera](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/gbu/hospitality/opera-solution-definition/)
- [Retail Applications](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/gbu/retail/retail-solution-definition/)
- [Essbase](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/hyperion-essbase/essbase-solution-definition/)
- [Hyperion](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/hyperion-essbase/hyperion-solution-definition/)
- [Siebel](../../cloud-architecture/oracle-apps-hyperion-siebel-gbu/siebel/siebel-solution-definition/)
- [Red Hat OpenShift](../../cloud-infrastructure/virtualization-solutions/openshift-on-oci/openshift-solution-definition-document/)
- [Oracle Cloud Migrations / VMware](../../cloud-infrastructure/virtualization-solutions/oracle-cloud-migrations/ocm-solution-definition-document/)
- [Oracle Cloud VMware Solution - Disaster Recovery](../../cloud-infrastructure/virtualization-solutions/oracle-cloud-vmware-solution/disaster-recovery-to-ocvs-solution-definition/)
- [Oracle Cloud VMware Solution](../../cloud-infrastructure/virtualization-solutions/oracle-cloud-vmware-solution/vmware-migration-solution-definition/)
- [Oracle Secure Desktops](../../cloud-infrastructure/virtualization-solutions/oracle-secure-desktops/secure-desktops-solution-definition/)
- [Cloud Analytics with OAC standalone](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/cloud-analytics-with-oac-standalone/)
- [Oracle DWH Analytics for IT](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/data-warehouse-analytics-for-IT/)
- [Oracle DWH Analytics for LoB](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/dwh-analytics-for-lob/)
- [In-database Machine Learning](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/in-database-machine-learning/)
- [Oracle BI Applications with Informatica Powercenter migration to Oracle OCI with Informatica IDMC, OAC and ADW](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/obia-with-informatica-to-oci-with-idmc/)
- [Oracle BI Applications 11g with ODI migration to Oracle OCI with ODI, OAC and Oracle DB](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/obia-with-odi-migration-to-oci/)
- [Oracle Database and OBIEE migration to Autonomous Data Warehouse and Oracle Analytics Cloud](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/obiee-db-migration-to-oac-adw/)
- [Lakehouse for HR](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/serverless-lakehouse/)
- [Stand-alone Data Science](../../data-platform/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/stand-alone-oci-data-science/)


Other related useful external portals are the OCI Documentation with our [Cloud Adoption Framework](https://www.oracle.com/uk/cloud/cloud-adoption-framework/), as well as the [Architecture Center](https://docs.oracle.com/solutions/?q=&cType=reference-architectures%2Csolution-playbook%2Cbuilt-deployed&sort=date-desc&lang=en) which outlines best reference architectures and practices, and includes the [Well-Architected Framework for OCI](https://docs.oracle.com/en/solutions/oci-best-practices/index.html). 

[The OCI Architecture Diagram Toolkit](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm) is another useful resource when creating architecture diagrams.

## What are the Benefits of Adopting an SDD for Our Customers and Partners?

**1. Improved Quality and Satisfaction:**

A standardized SDD ensures that the solution meets your specific needs and requirements. This leads to a higher quality product or service that is more likely to meet your expectations.

**2. Improved Communication and Alignment:**

A standardized SDD ensures that all stakeholders involved in a project (you, Oracle partners, IT teams, and vendors) are using the same language and understanding of the solution. This reduces ambiguity and misinterpretations, leading to better alignment between expectations and outcomes.

The document acts as a central repository of information, making it easier for everyone to stay informed about the solution definition progress and any changes during the solutioning phase of the project. Version control is important to record changes and evolution of solution definition.

**3. Reduced Risk and Costs:**

By providing a comprehensive overview of the solution definition, the SDD helps to identify potential problems or challenges before they become major issues. This allows for proactive risk mitigation and can help to avoid costly rework or delays later in the project lifecycle.

A well-defined SDD can also help to reduce the overall cost of the project by ensuring that the solution is designed and implemented efficiently leveraging Oracle's best practices and standards.

**4. Enhanced Project Management:**

A standardized SDD provides a clear roadmap for the project, outlining the initial scope, objectives, timelines, and deliverables. This helps IT teams manage the project effectively, track progress, and identify potential risks or issues early on. The document can also serve as a basis for creating project plans, resource allocation, and budget estimations.

**5. Increased Efficiency and Productivity:**

The use of a standardized SDD can streamline the design and development process, leading to increased efficiency and productivity for you, your IT teams, and Oracle partners. 

The document can also be reused for future similar project architectures, saving time and effort. The SDD also helps with the handover of resources coming in and out of the project.

**Summary:**

The adoption of a standardized SDD offers numerous benefits for you, including improved communication, enhanced project management, reduced risk and costs, improved quality and satisfaction, and increased efficiency and productivity helping reduce project delivery timelines. By ensuring that all stakeholders are on the same page and that the project is well-defined and managed, the SDD can help to ensure that IT projects are successful and deliver the desired outcomes.

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.