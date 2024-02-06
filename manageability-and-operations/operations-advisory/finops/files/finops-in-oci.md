# How OCI Can Support FinOps Discipline

In Cloud, the ability to spin up infrastructure by the simple push of a button has shifted costs from a fixed model to a variable model, 
increasing the distance from Engineerig and Finance teams. At the same time, this increases the chance for resources to be deployed and under-utilized,
or to be under-utilized under particular circumstances.
OCI provides tools and constructs to ensure FinOps discipline can be applied:

**Organizations**: allows a parent-child relationship between various tenancies

**Tenancies**: provide strong isolation among workloads

**Compartments**: allow resources to be organized 

**Resources**: all OCI artifacts that can be deployed

**Tags**: add metadata information to resources to apply governance policies and break down cost reporting

**Budgets**: thresholds that can be set on cost per billing cycle that OCI will evaluate every hour to send an alert in case the value for the budget is crossed or closed. Budgets can be targeted toward subscriptions, child tenancies, compartments, and tags. The integration with the Event service can be used to trigger automation such as the creation of Quotas.

**Quotas**: limits are set by Admins on compartments to prevent overspending.



Cost reporting tools in OCI are aware of resource hierarchy and tags.
Understanding your organization's reporting needs is the first step that needs to be
taken into account when planning for a costing structure.

OCI provides powerful tools to support FinOps discipline.



1. **Cost Analysis** to visualize consumption over time. Group-by and filtering dimensions are available to customers. Queries can be saved for reuse. Data can be extracted as CSV and PDF. Future cost prediction is estimated based on current usage patterns. Reports can run at a specific time and deliver the content to an object storage.

2. **Custom Cost Reports** show usage hourly per resources. Combined reports can be generated for all tenancies in an organization, viewed in Oracle Analytics Cloud, and queried in Autonomous DB when transferred. This move can be automated.

3. Reporting needs across multiple cloud providers can be met by **3rd Party tools** such as Flexera, CloudHealth, and Cloudvane.

4. **Cloud Advisor** enables cost-saving opportunities with resource-specific recommendations and customizable profiles. These recommendations can be immediately implemented via the 'fix-it' flow, without navigating to the specific resource.







# Useful Links

[FinOps best practices for Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=0ia5wMwrAuI)
