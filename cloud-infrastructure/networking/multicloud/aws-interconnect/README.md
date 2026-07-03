# AWS Interconnect (Public Limited Availability)
 
Oracle Interconnect for AWS provides private, low-latency & reliable connectivity between OCI and AWS over their private backbones(bypassing the public internet and third party NSPs) to deliver predictable performance, high availability, and resilient cross-cloud networking

The goal is to let customers establish multi-cloud transport between AWS and OCI regions using a simplified provider-coordinated workflow that reduces manual provider-side provisioning steps after the required activation-key handoff between clouds.

From the OCI customer model perspective, the service is represented using the existing Partner FastConnect virtual circuit model, with AWS onboarded as a new provider and new UI support in the Partner VC experience

## Key Benefits

-  Private Layer 3 Connectivity: traffic stays on OCI and AWS private backbones, and bypasses the public internet or any third party NSP.
- High Availability and Resiliency: Oracle Interconnect for AWS follows best practices for maximum resilience. Infrastructure spans multiple network devices across at least two physical facilities with independent power and networking. 
- Predictable performance and lower latency vs. routing through on-prem/third parties/internet overlays.
- High bandwidth options: up to 100 Gbps per connection(5/10/20/50/100 Gbps).
- Simplified operations: no physical cross-connect management in colocation facilities required.
- Cost advantages: you pay port-hour fees; Oracle does notcharge FastConnect outbound data transfer fees, and AWS waives data transfer fees for Oracle Interconnect for AWS traffic
- Collaborative Support Model: Customers can open support tickets with My Oracle Support or AWS Support. Both organizations directly engage to resolve cross-cloud issues.
- Security. Each OCI-AWS Interconnect channel is MACsec-enabled

## Configuration Options

The OCI customer-facing configuration model uses the existing Partner FastConnect virtual circuit. AWS is onboarded as a new provider, and the customer creates the connection through the normal Partner VC experience with new UI support for OCI-AWS Interconnect creation.

The service supports two customer creation journeys that map to the two backend operating modes:

- OCI-Active: the customer starts in AWS, receives an activation key, and then creates an OCI Partner VC using that key. OCI is the backend side that actively drives negotiation.
- AWS-Active: the customer starts in OCI, creates a Partner VC with provider AWS, and then uses the OCI-generated activation key on the AWS side. AWS is the backend side that actively drives negotiation.

Although the two customer journeys start on different clouds, the underlying provider-coordination pattern is symmetric:

- The initiating cloud creates the initial customer-facing resource and activation key
- The accepting cloud validates that activation key and becomes the active negotiator for the shared connection
- Feature guidance and feature creation are performed on a per-channel basis
- OCI and AWS each provision their local network configuration independently
- Both providers exchange final status updates before the connection is considered operational
 
Reviewed: 03.07.2026

# Table of Contents
 
- [Useful Links](#useful-links)
 
# Useful Links
 
- [Oracle and AWS Collaborate to Expand Multicloud Networking](hhttps://www.oracle.com/news/announcement/oracle-and-aws-collaborate-to-expand-multicloud-networking-2026-04-16/)
- [Set Up Oracle Interconnect for AWS from Start to Finish](https://blogs.oracle.com/oracleuniversity/set-up-oracle-interconnect-for-aws-from-start-to-finish?source=:so:li:or:awr:ocl:::SetUpInterconnect&SC=:so:li:or:awr:ocl:::SetUpInterconnect&pcode=)


# License
 
Copyright (c) 2026 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
