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

## Karpenter on OKE

Karpenter requires a stable system node pool that it does not manage. Confirm at
least one Ready system node can schedule the controller before adding the chart.
When controller pods use required anti-affinity, do not request more replicas than
the available distinct system nodes; a blocked controller Deployment can prevent
later-wave `OCINodeClass` and `NodePool` resources from being applied.

For VCN-native OKE, verify the Karpenter values and resources use the cluster's
private API endpoint, worker and pod subnets/NSGs, cluster and network
compartments, and the intended workload-identity service account. Observe the
sequence explicitly:

```bash
kubectl -n karpenter get deploy,pods
kubectl get ocinodeclass,nodepool,nodeclaim
kubectl get nodes -L node-role/system,workload-tier
```

If the descriptor is merged but no Application appears, inspect the ApplicationSet
conditions and allow for its Git polling interval. An authorized operator may
request an ApplicationSet refresh; do not treat normal polling delay as a failed
deployment. A successful test requires the controller Application to be
`Synced/Healthy`, the `OCINodeClass` and `NodePool` to be Ready, and a provisioned
NodeClaim to register as a Ready Kubernetes node when pending workloads require it.

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
