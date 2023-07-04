#  Peering (LPG, RPC) 

Local VCN peering: is the process of connecting two VCNs in the same region so that their resources can communicate using private IP addresses without routing the traffic over the internet or through your on-premises network this process is achieved via LPG Gateways

Remote VCN peering is the process of connecting two VCNs in different regions (but the same tenancy ). The peering allows the VCNs' resources to communicate using private IP addresses without routing the traffic over the internet or through your on-premises network, RPC requires 2 DRG instances (one for each region see pic below), customer can also use RPC  to peer different tenants in the same region peering the DRGs.


## When to use this asset?
These documents can be use as reusable assets on different technologies around OCI regarding Secure Edge Connectivity

## How to use this asset?
The information is generic in nature and not specified for a particular customer. Appropriate changes in scope should be updated.


# Table of Contents
 
1. [Useful Links](#useful-links)
2. [Team Publications](#team-publications)
3. [Reusable Assets Overview](#reusable-assets-overviewdef)
 
## Useful Links

- [RPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/remoteVCNpeering.htm#Remote_VCN_Peering_Across_Regions)
- [LPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/localVCNpeering.htm)
## Team Publications

### Reference Architectures & Step-by-step Guides
- [asdas](ha-dr-patterns/files/HA%26DR%20Patterns%20in%20Network%20connectivity.pdf)

### Blogs
 



### Videos & Podcasts



# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
