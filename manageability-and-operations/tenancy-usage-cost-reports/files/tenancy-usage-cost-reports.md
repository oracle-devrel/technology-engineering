# Introduction

Usage2ADW is a tool which uses the Python SDK to extract the usage and cost reports from OCI tenancy and load it to Oracle Autonomous Database. It is an extension to OCI's native Billing & Cost management capabilities, to provide customers with granular understanding of their spend and utilization of OCI. Using ADW and OAC features, this solution can provide high-level overview, in-depth spend analysis, trends in resource utilization and forecast as well.
OCI automatically generates usage data and is stored in an Oracle owned Object Storage bucket. It contains one row per each OCI resource per hour along with consumption information, metadata, namespace and tags. Usage2ADW load this data to ADW database and OAC visualizations can be created on top of this database.

## Required technical skills

- Python scripting.
- Oracle SQL.
- Oracle Analytics Cloud (OAC).
- Application Express (Apex).

## OCI APIs Used

- IdentityClient.list_compartments - Policy COMPARTMENT_INSPECT
- IdentityClient.get_tenancy - Policy TENANCY_INSPECT
- ObjectStorageClient.list_objects - Policy OBJECT_INSPECT
- ObjectStorageClient.get_object - Policy OBJECT_READ

## SDK Modules Used

- oci.identity.IdentityClient
- oci.object_storage.ObjectStorageClient

## OCI Resources Used

- Compute VM: The compute VM houses install script to create the required data structures and installs the package and Apex application. All data integrations to retrieve OCI information and load into ADW tables are run on the compute VM.
  
- Oracle Analytics Cloud: OAC instance will contain Dashboards and Visualization of the cost and usage reports.
  
- Autonomous Data Warehouse: ADW instance will be used to store and process the cost and usage data and effectively support a data mart that will provide usage and cost visibility of the tenancy and different dimensions like tenancy, region, project, environments.
  
- ADW Private Endpoint: PE is used in order that ADW to be deployed on a private subnet and hence be only accessible from private connection and not from internet.
  
- AC Private Access Channel: PAC provides the connectivity to private database from Oracle Analytics Cloud. It will enable a private endpoint in a private subnet of the Virtual Cloud Network (VCN) of OCI that will let OAC query the private ADW using the private endpoint of ADW.

## Main features:

- Load Usage Report to ADW.
- Load Cost Reports to ADW.
- Load Public Rates to ADW.
- Report Usage Current State.
- Report Usage Over Time.
- Report Cost Analysis.
- Report Cost Over Time.
- Report Rate Card for Used Products.

# Business Value

 With Usage2ADW, the customer will enjoy the benefits of an analytics platform with dashboards and data visualizations that provide cost by OCI Resources, PaaS and IaaS services and can be grouped by regions, compartments, etc. for budgetary purpose and chargeback. The analysis can be personalized by application, department, based on custom tags. Additionally, performance monitoring and utilization metrics will be available for applications running on OCI compute instances.

## Use case

When the extension Usage2ADW is implemented, the user through a dashboard will be able to visualize usage and cost reports over the dimension values. The Tag Namespace and Keys can be used to classify and group resources for Usage and Costing visibility.
The Usage and Cost Reports provides customers granular understanding of their spend and utilization of OCI. This solution provides in-depth spend analysis on OCI. It includes high-level overview for executives, resource and cost trends for line of business application owners, trends in resource utilization and more. Usage2ADW is ideal for self-service analysis and allows users to build their own visualizations and enrich the analysis by bringing in their own data like departmental budgets. Customers can leverage a management module to securely retrieve their tenancy cost and usage data. The module can also be configured to retrieve multiple OCI tenancies data for analysis. This solution extends the core Usage2ADW solution with an integration to retrieve usage and cost metrics from other sources, in particular from OEM for the customer on-prem database estate.

The implemented solution satisfies a broader set of functional requirements like:

- Provides the cost of a specific instance.
- Plot the cost evolution of a specific project over 1, 3, 6, 12, 24 months.
- Plot the usage evolution of a specific instance per days & months.
- View the current global consumption.
- Predict of the consumption.
- Plan budget in a better way.
  
  
  The solution can also be extended with the following set of capabilities using OCI Tags and drill-down features:

- Extract and Load OCI Tags and Resource Identifiers into the database.
- Define Meta-Data information about OCI Tags on OCI Resource Identifiers.
- Data model for Oracle Analytics Cloud (OAC), extended tables for Tags, Meta-Data and Resource Identifies tables.
- Custom Canvas/Report in OAC based on the Data Model with drill-down capabilities.

## Sample visualizations

Below are few visualizations that can be derived out of OCI usage data, using Usage2ADW.

![Alt text](image.png)

Figure 1. Representation of total cost incurred by compartments over period of time.

![Alt text](image-1.png)

Figure 2. Representation of total cost incurred by services over period of time.

![Alt text](image-2.png)

Figure 3. Representation of Oracle CPU usage in hours by compartments.

![Alt text](image-3.png)

Figure 4. Representation of running hours of each resource.

![Alt text](image-4.png)

Figure 5. Representation of profit earned each month and forecast for future months.

![Alt text](image-5.png)


Figure 6. Representation of cost incurred each month.








