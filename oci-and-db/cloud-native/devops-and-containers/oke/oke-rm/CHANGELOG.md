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

## 2026-08-24

### Changed

- Upgraded `oracle-terraform-modules/oke/oci` from `5.5.0` to `5.5.1`.

### Fixed

- Ensured the IAM policy for a customer-managed OKE cluster encryption key is created before the cluster.

## 2026-07-01

### Changed

- OKE-managed worker node pools now default to Oracle Linux 9 images.

## 2026-06-30

### Added

- Added outputs that simplify passing network resources from the infrastructure stack to the OKE stack, including VCN, subnet, and NSG OCIDs.
- Added database and messaging outputs, including database-side NSGs, client NSGs, and the OCI Streaming NSG.
- Added `create_database_nsgs` to control the creation of database NSGs and corresponding pod or worker rules. Resources are created only when this option is enabled and at least one database service is selected.
- Added a custom worker hostname cloud-init example for Kubernetes 1.32 and later. The example also expands the boot volume with `oci-growfs`.
- Added a disabled-by-default managed node pool example using Generic VNIC Attachments (GVA), including a secondary VNIC profile and Application Resource.

### Changed

- Upgraded the OCI Terraform provider from `8.1.0` to `8.19.0` in both stacks.
- Upgraded `oracle-terraform-modules/oke/oci` from `5.4.3` to `5.5.0`.
- Added Terraform dependency lock files to provide reproducible provider selections.
- Renamed `cloud-init/oca.yml` to `cloud-init/storage.yml` and updated its example reference.
- Reorganized the infrastructure stack interface into separate **Database** and **Messaging** sections.
- Made the database service selector and separate-NSG option visible only when database NSG creation is enabled.
- Disabled the CoreDNS Terraform override by default. It can still be enabled when the required worker capacity is available.
- Clarified the infrastructure stack's two deployment modes:
  - Create and manage a new VCN and its network resources.
  - Deploy supported network configuration on an existing VCN.
  - Create the applicable OKE NSGs in either mode.

### Fixed

- Corrected the KMS vault and key selectors to use `kms_compartment_id`.
- Clarified that customer-managed OKE encryption keys require an IAM policy, either created by the stack or supplied by the customer.
- Included generated KMS statements in the `policy_statements` output.
- Prevented automatic KMS policy resource creation when stack policy creation is disabled.
- Corrected the Karpenter `CLUSTER_JOIN` policy condition syntax.
- Prevented unnecessary updates caused by service-managed identity-domain dynamic resource group attributes.
- Updated external subnet and NSG handling for compatibility with the stricter validation in OKE module 5.5.0.
- Explicitly constrained the OKE wrapper to `oke_ip_families = ["IPv4"]`, matching the stack's current capabilities.
- Corrected Resource Manager output definitions so OCIDs are displayed as copyable values instead of malformed resource paths.
- Exposed database and messaging subnet and NSG outputs in the Resource Manager UI.
