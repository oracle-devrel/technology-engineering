# Changelog

This file documents notable user-facing changes to the OCI Resource Manager infrastructure and OKE stacks.

## 2026-09-04

### Added

- Added Terraform input validation for identifiers, CIDRs, supported CNI and cluster types, Kubernetes versions, and dependent configuration.
- Added a Resource Manager security notice for the permissive default control-plane and public bastion network rules.
- Added and linked a detailed network-rules report covering OKE, database, and OCI Streaming NSGs.
- Added automatic least-privilege policies for VCN-native clusters whose worker and network resources are in different compartments.
- Added policy outputs grouped by feature and an inventory of the IAM policy resources created by the stack.
- Added documentation for additional policies that might be required by workload, storage, load balancer, encryption, and advanced node-pool features.
- Added a persistent eight-character per-stack UUID suffix to make generated NSG and gateway names, and Karpenter worker and pod network role tags, unique.
- Added bidirectional FSS rules to the pod and FSS NSGs so Virtual Node pods can connect directly to FSS mount targets when FSS support is enabled.
- Added an `fss_nsg_id` stack output so the generated FSS NSG can be attached directly to mount targets.

### Changed

- Updated the post-install documentation to direct customers to the OKE GitOps Solution or the OKE DevOps Starter.
- Reorganized the README around the infrastructure, cluster, worker-node, and operational workflows, with direct links to the local policy guide and generated network-rules report.
- Reworked the Karpenter guide into a complete installation, configuration, validation, and cleanup workflow aligned with the stack's IAM and networking defaults.
- Limited DRG creation to VCNs created by the infrastructure stack.
- Derived the tenancy home region automatically when creating IAM resources.
- Limited Karpenter policy configuration to enhanced clusters.
- Exposed generated policy statements in the Resource Manager output section.
- Deduplicated Cluster Autoscaler statements when node pools and networking share a compartment while preserving OCI's required policy sets for separate compartments.
- Made the Karpenter namespace and service account configurable for workload identity policies.
- Updated policy dry-run mode so it does not create Karpenter identity resources.

### Fixed

- Decoupled database subnet creation from database NSG and database service selection.
- Prevented Karpenter dynamic-group evaluation when Karpenter policies are not supported by the selected cluster type.
- Added the required Karpenter permission to manage volume attachments.
- Corrected the Karpenter capacity reservation policy to use the `compute-capacity-reservations` resource type.
- Corrected the Karpenter guide to use deterministic network OCIDs, a supported CNI version check, and a safe secondary-VNIC IP count.
