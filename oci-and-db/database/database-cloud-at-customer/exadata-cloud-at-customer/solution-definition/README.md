# Oracle Exadata Cloud@Customer Solution Definition

This directory contains solution-definition material for Oracle Exadata Cloud@Customer (ExaDB-C@C) engagements. It supports customer discovery, architecture design, sizing, deployment planning, and operational handover for Oracle Database services running in the customer's data center and managed through Oracle Cloud Infrastructure (OCI).

ExaDB-C@C provides Exadata performance and cloud automation while helping customers meet data-residency, latency, and on-premises integration requirements. The solution can support both co-managed Oracle Database services and Autonomous Database on Exadata Cloud@Customer.

Reviewed: 09/09/2026

## Purpose

Use the Solution Definition Document (SDD) to capture and agree the customer-specific design before implementation. It provides a reusable framework for:

- Business context, workload scope, and measurable business value
- Functional and non-functional requirements
- Target logical and physical architecture
- Data-center, networking, security, and operator-access requirements
- High availability, disaster recovery, and backup/recovery strategy
- Monitoring, manageability, maintenance, and responsibility model
- Workload sizing, consumption plan, and bill of materials
- Implementation scope, work plan, RACI, assumptions, and handover

## Audience

This material is intended for:

- Solution Architects and Cloud Architects
- Oracle Exadata Cloud@Customer specialists
- Customer infrastructure, network, security, application, and DBA teams
- Implementation and project-delivery teams
- Operations and support teams

## Solution Overview

An ExaDB-C@C solution definition should describe the complete workload—not only the implementation subset—and document the decisions required to operate it successfully in the customer data center. Key design areas include:

- Exadata Cloud@Customer infrastructure, VM clusters, database services, and storage
- OCI connectivity and landing-zone readiness
- Client, backup, and control-plane network design, including DNS and private connectivity
- Data-center floor space, power, rack, cabling, transceivers, and site-readiness requirements
- Identity and access management, encryption, key management, auditing, and Operator Access Control
- Oracle RAC, Data Guard, backup, and Oracle Maximum Availability Architecture (MAA) service levels
- OCI and Oracle monitoring, observability, maintenance, and shared operational responsibilities

## SDD Structure

The customer-facing SDD should normally contain the following sections:

1. Document control, stakeholders, and abbreviations
2. Business context, executive summary, and workload business value
3. Workload overview and customer non-functional requirements
4. Future-state logical and physical architecture
5. Solution considerations for security, networking, HA/DR, backup, and observability
6. Exadata Cloud@Customer architecture and operations/RACI model
7. Sizing analysis, proposed hardware shape, consumption plan, and bill of materials
8. Implementation scope, work plan, assumptions, obligations, dependencies, and transition plan, where Oracle performs the implementation
9. Glossary and technical annexes

## Sizing and Capacity Planning

Sizing should be based on collected workload data and documented assumptions. The SDD should record the selected sizing method, VM-cluster cohorts, time-aligned peak demand, projected growth, high-availability and disaster-recovery overhead, storage requirements, and capacity safety margins. The resulting hardware shape, estimated ECPU consumption, and bill of materials must be aligned with the approved commercial quote.

## Related Guidance

- [ExaDB-C@C Infrastructure](../exacc-infra/)
- [ExaDB-C@C Network](../exacc-network/)
- [ExaDB-C@C Security](../exacc-security/)
- [ExaDB-C@C Data Protection](../exacc-data-protection/)
- [Autonomous Database on Exadata Cloud@Customer](../adb-cc/)
- [Oracle Exadata Cloud@Customer documentation](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/)
- [Exadata Cloud@Customer X11M data sheet](https://www.oracle.com/a/ocom/docs/engineered-systems/exadata/exadb-cc-x11m-ds.pdf)
- [Oracle Maximum Availability Architecture](https://www.oracle.com/database/maximum-availability/)

## Notes

- Treat the SDD as a customer-specific design artifact; validate all architecture decisions, requirements, sizing assumptions, and commercial details with the customer and the relevant Oracle teams.
- The implementation section applies only when Oracle is delivering the implementation; adjust or remove it for customer- or partner-led delivery.
- Keep customer-identifying details, commercial data, and internal-only process references out of any externally shared version.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
