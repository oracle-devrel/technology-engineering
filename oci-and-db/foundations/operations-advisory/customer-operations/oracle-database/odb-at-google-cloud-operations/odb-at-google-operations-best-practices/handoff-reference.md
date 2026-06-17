# **OD@GCP Module Handoff Reference**

&nbsp;

Last reviewed: 2026-06-02

Welcome to the **OD@GCP Module Handoff Reference**.

This asset is the implementation companion to [Operational Best Practices for Oracle Database@Google Cloud](./README.md). The best-practices document remains the source of truth for control-plane ownership, drift contracts, Day 2 tool selection, and the single-writer rule. This reference focuses only on the normal handoff path from the Google Cloud-side modules to the OCI database layer.

&nbsp;

## **Table of Contents**

[1. Scope](#1-scope)</br>
[2. Recommended Handoff Pattern](#2-recommended-handoff-pattern)</br>
[3. Handoff Contract](#3-handoff-contract)</br>
[4. OCI Database Layer Input](#4-oci-database-layer-input)</br>
[5. Reference Examples](#5-reference-examples)</br>
[6. Post-Handoff Checks](#6-post-handoff-checks)</br>
[7. Common Mistakes](#7-common-mistakes)</br>

&nbsp;

## **1. Scope**

This reference covers the normal handoff path across three long-lived stacks:

1. **Google Cloud networking**: create ODB Network and ODB Subnets with `modules/odb-networking`.
2. **Google Cloud Exadata**: create Cloud Exadata Infrastructure and Cloud VM Cluster with `modules/exadb`.
3. **OCI database layer**: connect the OCI database stack to the VM Cluster OCI OCID and create DB Homes, CDBs/databases, PDBs, and backup configuration when that layer should be managed declaratively.

Patching, upgrades, support procedures, and the declarative Day 2 path for Infrastructure or VM Cluster updates are out of scope here. Those topics are covered in the best-practices document.

&nbsp;

## **2. Recommended Handoff Pattern**

The Google Cloud-side stack creates and publishes identifiers. The OCI-side stack consumes the OCI Cloud VM Cluster OCID.

| STACK | LONG-LIVED OWNER | HANDOFF ROLE |
|---|---|---|
| `01-gcp-networking` | ODB Network and ODB Subnets. | Publishes `gcp_odb_networks_dependency` and `gcp_odb_subnets_dependency`. |
| `02-gcp-exadb` | Cloud Exadata Infrastructure and Cloud VM Cluster identity. | Consumes networking maps and publishes `gcp_cloud_vm_clusters_dependency`. |
| `03-oci-db-layer` | DB Homes, CDBs/databases, PDBs, and database-level backup configuration. | Consumes the OCI Cloud VM Cluster OCID and OCI provider region. |

Use separate Terraform states when there is a clear lifecycle, ownership, permission, change-window, or blast-radius reason. Add a fourth stack only for the optional declarative Day 2 path described in the best-practices document; that stack owns only agreed mutable fields and never resource identity.

&nbsp;

## **3. Handoff Contract**

Publish a small, sanitized handoff contract from the Google Cloud Exadata stack. The `ocid` field is the key value consumed by the OCI database layer and OCI-native tools. The `state` field is useful for wrapper pre-flight validation.

```hcl
gcp_cloud_vm_clusters_dependency = {
  PRIMARY = {
    id    = "projects/<project>/locations/<gcp-region>/cloudVmClusters/<name>"
    ocid  = "ocid1.cloudvmcluster.oc1.<oci-region>.<unique-id>"
    state = "AVAILABLE"
  }
}
```

The OCI provider region is not the Google Cloud region. Derive `oci_region` from the VM Cluster OCID - the fourth dot-separated segment - or resolve it in the orchestration layer. Pass it separately to the OCI provider configuration; do not add it to `gcp_cloud_vm_clusters_dependency`, whose object type accepts only `id`, `name`, `ocid`, and `state`.

Useful evidence fields to capture alongside the OCID include VM Cluster state, OCI compartment ID, OCI region, Google Cloud location, Google Cloud Oracle Database zone, SCAN DNS, listener ports, initial capacity, Grid Infrastructure version, and system version. Do not copy full real outputs into Git or tickets unless they are sanitized.

&nbsp;

## **4. OCI Database Layer Input**

There are two valid input paths for the OCI database layer.

| PATH | POSITION | WHEN TO USE |
|---|---|---|
| **Path A - Direct OCID** | **Recommended** | Use when an orchestration layer already resolves and passes the OCI Cloud VM Cluster OCID directly to the OCI database stack. |
| **Path B - Handoff Wrapper** | **Optional adapter** | Use when no orchestration layer resolves the OCI Cloud VM Cluster OCID before calling the OCI database module, or when the OCI stack should resolve the VM Cluster by logical key. |

In either path, the OCI module requires the OCI Cloud VM Cluster OCID, not the Google Cloud resource name, and the OCI provider region is the region resolved from the OCID.

For **Path A**, pass the resolved OCID directly to the OCI database module, for example `vm_cluster_id = var.vm_cluster_ocid`. In production, this resolution is usually handled by the orchestration layer, such as Terragrunt dependencies, HCP Terraform / Terraform Enterprise workspace outputs, `terraform_remote_state`, or CI/CD pipeline variables/artifacts.

For **Path B**, use the [`oci-dbhome-handoff`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/oci-dbhome-handoff) wrapper. The wrapper accepts `vm_cluster_id` as either a direct OCI Cloud VM Cluster OCID or a lookup key from `gcp_cloud_vm_clusters_dependency`, validates the handoff contract, and forwards the resolved OCI OCID to `exadata-database`.

If the wrapper pattern is used in production, treat it as approved module code: pin it to a validated tag or commit SHA, or promote the wrapper into the customer's approved module repository.

&nbsp;

## **5. Reference Examples**

| REFERENCE | WHAT IT SHOWS |
|---|---|
| [`modules/odb-networking/examples/basic`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/odb-networking/examples/basic) | Standalone networking stack that creates ODB Network and ODB Subnets. |
| [`modules/exadb/examples/cluster`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/cluster) | VM Cluster consumer stack that receives dependency maps from upstream stacks. |
| [`modules/exadb/examples/vision`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/vision) | Single-root example for smaller or vision-style deployments. Larger environments usually use separate states. |
| [`modules/exadb/examples/oci-dbhome-handoff`](https://github.com/oci-landing-zones/terraform-oci-multicloud-google/tree/release-0.2.0/modules/exadb/examples/oci-dbhome-handoff) | Optional wrapper pattern that resolves `vm_cluster_id` from the Google Cloud-side VM Cluster output. |
| [`terraform-oci-modules-exadata/exadata-database`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/v1.1.0/exadata-database) | OCI module for DB Homes, CDBs/databases, PDBs, and database-level backup configuration. |

For production, replace example tags with the release tag or commit SHA validated by the customer.

&nbsp;

## **6. Post-Handoff Checks**

After the database layer is created, and after any OCI-side operation that may affect Terraform-managed or handoff-relevant fields, verify that the ownership contract remains clean:

1. The Google Cloud networking stack still owns only ODB Network and ODB Subnets.
2. The Google Cloud Exadata stack still owns Cloud Exadata Infrastructure and Cloud VM Cluster identity.
3. The OCI database stack owns only DB Homes, CDBs/databases, PDBs, and database-level backup configuration.
4. Expected drift from OCI-side operations matches the owning module's `ignore_changes` contract.
5. Unexpected network, placement, or identity drift remains visible in the owning module plans.
6. Evidence is captured: ticket, operator, work request where applicable, relevant output, plan output, and final state.

&nbsp;

## **7. Common Mistakes**

| MISTAKE | WHY IT IS A PROBLEM |
|---|---|
| Passing the Google Cloud resource name as `vm_cluster_id`. | The OCI module requires the OCI Cloud VM Cluster OCID. |
| Assuming the Google Cloud region is the OCI provider region. | Use the OCI region derived from the VM Cluster OCID. |
| Adding `oci_region` to `gcp_cloud_vm_clusters_dependency`. | The dependency map accepts only `id`, `name`, `ocid`, and `state`; pass `oci_region` separately. |
| Using lowercase keys with the handoff wrapper. | Wrapper keys must be uppercase semantic identifiers such as `PRIMARY` or `DBHOME1`. |
| Importing Infrastructure or VM Cluster into the normal OCI database-layer stack. | It creates a second long-lived owner for resources owned by the Google Cloud-side stack. |
| Using broad `ignore_changes` blocks. | Broad ignores can hide unknown drift. Keep `ignore_changes` narrow and module-owned. |
| Copying full real outputs into Git or tickets. | Outputs can include sensitive identifiers or operational details. Sanitize first. |
| Copying reusable module code into the live configuration repository. | It weakens separation of duties and creates uncontrolled forks. Reference versioned modules instead. |
| Using `ref=main` in executable examples. | The documentation becomes non-reproducible because the default branch can change. Use a pinned tag or commit SHA. |

&nbsp;

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
