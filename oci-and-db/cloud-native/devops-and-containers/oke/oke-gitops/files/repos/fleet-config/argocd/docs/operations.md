# Operations

## Before merge

Render every changed Kustomize directory:

```bash
kubectl kustomize profiles/<profile>/cluster-resources
kubectl kustomize profiles/<profile>/applications/<application>/resources
```

For a Git-hosted chart:

```bash
helm lint profiles/<profile>/applications/<application>/chart
```

Review the descriptor's cluster, namespace, profile paths, chart version,
ordered values, and pruning impact.

## Verify

On the hub:

```bash
kubectl -n argocd get applicationsets
kubectl -n argocd get applications
kubectl -n argocd describe application <application>-<cluster>
```

Every generated Application must show the spoke's private API URL as its
destination. Workload health still needs verification on the spoke.

## Roll back

Revert the Git commit and merge the revert. Removing a descriptor deletes its
generated Applications and normally prunes their resources, so review
descriptor deletion and cluster-label changes carefully.

## Troubleshooting order

1. Confirm the cluster Secret exists and has the expected cluster label.
2. Confirm the ApplicationSet generated an Application.
3. Inspect Application conditions and repository authentication.
4. Test hub-to-spoke private API connectivity.
5. Inspect the rendered manifests and ordered values.
6. Query the spoke workload directly.
