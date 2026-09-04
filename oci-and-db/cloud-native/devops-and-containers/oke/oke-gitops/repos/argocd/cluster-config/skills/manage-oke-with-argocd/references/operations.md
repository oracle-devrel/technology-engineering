# Operations and troubleshooting

## Observe

```bash
kubectl -n argocd get applicationsets,applications
kubectl -n argocd describe applicationset <name>
kubectl -n argocd describe application <name>
kubectl -n <namespace> get deploy,sts,ds,pod,svc
kubectl -n <namespace> get events --sort-by=.lastTimestamp
```

For environment-aware applications, follow parent → infrastructure Application
(wave -10) → component ApplicationSet (wave 0) → generated component
Applications.

## Prove the rendered impact

Run the skill's Kustomize or Helm diff helper against the intended base
revision. Interpret the unified diff by Kubernetes document identity
(`apiVersion`, `kind`, `metadata.namespace`, `metadata.name`). An object merely
appearing in the complete render is not evidence that it changed. Report only
objects whose before/after manifest differs; report removed documents as
pruning candidates.

## Troubleshoot in order

1. Descriptor filename/path and ApplicationSet discovery.
2. ApplicationSet conditions and generated Application.
3. Repository access and source revision/path.
4. Local Kustomize or Helm rendering with identical ordered values.
5. Destination cluster and namespace; private endpoint for spokes.
6. Shared-resource ownership conflicts.
7. Kubernetes workload status and events.

Do not disable `FailOnSharedResource` to hide overlap. Do not force-sync around
bad desired state.

## Roll back

Use an auditable Git revert:

```bash
git log --oneline
git revert <bad-commit>
git push origin main
```

Do not use `kubectl rollout undo` or `helm rollback`; Argo restores the version
declared in Git.

## Delete in dependency order

For a logical application, remove component/environment selections first,
verify pruning, remove the parent activation, remove infrastructure last, and
delete catalog content only when no local or fleet binding uses it.

## UI access

Keep Argo TLS-enabled and `ClusterIP`. Port-forward temporarily. Use a private
ingress and OIDC for shared access. Never expose the UI with a public
LoadBalancer or disable TLS as a shortcut.
