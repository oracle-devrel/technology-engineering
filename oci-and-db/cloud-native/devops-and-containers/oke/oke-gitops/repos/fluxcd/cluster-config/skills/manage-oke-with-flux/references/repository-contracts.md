# Repository contracts

## Cluster resources

`cluster-config/platform/cluster-resources/` owns both cluster-scoped objects
and every namespaced object rendered into `kube-system`. Put `kube-system`
manifests below `platform/cluster-resources/<group>/` and reference that group
from `platform/cluster-resources/kustomization.yml`, alongside the other
cluster-wide resources.

Never create an application ResourceSet, application infrastructure folder, or
Namespace manifest for `kube-system`. On a decentralized fleet member, apply
the same rule below an activated profile's `cluster-resources/` root rather
than its `applications/` tree.

## Local platform application

Store one logical tool below `cluster-config/platform/applications/<name>/`:

```text
<name>/
  kustomization.yml
  resourceset.yml
  values/{00-base,90-user}.yml   # Helm only; explicit order
  chart/                         # Git-hosted Helm only
  resources/kustomization.yml   # optional related YAML
```

The ResourceSet may create one Namespace, source, HelmRelease, and
Kustomization. Use `GitRepository/flux-system` for cluster-config paths.
Generated controller objects live in `flux-system`; workloads target the
application namespace. A tool normally uses the same name for both. The
ResourceSet, not a standalone `namespace.yaml`, owns the Namespace.

Stable ConfigMaps expose ordered values to HelmRelease `valuesFrom`. List files
from least to most specific; later map keys win and lists normally replace.
The `valuesFrom` list is authoritative.

## Developer application placement

```text
cluster-config/platform/applications/<app>/
  kustomization.yml
  infrastructure/{kustomization.yml,resourceset.yml,resources/}
  components/{kustomization.yml,resourceset.yml}
```

Infrastructure owns Namespace, quota, limits, and shared policies. Component
ResourceSet inputs select component/environment pairs from `apps-config` and
depend on infrastructure readiness. Each input creates one Kustomization or
HelmRelease and is an independent reconciliation/pruning boundary.

## Flux ownership invariants

- No two inputs or ResourceSets may generate the same Kubernetes identity.
- Preserve `prune: true`, `wait: true`, bounded timeouts, and explicit
  `dependsOn` where ordering matters.
- Do not add `cluster-config` as a source on additional fleet members.
- Bootstrap ResourceSets intentionally disable pruning. Applying bootstrap is
  installation/recovery, not the normal delivery path.
