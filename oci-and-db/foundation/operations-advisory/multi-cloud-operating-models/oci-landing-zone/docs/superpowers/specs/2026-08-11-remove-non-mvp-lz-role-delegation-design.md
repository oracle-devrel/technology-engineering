# Preserve official One-OE and TBAC role namespaces

## Decision

Keep the official One-OE Landing Zone role delegation and the official OCI
TBAC project-role add-on. They have separate purposes and must coexist in the
MVP. The Instance Principal GitOps runner remains the foundation operator.

## Evidence

- The pinned OE source is `dab13856ba6701c45baafc163780bb76562c039a`.
- One-OE emits `tagns-lz-role.tag-lz-role` on the shared Network and Security
  compartments and the corresponding standard administrator groups/policies.
- The OCI TBAC add-on emits the separate `tn-lzp-proj-role` namespace for
  project roles; OP04 depends on that namespace.
- The protected adapter shallow-merged the two `namespaces` maps, causing the
  TBAC map to replace One-OE's map. OCI then rejected the One-OE compartment
  tags because `tagns-lz-role` did not exist.
- The pinned OE source has no supported customer configuration switch that
  disables its Landing Zone role delegation.

## Target state

- OP01 governance emits both `TAGNS-LZ-ROLE-KEY` (`tagns-lz-role`) and
  `TAGNS-PROJ-ROLE-KEY` (`tn-lzp-proj-role`).
- One-OE shared-compartment tags, policies, and groups remain standard.
- TBAC project tags, policies, project groups, One-OE, and Hub E remain
  unchanged.

## Delivery order

1. Correct the protected adapter's namespace merge.
2. Regenerate and certify OP01 governance. The only OCI resource addition is
   the missing standard `tagns-lz-role` namespace and tag definition.

There is no compatibility layer, manual edit of generated IAM, overlay, or
alternative role model.
