#  Peering (LPG, RPC) 

Local VCN peering: is the process of connecting two VCNs in the same region so that their resources can communicate using private IP addresses without routing the traffic over the internet or through your on-premises network this process is achieved via LPG Gateways

Remote VCN peering is the process of connecting two VCNs in different regions (but with the same tenancy ). The peering allows the VCNs' resources to communicate using private IP addresses without routing the traffic over the internet or through your on-premises network. RPC requires 2 DRG instances (one for each region see pic below). The customer can also use RPC  to peer different tenants in the same region peering the DRGs.


# Table of Contents
 
1. [Useful Links](#useful-links)
2. [Team Publications](#team-publications)
3. [Reusable Assets Overview](#reusable-assets-overviewdef)
 
## Useful Links

- [RPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/remoteVCNpeering.htm#Remote_VCN_Peering_Across_Regions)
- [LPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/localVCNpeering.htm)
## Team Publications

### Reference Architectures & Step-by-step Guides


### Blogs
 

### Videos & Podcasts

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
