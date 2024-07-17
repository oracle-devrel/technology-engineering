# Block Storage

High-performance block storage at any scale.

We've designed our storage platform as an ideal complement to Oracle compute and networking services to support the highest performance requirements. OCI Block Volume uses the latest NVMe SSDs and provides nonblocking network connectivity to every host. Oracle delivers a consistent, low-latency performance of up to 225 IOPS/GB to a maximum of 300,000 IOPS and 2,680 MB/sec of throughput per volume.

Reviewed: 23.01.2024

# Table of Contents

1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)

# Team Publications

- [OCI provides native high availability and data resilience](https://blogs.oracle.com/cloud-infrastructure/post/oci-provide-cloud-resilience-by-default)
- [Make your cloud resilient against regional outages](https://www.youtube.com/watch?v=IVqLe_XH_AE)
- [Effortless Cloud Resilience – Automate your Disaster Recovery with Oracle Cloud Infrastructure](https://www.youtube.com/watch?v=P3qWyjE9HMQ)
- [Cloud Resilience](https://gitlab.com/hmielimo/cloud-resilience/-/blob/main/doc/cloud.resilience/README.md)
- [Cloud Resilience by default](https://gitlab.com/hmielimo/cloud-resilience-by-default/)
- [OCI Storage Health-Check](https://gitlab.com/hmielimo/oci-storage-health-check/)
- Showcase section
  - [Showcase 1: Demonstrate block volume backup copy to a different region in a customer managed key environment.](https://gitlab.com/hmielimo/cloud-resilience-by-default/-/tree/main/copy.customer.managed.key.backup)
  - [Showcase 2: TRIM showcase](showcase-2)
  - [Showcase 3: boot/block volume security best practice](showcase-3)
  - [Showcase 4: boot/block volume individual (to a customer-managed bucket) backup and restore](showcase-4)
  - [Showcase 5: Shatter the Million IOPS Barrier in the Cloud with OCI Block Storage](https://gitlab.com/hmielimo/next-generation-cloud/-/tree/main/doc/oci.block.storage.plan.and.proof)


# Useful Links

- [OCI Block Storage documentation](https://docs.oracle.com/en-us/iaas/Content/Block/home.htm)
  - Oracle Block Storage documentation.
- Introduction to Oracle Cloud Infrastructure Block Volume [Part 01](https://www.youtube.com/watch?v=rNrBxdDC8vc) and [Part 02](https://www.youtube.com/watch?v=ldZDySWv8sw)
  - Short Videos to introduce Oracle Cloud Infrastructure Block Volume.
- [OCI Block Storage on oracle.com](https://www.oracle.com/cloud/storage/block-volumes/)
  - Oracle Cloud Infrastructure (OCI) Block Volumes provide reliable, high-performance, low-cost block storage. OCI Block Volumes persist beyond the lifespan of a virtual machine, have built-in redundancy, and can scale to 1 PB per compute instance.
- [Blogs on Block Storage](https://blogs.oracle.com/authors/max-verun)
  - See all Block Storage Blogs from Oracle's Product Management.
- [Block Storage Release Notes](https://docs.oracle.com/en-us/iaas/releasenotes/services/blockvolume/)
- [Block Volumes FAQ](https://www.oracle.com/cloud/storage/block-volumes/faq)
- [Migrate Oracle Cloud Infrastructure volume data across tenancies](https://docs.oracle.com/en/solutions/migrate-data-across-tenancies)
  - Migrating data across tenancies can be a challenging task, but with proper planning and by using well-tested processes, you can migrate data from one tenancy to another safely, securely, and with little downtime.
- [Oracle Cloud Infrastructure Vault: Block Volume Encryption](https://www.youtube.com/watch?v=3GBPIx4hlRU)
  - This video helps you to encrypt a block volume with the KMS Vault customer-managed encryption key.

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
