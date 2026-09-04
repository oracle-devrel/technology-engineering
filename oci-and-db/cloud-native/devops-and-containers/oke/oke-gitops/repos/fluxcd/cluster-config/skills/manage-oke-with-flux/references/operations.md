# Operations and troubleshooting

## Observe one target cluster

```bash
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepository,kustomization,helmrelease
kubectl -n flux-system describe resourceset <name>
kubectl -n flux-system describe kustomization <name>
kubectl -n <namespace> get deploy,sts,ds,pod,svc
kubectl -n <namespace> get events --sort-by=.lastTimestamp
```

Follow root Kustomization → profile/platform Kustomization → ResourceSet →
generated Kustomization or HelmRelease → workload. For developer applications,
check infrastructure before components.

## Prove impact

Use the relevant diff helper against the intended base. Interpret YAML by
Kubernetes identity. Report only manifests whose content differs and removed
documents as pruning candidates. ResourceSet input removal can prune a
generated object even when no file is deleted; inspect list changes manually.

## Troubleshoot in order

1. Correct target cluster and kubeconfig context.
2. GitRepository readiness, authentication, revision, and path.
3. Root/profile Kustomization readiness and dependencies.
4. ResourceSet conditions, inputs, generated names, and dependencies.
5. Local Kustomize/Helm rendering with identical paths and value order.
6. HelmRepository/OCIRepository and HelmRelease conditions.
7. Namespace quota, policy, workload status, and events.

Do not suspend reconciliation, remove finalizers, or force-delete as a routine
fix. If absent controllers leave finalizers orphaned, report exact objects and
require explicit authorization for surgical cleanup.

## Rollback and delete

Use `git revert <bad-commit>` and let Flux reconcile. Do not use `kubectl
rollout undo` or `helm rollback`. Remove component inputs first and verify
pruning, then remove placement and infrastructure. Delete catalog payload last
only when no cluster uses it.

Deleting a bootstrap ResourceSet is not uninstall because bootstrap pruning is
disabled. Full Flux/operator teardown is exceptional and must be planned from
live ownership and finalizer state.
