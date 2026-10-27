# Oracle Base Database Cloud@Customer Solution Definition

This directory contains solution-definition material for Oracle Base Database Cloud@Customer (BaseDB-C@C) engagements. It supports customer discovery, architecture design, sizing, deployment planning, and operational handover for Oracle Database and application workloads hosted in the customer's data center and managed through Oracle Cloud Infrastructure (OCI).

BaseDB-C@C combines Oracle-managed infrastructure and cloud automation with on-premises deployment. It is suited to customers that need data residency, low latency, and local application integration, including distributed, edge, and space-constrained environments.

Reviewed: 09/09/2026

## Purpose

Use the Solution Definition Document (SDD) to capture and agree the customer-specific design before implementation. It provides a reusable framework for:

- Business context, workload scope, and measurable business value
- Functional and non-functional requirements
- Target logical and physical architecture
- Data-center, networking, security, and access-control requirements
- High availability, disaster recovery, and backup/recovery strategy
- Monitoring, manageability, maintenance, and responsibility model
- Workload sizing, consumption plan, and bill of materials
- Implementation scope, work plan, RACI, assumptions, and handover

## Audience

This material is intended for:

- Solution Architects and Cloud Architects
- Base Database Cloud@Customer specialists
- Customer infrastructure, network, security, application, and DBA teams
- Implementation and project-delivery teams
- Operations and support teams

## Solution Overview

A BaseDB-C@C solution definition should describe the complete workload—not only the implementation subset—and record the decisions required to operate it successfully in the customer data center. Key design areas include:

- Base Database Cloud@Customer infrastructure, VM clusters, database VMs, and application VMs
- OCI connectivity and landing-zone readiness
- Client, backup, and control-plane connectivity, including DNS, NTP, and private OCI connectivity
- Data-center power, rack, cabling, transceivers, and site-readiness requirements
- Identity and access management, encryption, Oracle Key Vault, auditing, and security controls
- Oracle RAC, Data Guard, backup, and Oracle Maximum Availability Architecture (MAA) service levels
- Storage-shelf capacity, ASM DATA and RECO allocation, and workload growth
- OCI and Oracle monitoring, maintenance, and the shared Oracle/customer operations model

## SDD Structure

The customer-facing SDD should normally contain the following sections:

1. Document control, stakeholders, and abbreviations
2. Business context, executive summary, and workload business value
3. Workload overview and customer non-functional requirements
4. Future-state logical and physical architecture
5. Solution considerations for security, networking, HA/DR, backup, and observability
6. Base Database Cloud@Customer architecture, operations, RACI, and maintenance
7. Sizing assumptions, proposed hardware shape, consumption plan, and bill of materials
8. Implementation scope, work plan, assumptions, obligations, dependencies, and transition plan, where Oracle performs the implementation
9. Glossary and technical annexes

## Sizing and Capacity Planning

Sizing should be based on collected workload data and documented assumptions. The SDD should record the selected sizing method, required database and application VM clusters, peak compute and memory demand, storage needs, growth forecasts, HA/DR overhead, and capacity safety margins. Consider ASM DATA and RECO allocations, database backup requirements, VM storage, and the workload's resilience objectives. Align the resulting infrastructure shape, consumption plan, and bill of materials with the approved commercial quote.

## Files

- [Compact BaseDB-C@C Solution Definition PDF](./files/Base-Database-Cloud-at-Customer-Solution-Definition.pdf)

## Related Guidance

- [BaseDB-C@C Infrastructure](../basedbcc-infra/)
- [Oracle Base Database Cloud@Customer documentation](https://docs.oracle.com/en/cloud/cloud-at-customer/base-database/admin/index.html)
- [Oracle Base Database Cloud@Customer X11 data sheet](https://www.oracle.com/a/ocom/docs/database/base-database-cloud-at-customer-x11.pdf)
- [Oracle Maximum Availability Architecture](https://www.oracle.com/database/maximum-availability/)
- [OCI landing-zone guidance](https://github.com/oracle-devrel/technology-engineering/tree/main/landing-zones)

## Notes

- Treat the SDD as a customer-specific design artifact; validate all architecture decisions, requirements, sizing assumptions, and commercial details with the customer and the relevant Oracle teams.
- The implementation section applies only when Oracle is delivering the implementation; adjust or remove it for customer- or partner-led delivery.
- Keep customer-identifying details, commercial data, and internal-only process references out of any externally shared version.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
