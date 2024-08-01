# Adding a 3rd Network Card to ExaCC Rack

- [Adding a 3rd Network Card requires a Technical Exception.]
- [The 3rd NIC cannot be added to infrastructures already shipped and deployed with only 2 NICs.]
- [3rd NIC will be the same type and speed as the client.]
- [This network card can only be used for DataGuard purposes. Customers will need to provide VIP/Scan IPs/hostnames for this network as well.]
- [Once exception is approved, add it to each SAR that should contain the 3rd NIC. This will trigger adding the required network cards/SFPs (if fiber).]


Please Note: To validate a VMCluster network and effectively configure the 3rd NIC, the DG network default gateway MUST answer (the IPs must be pingable).

# Useful Links

- [Overview](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/overviewIPsec.htm)

- [Steps to create](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/settingupIPsec.htm)

- [Troubleshooting](https://www.ateam-oracle.com/post/oracle-cloud-vpn-connect-troubleshooting)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
