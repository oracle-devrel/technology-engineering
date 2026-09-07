# Flux CD engine adapter

The Resource Manager stack generates the Flux resources in this directory.
They connect this cluster to its reconciliation roots:

- `flux-operator.yml` loads the administrator-owned self-managed Flux Operator
  application.
- `platform.yml` reconciles `cluster-config/platform`.
- `apps.yml` creates `GitRepository/apps-config` as a reusable source. Logical
  applications under `platform/applications/<name>/` keep infrastructure and
  a component-selection ResourceSet together; each generated component and
  environment Kustomization uses `dependsOn` to wait for infrastructure.
- `fleet.yml` is present only when optional multi-cluster support is enabled;
  it connects this local Flux installation to only its generated
  `fleet-config/clusters/<name>` activation root.

`bootstrap/flux-bootstrap.yml` creates the FluxInstance and the initial
ResourceSet that loads this directory.

These files are initially generated integration defaults. After the first
repository seed, they are administrator-owned like every other Git file and
may be changed directly. A normal Resource Manager apply preserves them.
Use `platform/` for cluster configuration and the `apps-config` repository for
workloads unless intentionally changing the adapter itself.

Check the adapter with:

```bash
kubectl -n flux-system get resourcesets
kubectl -n flux-system get gitrepositories,kustomizations,helmreleases
```

Start with the repository root `README.md` for bootstrap, daily operation,
rollback, and troubleshooting.
