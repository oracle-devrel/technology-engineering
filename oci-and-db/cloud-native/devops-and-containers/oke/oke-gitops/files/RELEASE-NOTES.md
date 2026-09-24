# OKE GitOps stack 2.1.1

This patch corrects Resource Manager bootstrap failures and aligns the portable
administration skills with the current repository and credential model.

## Fixes in 2.1.1

- Reject new or reused DevOps projects in the tenancy root before deployment.
- Attach IAM policies at the tenancy root by default, with a configurable
  common ancestor for installations using sibling compartments.
- Keep bootstrap credential Secrets in the DevOps project compartment and
  remove the separate Vault-compartment input.
- Ignore OCI-added dynamic-group schema extensions without ignoring matching rules.
- Replace the unsupported Helm nonce override with ENFORCE_HELM_DEPLOYMENT.
- Remove the deprecated shared-token parameter and fallback. Document exact
  JSON credential examples with OCI-compatible parameter descriptions.
- Omit apps-config, its seed and controller source in cluster_admin scope.
- Manage Flux Operator as a normal platform application through the single
  platform reconciliation root, with a documented existing-installation handoff.
- Update both portable administrator skills with the corrected workflow.

Changing from full application scope to cluster_admin may delete the
Terraform-managed apps-config repository. Existing Git content is preserved;
the Flux ownership migration must be applied separately through Git.

Local validation covers Terraform, credentials command syntax, repository
seeding, skill metadata, and archive integrity. The supplied Resource Manager
log confirms a successful apply of the preceding bootstrap fixes; the final
Flux ownership consolidation has not been applied to a live cluster here.

## Inherited from 2.1.0

This release makes the GitOps stack easier to combine with existing OCI DevOps
delivery workflows while preserving clear Kubernetes object ownership.

## Included

- Create a new OCI DevOps project or reuse an existing project without
  overwriting its project-level settings.
- Select `cluster_admin` or `applications_and_cluster` GitOps scope according
  to the desired ownership boundary.
- Use the configurable `gitops-pipelines` repository alongside other delivery
  systems in a shared OCI DevOps project.
- Preserve cluster-administrator ownership of namespace-scoped infrastructure,
  including quotas and policies inside application namespaces.
- Seed existing repositories safely and expose migration guidance for legacy
  pipeline repository names.
- Validate cross-variable constraints through root checks compatible with the
  Terraform version used by OCI Resource Manager.
- Extend the Argo CD and Flux repository documentation and portable skills for
  hybrid OCI DevOps/GitOps operation.

## Acceptance status

- Terraform, schema, repository seed, documentation, and skill validation
  passed.
- Hybrid OCI DevOps application delivery with Argo CD cluster administration
  was exercised on OKE.
- Karpenter and kube-prometheus were reconciled successfully through GitOps.
- Resource Manager compatibility failures found during the clean-room test
  were converted into regression tests.

The authoritative layout is [REPOSITORY-CONTRACT.md](REPOSITORY-CONTRACT.md).
