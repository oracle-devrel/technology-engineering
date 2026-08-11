# Preserve Official One-OE and TBAC Role Namespaces

**Goal:** Correct the protected adapter's governance namespace composition so
official One-OE role delegation and official TBAC project roles coexist.

**Architecture:** Keep pinned One-OE, Hub E, and OCI TBAC unchanged.
Deep-merge the two official namespace maps in the existing projection adapter,
then certify the regenerated OP01 governance input.

## Constraints

- Preserve One-OE, Hub E, official TBAC `tn-lzp-proj-role`, Instance
  Principal, and OP00/OP01/OP02/OP04 state boundaries.
- Do not introduce a new role model, compatibility alias, migration, custom
  IAM policy, or hand-edited generated IAM.
- Do not run Terraform locally or publish `OperationsAdvisory-updates2`.

## Steps

1. Prove the regression by generating OP01 from the real certified customer
   configuration and asserting that both namespace keys are present. The
   current shallow merge fails this assertion because it emits only TBAC.
2. Change only the existing `tags_configuration+` composition to deep-merge
   `namespaces+` from the official TBAC governance object.
3. Regenerate OP01 and assert that its governance input has both
   `TAGNS-LZ-ROLE-KEY` and `TAGNS-PROJ-ROLE-KEY`, with no IAM, OP00, OP02,
   Hub E, or project-TBAC changes.
4. Validate the source diff and record it locally without pushing the source
   branch.
5. Release the protected adapter through the approved maintainer path, then
   certify the OP01 governance input. Review a plan that creates only the
   missing standard tag namespace and tag definition.
6. Verify read-only that both namespaces exist, One-OE's standard tags are
   valid, TBAC project tags remain, and OP04 is unchanged.
