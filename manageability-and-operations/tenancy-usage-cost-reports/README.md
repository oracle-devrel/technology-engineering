# Tenancy Usage and Cost Reports
​
Usage2ADW is a tool which uses the Python SDK to extract the usage and cost reports from OCI tenancy and load it to Oracle Autonomous Database. It is an extension to OCI's native Billing & Cost management capabilities, to provide customers with granular understanding of their spend and utilization of OCI. Using ADW and OAC features, this solution can provide high-level overview, in-depth spend analysis, trends in resource utilization and forecast as well.

OCI automatically generates usage data and is stored in an Oracle owned Object Storage bucket. It contains one row per each OCI resource per hour along with consumption information, metadata, namespace and tags. Usage2ADW load this data to ADW database and OAC visualizations can be created on top of this database.
​
# When to use this asset?
​
Usage2ADW provides customers granular understanding of their spend and utilization of OCI. This solution provides in-depth spend analysis on OCI. It includes high-level overview for executives, resource and cost trends for line of business application owners, trends in resource utilization and more. Usage2ADW is ideal for self-service analysis and allows users to build their own visualizations and enrich the analysis by bringing in their own data like departmental budgets.

Customers can leverage a management module to securely retrieve their tenancy cost and usage data. The module can also be configured to retrieve multiple OCI tenancies data for analysis. This solution extends the core Usage2ADW solution with an integration to retrieve usage and cost metrics from other sources, in particular from OEM for the customer on-premises database estate.
​
This asset will provide the following key features and benefits:
​
1) Load Usage Report to ADW.
2) Load Cost Reports to ADW.
3) Load Public Rates to ADW.
4) Report Usage Current State.
5) Report Usage Over Time.
6) Report Cost Analysis.
7) Report Cost Over Time.
8) Report Rate Card for Used Products.
​
# How to use this asset?
​
Here is an overview of how to use this asset:
​
Step 1: Provision ADW, OAC and a VM on Oracle cloud.
Step 2: Deploy Usage2ADW scripts on VM.
Step 3: Upload and restore catalog file on OAC.
Step 4: Create necessary connections between OCI, ADW and OAC.
Step 5: Refresh OAC dashboard to retrieve your tenancy usage and cost details.

Note: Usage2ADW can be downloaded from https://github.com/oracle/oci-python-sdk/tree/master/examples/usage_reports_to_adw .


## License
Copyright (c) 2023 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](LICENSE) for more details.
