# BUDGETS AND TAGGING

## 1. Tagging

OCI Tagging allows you to assign **key:value** pairs to resources and use these assigned tags for the purpose of organizing and listing resources, based on requirements. Tagging can be used for organizing/listing resources, cost-tracking, and access control purposes. There are two ways for you to add tags to resources. Each approach offers a different type of tag for you to work with:

- **Defined tags**: tag administrators manage resource metadata.
- **Free-form tags**: unmanaged metadata applied to resources by users (these are out of scope)

**Cost tracking** is a feature available with defined tags. This feature is currently only relevant for use with **Budgets**.

Tags are grouped into **Tag Namespaces** which are a container for tag keys. They consist of a name and zero or more tag key definitions. Tag namespaces are not case-sensitive and must be unique across the tenancy. The namespace is also a natural grouping to which administrators can apply policy. One policy on the tag namespace applies to all the tag definitions contained within that namespace.

Below are some service limitations with respect to using tags:

- Tags per tenancy: unlimited
- Tags per resource: 10 free-form tags and 64 defined tags
- Tags enabled for cost-tracking: 10 per tenancy (includes both active and retired tags)
- Total tag data size: 5 K (JSON). The total tag data size includes all tag data for a single resource (all applied tags and tag values). Sizing is per UTF-8.
- Number of pre-defined values for a tag key: 100 per list
&nbsp; 
### 1.2 Design and Usage of Defined Tags 

The design and usage of defined tags are customers, business, and even OE-specific. It must be designed and used that matches the customer's nomenclature and values.

Defined tags can be assigned to resources and used in policy statements or Cloud Guard recipes.

Defined tags can be applied to Terraform configurations at any time. They are considered updates to existing resources and will not trigger any recreation of these.

&nbsp; 
## 2. Budgets

Budgets can be used to set limits on OCI spending (i.e., Quotas). You can set alerts on your budget to inform you when you are close to exceeding your budget. The budgets and spending are available directly from the OCI console.

Budgets are set on a cost-tracking tags or compartment basis and allow the tracking of all spending in that cost-tracking tag or for the compartment and its child compartments. A monthly threshold is defined for OCI spending and email alerts can be defined to get sent out for the respective budget. Alerts are evaluated every hour in most regions and can be triggered when the actual or forecasted spending hits either a percentage of the budget or a specified set amount.

In addition, automation can be created for Budgets with the use of Events Service.

&nbsp; 
### 2.1 Budget Control and Billing

For budget control and billing two approaches are recommended:

- Tenancy-global to identify unauthenticated usage
- Landing Zone structure specific
  

While the tenancy-global budget control applies to the overall average consumption, the landing zone compartment structure enables the creation of budgets to set soft limits on OCI tenancy spending, by shared elements, operating entities, departments, projects, etc. With budget control, the available budget can be controlled using quotas and also trigger alarms when unusual costs occur.

Budget control and billing is a global task for every tenancy, and since it's a generic OCI topic not specific to any landing zone, it is not described in this asset. 

&nbsp; 
&nbsp; 
# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
