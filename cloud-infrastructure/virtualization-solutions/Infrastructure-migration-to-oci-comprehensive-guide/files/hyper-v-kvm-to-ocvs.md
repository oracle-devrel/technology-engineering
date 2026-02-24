# Hyper-V/KVM to Oracle Cloud VMware Solution (OCVS)

## Overview

This guide covers migrating workloads from Microsoft Hyper-V or KVM environments to Oracle Cloud VMware Solution (OCVS). Although less common than other migration paths, this option consolidates workloads under a single VMware SDDC on OCI for standardization. It requires cross-hypervisor conversion tools to preserve VM configuration attributes and migrate workloads reliably.

## Introduction

Oracle Cloud Infrastructure (OCI) is a global cloud services platform offering a comprehensive portfolio of IaaS, PaaS, SaaS, and DaaS capabilities across distributed datacenters. Oracle Cloud VMware Solution (OCVS) is purpose-built for lift-and-shift migrations of existing VMware environments, preserving the full VMware software-defined datacenter (vSphere, vSAN, NSX, vCenter), enabling organizations to maintain existing tools, processes, and operational models with minimal disruption.

Migrating Hyper-V or KVM workloads to OCVS enables organizations to standardize on VMware infrastructure while leveraging OCI's cloud capabilities.

## Target Platform: Oracle Cloud VMware Solution (OCVS)

**Key Characteristics:**
- **Hypervisor:** VMware ESXi
- **Management Tools:** vCenter, HCX, NSX, vSAN
- **Best Use Case:** Lift-and-shift of VMware estates, standardization of heterogeneous environments
- **Compute Shapes:** Dedicated Bare Metal DenseIO, Standard and GPU shapes
- **Networking:** VMware NSX-T
- **Primary Storage:** vSAN or OCI Block Storage
- **Supported OS:** All OS supported by vSphere

## Migration Tools

### VMware HCX Enterprise with OS-Assisted Migration (OSAM)

**OS-Assisted Migration (OSAM)** enables the migration of workloads from non-vSphere hypervisors, such as Microsoft Hyper-V or KVM, into OCVS. Unlike vMotion or Bulk Migration, OSAM performs a guest-level migration by installing an HCX migration agent within the operating system. The agent copies the VM's disk and configuration data to the target vSphere environment, where the VM is then reconstructed. This method is particularly useful for consolidating heterogeneous environments into VMware-based infrastructure.

OSAM requires an HCX Enterprise license and is typically used for one-time migrations of workloads that cannot be moved using standard vSphere-based replication methods.

**Key Considerations:**
- Replication begins a full synchronization transfer to the destination site. The guest virtual machine remains online during replication until the final delta synchronization.
- After the full sync, the switch over can be immediate or at a specific schedule just like Bulk Migration
- Final delta sync starts when the switch phase starts, until then it maintains a continuous sync of changes
- HCX performs a hardware mapping of the replicated volumes to ensure proper operation, including updates of the software stack on the replica. This fix-up process includes adding drivers and modifying the OS configuration files at the destination. The migrated virtual machine reboots during this process.
- VMware Tools is installed on the migrated virtual machine and migration completes.
- OSAM does not support P2V
- If the source VM does not power off, HCX will attempt to power off the replica VM.
  - **If the replica powers off successfully:** It remains connected to its NICs. You can then manually power off the source VM and power on the replica.
  - **If the replica fails to power off:** Both the source and replica remain powered on, but the replica is disconnected from the network. In this case, manually enable the NICs for the replica in vCenter, power off the source VM (if it is still running), and then power on the migrated VM.

### RackWare (Alternative)

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

RMM is available in OCI Marketplace with built-in support for Oracle Cloud VMware Solution (OCVS) migrations.

**Best Suited For:**
- Organizations preferring a single tool for heterogeneous migrations
- Environments requiring migration, DR, and backup capabilities
- Complex migrations requiring policy-driven automation

## Assessment and Discovery Mapping

A structured assessment, planning, and testing phase is essential for validating the migration design, minimizing risk, and ensuring a smooth transition to Oracle Cloud VMware Solution (OCVS). This phase should include:

- **Workload Discovery & Classification** – Use inventory tools (e.g., RackWare, Hyper-V Manager, KVM management tools, or HCX discovery) to map out virtual machines, applications, and dependencies. Classify workloads by criticality (mission-critical, business-critical, dev/test) and migration complexity.
- **Dependency Mapping** – Identify application interdependencies, DNS records, firewall rules, and IP address requirements. Pay special attention to workloads requiring strict IP preservation or low-latency communication.
- **Right-Sizing & Capacity Planning** – Assess CPU, memory, and storage utilization to define the required OCVS node count and storage architecture (OCI Block Volumes, or vSAN). Consider current utilization and growth factors.
- **Network & Security Planning** – Validate OCVS networking design, including NSX-T configuration, security policies, and FastConnect/IPSec VPN. Plan for Layer 2 extension where IP preservation is required.
- **Testing & Validation** – Conduct pilot migrations for representative workloads before executing large-scale cutovers. Validate performance, failover, and recovery procedures.

## Migration Considerations

### Format Conversion

**Hyper-V:** VHD/VHDX disk formats must be converted to VMDK format for vSphere. Both HCX OSAM and RackWare handle this conversion automatically.

**KVM:** QCOW2, RAW, or other KVM disk formats must be converted to VMDK format. Both tools support these conversions.

### Networking Considerations

- **IP Address Preservation:** With HCX Layer 2 Extension, VMs can retain their original IP addresses
- **Network Extension:** HCX L2E can extend networks from source to OCVS, minimizing reconfiguration
- **NSX-T Integration:** Migrated VMs will integrate with NSX-T networking in OCVS

### Storage Migration

- Hyper-V storage (VHD/VHDX) or KVM storage (QCOW2, RAW) is converted to VMDK format
- Storage can be placed on vSAN or OCI Block Storage in OCVS
- Disk sizes and performance characteristics may need adjustment

### Operating System Considerations

- Ensure guest OS versions are supported by vSphere
- Hyper-V Integration Services or KVM-specific tools will be removed
- VMware Tools will be installed during migration (for OSAM)
- Some hypervisor-specific configurations may need adjustment

## Special Considerations for Enterprise and Mission Critical Databases

While VM-level migration tools (e.g., HCX OSAM, RackWare) can handle the majority of workloads, they may not be sufficient for enterprise-scale, mission-critical applications where downtime is unacceptable. For large and transaction-heavy databases, a pure VM-level migration introduces significant challenges due to:
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

To ensure a smooth and resilient transition to a new OCVS-based infrastucture, the following best practices should be incorporated into any migration strategy:

- **Adopt a phased migration approach** – Start with lower-priority or non-production workloads to validate tooling, processes, and network designs. Use early phases as learning cycles before addressing mission-critical systems.

- **Plan for IP remapping** – Document all IP addresses, DNS records, and firewall rules that will need updating. Create a comprehensive IP mapping table and security group mapping before migration begins.

- **Leverage OCI-native services** – Take advantage of OCI's managed services such as Autonomous Database, Object Storage, and monitoring services to modernize applications post-migration.
