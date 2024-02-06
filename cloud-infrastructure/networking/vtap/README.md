#  Virtual Test Access Points (VTAP) 

A Virtual Test Access Point (VTAP) provides a way to mirror traffic from a designated source to a selected target to facilitate troubleshooting, security analysis, and data monitoring. The VTAP uses a capture filter, which contains a set of rules governing what traffic a VTAP mirrors. A VTAP is STOPPED by default at creation, so you need to click the Start VTAP before it mirrors traffic as intended.

You can create a capture filter while you create a VTAP, or assign an existing capture filter to a new VTAP.

VTAP sources can be:

- A single compute instance VNIC in a subnet
- A Load Balancer
- A Database system
- An Exadata VM Cluster
- An Autonomous Database for Analytics and Data Warehousing instance using a private endpoint

Reviewed: 06.02.2024

# Useful Links

- [VTAP Introduction and Setup](https://blogs.oracle.com/cloud-infrastructure/post/announcing-vtap-for-oracle-cloud-infrastructure)
- [Exploring traffic Mirroring with VTAP](https://blogs.oracle.com/cloud-infrastructure/post/explore-traffic-mirroring-vtap-functionality-with-network-and-monitoring-partners-on-oci)
- [Troubleshoot network issues with vTAP and Wireshark](https://docs.oracle.com/en/solutions/oci-network-vtap-wireshark/index.htm)

## Reference Architectures & Step-by-step Guides

 -[Troubleshoot Step by step network issues with VTAP for OCI and Wireshark](https://docs.oracle.com/en/solutions/oci-network-vtap-wireshark/index.html#GUID-3196621D-12EB-470A-982C-4F7F6F3723EC)

## Blogs

 - [Announcing VTAP for Oracle Cloud Infrastructure](https://blogs.oracle.com/cloud-infrastructure/post/announcing-vtap-for-oracle-cloud-infrastructure)
 
 - [Explore traffic mirroring VTAP functionality with network and monitoring partners on OCI ](https://blogs.oracle.com/cloudmarketplace/post/explore-traffic-mirroring-vtap-functionality-with-network-and-monitoring-partners-on-oci)

## Videos & Podcasts

- [How to monitor and inspect your Network Traffic flow](https://www.youtube.com/watch?v=f29iNJ1paMU)
- [Perform Live Traffic Analysis with Wireshark and VTAP on OCI](https://www.youtube.com/watch?v=7nWY_8BjJis)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
