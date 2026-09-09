# Day-two Flux CD operations

Use Git for desired-state changes and use Flux and Kubernetes for observation.
Always select the target cluster explicitly: decentralized fleet members do
not share a control plane.

## Before every change

```bash
git switch main
git pull --ff-only
git status --short
git switch -c <short-change-name>
```

Choose the pattern in [the use-case catalog](use-cases.md), inspect the
existing ResourceSet and every referenced path, and render the smallest
affected unit before committing.

## Observe reconciliation

```bash
kubectl config current-context
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepository,kustomization,helmrelease
kubectl -n flux-system describe resourceset <name>
```

Every relevant object should report `Ready=True`. Follow the ownership chain
instead of jumping directly to the workload:

```text
GitRepository
  -> root or profile Kustomization
     -> ResourceSet
        -> generated Kustomization or HelmRelease
           -> workload
```

For an environment-aware application, verify its infrastructure ResourceSet
and Kustomization before its component ResourceSet and generated component
reconciliations.

## Request an immediate reconciliation

Normal operation relies on configured intervals. When an authorized operator
needs to verify a merged change immediately, use the Flux CLI against the
target cluster:

```bash
flux reconcile source git flux-system
flux reconcile kustomization platform --with-source
flux get all -A
```

On an additional fleet member, reconcile its local fleet source and that
member's root Kustomization instead. Reconciliation is an observation aid; it
does not replace committing the desired state to Git.

## Roll back

Prefer a Git revert so desired-state history remains auditable:

```bash
git log --oneline
git revert <bad-commit-sha>
git push origin main
```

For Helm, confirm the previous chart artifact remains available, then revert
the version or values change in Git. Do not run `helm rollback` against a
Flux-managed release because Flux will restore the Git revision.

## Remove an application safely

Pruning is enabled. Removing a manifest, ResourceSet input, application
Kustomization entry, or fleet profile activation is a deletion request.

For an environment-aware application:

1. Remove component/environment inputs and verify the generated workloads are
   pruned on every intended cluster.
2. Remove the component and application activation after no workload remains.
3. Remove namespace infrastructure last.
4. Remove catalog content only after checking every primary and fleet
   placement.

This procedure removes a managed application. It is not a controller-uninstall
procedure.

## Troubleshooting order

1. **Target:** confirm kubeconfig context, cluster, namespace, and expected Git
   repository revision.
2. **Source:** inspect GitRepository readiness, authentication, URL, branch,
   and observed revision.
3. **Activation:** inspect the root/platform/profile Kustomization, path, and
   dependencies.
4. **Generation:** inspect ResourceSet conditions, inputs, generated names, and
   dependencies.
5. **Rendering:** reproduce the Kustomize or Helm render locally with identical
   paths and ordered values.
6. **Delivery:** inspect generated Kustomization, HelmRepository,
   OCIRepository, or HelmRelease conditions.
7. **Workload:** inspect quota, policies, workload status, and recent events.

Useful commands:

```bash
kubectl -n flux-system get gitrepository,kustomization,resourceset,helmrelease
kubectl -n flux-system describe gitrepository <name>
kubectl -n flux-system describe kustomization <name>
kubectl -n flux-system describe helmrelease <name>
kubectl -n <namespace> get events --sort-by=.lastTimestamp
kubectl -n <namespace> describe pod <pod>
```

Common causes:

| Symptom | Check |
|---|---|
| Source is not Ready | Repository URL, branch, `git-token-auth`, network access, and observed revision |
| ResourceSet generates nothing | Inputs, template fields, API version, source dependency, and ResourceSet conditions |
| Kustomization build failure | Path, `kustomization.yml`, duplicate identities, and local render output |
| HelmRelease is not Ready | Source readiness, chart path/version, ordered values, target namespace, and Helm events |
| `ImagePullBackOff` | Fully qualified image, CPU architecture, and namespace-specific OCIR pull Secret |
| Custom resource fails before its CRD | HelmRelease health gate and dependent Kustomization `dependsOn` |
| One fleet member differs from another | That member's own source revision, cluster-root activation, and local Flux conditions |
| Immediate reversion of a manual fix | Expected reconciliation; make or revert the change in Git |

Do not suspend reconciliation, remove finalizers, force-delete objects, or
change managed workloads directly as a routine fix. Diagnose the failing
ownership layer and correct Git.
