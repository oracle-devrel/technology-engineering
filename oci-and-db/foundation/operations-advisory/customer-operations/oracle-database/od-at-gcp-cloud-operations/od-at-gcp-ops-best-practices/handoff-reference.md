# OD@GCP Exadata Module Handoff Reference

&nbsp;

Last reviewed: 2026-06-18 (module wiring verified against source code; OCID and OCI region handling verified against Google and Oracle documentation)

This document is the implementation companion to [Operational Best Practices for Oracle Database@Google Cloud Exadata Database Service](./README.md). It answers one practical question: how does the Google Cloud-created OD@GCP Exadata VM Cluster become input to the OCI Exadata operating stack?

For ownership rules, drift handling, Day 2 tool selection, and the single-writer model, use the README as the source of truth. This file stays focused on the handoff from [`terraform-oci-multicloud-google`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google) to [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database).

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

1. **Google Cloud networking** creates ODB Network and ODB Subnets with [`modules/odb-networking`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/odb-networking).
2. **Google Cloud Exadata** creates Cloud Exadata Infrastructure and Cloud VM Cluster with [`modules/exadb`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb), then publishes the OCI VM Cluster OCID.
3. **OCI Exadata operations** connect [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database) to that OCID and manage the OCI-side declarative layer: DB Homes, CDBs/databases, PDBs, database-level backup configuration, and OCI-side fields explicitly assigned to that state.

Patching, upgrades, refreshable clone maintenance, [ODyS](../../scaling/exacc-exacs-dynamic-scaling/README.md) for Dynamic Scaling / OCPU cost-optimization, restore/recovery, Data Guard actions, support procedures, and other procedural workflows are intentionally out of scope. Use the README for those tooling decisions.

&nbsp;

## 2. Recommended Handoff Pattern

The contract is small: Google Cloud publishes identity; OCI consumes identity.

The Google Cloud stack creates OD@GCP Exadata resources and publishes the OCI VM Cluster OCID. The OCI Exadata stack consumes that OCID, together with the OCI provider region. The Google Cloud stack is not an OCI operations engine; it creates Google Cloud-owned Exadata resources, publishes identity, and absorbs expected OCI-side drift through narrow `ignore_changes`.

| STACK | LONG-LIVED OWNER | HANDOFF ROLE |
|---|---|---|
| Google Cloud networking | ODB Network and ODB Subnets. | Publishes `gcp_odb_networks` and `gcp_odb_subnets`; downstream stacks can pass them as `gcp_odb_networks_dependency` and `gcp_odb_subnets_dependency`. |
| Google Cloud Exadata | Cloud Exadata Infrastructure and Cloud VM Cluster identity. | Consumes ODB Network and ODB Subnet dependency maps, and publishes `gcp_cloud_exadata_infrastructures` and `gcp_cloud_vm_clusters`. |
| OCI Exadata operations | DB Homes, CDBs/databases, PDBs, database-level backup configuration, and OCI-side fields explicitly assigned to the OCI Exadata module. | Consumes the OCI Cloud VM Cluster OCID and the OCI provider region, either directly or through the optional handoff wrapper. |

Use separate Terraform states only when lifecycle, ownership, permissions, change windows, or blast radius justify it. If the OCI Exadata module maintains OCI-side fields on Infrastructure or VM Cluster resources created from Google Cloud, those fields need one explicit OCI writer and matching narrow `ignore_changes` coverage on the Google Cloud side.

Unlike the OD@Azure reference modules, the OD@GCP reference modules publish map-shaped outputs. The normal handoff is either a direct OCID taken from `gcp_cloud_vm_clusters[<key>].ocid`, or a sanitized dependency map consumed by the optional `oci-dbhome-handoff` wrapper.

&nbsp;

## 3. Handoff Contract

The handoff value is the OCI Cloud VM Cluster OCID. The Google Cloud Exadata module exports VM Cluster outputs as a map:

```hcl
output "gcp_cloud_vm_clusters" {
  description = "Created Exadata VM clusters, keyed by input key."
  value       = var.enable_output ? local.gcp_cloud_vm_clusters_output : null
}
```

