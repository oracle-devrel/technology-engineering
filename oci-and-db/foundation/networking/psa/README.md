# Private Service Access - (PSA)

As organizations expand their cloud adoption, protecting sensitive data while maintaining operational agility has become a top priority. In Oracle Cloud Infrastructure (OCI), the Service Gateway has long enabled private, on-cloud access to the Oracle Service Network (OSN), keeping service traffic off the public internet and within the Oracle network. However, because it allowed access to all OSN services in a region, customers with strict compliance or security mandates often found themselves needing finer control.

They wanted to restrict connectivity to only the services they trust, enforce precise policies that reflect Zero Trust security principles, and protect against risks like data exfiltration or unauthorized service use. They also needed the ability to use private IPs for service endpoints ensuring a stronger security posture without complicating operations.

## What is PSA ?

Think of PSA as your own private door to each Oracle service. You open only the doors you want. When you set up PSA, a private IP from your selected subnet is assigned to the target Oracle service. Private DNS does the wiring, so your existing app logic keeps working (no code changes needed).

Your API traffic now travels a route tailored for privacy and visibility:

- Direct to the service

- Staying on your private network

- Never hitting public IPs (unless you allow it)

## Stronger data protection through controlled private access

With OCI Private Service Access (PSA), customers now gain the control and assurance they’ve been waiting for—private connectivity that is service-specific, policy-aware, and designed to align with Zero Trust security models.

## Quick to Set Up, Easy to Manage

Deploying Private Service Access is quick and simple. You can enable PSA directly from the OCI Console in just a few clicks, and it integrates seamlessly with your VCN.

Reviewed: 03.07.2026

# Useful Links

- [Announcing Private Service Access: Fine-Grained, Private Connectivity for OCI Service Access](https://blogs.oracle.com/cloud-infrastructure/announcing-private-service-access/)
- [Enabling Oracle Linux YUM Service Access using Private Service Access](https://blogs.oracle.com/cloud-infrastructure/yum-access-using-private-service-access)
- [Service Gateway vs Private Endpoint vs Private Service Access in OCI: A Practical Decision Guide](https://www.ateam-oracle.com/service-gateway-vs-private-endpoint-vs-private-service-access-in-oci-a-practical-decision-guide)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
