# VMware vSphere to OCI Native Compute Instances

## Overview

This guide covers migrating workloads from on-premises VMware vSphere environments to OCI Native Compute Instances. In this scenario, VMware VMs are replatformed into OCI Native Compute. The process involves converting VM formats, adapting networking and storage, and integrating with OCI services.

## Introduction

Oracle Cloud Infrastructure (OCI) is a global cloud services platform offering a comprehensive portfolio of IaaS, PaaS, SaaS, and DaaS capabilities across distributed datacenters. OCI Native Compute Instances are designed for replatformed or cloud-native workloads, offering secure, elastic, and high-performance virtual machines provisioned directly within OCI. This option is ideal for modernizing applications, integrating with OCI-native services, or optimizing costs and scalability.

## Target Platform: OCI Native Compute Instances

**Key Characteristics:**
- **Hypervisor:** OCI Compute Service
- **Management Tools:** OCI Console
- **Best Use Case:** Cloud-native apps, replatformed VMs, containers
- **Compute Shapes:** Flexibly defined OCPU/RAM; Standard, DenseIO, GPU, HPC, Ampere
- **Networking:** OCI Virtual Cloud Network (VCN)
- **Primary Storage:** OCI Block Volumes
- **Supported OS:** Latest Linux/Windows distributions

## Migration Tools

### Oracle Cloud Migrations (OCM)

Oracle Cloud Migrations is a managed service that automates the migration of workloads—specifically VMware virtual machines—to Oracle Cloud Infrastructure (OCI). It streamlines every step of the process—from discovery and planning to replication and deployment—using OCI Console, CLI, or API interface.

**Key Capabilities:**

**Automated Asset Discovery & Inventory:**
- For VMware, a remote agent appliance is deployed to discover VMs and their metadata.
- Discovered assets are stored in an OCI-hosted Inventory, along with performance data available in the OCI Monitoring service.

**Migration Planning & Execution:**
- Assets are grouped into Migration Projects, each containing one or more Migration Plans.
- The service recommends target OCI configurations—such as compute shape and placement—based on source attributes and performance metrics. Users can customize these plans and evaluate cost estimates.
- Supports incremental replication of VM data to OCI.

**Secure, Compliant Access & Governance:**
- Integrates with OCI Identity and Access Management (IAM) and Vault to ensure secure authentication, authorization, and management of credentials.
- Administrators must configure compartments, dynamic groups, and IAM policies to enable migration components and access control.

**Supported Environments:**
- VMware vSphere versions 6.5 through 8.0 (vSphere 8.0 support requires VDDK 7.0U2).
- Supports a wide range of Linux and Windows guest OS versions.

Oracle Cloud Migrations provides a streamlined, end-to-end migration experience for VMware workloads moving into OCI. From discovery through validation and cutover, the service offers automation, governance integration, cost insights, and incremental replication. It's ideal for organizations seeking a secure, self-service migration path that integrates directly with OCI infrastructure.

**Best Suited For:**
- Low-complexity, non-mission-critical workloads
- Organizations seeking automated discovery and migration planning
- VMware environments requiring integration with OCI-native services

### RackWare

RackWare is a cloud-agnostic workload mobility and resilience platform that simplifies migration, disaster recovery, and backup across physical, virtual, and cloud-native environments. Its core product, the RackWare Management Module (RMM), provides agentless, policy driven automation to move and protect workloads.

**Key Benefits:**
- **Broad Compatibility** – Supports VMware, Hyper-V, KVM, physical servers, and containers (Kubernetes). Works with all major public clouds, including OCI, AWS, Azure, and GCP.
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

RMM is available in OCI Marketplace with built-in support for OCI Native migrations.

**Best Suited For:**
- Heterogeneous environments where non-VMware workloads must be migrated alongside VMware workloads
- Organizations requiring migration, DR, and backup in a single platform
- Complex migrations requiring policy-driven automation

## Assessment and Discovery Mapping

A structured assessment, planning, and testing phase is essential for validating the migration design, minimizing risk, and ensuring a smooth transition to OCI Native Compute Instances. This phase should include:

- **Workload Discovery & Classification** – Use inventory tools (e.g., RVTools, OCM discovery, vSphere inventory, or RackWare) to map out virtual machines, applications, and dependencies. Classify workloads by criticality (mission-critical, business-critical, dev/test) and migration complexity.
- **Dependency Mapping** – Identify application interdependencies, DNS records, firewall rules, and IP address requirements. Note that IP addresses will need to be remapped unless using custom networking solutions.
- **Right-Sizing & Capacity Planning** – Assess CPU, memory, and storage utilization to define the required OCI compute shape and storage architecture (OCI Block Volumes). Consider current utilization and growth factors. OCM provides automated recommendations based on performance metrics.
- **Network & Security Planning** – Validate OCI networking design, including VCNs, subnets, security lists, and FastConnect/IPSec VPN. Plan for IP remapping and DNS updates.
- **Testing & Validation** – Conduct pilot migrations for representative workloads before executing large-scale cutovers. Validate performance, failover, and recovery procedures.

## Migration Considerations

### Format Conversion

VMware VMs use VMDK disk format, which must be converted to OCI-compatible formats during migration. Both OCM and RackWare handle this conversion automatically.

### Networking Changes

Unlike VMware-to-VMware migrations, migrating to OCI Native requires:
- **IP Address Remapping:** VMs will receive new IP addresses in OCI VCNs unless using custom solutions
- **DNS Updates:** DNS records must be updated to point to new IP addresses
- **Firewall Rules:** Security lists and network security groups must be configured in OCI
- **Gateway Configuration:** Default gateways will change to OCI VCN gateways

### Storage Migration

- VMware storage (VMFS, NFS, vSAN) is converted to OCI Block Volumes
- Disk sizes and performance characteristics may need adjustment
- Consider OCI storage performance tiers (Standard, Balanced, High Performance)

### Operating System Considerations

- Ensure guest OS versions are supported by OCI
- VMware Tools will be removed; OCI-specific agents may need to be installed
- Some VMware-specific configurations may need adjustment

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