The VM Cluster output includes the Google Cloud resource identity, OCI OCID, state, placement, and operational evidence fields. A root module or wrapper stack can re-export a small sanitized contract for downstream consumers:

```hcl
output "gcp_cloud_vm_clusters_dependency" {
  value = {
    for key, cluster in module.exadb.gcp_cloud_vm_clusters : key => {
      id    = cluster.id
      name  = cluster.name
      ocid  = cluster.ocid
      state = cluster.state
    }
  }
}
```

A downstream handoff object should stay small:

```hcl
gcp_cloud_vm_clusters_dependency = {
  PRIMARY = {
    id    = "projects/<project>/locations/<gcp-region>/cloudVmClusters/<name>"
    name  = "<name>"
    ocid  = "ocid1.cloudvmcluster.oc1.<oci-region-segment>.<unique-id>"
    state = "AVAILABLE"
  }
}
```

The OCI Exadata module ultimately consumes the OCID. Pass the same OCID as `vm_cluster_id` when defining DB Homes or other OCI-side resources that attach to the existing VM Cluster. The module accepts a direct OCID for the handoff path and does not need to create a new VM Cluster.

In this guide, DB Homes, CDBs/databases, PDBs, backup configuration, and creation-time DB software image selection belong to [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database).

The OCI provider region is a separate input. It is not a Google Cloud location, and it should not be copied blindly from the OCID text. The OCI provider expects a region name such as `us-ashburn-1`, not a region key such as `iad`.

Resolve the OCI provider region in the orchestration layer. If only the OCID is available, resolve its region segment through an approved region-key mapping and validate the result before using it in the OCI provider. Do not add `oci_region` to `gcp_cloud_vm_clusters_dependency`; the wrapper contract accepts `id`, `name`, `ocid`, and `state`.

Useful evidence fields to capture alongside the OCID include VM Cluster state, OCI compartment ID, OCI region, Google Cloud project, Google Cloud location, Google Cloud Oracle Database zone, ODB Network, ODB Subnets, SCAN DNS, listener ports, Grid Infrastructure version, and system version. Sanitize real outputs before copying them into Git or tickets.

&nbsp;

## 4. OCI Exadata Module Input

The recommended OCI-side module for this operating model is [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database). It consumes the OCI Cloud VM Cluster OCID, not a Google Cloud resource name, and the OCI provider region must be supplied separately as a validated OCI region name.

| MODULE | POSITION | WHEN TO USE |
|---|---|---|
| **`terraform-oci-modules-exadata/exadata-database`** | **Recommended OCI operating module** | Use for the OCI-side declarative layer: DB Homes, CDBs/databases, PDBs, database-level backup configuration, creation-time DB software image selection, and OCI-side Infrastructure or VM Cluster fields explicitly assigned to the OCI Exadata state. |
| **`modules/exadb/examples/oci-dbhome-handoff`** | **Optional adapter** | Use when the OCI stack should resolve `vm_cluster_id` from either a direct OCI Cloud VM Cluster OCID or a key in `gcp_cloud_vm_clusters_dependency` before calling the OCI Exadata module. |

For the **`exadata-database`** module, the DB Home definition accepts `vm_cluster_id` as either a direct OCI Cloud VM Cluster OCID (the module detects values matching `^ocid1\.`) or a logical key referencing a VM Cluster created within the same module. For OD@GCP, pass the resolved OCID directly when the orchestration layer already has it.

For the **`oci-dbhome-handoff`** wrapper, `vm_cluster_id` can be a direct OCI Cloud VM Cluster OCID or a key from `gcp_cloud_vm_clusters_dependency`. The wrapper validates the handoff shape, requires referenced VM Cluster dependencies to be `AVAILABLE`, resolves the OCI OCID, and forwards that OCID to `exadata-database`.

Use the module lifecycle contract to decide the execution tool. In `v1.1.0`, DB Home `db_version` and `database_software_image_id` are ignored after creation; CDB `db_home_id`, `db_version`, and admin password are ignored; and PDB container/password fields are ignored. Those ignored fields are not Terraform update paths. Database patching should be treated as an out-of-place DB Home workflow; password work, refreshable clone operations, restore/recovery, and [ODyS](../../scaling/exacc-exacs-dynamic-scaling/README.md) should use the Day 2 tooling described in the README.

