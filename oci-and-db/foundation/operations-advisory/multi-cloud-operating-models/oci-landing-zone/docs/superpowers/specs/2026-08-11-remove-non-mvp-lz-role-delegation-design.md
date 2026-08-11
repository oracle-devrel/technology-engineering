# Remove non-MVP Landing Zone role delegation

## Decision

Remove the `tagns-lz-role.tag-lz-role` delegation completely.  The MVP keeps
the official One-OE base, Hub E, and the OCI TBAC add-on, but does not provide
separate human administration of the shared Network and Security compartments.
The Instance Principal GitOps runner remains the foundation operator.

## Evidence

- The pinned OE source is `dab13856ba6701c45baafc163780bb76562c039a`.
- The TBAC add-on emits the separate `tn-lzp-proj-role` namespace for project
  roles; OP04 project onboarding depends on that namespace, not on
  `tagns-lz-role`.
- `op01_manage_landing_zone_environment/generated/governance.json` creates
  only `tn-lzp-proj-role`.
- OP01 nevertheless attempted to add `tagns-lz-role.tag-lz-role` to
  `cmp-lz-network` and `cmp-lz-security` and OCI rejected both updates because
  that namespace does not exist.
- The two associated identity-domain groups have no members.

## Target state

- OP01 no longer emits `tagns-lz-role.tag-lz-role` on shared compartments.
- OP01 no longer manages the two tag-conditioned Landing Zone administrator
  policies.
- OP00 no longer manages the two empty Landing Zone administrator groups.
- TBAC project tags, policies, project groups, One-OE, and Hub E remain
  unchanged.

## Delivery order

1. Certify and apply the OP01 generated IAM change. This removes the invalid
   tag projection and the two policies.
2. After the OP01 apply succeeds, certify and apply the OP00 generated IAM
   change to remove the now-unreferenced empty groups.

There is deliberately no compatibility layer, migration path, or replacement
tag namespace. Reintroducing shared Network or Security human delegation later
is a separately designed feature.
