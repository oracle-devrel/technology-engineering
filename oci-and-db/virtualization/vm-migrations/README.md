# VM Migrations to OCI

This area covers two complementary ways to move virtual machines into Oracle Cloud Infrastructure (OCI) Compute. Choose based on scale, source environment, and how much downtime you can accept during cutover.

Reviewed: 04.11.2026

# Table of Contents

1. [Oracle Cloud Migrations (OCM)](#oracle-cloud-migrations-ocm)
2. [OCI Offline Migration Assistant](#oci-offline-migration-assistant)
3. [License](#license)

# Oracle Cloud Migrations (OCM)

[Oracle Cloud Migrations](./oracle-cloud-migrations/) is the managed OCI service for **large-scale, planned migrations** from supported enterprise and cloud sources. It is built for migration programs: discover workloads, group them into waves, and execute moves with consistent tooling and reporting.

**Best when**

- You are migrating **many VMs** from **VMware vSphere** or **AWS EC2** as part of a datacenter or cloud exit program
- You need **ongoing replication** while source VMs stay running, then a **controlled cutover** with a **short maintenance window** rather than a long outage
- You want a **service-centric** workflow (discovery, replication, cutover, validation) integrated with OCI rather than operating a separate migration appliance for the whole program

OCM uses **delta replication** to sync changes after the initial copy, so cutover can focus on the final sync and switch-over instead of re-copying full disks. That model supports tighter cutover windows for production workloads when the source environment and networking are prepared accordingly.

**Go deeper:** [Oracle Cloud Migrations — publications and reusable assets](./oracle-cloud-migrations/README.md)

# OCI Offline Migration Assistant

The [OCI Offline Migration Assistant](./offline-vm-migrations/) is a **deployable assistant VM** with a web UI for **straightforward, offline-style imports**: connect to a source (or upload disk images), select VMs, and create matching OCI instances. It suits ad hoc moves, pilots, and sources that OCM does not cover, without standing up a full OCM migration project for every workload.

**Best when**

- You want a **quick path** to import **individual VMs or small batches** from **many platforms** (VMware, Hyper-V, OLVM, Nutanix, Proxmox, Azure, AWS, GCP, or OVA/OVF/VMDK/QCOW2 in Object Storage)
- Workloads can be migrated **while powered off** or exported as images (this tool does **not** replace OCM’s live delta replication model)
- You need extras such as **ISO-based installs**, **in-browser Remote Console**, or **export from OCI to OVA/OVF**

**Go deeper:** [OCI Offline Migration Assistant — quick start and documentation](./offline-vm-migrations/README.md)

# Choosing an approach

| | **Oracle Cloud Migrations (OCM)** | **OCI Offline Migration Assistant** |
| --- | --- | --- |
| **Typical scope** | Large programs, many VMs | Single VMs to small sets |
| **Primary sources** | VMware vSphere, AWS EC2 | Many hypervisors and clouds plus manual image import |
| **Replication model** | Initial copy plus **delta sync** for **short cutover windows** | Offline / one-shot import (no live delta sync) |
| **How you operate it** | OCI **Cloud Migrations** service | **Assistant VM** in your tenancy (Resource Manager stack) |

Many customers use **OCM for production VMware and AWS estate moves** and the **Offline Migration Assistant** for other platforms, one-offs, image-based imports, or supporting tools around the same tenancy.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
