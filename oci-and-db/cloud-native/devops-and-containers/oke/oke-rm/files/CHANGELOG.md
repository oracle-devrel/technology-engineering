# OKE Resource Manager 1.4.0

## Changes

- Accept multiple IPv4 CIDRs for control-plane API access and optional external egress in the infrastructure stack.
- Expose both inputs as Resource Manager lists with per-entry IPv4 validation.
- Deduplicate repeated entries and support empty lists without removing internal OKE communication rules.
- Preserve existing API rule state through Terraform moved blocks.
- Upgrade the OCI Terraform provider to 9.2.0 for both infrastructure and OKE stacks. Other provider versions remain unchanged.

## Upgrade Notes

The existing input names remain `cp_allowed_source_cidr` and `cp_egress_cidr`, but their types change from string to list(string). Convert saved scalar values before planning:

```hcl
cp_allowed_source_cidr = ["192.0.2.10/32", "198.51.100.0/24"]
cp_egress_cidr         = ["10.10.0.0/16", "10.20.0.0/16"]
```

Keep the previous CIDR first to retain the existing rule at index zero. Append additional entries where possible; reordering can update indexed rules. Defaults remain `["0.0.0.0/0"]`; restrict access appropriately.

Review the complete plan before upgrading. The Amsterdam repeat plan showed no CIDR-rule drift, but proposed removing tenancy-injected defined tags from 34 resources. That unrelated plan was not applied; this release does not change tag ownership.

## Verification

- Terraform formatting and validation passed for both stacks.
- All 19 native Terraform tests passed: nine infrastructure and ten OKE tests.
- Resource Manager Terraform 1.5 successfully planned and applied both stacks with OCI provider 9.2.0 in eu-amsterdam-1.
- The public-endpoint, VCN-native cluster and its test worker reached ACTIVE.
- Both ingress/return CIDR pairs and both egress CIDRs were verified through OCI, then manually verified by the user.
- Direct kubectl access from the test laptop was blocked/refused on its corporate network; Kubernetes API readiness was not independently verified from that laptop.
- Test cleanup completed successfully: the external node pool, worker instance, boot volume, cluster, all 132 infrastructure resources, and both temporary Resource Manager stacks were removed.

The draft includes `infra.zip` and `oke.zip`. Deploy buttons target this release and become usable after publication.

## SHA-256

```text
3722860407945386b54f985c0acfbeab9beef593b825db2b829079305d6891a9  infra.zip
1e6a97c685e400af44b591ce983a5a1f8733b3e27f9603e90391c615ed88e5d0  oke.zip
```
