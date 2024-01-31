# Fast Connect Reusable Assets

OCI FastConnect allows customers to connect from their on-premises data centers to their OCI virtual cloud networks (VCNs) through dedicated, private, high-speed connections. FastConnect offers multiple high-bandwidth options and different connectivity models using OCI FastConnect partners like Colt, Equinix, Megaport and others or direct connections when colocating in the same data center facility. FastConnect provides a more reliable and consistent networking experience when compared to any internet-based communication like IPSec VPNs. There are three FastConnect options to choose from Oracle Provider : provider or carrier has already established connectivity with OCI at the FastConnect DCs. The provider has established a network-to-network interface (NNI) between the provider’s network and OCI. The NNI is a SHARED connection that can be used by multiple customers separated by virtual circuits. Third-Party Provider: typically works with a provider or carrier that has a good relation with or is the current MPLS or backbone network provider. The customer will place an order with  the provider to deliver a private dedicated circuit to connect on-prem to OCI and Colocation: customer’s DC is located at the same physical DC as the FastConnect DC location. To deploy FastConnect, the customer requests a cross connect from the its cage to the Oracle cage.
Use Case

    Private peering: To extend your existing infrastructure into a virtual cloud network (VCN) in Oracle Cloud Infrastructure (for example, to implement a hybrid cloud, or a lift and shift scenario). Communication across the connection is with IPv4 private addresses (typically RFC 1918).
    Public peering: To access public services in Oracle Cloud Infrastructure without using the internet. For example, Object Storage, the Oracle Cloud Infrastructure Console and APIs, or public load balancers in your VCN



## Useful Links
- [OCI Fastconnect Partners](https://www.oracle.com/it/cloud/networking/fastconnect/providers/)
- [Fastconnect troubleshooting](https://www.ateam-oracle.com/post/fastconnect-troubleshooting)
- [Price list](https://www.oracle.com/cloud/price-list/#fastconnect)
- [FastConnect Step by Step Interactive To Setup FastConnect Partner Mode](http://docs.hol.vmware.com/hol-isim/hol-2021/hol-isim-player.htm?isim=hol-2296-01-ism_connecting_to_on-premises_environment.json)
- [FastConnect providers by Region](https://www.oracle.com/it/cloud/networking/fastconnect/providers/)

## Team Publications

### Reference Architectures & Step-by-step Guides

 - [FastConnect Provisioning Partner Mode Equinix:](https://www.youtube.com/watch?v=TezGaTjXxKQ)
 - [FastConnect Full Video for Partner Mode, Colo and 3rd Parties, part 1](https://www.youtube.com/watch?v=nI0J4RSpCCA)
 - [FastConnect Full Video for Partner Mode, Colo and 3rd Parties, part 2](https://www.youtube.com/watch?v=nI0J4RSpCCA)
 


## Reusable assets overview

 
### Blogs
 - [OCI Fastconnect integration with COLT](https://blogs.oracle.com/cloud-infrastructure/post/oracle-cloud-infrastructure-fastconnect-integration-with-colt) 



### Videos & Podcasts



# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
