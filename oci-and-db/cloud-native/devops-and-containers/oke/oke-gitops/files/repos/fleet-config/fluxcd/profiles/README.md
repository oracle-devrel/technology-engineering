# Reusable profiles

Profiles contain local Flux Operator `ResourceSet`, `Kustomization`, source,
and `HelmRelease` definitions. They do not contain cluster selectors or remote
credentials. Cluster roots activate profiles explicitly.

- `common` demonstrates cluster-scoped Kustomize, namespaced Kustomize, and a
  repository Helm chart with ordered values.
- `development` creates infrastructure for the shared Kustomize
  `reference-app` and umbrella Helm `reference-helm-app` catalogs before
  activating independent frontend/dev and api/dev reconciliations.
- `flux-operator` self-manages the mirrored Flux Operator chart on additional
  fleet members. The primary cluster already owns this through
  `cluster-config` and therefore does not activate this profile.
- `advanced` is an inactive, reusable reference for Git-hosted Helm, ordered
  values, Helm plus Kustomize, and External Secrets Operator backed by OCI
  Vault Workload Identity. Its ordered ResourceSet installs and health-checks
  ESO before reconciling `SecretStore` and `ExternalSecret` resources. Replace
  its Vault placeholders before activating it.

A profile dedicated to one member follows the same contract. Name it after
the cluster object, for example `profiles/oke-2-specific/`, and reference it
only from `clusters/oke-2/`.
