# Self-managed Argo CD application

The Resource Manager stack writes the initial
`values/00-bootstrap.yml` and `helm-repository.application.yaml` when it seeds
the repository. The initially seeded platform ApplicationSet discovers the
descriptor and generates `Application/argocd`.

After bootstrap, cluster administrators own the descriptor and value files.
Edit them through the normal branch, review, and merge workflow. Any value
supported by the upstream `argo-cd` chart can be added.

Put normal overrides in `values/90-user.yml`. Keep the server Service private:

```yaml
server:
  service:
    type: ClusterIP

controller:
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
```

Do not remove the generated private-registry image settings unless the chart
and images are intentionally moved elsewhere.

For port-forwarding, private ingress, OCI Identity Domain OIDC, RBAC, and safe
local-admin removal, follow [Secure Argo CD access](../../../docs/argocd-access.md).

`helm.valueFiles` in the descriptor is the authoritative merge order. Later
files override earlier files. Add a file under `values/` and add it to that list
at the required precedence position; filenames are not sorted automatically.

Verify a change with:

```bash
kubectl -n argocd get application argocd
kubectl -n argocd get pods
```
