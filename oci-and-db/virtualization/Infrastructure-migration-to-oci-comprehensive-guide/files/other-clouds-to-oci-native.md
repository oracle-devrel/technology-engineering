# Other Public Clouds to OCI Native Compute Instances

## Overview

This guide covers migrating workloads from other public cloud providers (Microsoft Azure, Google Cloud Platform (GCP), and other cloud environments) to OCI Native Compute Instances. Migration from these platforms requires VM format conversion, networking adaptation, and integration with OCI services. This path suits organizations seeking to optimize costs, leverage OCI-native services, consolidate cloud environments, or avoid vendor lock-in.

## Introduction

Oracle Cloud Infrastructure (OCI) is a global cloud services platform offering a comprehensive portfolio of IaaS, PaaS, SaaS, and DaaS capabilities across distributed datacenters. OCI Native Compute Instances are designed for replatformed or cloud-native workloads, offering secure, elastic, and high-performance virtual machines provisioned directly within OCI. Migrating from AWS to OCI enables organizations to leverage OCI's low cost and flexible pricing, high-performance infrastructure, and an unique off-box virtualization security model.

## Target Platform: OCI Native Compute Instances

**Key Characteristics:**
- **Hypervisor:** OCI Compute Service
- **Management Tools:** OCI Console
- **Best Use Case:** Cloud-native apps, replatformed VMs, containers
- **Compute Shapes:** Flexibly defined OCPU/RAM; Standard, DenseIO, GPU, HPC, Ampere
- **Networking:** OCI Virtual Cloud Network (VCN)
- **Primary Storage:** OCI Block Volumes
- **Supported OS:** Latest Linux/Windows distributions

## Migration Tool: RackWare (Primary)

RackWare is a cloud-agnostic workload mobility and resilience platform that simplifies migration, disaster recovery, and backup across physical, virtual, and cloud-native environments. Its core product, the RackWare Management Module (RMM), provides agentless, policy driven automation to move and protect workloads.

**Key Benefits:**
- **Broad Compatibility** – Supports Azure VMs, GCP Compute Engine, AWS EC2, VMware, Hyper-V, KVM, physical servers, and containers (Kubernetes). Works with all major public clouds, including OCI.
- **Agentless & Lightweight** – No permanent agents required; minimal impact on production systems.
- **Multi-Use Platform** – One solution for migration, DR, and backup—reducing tool sprawl and complexity.
- **Efficient Replication** – Delta-based sync ensures faster migrations and near-zero RPO/RTO for DR.
- **Scalability** – Handles migrations from a few to thousands of workloads in coordinated "waves."
- **Oracle Integration** – Available on Oracle Cloud Marketplace; supports OCI and on-prem Oracle environments (C3, PCA).

**Key Capabilities:**
- **Migration** – workload migrations with automated sizing and IP/DNS remapping.
- **Disaster Recovery** – Policy-based DR with automated failover/fallback and non-disruptive testing.
- **Backup** – Application-consistent snapshots, long-term retention, and granular restore.
- **Heterogeneous Support** – Windows, Linux, and container workloads.
- **Automated Discovery** – Discovers VMs, dependencies, and performance metrics across cloud platforms.

RMM is available in OCI Marketplace with built-in support for OCI Native migrations from Azure, GCP, and other cloud providers.

**Best Suited For:**
- Multi-cloud environments with workloads across Azure, GCP, AWS, and other providers
- Organizations requiring migration, DR, and backup in a single platform
- Cloud-to-cloud migrations where native tools are not available

## Migration Considerations

### Networking Changes

Migrating from other public clouds to OCI Native requires:

- **IP Address Remapping:** VMs will receive new IP addresses in OCI VCNs
- **Security Groups:** 
  - Plan on using OCI Network Security List and/or Network Security Groups to control network traffic between instances
- **DNS Updates:** DNS records must be updated to point to new IP addresses
- **Gateway Configuration:** Internet gateways, NAT gateways, and VPN connections need OCI equivalents and will have different public egress IP addresses


### Operating System Considerations

- **Cloud-Specific Images:** Cloud provider-specific OS images may need updates or conversion to standard distributions
- **Windows Instances:** Windows instances may need driver updates for OCI compatibility
- **Cloud Agents:** Cloud-specific agents (Azure VM Agent, GCP guest environment) will be removed; OCI agents may need to be installed
- **Cloud-Init:** Cloud-specific user-data scripts may need adaptation for OCI cloud-init
- **Instance Metadata:** Cloud-specific instance metadata services are replaced with OCI instance metadata service

## Special Considerations for Enterprise and Mission Critical Databases

While VM-level migration tools (e.g., OCM, RackWare) can handle the majority of workloads, they may not be sufficient for enterprise-scale, mission-critical applications where downtime is unacceptable. For large and transaction-heavy databases, a pure VM-level migration introduces significant challenges due to:
- Database size (terabytes or petabytes).
- Continuous write activity (transaction-heavy workloads).
- The requirement for zero or near-zero downtime.

To migrate such mission critical workloads and RDBMS environments you might consider dedicated solutions and architectures:

- **Oracle Databases** – Use Oracle Data Guard or GoldenGate for robust replication, synchronization, and failover capabilities.
- **PostgreSQL/MySQL** – Use native replication or database-specific migration tools.
- **Microsoft Active Directory** – Use native AD replication between domain controllers to maintain consistency.
- **Microsoft Exchange Server** – Leverage Exchange Hybrid configurations or Database Availability Groups (DAGs) for continuity during migration.

By combining VM-level mobility with application-aware replication, enterprises can achieve data consistency, reduced downtime, and a resilient cutover strategy for their most business-critical workloads.

## Best Practices & Guidance

To ensure a smooth and resilient transition to OCI Native Compute Instances, the following best practices should be incorporated into any migration strategy:

- **Adopt a phased migration approach** – Start with lower-priority or non-production workloads to validate tooling, processes, and network designs. Use early phases as learning cycles before addressing mission-critical systems.

- **Plan for IP remapping** – Document all IP addresses, DNS records, and firewall rules that will need updating. Create a comprehensive IP mapping table and security group mapping before migration begins.

- **Leverage OCI-native services** – Take advantage of OCI's managed services such as Autonomous Database, Object Storage, and monitoring services to modernize applications post-migration.
