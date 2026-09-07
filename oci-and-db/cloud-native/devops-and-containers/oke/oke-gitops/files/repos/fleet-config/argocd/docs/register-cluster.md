# Register a spoke with Argo CD

Use this procedure only when the hub runs Argo CD. The registered server URL
must be the spoke's **private** Kubernetes API endpoint, reachable from the
Argo CD application controller and repo server.

## Credential

Create a narrowly scoped service account on the spoke. During an evaluation,
`cluster-admin` can establish whether the delivery model works; production
deployments should replace it with the RBAC required by the selected fleet
applications.

Do not commit its token or a populated cluster Secret. Store the credential in
OCI Vault and materialize it into the hub's `argocd` namespace with External
Secrets, or create the Secret operationally.

Argo CD recognizes a Secret with this shape:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spoke-oke-2
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    fleet.oke.oracle.com/cluster: oke-2
stringData:
  name: oke-2
  server: https://10.0.0.10:6443
  config: |
    {
      "bearerToken": "<from-OCI-Vault>",
      "tlsClientConfig": {
        "insecure": false,
        "caData": "<base64-encoded-cluster-CA>"
      }
    }
```

The `fleet.oke.oracle.com/cluster` value must match the cluster directory,
`cluster.yaml`, and every binding descriptor's `cluster` field. Reusable
profiles are selected by explicit binding files in that directory, not by
adding more profile labels to the Secret.

Verify registration without printing the Secret:

```bash
kubectl -n argocd get secrets \
  -l argocd.argoproj.io/secret-type=cluster \
  -L fleet.oke.oracle.com/cluster

kubectl -n argocd get applicationsets
kubectl -n argocd get applications
```

Changing the cluster label changes which Applications exist for that spoke.
Review it like any other deployment operation.
