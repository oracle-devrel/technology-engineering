# AWS to OCI Native Compute Instances

## Overview

This guide covers migrating workloads from Amazon Web Services (AWS) EC2 instances to OCI Native Compute Instances. Migration from AWS requires VM format conversion, networking adaptation, and integration with OCI services. This path suits organizations seeking to optimize costs, leverage OCI-native services, or consolidate cloud environments.

## Introduction

Oracle Cloud Infrastructure (OCI) is a global cloud services platform offering a comprehensive portfolio of IaaS, PaaS, SaaS, and DaaS capabilities across distributed datacenters. OCI Native Compute Instances are designed for replatformed or cloud-native workloads, offering secure, elastic, and high-performance virtual machines provisioned directly within OCI. Migrating from AWS to OCI enables organizations to leverage OCI's low cost and flexible pricing, high-performance infrastructure, and a unique off-box virtualization security model.

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

### Oracle Cloud Migrations (OCM) (Recommended)

Oracle Cloud Migrations is a managed service that automates the migration of workloads—specifically AWS EC2 instances—to Oracle Cloud Infrastructure (OCI). It streamlines every step of the process—from discovery and planning to replication and deployment—using OCI Console, CLI, or API interface.

**Key Capabilities:**

**Automated Asset Discovery & Inventory:**
- For AWS, the service performs agentless discovery of EC2 instances.
- Discovered assets are stored in an OCI-hosted Inventory.

**Migration Planning & Execution:**
- Assets are grouped into Migration Projects, each containing one or more Migration Plans.
- The service recommends target OCI configurations—such as compute shape and placement—based on source attributes and performance metrics. Users can customize these plans and evaluate cost estimates.
- Supports incremental replication of instance data to OCI.


**Supported Environments:**
- AWS EC2 (x86/EBS-backed instances).
- Supports a wide range of Linux and Windows guest OS versions.

Oracle Cloud Migrations provides a streamlined, end-to-end migration experience for AWS workloads moving into OCI. From discovery through validation and cutover, the service offers automation, cost insights, and incremental replication. It's ideal for organizations seeking a secure, self-service migration path that integrates directly with OCI infrastructure.

**Best Suited For:**
- Native OCI out-of-the-box AWS EC2 migration
- Organizations seeking cost reducation and/or perfomance improvement 
- Workloads that benefit from integration with OCI other 120+ cloud services

### RackWare (Alternative)

RackWare is a cloud-agnostic workload mobility and resilience platform that simplifies migration, disaster recovery, and backup across physical, virtual, and cloud-native environments. Its core product, the RackWare Management Module (RMM), provides agentless, policy driven automation to move and protect workloads.

**Key Benefits:**
- **Broad Compatibility** – Supports AWS EC2, Azure VMs, GCP Compute Engine, VMware, Hyper-V, KVM, physical servers, and containers (Kubernetes). Works with all major public clouds, including OCI.
- **Agentless & Lightweight** – No permanent agents required; minimal impact on production systems.
- **Multi-Use Platform** – One solution for migration, DR, and backup—reducing tool sprawl and complexity.
- **Efficient Replication** – Delta-based sync ensures fast migrations.
- **Scalability** – Handles migrations from a few to thousands of workloads in coordinated "waves."
- **Oracle Integration** – Available on Oracle Cloud Marketplace; supports OCI and on-prem Oracle environments (C3, PCA).

**Key Capabilities:**
- **Migration** – workload migrations with automated sizing.
- **Disaster Recovery** – Policy-based DR with automated failover/fallback and non-disruptive testing.
- **Backup** – Application-consistent snapshots, long-term retention, and granular restore.
- **Heterogeneous Support** – Windows, Linux, and container workloads.

RMM is available in OCI Marketplace with built-in support for OCI Native migrations from AWS and other cloud providers.

**Best Suited For:**
- Complex migrations requiring policy-driven automation
- Organizations requiring migration, DR, and backup in a single platform
- Multi-cloud environments with workloads across AWS, Azure, and GCP

## Assessment and Discovery Mapping

A structured assessment, planning, and testing phase is essential for validating the migration design, minimizing risk, and ensuring a smooth transition to OCI Native Compute Instances. This phase should include:

- **Right-Sizing & Capacity Planning** – Assess CPU, memory, and storage utilization to define the required OCI compute shape and storage architecture (OCI Block Volumes). Consider current utilization and growth factors. OCM provides automated recommendations based on AWS CloudWatch performance metrics.
- **Network & Security Planning** – Validate OCI networking design, including VCNs, subnets, and security lists/NSGs. Map AWS security groups to OCI security lists and network security groups. Plan for IP remapping and DNS updates.
- **Testing & Validation** – Conduct pilot migrations for representative workloads before executing large-scale cutovers. Validate performance, failover, and recovery procedures.

## Migration Considerations

### Format Conversion

AWS EC2 instances use EBS volumes (backed by various formats), which must be converted to OCI-compatible formats during migration. Both OCM and RackWare handle this conversion automatically.

### Networking Changes

Migrating from AWS to OCI Native requires:

- **IP Address Remapping:** EC2 instances will receive new IP addresses in OCI VCNs
- **VPC to VCN Mapping:** AWS VPCs map to OCI VCNs; subnets map to OCI subnets
- **Security Groups:** AWS security groups map to OCI security lists and network security groups (NSGs)
- **DNS Updates:** DNS records must be updated to point to new IP addresses
- **Gateway Configuration:** Internet gateways, NAT gateways, and VPN connections need OCI equivalents
- **Elastic IPs:** AWS Elastic IPs cannot be migrated; plan for new public IP addresses in OCI

### Storage Migration

- **EBS Volumes:** AWS EBS volumes are converted to OCI Block Volumes
- **Instance Store:** Ephemeral instance store volumes are not migrated; ensure data is on EBS
- **Storage Performance:** Map AWS EBS volume types (gp3, io1, io2) to OCI storage performance tiers (Standard, Balanced, High Performance)

### AWS-Specific Considerations

- **Instance Types:** AWS instance types map to OCI compute shapes; OCM provides automated recommendations
- **CloudWatch:** AWS CloudWatch monitoring is replaced with OCI Monitoring service
- **Systems Manager:** AWS Systems Manager agents are replaced with OCI agents
- **Elastic Load Balancers:** AWS ELBs/ALBs need to be replaced with OCI Load Balancers
- **Auto Scaling Groups:** AWS Auto Scaling Groups need to be recreated using OCI Instance pools with Auto Scaling

### Cost Optimization Opportunities

- **Reserved Instances:** AWS Reserved Instances cannot be transferred; OCI provide cost benefits based on Universal Credits volumes, not by locking into a specific service or shape.
- **Spot Instances:** AWS Spot Instances are replaced with OCI Preemptible Instances for cost savings
- **Storage Costs:** OCI Block Storage often provides better price-performance than AWS EBS using flexible Volume Performance Units (VPUs)

## Special Considerations for Enterprise and Mission Critical Databases

While VM-level migration tools (e.g., OCM, RackWare) can handle the majority of workloads, they may not be sufficient for enterprise-scale, mission-critical applications where downtime is unacceptable. For large and transaction-heavy databases, a pure VM-level migration introduces significant challenges due to:
- Database size (terabytes or petabytes).
- Continuous write activity (transaction-heavy workloads).
- The requirement for zero or near-zero downtime.

To migrate such mission critical workloads and RDBMS environments, you might consider dedicated solutions and architectures:

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

