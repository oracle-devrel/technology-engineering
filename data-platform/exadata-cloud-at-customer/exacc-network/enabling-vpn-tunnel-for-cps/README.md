# Exadata Cloud@Customer Enabling VPN Tunnel for CPS Connections

A number of customers have expressed a requirement that ALL traffic between the ExaC@C and Oracle be tunnelled using IPSec VPN.

While the actual CPS connection uses secure mTLS web socket secure tunnels, as this does not adhere to the security standards of some customers, it is possible to tunnel these tunnels using standard OCI connectivity methods. 

We can use either IPSec Site to Site VPN or Fastconnect to establish a permanent secure tunnel between the customer DC and OCI. Then we simply route the CPS traffic via this connection. As far as the ExaC@C CPS servers are concerned, it is simply an IP route it uses to get to the Internet and access the OCI services.  It connects and communicates with the OCI Service endpoints in exactly the same way, except that all traffic is routed through the Site to Site VPN tunnel.

If you want to do this, then you must raise a Technical Exception to ensure that Cloud Ops and Engineering are aware of any special setup required.

The first thing the customer needs to do is create a Private VPN Tunnel between their DC and Oracle. The details of this are here: Site-to-Site VPN Overview

Then the VCN needs to be configured with a Service Gateway, which allows the customer internal network to access public Oracle services without going out to the internet. This is described here: Access to Oracle Services: Service Gateway

The list of services is here: Service Gateway Supported Cloud Services

You can see that Exadata Cloud@Customer Gen2 is listed.

All the customer has to do is ensure that this config is in place, and then ensure that the CPS network is routed via the customers CPE for all outgoing traffic. 

End result is that ALL traffic to and from the CPS to Oracle is tunnelled in the VPN.

# Additional Links:

[Overview](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/overviewIPsec.htm)

[Steps to create](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/settingupIPsec.htm)

[Troubleshooting](https://www.ateam-oracle.com/post/oracle-cloud-vpn-connect-troubleshooting)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
