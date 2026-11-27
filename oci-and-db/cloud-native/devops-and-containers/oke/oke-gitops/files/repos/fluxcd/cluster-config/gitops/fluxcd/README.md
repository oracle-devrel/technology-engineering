# Flux CD engine adapter

The Resource Manager stack generates the Flux resources in this directory.
They connect this cluster to its reconciliation roots:

- `platform.yml` defines the `platform` Kustomization. Its application list
  includes `flux-operator` as a normal platform tool in both scopes.
- `apps.yml` exists only in `applications_and_cluster` mode and creates
  `GitRepository/apps-config` as a reusable source. Logical
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
For an existing repository, follow the controlled ownership handoff in
[the operations guide](../../docs/operations.md#consolidate-flux-operator-under-platform).
Do not simply delete the old pruning Kustomization. Updating the stack alone
does not migrate an existing repository.
Use `platform/` for cluster configuration and the `apps-config` repository for
workloads unless intentionally changing the adapter itself.

Check the adapter with:

```bash
kubectl -n flux-system get resourcesets
kubectl -n flux-system get gitrepositories,kustomizations,helmreleases
```

Start with the repository root `README.md` for bootstrap, daily operation,
rollback, and troubleshooting.
