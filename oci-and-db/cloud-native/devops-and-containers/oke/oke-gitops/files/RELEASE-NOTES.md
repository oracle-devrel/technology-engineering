# OKE GitOps stack 2.1.0

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
