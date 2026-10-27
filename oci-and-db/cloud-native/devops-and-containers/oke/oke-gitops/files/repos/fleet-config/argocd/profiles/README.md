# Reusable profile objects

Each child directory is one reusable umbrella profile. A profile may own one
`cluster-resources/kustomization.yml` and many application payloads below
`applications/<application>/`: Kustomize resources, ordered Helm values, a
Git-hosted chart, or a composition of these. It does not select clusters and
does not deploy by itself.

Point a cluster's singleton `clusterResourcesPath` at the selected profile's
cluster-resource root. Bind the required namespaced or Helm payloads with
descriptors under:

```text
clusters/<cluster>/applications/<binding>/
```

The descriptor names the cluster and references a path below
`profiles/<profile>/applications/`. This keeps a complete reusable
configuration set together while making every workload assignment explicit.

Profiles are not required to be shared. A profile such as
`profiles/oke-2-specific/` may be dedicated to one cluster and may contain that
cluster's complete cluster-resource root, application resources, charts, and
values. Use a dedicated profile for all cluster-specific configuration,
including a small exception, so every payload follows the same model.

For an environment-aware application, keep administrator-owned prerequisites
under `applications/<application>/infrastructure/`. The cluster's corresponding
logical application folder points its wave `-10` child there and points wave `0`
component Applications to `apps-config` through one ApplicationSet.
