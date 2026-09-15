# OD@Azure Exadata Module Handoff Reference

&nbsp;

Last reviewed: 2026-06-18 (module wiring verified against source code; OCID and OCI region handling verified against Microsoft and Oracle documentation)

This document is the implementation companion to [Operational Best Practices for Oracle Database@Azure Exadata Database Service](./README.md). It answers one practical question: how does the Azure-created OD@Azure Exadata VM Cluster become input to the OCI Exadata operating stack?

For ownership rules, drift handling, Day 2 tool selection, and the single-writer model, use the README as the source of truth. This file stays focused on the handoff from [`terraform-oci-multicloud-azure`](https://github.com/oci-landing-zones/terraform-oci-multicloud-azure) to [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database).

&nbsp;

## Table of Contents

1. [Scope](#1-scope)
2. [Recommended Handoff Pattern](#2-recommended-handoff-pattern)
3. [Handoff Contract](#3-handoff-contract)
4. [OCI Exadata Module Input](#4-oci-exadata-module-input)
5. [Reference Examples](#5-reference-examples)
6. [Post-Handoff Checks](#6-post-handoff-checks)
7. [Common Mistakes](#7-common-mistakes)

&nbsp;

## 1. Scope

This reference covers the normal path across three long-lived stacks:

1. **Azure networking** creates the VNet and delegated subnet with a pinned revision of the Azure Verified Module `Azure/avm-res-network-virtualnetwork/azurerm`, or the thin `modules/azure-vnet-subnet` helper.
2. **Azure Exadata** creates Cloud Exadata Infrastructure and Cloud VM Cluster with [`terraform-oci-multicloud-azure`](https://github.com/oci-landing-zones/terraform-oci-multicloud-azure), then publishes the OCI VM Cluster OCID.
3. **OCI Exadata operations** connect [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database) to that OCID and manage the OCI-side declarative layer: DB Homes, CDBs/databases, PDBs, database-level backup configuration, and OCI-side fields explicitly assigned to that state.

Patching, upgrades, refreshable clone maintenance, [ODyS](../../scaling/exacc-exacs-dynamic-scaling/README.md) for Dynamic Scaling / OCPU cost-optimization, restore/recovery, Data Guard actions, support procedures, and other procedural workflows are intentionally out of scope. Use the README for those tooling decisions.

&nbsp;

## 2. Recommended Handoff Pattern

The contract is small: Azure publishes identity; OCI consumes identity.

The Azure stack creates OD@Azure Exadata resources and publishes the OCI VM Cluster OCID. The OCI Exadata stack consumes that OCID, together with the OCI provider region. The Azure stack is not an OCI operations engine; it creates Azure-owned Exadata resources, publishes identity, and absorbs expected OCI-side drift through the selected module's narrow `ignore_changes`.

| STACK | LONG-LIVED OWNER | HANDOFF ROLE |
|---|---|---|
| Azure networking | VNet and delegated subnet (`Oracle.Database/networkAttachments`). | Publishes the VNet resource ID and the delegated subnet resource ID. |
| Azure Exadata | Cloud Exadata Infrastructure and Cloud VM Cluster identity. | Consumes the VNet and subnet IDs, and publishes `vm_cluster_ocid`. |
| OCI Exadata operations | DB Homes, CDBs/databases, PDBs, database-level backup configuration, and OCI-side fields explicitly assigned to the OCI Exadata module. | Consumes the OCI Cloud VM Cluster OCID and the OCI provider region. |

Use separate Terraform states only when lifecycle, ownership, permissions, change windows, or blast radius justify it. If the OCI Exadata module maintains OCI-side fields on Infrastructure or VM Cluster resources created from Azure, those fields need one explicit OCI writer and matching narrow `ignore_changes` coverage on the Azure side.

Do not look for a dependency-map object. Unlike the OD@GCP modules, the OD@Azure reference modules export the VM Cluster OCID directly as `vm_cluster_ocid`, and the handoff is a direct reference.

&nbsp;

## 3. Handoff Contract

The handoff value is the OCI Cloud VM Cluster OCID. The Azure-side combined module exports the OCID directly:

```hcl
output "vm_cluster_ocid" {
  value = azapi_resource.cloudVmCluster.output.properties.ocid
}
```

A root module or wrapper stack can re-export that module output for downstream consumers:

```hcl
output "vm_cluster_ocid" {
  value = module.exa_infra_and_vm_cluster.vm_cluster_ocid
}
```

The OCI Exadata module consumes that value directly. Pass the same OCID as `vm_cluster_id` when defining DB Homes or other OCI-side resources that attach to the existing VM Cluster. The module accepts a direct OCID for the handoff path and does not need to create a new VM Cluster.

In this guide, DB Homes, CDBs/databases, PDBs, backup configuration, and creation-time DB software image selection belong to [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database).

The OCI provider region is a separate input. It is not an Azure location, and it should not be copied blindly from the OCID text. The OCI provider expects a region name such as `us-ashburn-1`, not a region key such as `iad`.

Prefer a validated `oci_region` output from the AzureRM split modules. If only the OCID is available, resolve its region segment through an approved region-key mapping and validate the result before using it in the OCI provider.

If you use the AzureRM split modules (`main` branch) instead of the AzAPI combined module, the VM Cluster module additionally exports OCI-identity outputs (`oci_region`, `oci_compartment_ocid`, `oci_vcn_ocid`, `oci_nsg_ocid`) alongside `vm_cluster_ocid`. In that case, use the validated `oci_region` output instead of parsing the OCID.

Useful evidence fields to capture alongside the OCID include VM Cluster state, OCI compartment ID, OCI region, Azure resource group, SCAN DNS, listener ports, Grid Infrastructure version, and system version. Sanitize real outputs before copying them into Git or tickets.

&nbsp;

## 4. OCI Exadata Module Input

The recommended OCI-side module for this operating model is [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database). It consumes the OCI Cloud VM Cluster OCID, not an Azure resource ID, and the OCI provider region must be supplied separately as a validated OCI region name.

| MODULE | POSITION | WHEN TO USE |
|---|---|---|
| **`terraform-oci-modules-exadata/exadata-database`** | **Recommended OCI operating module** | Use for the OCI-side declarative layer: DB Homes, CDBs/databases, PDBs, database-level backup configuration, creation-time DB software image selection, and OCI-side Infrastructure or VM Cluster fields explicitly assigned to the OCI Exadata state. |

For the **`exadata-database`** module, the DB Home definition accepts `vm_cluster_id` as either a direct OCI Cloud VM Cluster OCID (the module detects values matching `^ocid1\.`) or a logical key referencing a VM Cluster created within the same module. For OD@Azure, pass the resolved OCID directly so the module attaches the DB Home to the existing VM Cluster.

Use the module lifecycle contract to decide the execution tool. In `v1.1.0`, DB Home `db_version` and `database_software_image_id` are ignored after creation; CDB `db_home_id`, `db_version`, and admin password are ignored; and PDB container/password fields are ignored. Those ignored fields are not Terraform update paths. Database patching should be treated as an out-of-place DB Home workflow; password work, refreshable clone operations, restore/recovery, and [ODyS](../../scaling/exacc-exacs-dynamic-scaling/README.md) should use the Day 2 tooling described in the README.

In production, OCID resolution usually happens in the orchestration layer: Terragrunt dependencies, HCP Terraform / Terraform Enterprise workspace outputs, `terraform_remote_state`, or CI/CD pipeline variables and artifacts.

&nbsp;

## 5. Reference Examples

| REFERENCE | WHAT IT SHOWS |
|---|---|
| [`modules/azure-vnet-subnet`](https://github.com/oci-landing-zones/terraform-oci-multicloud-azure/tree/release-0.1.0/modules/azure-vnet-subnet) | Thin helper for the VNet and the subnet delegated to `Oracle.Database/networkAttachments`. The templates use the `Azure/avm-res-network-virtualnetwork/azurerm` Verified Module instead. |
| [`modules/azure-exainfra-vmcluster`](https://github.com/oci-landing-zones/terraform-oci-multicloud-azure/tree/release-0.1.0/modules/azure-exainfra-vmcluster) | AzAPI combined module that creates Cloud Exadata Infrastructure and Cloud VM Cluster and exports `vm_cluster_ocid`. |
| [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database) | Richer OCI module for DB Homes, CDBs/databases, PDBs, and database-level backup configuration; accepts `vm_cluster_id` as a direct OCID for the handoff path. |

For production, replace example source references with customer-validated, pinned revisions. Re-validate the selected Azure-side module revision before using it in customer deployments, and use the pinned OCI Exadata module revision as the source of truth for OCI-side lifecycle behavior.

&nbsp;

## 6. Post-Handoff Checks

After creating the OCI Exadata layer, and after any OCI-side operation that may affect Terraform-managed or handoff-relevant fields, verify the contract:

1. The Azure networking stack still owns only the VNet and the delegated subnet.
2. The Azure Exadata stack still owns Cloud Exadata Infrastructure and Cloud VM Cluster identity.
3. The OCI Exadata stack owns only the OCI-side fields explicitly modeled and intended for declarative ownership.
4. Expected drift from OCI-side operations matches the owning module's `ignore_changes` contract.
5. Unexpected network, placement, or identity drift remains visible in the owning module plans.
6. Evidence is captured: ticket, operator, work request where applicable, relevant output, plan output, and final state.

&nbsp;

## 7. Common Mistakes

| MISTAKE | WHY IT IS A PROBLEM |
|---|---|
| Passing an Azure resource ID as `vm_cluster_ocid`. | The OCI module requires the OCI Cloud VM Cluster OCID, not the Azure resource ID. |
| Assuming the Azure location is the OCI provider region. | Use the validated `oci_region` output when available, or resolve the OCI provider region in the orchestration layer. Azure locations and OCI provider regions are different naming systems. |
| Passing a raw OCID region key as the provider region. | OCIDs may contain region keys such as `iad`; the OCI provider/module expects a valid OCI region name such as `us-ashburn-1`. Map and validate before use. |
| Using an Azure-side example as the database operating module. | The Azure stack publishes the VM Cluster OCID. DB Homes, CDBs/databases, PDBs, backup configuration, and DB software image selection belong to the OCI Exadata module in this operating model. |
| Using the Azure module to perform OCI operations. | The Azure module creates and publishes Azure-owned OD@Azure resources. OCI operations belong to the OCI Exadata module or OCI-native tooling. |
| Importing Infrastructure or VM Cluster into an OCI state without a single-writer plan. | It can create a second long-lived owner for resources created by the Azure stack. Import only when the selected OCI-side fields are explicitly assigned to the OCI Exadata state and the Azure-side `ignore_changes` coverage matches. |
| Treating Dynamic Scaling / OCPU changes as ordinary handoff inputs. | For FinOps, [ODyS](../../scaling/exacc-exacs-dynamic-scaling/README.md) is the Dynamic Scaling app for VM Cluster OCPU capacity: it scales capacity to match workload demand and captures operational evidence. Terraform can own the baseline topology, but it should not be the scheduler or autoscaler. If a Terraform state owns the same OCPU or sizing fields, the next plan will see ODyS scaling as drift and try to return capacity to the configured value unless the state deliberately does not manage those fields or ignores them. |
| Using broad `ignore_changes` blocks. | Broad ignores can hide unknown drift. Keep `ignore_changes` narrow and module-owned. |
| Copying full real outputs into Git or tickets. | Outputs can include sensitive identifiers or operational details. Sanitize first. |
| Copying reusable module code into the live configuration repository. | It weakens separation of duties and creates uncontrolled forks. Reference versioned modules instead. |
| Using `ref=main` in executable examples. | The documentation becomes non-reproducible because the default branch can change. Use a customer-validated pinned revision. |

&nbsp;

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
