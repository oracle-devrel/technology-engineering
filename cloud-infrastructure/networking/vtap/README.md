#  Virtual Test Access Points (VTAP) 

A Virtual Test Access Point (VTAP) provides a way to mirror traffic from a designated source to a selected target to facilitate troubleshooting, security analysis, and data monitoring. The VTAP uses a capture filter, which contains a set of rules governing what traffic a VTAP mirrors. A VTAP is STOPPED by default at creation, so you need to click the Start VTAP before it mirrors traffic as intended.

You can create a capture filter while you create a VTAP, or assign an existing capture filter to a new VTAP

VTAP sources can be:

    A single compute instance VNIC in a subnet
    A Load Balancer
    A Database system
    An Exadata VM Cluster
    An Autonomous Database for Analytics and Data Warehousing instance using a private endpoint
    
# Table of Contents
 
1. [Useful Links](#useful-links)
2. [Team Publications](#team-publications)

## Useful Links

- [VTAP Introduction and Setup](https://blogs.oracle.com/cloud-infrastructure/post/announcing-vtap-for-oracle-cloud-infrastructure)
- [Exploring traffic Mirroring with VTAP](https://blogs.oracle.com/cloud-infrastructure/post/explore-traffic-mirroring-vtap-functionality-with-network-and-monitoring-partners-on-oci)
- [Troubleshoot network issues with vTAP and Wireshark](https://docs.oracle.com/en/solutions/oci-network-vtap-wireshark/index.htm)

## Team Publications

### Reference Architectures & Step-by-step Guides

### Blogs
 
### Videos & Podcasts

- [How to monitor and inspect your Network Traffic flow](https://www.youtube.com/watch?v=f29iNJ1paMU)

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
