# Oracle Database@AWS Solution Definition

This repository contains the solution definition material for Oracle Database@AWS (OD@AWS) engagements. It is intended to support discovery, architecture design, implementation planning, onboarding, and operational readiness for customers adopting Oracle Database services within AWS.

Oracle Database@AWS combines Oracle Exadata Database Service and Oracle database capabilities with AWS networking, identity, and operational services. The solution is designed for mission-critical workloads that require enterprise performance, security, availability, and cloud-native integration.

Reviewed: 03.08.2026

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

Oracle Database@AWS provides Oracle database services deployed natively inside Azure data centers. It enables customers to:

- Keep applications in AWS
- Use Oracle Exadata-class performance
- Maintain enterprise database security and availability
- Integrate with AWS networking and identity services
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
- Oracle Database@AWS onboarding requirements
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
- AWS RBAC and OCI IAM model
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
- Separation of duties across Oracle, AWS, and customer teams

## Monitoring and Operations

The solution may use a combination of:

- AWS Monitor
- AWS Log Analytics
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

- Oracle Database@AWS documentation
- OCI networking and security documentation
- AWS networking and identity documentation
- Oracle MAA best practices
- Oracle Data Guard and GoldenGate references
- Internal architecture and enablement materials

## Notes

- This repository is intended to support solution design and enablement.
- Any customer-specific architecture decisions should be validated against the agreed SDD.
- Use the latest approved Oracle and Microsoft reference architectures where applicable.
