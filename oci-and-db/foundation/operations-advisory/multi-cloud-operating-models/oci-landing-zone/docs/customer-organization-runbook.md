# Customer organization adoption runbook

Use this manual runbook to create a clean OCI Landing Zone foundation in a
different customer GitHub organization.

## Prerequisites

- A private customer GitHub organization, an OCI tenancy in commercial `oc1`,
  and an approved OCI administrator.
- A private foundation runner with its Instance Principal and separate
  foundation/project state buckets, as described in [deployment](deployment.md).
- Git, `jq`, Jsonnet, `rg`, GitHub CLI, and outbound GitHub HTTPS on the
  publication workstation.

## Configure the customer values

1. Copy the reviewed `oci-landing-zone` component into the customer's private
   foundation repository. Keep the reviewed OE `master` SHA in
   `components/oci-landing-zone/scripts/generate_foundation.sh`; do not replace
   it with an unpinned branch fetch.
2. Edit only `components/oci-landing-zone/config/customer.jsonnet` for the
   customer notification address, OCI region, hub CIDR, DEV CIDR, and optional
   Bastion endpoint. Add environments only after their OP02 state exists.
3. Keep `config/projects.json` empty until OP02 for the selected environment
   has completed. Do not hand-edit generated JSON.

## Establish the TBAC foundation

1. Run the reviewed OP00 and OP01 core workflow sequence. When MCCP is hosted
   in this tenancy, complete OP03 infrastructure and identity before DEV OP02;
   the runner dynamic group must exist before OCI compiles OP02 runner policies.
   Then run DEV OP02. Review every plan and apply only after the required human
   approvals.
2. Verify OP01 governance contains namespace `tn-lzp-proj-role` and tag keys
   `proj-admin`, `app-admin`, `db-admin`, and `infra-admin`.
3. Verify OP02 IAM contains the official tag-based policy conditions using
   `request.principal.group.tag` and `target.resource.compartment.tag`.
4. Add one `dev-<project>` catalogue entry, generate its OP04 artifacts, and
   review the root plus Application, Database, and Infrastructure children.
5. After the human-merged OP04 run succeeds, validate the handoff artifact.
   It must be schema 3 and contain four distinct compartment OCIDs: project
   root, App, DB, and Infra.

## Project handoff

Create `nonprod-<project>` only from that validated schema-3 handoff. Project
workloads use the handed-off role-specific target: Compute/App, ADB and ADB
lifecycle/DB, and NSG/Infrastructure. ADB lifecycle manifests include
`database_compartment_id`.

## Local checks before a remote apply

```bash
cd components/oci-landing-zone
./scripts/generate_foundation.sh all
```

The generation command rejects unresolved customer placeholders. Run it only
after replacing them with reviewed values; it generates JSON but never applies
OCI resources.
