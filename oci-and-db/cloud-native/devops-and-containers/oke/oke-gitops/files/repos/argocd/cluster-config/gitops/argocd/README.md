# Argo CD engine adapter

The Resource Manager stack generates the Application manifests in this
directory. They connect this cluster to its reconciliation roots:

- `platform.yml` reconciles cluster resources and uses ApplicationSets to
  discover platform descriptors, including self-managed Argo CD.
- `apps.yml` discovers logical application parents under
  `platform/applications/*/application.yaml`. Each parent owns its
  infrastructure and component ApplicationSet from the same folder. Sync waves
  reconcile infrastructure before the ApplicationSet generates independently
  managed component/environment Applications from `apps-config`.
- `fleet.yml` is the optional native multi-cluster adapter. It is absent when
  fleet support is disabled, but the root README documents its cluster/profile
  model and application parents.
- `projects.yml` restricts bootstrap, platform, and developer application
  permissions. The optional fleet adapter adds the `fleet` project.

`bootstrap/argocd-bootstrap.yml` loads this directory into the cluster.

These files are initially generated integration defaults. After the first
repository seed, they are administrator-owned like every other Git file and
may be changed directly. A normal Resource Manager apply preserves them.
Use `platform/` for cluster configuration and the `apps-config` repository for
workloads unless intentionally changing the adapter itself.

Generated Applications use `FailOnSharedResource=true` to reject competing
ownership and `PruneLast=true` to defer deletion until updated resources are
healthy. Treat both options as safety contracts.

Check the adapter with:

```bash
kubectl -n argocd get applications
kubectl -n argocd describe application <name>
```

Start with the repository root `README.md` for bootstrap, daily operation,
rollback, and troubleshooting.
