#  Peering (LPG, RPC) 

Local VCN peering: is the process of connecting two VCNs in the same region so that their resources can communicate using private IP addresses without routing the traffic over the internet or through your on-premises network this process is achieved via LPG Gateways.

Remote VCN peering is the process of connecting two VCNs in different regions (but with the same tenancy ). The peering allows the VCNs' resources to communicate using private IP addresses without routing the traffic over the internet or through your on-premises network. RPC requires 2 DRG instances (one for each region see pic below). The customer can also use RPC  to peer different tenants in the same region peering the DRGs.

Reviewed: 10.10.2025

# Useful Links

- [RPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/remoteVCNpeering.htm#Remote_VCN_Peering_Across_Regions)
- [LPC Documentation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/localVCNpeering.htm)
- [Use Terraform to Deploy Multiple Kubernetes Clusters across different OCI Regions using OKE and Create a Full Mesh Network using RPC](https://docs.oracle.com/en/learn/oci-oke-multicluster-k8s-terraform/#introduction)

## Blogs

- [Cloud Infrastructure's VCN Peering Solution ](https://blogs.oracle.com/cloud-infrastructure/post/easily-connect-isolated-networks-using-oracle-cloud-infrastructures-vcn-peering-solution-part-2)
- [LPG inter tenancy](https://www.ateam-oracle.com/post/inter-tenancy-vcn-peering-using-remote-peering-connection)
- [RPC 2 Regions](https://learnoci.cloud/how-to-connect-2-vcns-in-different-regions-using-remote-peering-connection-decac8b9e4de)
- [RPC IAM Policy Tool](https://iwanhoogendoorn.nl/rpc-iam-policy-creator/)

## Videos & Podcasts

- [LPG video tutorial](https://www.youtube.com/watch?v=kO1UlrwffgM)
- [RPC video tutorial](https://www.youtube.com/watch?v=2TOL5tJQ-fU)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
