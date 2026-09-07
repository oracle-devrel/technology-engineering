# FinOps in OCI

# What is this asset?

This asset explains OCI services and constructs that support FinOps discipline, including resource hierarchy, tags, budgets, quotas, cost analysis, and Cloud Advisor.

# How to use this asset?

Use the guidance below to design OCI resource hierarchy, governance, reporting, and optimization practices that support FinOps discipline.

# How OCI Can Support FinOps Discipline

In cloud environments, the ability to provision infrastructure with a simple action shifts costs from a fixed model to a variable model. This can increase the distance between Engineering and Finance teams and make it easier for resources to be underutilized.

OCI provides tools and constructs to support FinOps discipline:

- **Organizations** establish parent-child relationships between tenancies.
- **Tenancies** provide strong workload isolation.
- **Compartments** organize resources.
- **Resources** are OCI artifacts that can be deployed.
- **Tags** add metadata for governance policies and cost-reporting breakdowns.
- **Budgets** set cost thresholds and can trigger alerts and automation.
- **Quotas** let administrators prevent overspending in compartments.

Cost-reporting tools in OCI understand resource hierarchy and tags. Define reporting requirements before planning a cost structure.

OCI also provides the following FinOps capabilities:

1. **Cost Analysis** visualizes consumption over time with grouping and filtering, saved queries, CSV and PDF exports, and future-cost prediction.
2. **Custom Cost Reports** provide hourly resource usage and can be combined across tenancies, analyzed in Oracle Analytics Cloud, or queried from Autonomous Database.
3. **Third-party tools** such as Flexera, CloudHealth, and Cloudvane can support multi-cloud reporting.
4. **Cloud Advisor** provides resource-specific cost-saving recommendations and customizable profiles.

# Useful Links

- [FinOps best practices for Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=0ia5wMwrAuI)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