In production, OCID resolution usually happens in the orchestration layer: Terragrunt dependencies, HCP Terraform / Terraform Enterprise workspace outputs, `terraform_remote_state`, or CI/CD pipeline variables and artifacts. If the wrapper pattern is used in production, treat it as approved module code: pin it to a validated tag or commit SHA, or promote the wrapper into the customer's approved module repository.

&nbsp;

## 5. Reference Examples

| REFERENCE | WHAT IT SHOWS |
|---|---|
| [`modules/odb-networking/examples/basic`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/odb-networking/examples/basic) | Standalone networking stack that creates ODB Network and ODB Subnets. |
| [`modules/exadb/examples/cluster`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/cluster) | VM Cluster consumer stack that receives dependency maps from upstream stacks. |
| [`modules/exadb/examples/vision`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/vision) | Single-root example for smaller or vision-style deployments. Larger environments usually use separate states. |
| [`modules/exadb/examples/oci-dbhome-handoff`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/oci-dbhome-handoff) | Optional wrapper pattern that resolves `vm_cluster_id` from the Google Cloud-side VM Cluster output map or a direct OCI OCID. |
| [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database) | Richer OCI module for DB Homes, CDBs/databases, PDBs, and database-level backup configuration; accepts `vm_cluster_id` as a direct OCID for the handoff path. |

For production, replace example source references with customer-validated, pinned revisions. Re-validate the selected Google Cloud-side module revision before using it in customer deployments, and use the pinned OCI Exadata module revision as the source of truth for OCI-side lifecycle behavior.

&nbsp;

## 6. Post-Handoff Checks

After creating the OCI Exadata layer, and after any OCI-side operation that may affect Terraform-managed or handoff-relevant fields, verify the contract:

1. The Google Cloud networking stack still owns only ODB Network and ODB Subnets.
2. The Google Cloud Exadata stack still owns Cloud Exadata Infrastructure and Cloud VM Cluster identity.
3. The OCI Exadata stack owns only the OCI-side fields explicitly modeled and intended for declarative ownership.
4. Expected drift from OCI-side operations matches the owning module's `ignore_changes` contract.
5. Unexpected network, placement, or identity drift remains visible in the owning module plans.
6. Evidence is captured: ticket, operator, work request where applicable, relevant output, plan output, and final state.

&nbsp;

## 7. Common Mistakes

| MISTAKE | WHY IT IS A PROBLEM |
|---|---|
| Passing a Google Cloud resource name as `vm_cluster_id`. | The OCI module requires the OCI Cloud VM Cluster OCID, not the Google Cloud resource name. |
| Assuming the Google Cloud location is the OCI provider region. | Use a validated OCI provider region resolved in the orchestration layer. Google Cloud locations and OCI provider regions are different naming systems. |
| Passing a raw OCID region key as the provider region. | OCIDs may contain region keys such as `iad`; the OCI provider/module expects a valid OCI region name such as `us-ashburn-1`. Map and validate before use. |
| Adding `oci_region` to `gcp_cloud_vm_clusters_dependency`. | The wrapper dependency map accepts `id`, `name`, `ocid`, and `state`; pass `oci_region` separately. |
| Passing a wrapper key that is not present in `gcp_cloud_vm_clusters_dependency`. | The wrapper can resolve only a direct OCID or an existing dependency-map key. |
| Using a Google Cloud-side example as the database operating module. | The Google Cloud stack publishes the VM Cluster OCID. DB Homes, CDBs/databases, PDBs, backup configuration, and DB software image selection belong to the OCI Exadata module in this operating model. |
| Using the Google Cloud module to perform OCI operations. | The Google Cloud module creates and publishes Google Cloud-owned OD@GCP resources. OCI operations belong to the OCI Exadata module or OCI-native tooling. |
| Importing Infrastructure or VM Cluster into an OCI state without a single-writer plan. | It can create a second long-lived owner for resources created by the Google Cloud-side stack. Import only when the OCI Exadata state explicitly owns the selected OCI-side fields and the Google Cloud-side `ignore_changes` coverage matches. |
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
