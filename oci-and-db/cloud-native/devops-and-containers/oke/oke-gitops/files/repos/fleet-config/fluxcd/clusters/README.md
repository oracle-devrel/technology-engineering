# Cluster activation roots

Resource Manager generates a directory only for the selected primary member.
Administrators create one directory for each additional cluster when they
onboard it manually. Each root contains only local Flux `Kustomization`
objects selecting reusable profiles.

```text
clusters/oke-2/
  kustomization.yml
  flux-operator.yml
  common.yml
  development.yml
```

Adding or removing a profile file changes only that cluster. A profile may be
shared by many roots or dedicated to a single cluster, for example
`profiles/oke-2-specific/`.

The generated primary root activates `common`. A typical development member
also activates `flux-operator` for self-management and `development` for the
reference applications. See [Add another Flux member](../docs/add-member.md).
