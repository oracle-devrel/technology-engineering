# Physical x86 Servers to OCI

## Overview

This guide covers migrating workloads from physical x86 servers to Oracle Cloud Infrastructure (OCI), either as OCI Native Compute Instances or as VMs in Oracle Cloud VMware Solution (OCVS). This path is often chosen for legacy applications or workloads running on physical infrastructure that require modernization or consolidation.

## Introduction

Oracle Cloud Infrastructure (OCI) is a global cloud services platform offering a comprehensive portfolio of IaaS, PaaS, SaaS, and DaaS capabilities across distributed datacenters. Physical-to-cloud migration enables organizations to modernize legacy infrastructure, improve scalability, and reduce operational overhead.

Enterprises can choose between two primary target platforms in OCI:
- **Oracle Cloud VMware Solution (OCVS):** Purpose-built for lift-and-shift migrations, preserving VMware software-defined datacenter capabilities.
- **OCI Native Compute Instances:** Designed for replatformed or cloud-native workloads, offering secure, elastic, and high-performance virtual machines.

## Target Platforms

### OCI Native Compute Instances

**Key Characteristics:**
- **Hypervisor:** OCI Compute Service
- **Management Tools:** OCI Console
- **Best Use Case:** Cloud-native apps, replatformed VMs, containers
- **Compute Shapes:** Flexibly defined OCPU/RAM; Standard, DenseIO, GPU, HPC, Ampere
- **Networking:** OCI Virtual Cloud Network (VCN)
- **Primary Storage:** OCI Block Volumes
- **Supported OS:** Latest Linux/Windows distributions

### Oracle Cloud VMware Solution (OCVS)

**Key Characteristics:**
- **Hypervisor:** VMware ESXi
- **Management Tools:** vCenter, HCX, NSX, vSAN
- **Best Use Case:** Lift-and-shift of VMware estates
- **Compute Shapes:** Dedicated Bare Metal DenseIO, Standard and GPU shapes
- **Networking:** VMware NSX-T
- **Primary Storage:** vSAN or OCI Block Storage
- **Supported OS:** All OS supported by vSphere

## Migration Tool: RackWare

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

RMM is available in OCI Marketplace with built-in support for Oracle Cloud VMware Solution (OCVS) and OCI Native migrations.

**Physical-to-Virtual (P2V) Migration:**
RackWare performs OS-level replication and transformation for smooth cutover from physical servers to virtual machines in OCI. The process involves:
- Installing a temporary migration agent on the physical server
- Replicating disk data and system configuration
- Converting physical hardware configurations to virtual equivalents
- Deploying the migrated workload in the target environment

## Assessment and Discovery Mapping

A structured assessment, planning, and testing phase is essential for validating the migration design, minimizing risk, and ensuring a smooth transition to Oracle Cloud Infrastructure (OCI). This phase should include:

- **Workload Discovery & Classification** – Use inventory tools (e.g., RackWare discovery, system inventory tools) to map out physical servers, applications, and dependencies. Classify workloads by criticality (mission-critical, business-critical, dev/test) and migration complexity.
- **Dependency Mapping** – Identify application interdependencies, DNS records, firewall rules, and IP address requirements. Pay special attention to workloads requiring strict IP preservation or low-latency communication.
- **Right-Sizing & Capacity Planning** – Assess CPU, memory, and storage utilization to define the required OCI shape, OCVS node count, and storage architecture (OCI Block Volumes, or vSAN). Consider current utilization and growth factors. Physical servers often have over-provisioned resources that can be optimized in the cloud.
- **Network & Security Planning** – Validate OCI networking design, including subnets, security lists, and FastConnect/IPSec VPN. Plan for Layer 2 extension where IP preservation is required (for OCVS migrations).
- **Testing & Validation** – Conduct pilot migrations for representative workloads before executing large-scale cutovers. Validate performance, failover, and recovery procedures.

## Migration Considerations

### Physical-to-Virtual Conversion

- **Hardware Abstraction:** Physical hardware components are replaced with virtual ones
- **Boot Configuration:** BIOS/UEFI settings may need adjustment for virtual environments
- **Storage Migration:** Physical disks are converted to virtual disk formats (VMDK for OCVS, OCI Block Volumes for Native)
- **Network Configuration:** Physical NICs are replaced with virtual NICs

### Operating System Considerations

- **Driver Updates:** Physical hardware drivers are replaced with virtual drivers
- **Boot Process:** May require adjustment for virtual boot environments
- **Licensing:** Verify OS licensing for virtual environments
- **Performance:** Virtual environments may have different performance characteristics

### Storage Considerations

- **Disk Format Conversion:** Physical disk formats are converted to virtual formats
- **RAID Configuration:** Software RAID may need reconfiguration
- **Storage Performance:** Consider OCI storage performance tiers and vSAN capabilities
- **Data Migration:** Large data volumes may require extended migration windows

### Networking Considerations

**For OCI Native Migrations:**
- **IP Address Remapping:** VMs will receive new IP addresses in OCI VCNs
- **DNS Updates:** DNS records must be updated to point to new IP addresses
- **Firewall Rules:** Security lists and network security groups must be configured in OCI

**For OCVS Migrations:**
- **IP Address Preservation:** With HCX Layer 2 Extension, VMs can retain their original IP addresses
- **Network Extension:** HCX L2E can extend networks from source to OCVS, minimizing reconfiguration

### Application Considerations

- **Legacy Applications:** Some legacy applications may have hardware dependencies that need addressing
- **Performance Testing:** Virtual environments may have different performance characteristics
- **Licensing:** Verify application licensing for virtual/cloud environments
- **Dependencies:** Identify and migrate any hardware-specific dependencies

## Choosing Between OCI Native and OCVS

**Choose OCI Native Compute Instances if:**
- You want to modernize and leverage OCI-native services
- Cost optimization is a priority
- You're consolidating multiple platforms
- Applications can be replatformed

**Choose Oracle Cloud VMware Solution (OCVS) if:**
- You need to preserve existing VMware infrastructure and tools
- You have strict IP preservation requirements
- You want minimal operational changes
- You're migrating alongside other VMware workloads

## Special Considerations for Enterprise and Mission Critical Databases

While VM-level migration tools like RackWare can handle the majority of workloads, they may not be sufficient for enterprise-scale, mission-critical applications where downtime is unacceptable. For large and transaction-heavy databases, a pure VM-level migration introduces significant challenges due to:
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

To ensure a smooth and resilient transition to OCI Native Compute Instances or OCVS-based infrastructure, the following best practices should be incorporated into any migration strategy:

- **Adopt a phased migration approach** – Start with lower-priority or non-production workloads to validate tooling, processes, and network designs. Use early phases as learning cycles before addressing mission-critical systems.

- **Plan for IP remapping** – Document all IP addresses, DNS records, and firewall rules that will need updating. Create a comprehensive IP mapping table and security group mapping before migration begins.

- **Leverage OCI-native services** – Take advantage of OCI's managed services such as Autonomous Database, Object Storage, and monitoring services to modernize applications post-migration.
