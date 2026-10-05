# OKE Resource Manager 1.5.0

## Changes

- Make the default load balancer subnet optional. An empty selection creates the OKE cluster without a default service load balancer subnet; no load balancer is created during cluster provisioning.
- Move disabled managed, GVA, system, and virtual worker-pool examples into the code-configurable `worker_pools` input in `node-pools.tf`. Keep this input hidden in the Resource Manager form.
- Preserve system-node cloud-init and support raw, base64, and bundled-file cloud-init content.
- Validate worker-pool modes, pool sizes, availability-domain selections, managed-node GVA, and virtual-node-only taints.
- Add OpenSearch to the optional database networking configuration. One service NSG permits TCP 9200 (API) and 5601 (Dashboards), with matching stateless return rules and existing shared/dedicated pod or worker client selection.
- Keep managed Data Prepper and OpenTelemetry ingestion outside the OKE provisioning stack.
- Correct Resource Manager policy visibility, tag compartment dependencies, and policy output types.
- Document the private-template installer in OCI Cloud Shell, immediately after the two Deploy to Oracle Cloud buttons.
- Update both deployment buttons to release `oke-rm-1.5.0`.

## Upgrade Notes

Existing LB subnet selections remain valid. If no default is configured, supply the appropriate subnet annotations on Kubernetes LoadBalancer Services when needed.

Existing `worker_pools` stack inputs take precedence over code defaults. Review pool changes carefully: disabling or removing a pool can destroy it. The supplied examples remain disabled by default.

The OpenSearch network feature does not provision OpenSearch. Attach its generated NSG to the service. Existing configurations that used the unreleased OpenTelemetry rules will remove ports 21890, 21891, and 21892 when applied.

Tenancy-injected defined tags can appear as unrelated plan drift. Review them separately; this release does not introduce a tag-ownership policy or the unrelated frontend-rule lifecycle change.

## Verification

- Terraform formatting and validation passed for both stacks. All 47 native tests passed: 14 infrastructure and 33 OKE tests.
- Functional testing in eu-amsterdam-1 created an ACTIVE public-endpoint, VCN-native OKE cluster without a default LB subnet, with managed and system worker pools.
- Resource Manager graphical checks verified the optional LB subnet and code-only worker-pool configuration.
- OpenSearch API and Dashboards connectivity succeeded from an OKE pod after removing all 12 OpenTelemetry-related rules. Both TLS certificates validated: API returned HTTP 401 without credentials; Dashboards returned HTTP 302 to login.
- The test did not validate authenticated search operations or OpenTelemetry ingestion.

## SHA-256

```text
e4ae97befc91d79f2a16a79818adfbdec7a076422103b4924bdb4b486f32580b  infra.zip
7359ea4b8d80fb803679285a3e3bdfa3c467e478f1de2fca59a1e221a78ed234  oke.zip
```

---

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
