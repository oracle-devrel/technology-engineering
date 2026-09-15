# Self-managed Flux Operator application

The Resource Manager stack writes the initial
`values/00-bootstrap.yml` and `resourceset.yml` when it seeds the repository.
The local Kustomization renders every value file as a separate key in
`ConfigMap/flux-operator-values`. The initially seeded
`gitops/fluxcd/flux-operator.yml` Kustomization loads this self-managed
application.

After bootstrap, cluster administrators own the ResourceSet and value files.
Edit them through the normal branch, review, and merge workflow. Any value
supported by the upstream `flux-operator` chart can be added.

Put normal overrides in `values/90-user.yml`:

```yaml
resources:
  limits:
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 128Mi
```

Do not remove the generated private-registry image settings unless the chart
and images are intentionally moved elsewhere.

`inputs.valuesFrom` in `resourceset.yml` is the authoritative merge order.
Later entries override earlier entries. When adding a file, add it to the
ConfigMap generator and to `inputs.valuesFrom` at the required precedence
position; filenames are not sorted automatically.

Verify a change with:

```bash
kubectl -n flux-system get kustomization flux-operator-values
kubectl -n flux-system get helmrelease flux-operator
kubectl -n flux-system get pods
```
