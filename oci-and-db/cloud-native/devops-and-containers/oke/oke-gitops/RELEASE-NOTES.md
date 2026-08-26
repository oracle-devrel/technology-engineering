# OKE GitOps stack 2.0.0

This release provides a complete Git-first operating model for administering
OKE with either Argo CD or Flux.

## Included

- One-cluster bootstrap through OCI Resource Manager and OCI DevOps, always
  using the OKE private API endpoint.
- Separate read-only Git and OCIR runtime identities stored in OCI Vault.
- Self-managed Argo CD or Flux Operator after initial installation.
- Cluster-scoped Kustomize, namespaced Kustomize, external/OCI Helm, Git-hosted
  Helm, Helm plus YAML, operator dependency, shared-namespace, and OCI Vault
  External Secrets patterns.
- A controller-neutral developer catalog for Kustomize and umbrella-Helm
  components across `dev`, `staging`, and `production`.
- Native centralized Argo CD fleet delivery and decentralized Flux fleet
  delivery, both behind the optional fleet flag.
- Portable `manage-oke-with-argocd` and `manage-oke-with-flux` skills for local
  AI agents.
- A slim Resource Manager archive containing only deployable stack and seed
  content.

## Acceptance status

- Terraform, YAML, shell, Kustomize, Helm, and skill validation passed.
- Argo CD local and native-fleet use cases were functionally exercised.
- Flux primary and decentralized-member use cases were functionally exercised
  on ARM64 OKE clusters.
- With repository overwrite disabled, a Resource Manager apply preserved all
  four non-empty Git repositories and both Flux clusters remained Ready.

The authoritative layout is [REPOSITORY-CONTRACT.md](REPOSITORY-CONTRACT.md).
