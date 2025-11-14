# Multi-Cluster OpenShift on OCI: Implementing Shared and Unique Domain Architectures
This repository provides architectural guidance for implementing a common base domain across multiple OpenShift Container Platform (OCP) clusters in Oracle Cloud Infrastructure (OCI). Designed for customers requiring unified DNS naming while maintaining cluster isolation. 

Reviewed: 12.11.2025

# When to use this asset?
Use this guide when:
- Deploying multiple OCP clusters across OCI regions
- Requring shared base domains
- Evaluating VCN architecture (single vs dedicated per cluster)
- DNS conditional forwarding
  
# Instructions for Utilizing This Asset
Follow this document as a design principles when using common and unique base domain names for your multiple OpenShift cluster in OCI regions. 


# Conclusion
The OpenShift implementation on OCI relies on DNS Zones for cluster access. This document provides guidance on deploying OCP clusters using dedicated VCNs, with the option to assign either cluster-specific subdomains or unique base domains for more efficient DNS management.

# License
Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.

