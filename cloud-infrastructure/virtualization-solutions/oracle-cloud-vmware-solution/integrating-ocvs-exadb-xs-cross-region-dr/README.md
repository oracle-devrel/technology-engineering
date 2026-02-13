# Integrating OCVS and Oracle Exadata Database Service on Exascale Infrastructure (ExaDB-XS) for Cross-Region Disaster Recovery
A unified, high-performance DR architecture for VMware and Oracle Database workloads.

Reviewed: 13.02.2026

# Introduction
Organizations operating mission-critical applications on VMware often depend on the unmatched performance and reliability of Oracle Database. As they modernize in the cloud, the challenge becomes:

- How do we preserve VMware operational consistency while leveraging Oracle Database platform in OCI?

Oracle Cloud Infrastructure (OCI) addresses this by combining:

- **Oracle Cloud VMware Solution (OCVS)** – a fully customer-controlled VMware SDDC with native vSphere, vSAN, and NSX-T
- **Oracle Exadata Database Service on Exascale Infrastructure (ExaDB-XS)** – leverages Exadata Exascale technology within OCI and is designed to deliver extreme performance, reliability and availability of Exadata with the cost and elasticity benefits of modern clouds
- **Oracle Data Guard** – for real-time cross-region database protection
- **VMware Site Recovery Manager (SRM)** – for automated application disaster recovery

Together, these services deliver a unified, end-to-end DR architecture that maintains VMware consistency while enabling Exadata-grade database resilience.

# Architecture Overview
This cross-region DR topology spans two OCI regions and includes:

- **OCVS clusters** in Region A and Region B
- **Oracle Exadata Database Service on Exascale Infrastructure (ExaDB-XS)** using Data Guard
  - Primary database in Region A
  - Standby database in Region B
- **SRM** orchestrating VMware application recovery
- Secure, low-latency inter-region connectivity via **DRG**, **VCN Peering**, and **NSX-T** networking

This ensures operational consistency for VMware workloads while delivering Exascale-level I/O performance for Oracle Databases.

# Why Oracle Exadata Database Service on Exascale Infrastructure (ExaDB-XS) Aligns Perfectly with OCVS for DR
Oracle Exadata Database Service on Exascale Infrastructure (ExaDB-XS) brings a modern architecture designed to deliver:

## 1. Next-generation Exadata performance
- NVMe-accelerated smart storage
- Low-latency RoCE fabric across the entire platform
- Linear scalability for both OLTP and analytics
- Intelligent offload engines for SQL, storage index, and redo processing
- Cloud elasticity and cost-effectiveness
- AI and analytics acceleration

## 2. Built-in multi-region DR with Data Guard
- Real-time redo apply
- Synchronous (zero-data-loss) or asynchronous modes
- Automated failover using Data Guard Broker

## 3. Perfect integration with OCVS
- Private app–DB connectivity with predictable latency
- No re-engineering or app redesign for VMware workloads
- Seamless failover when paired with SRM orchestration

## 4. Full customer control
- Use any Oracle Database feature or option
- Role transition (Failover/Switchover/Reinstate) and health monitoring via OCI Console
- Consistent operational lifecycle across primary and DR regions

**Result:** The most complete VMware + Oracle Database DR architecture available on any public cloud.

# Database Layer DR: Oracle Data Guard on ExaDB-XS
Data Guard forms the resilient foundation for the database DR stack with:

- Primary ExaDB-XS VM in Region A
- Standby ExaDB-XS VM in Region B
- Synchronous (zero data loss) or asynchronous replication
- Fully managed with OCI Console or Data Guard Broker
- Fast-start failover for automated recovery

During a failure in Region A:

- Standby in Region B promotes to **Primary**
- Database services and endpoints automatically switch
- VMware applications reconnect after SRM recovers the VMs in Region B

# Application Layer DR: VMware Site Recovery Manager (SRM)
SRM orchestrates application-level disaster recovery across OCI regions:

- vSphere Replication protects VM data
- Recovery Plans define VM startup order, dependencies, and network mapping
- NSX-T provides consistent network overlays across regions
- Automated failover and controlled failback
- Non-disruptive DR testing is supported

During a disaster:

- SRM initiates failover
- Applications are restarted on OCVS Region B
- ExaDB-XS Standby database in Region B is now the primary database
- Application-to-database communication resumes automatically

# End-to-End Disaster Recovery Flow
## 1 - Region A becomes unavailable
- Both application and database services are impacted

## 2 - Data Guard promotes ExaDB-XS standby database in Region B to Primary
- Zero data loss (if synchronous)
- Database becomes immediately available

## 3 - SRM triggers recovery plans
- VMs power up in OCVS cluster in Region B
- NSX-T networks map seamlessly

## 4 - Full-stack recovery is achieved
- Applications reconnect to the new ExaDB-XS primary database
- Business operations resume with predictable RTO

# Key Benefits
- Next-generation architecture of Oracle Exadata
- Zero application refactoring for VMware workloads
- Full-stack DR with Data Guard + SRM
- Zero or near-zero RPO depending on sync mode
- Predictable RTO via VMware orchestration
- Secure private connectivity between app and DB tiers
- Operational consistency with on-prem VMware and Exadata

# Conclusion
OCI supports a comprehensive disaster recovery architecture by combining:

- OCVS for VMware-based applications
- ExaDB-XS for Oracle Databases
- Data Guard and SRM for coordinated, cross-region protection

This integration enables a consistent and unified approach to disaster recovery for organizations running Oracle Database and VMware workloads in the cloud.

# License
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
