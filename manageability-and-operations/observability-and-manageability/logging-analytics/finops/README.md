# <Asset Name> Mastering Cloud Cost Control with OCI Log Analytics 
 
Oracle Cloud Infrastructure (OCI) provides several built-in tools to
help users monitor, analyze, and control cloud spending. Among these
tools are OCI Cost Analysis and Scheduled Reports, which offer
visibility into usage patterns and cost trends over time. These tools
are valuable for high-level reporting and day-to-day cost tracking,
especially when trying to stay within budget or identify cost anomalies.

However, for more in-depth analysis—such as breaking down spending
across departments, correlating costs with specific resource tags, or
building custom dashboards—access to raw cost and usage data becomes
essential. This is where the ability to export and analyze detailed cost
reports becomes particularly useful.

OCI is fully compliant with the FinOps Foundation’s FOCUS (FinOps Open
Cost and Usage Specification) standard. The FOCUS report provides a
standardized and comprehensive dataset that includes detailed
information about costs, services, compartments, tags, and more. This
standardized format makes it easier to integrate OCI cost data into
third-party tools or advanced analytics platforms.

In this asset I import
FOCUS report into OCI Log Analytics. By doing this, you can take
advantage of powerful querying capabilities and visualization features
within the Log Analytics platform. This approach allows you to build
customized dashboards, run advanced queries, and perform granular
analysis tailored to your organization’s specific needs.
 
 
Reviewed: 29.10.2025
 
# When to use this asset?
 
[**Better Cloud cost control**]
OCI’s cost analysis tool provides a great high-level view of your cloud costs, but sometimes you need more detailed customization. For instance, you might want to track when you hit an overage, monitor monthly costs, and calculate the percentage of your budget consumed. Additionally, having visibility at the resource level, rather than just service categories, can give you deeper insights into where your money is going.

[**Custom alerts on budgeting**] OCI’s Budget tool lets you set alerts based on compartments, tenancy, or billing tags. However, there may be instances where you need more granular control. For example, you might want alerts triggered when a new service is used, or to restrict usage to a specific set of services. This enables tighter cost control and better oversight over your cloud spending.

[**Cross-Referencing Costs with Resource Utilization**]In a cloud environment, it’s crucial to monitor both resource allocation and resource utilization on the same dashboard. This approach allows you to identify inefficiencies, such as underutilized resources that may be driving up costs. By aligning cost data with utilization insights, you can optimize infrastructure usage and better manage your cloud expenditures.

 
# How to use this asset?
 
You can follow the instruction of the [step by step guide](https://github.com/oracle-quickstart/oci-o11y-solutions/tree/main/knowledge-content/FinOps/files)
 
 
# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.


