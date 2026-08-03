# Oracle Database@Azure Solution Definition

This repository contains the solution definition material for Oracle Database@Azure (OD@Azure) engagements. It is intended to support discovery, architecture design, implementation planning, onboarding, and operational readiness for customers adopting Oracle Database services within Microsoft Azure.

Reviewed: 03.08.2026

Oracle Database@Azure combines Oracle Exadata Database Service and Oracle database capabilities with Microsoft Azure networking, identity, and operational services. The solution is designed for mission-critical workloads that require enterprise performance, security, availability, and cloud-native integration.

## Purpose

The purpose of this repository is to provide a structured, reusable, and customer-facing reference for:

- Solution definition and architecture alignment
- Landing zone and networking requirements
- Security and identity design
- High availability and disaster recovery planning
- Monitoring, observability, and manageability
- Sizing and bill of materials planning
- Implementation planning and onboarding readiness

## Audience

This material is intended for:

- Solution Architects
- Technical Leads
- Implementation Teams
- Customer Architects and DBA teams
  

## Solution Overview

Oracle Database@Azure provides Oracle database services deployed natively inside Azure data centers. It enables customers to:

- Keep applications in Azure
- Use Oracle Exadata-class performance
- Maintain enterprise database security and availability
- Integrate with Azure networking and identity services
- Support hybrid, multicloud, and sovereign cloud use cases

## Repository Contents

Typical content in this repository includes:

- Solution Definition Document (SDD)
- Architecture diagrams
- Networking and landing zone guidance
- Security and compliance notes
- HA/DR design options
- Backup and recovery guidance
- Monitoring and observability references
- Sizing assumptions and bill of materials
- Implementation scope and workplan
- Customer onboarding guidance
- FAQ and known issues

## Solution Scope

The exact scope of an engagement may vary by customer, but the solution definition typically covers:

- Current state architecture
- Future state architecture
- Azure landing zone readiness
- Oracle Database@Azure onboarding requirements
- Network connectivity and DNS
- Identity federation and access control
- Database sizing and service selection
- Backup and recovery strategy
- High availability and disaster recovery
- Operations, support, and handover

## Landing Zone Requirements

Before deployment, the Azure and OCI landing zones should be validated for:

- Subscription and resource group design
- Resource naming and tagging standards
- Azure RBAC and OCI IAM model
- Network segmentation and delegated subnets
- ExpressRoute or VPN connectivity
- DNS and private name resolution
- Security controls and key management
- Logging, monitoring, and alerting
- Backup and DR readiness
- Automation and governance controls


## Security and Compliance

Security design should account for:

- Identity federation and least privilege access
- Customer-managed keys where required
- Encryption in transit and at rest
- Database auditing and security controls
- Regulatory and sovereign cloud requirements
- Separation of duties across Oracle, Microsoft, and customer teams

## Monitoring and Operations

The solution may use a combination of:

- Azure Monitor
- Azure Log Analytics
- Microsoft Sentinel
- OCI Monitoring
- OCI Logging
- Oracle Data Safe
- Oracle Enterprise Manager
- Third-party SIEM and observability tools

## High Availability and Disaster Recovery

Common HA/DR patterns include:

- Oracle RAC for availability
- Oracle Data Guard for replication and failover
- GoldenGate for migration or logical replication
- Backup-based recovery using OCI Object Storage or Recovery Service
- Cross-region DR where required

## Sizing and Capacity Planning

Sizing should be based on:

- Database size and growth
- OCPU and memory requirements
- Storage consumption
- Workload peaks and service levels
- Consolidation strategy
- Licensing model (BYOL or license included)
- DR and backup requirements

## Implementation and Handover

Implementation planning should include:

- Scope and assumptions
- Deliverables and dependencies
- RACI and responsibilities
- Timeline and milestones
- Customer obligations
- Transition and handover plan

## References

Useful references may include:

- Oracle Database@Azure documentation
- OCI networking and security documentation
- Azure networking and identity documentation
- Oracle MAA best practices
- Oracle Data Guard and GoldenGate references
- Internal architecture and enablement materials

## Notes

- This repository is intended to support solution design and enablement.
- Any customer-specific architecture decisions should be validated against the agreed SDD.
- Use the latest approved Oracle and Microsoft reference architectures where applicable.

## Contributing

Before making changes:

1. Validate the customer scope and assumptions.
2. Confirm architecture impacts with the relevant solution owner.
3. Keep content aligned with Oracle and Microsoft reference guidance.
4. Update diagrams and notes consistently across all related artifacts.
5. Review any changes for security, compliance, and operational impact.

## License
Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
