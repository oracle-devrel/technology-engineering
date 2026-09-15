# Secure Argo CD access

Argo CD is installed with a `ClusterIP` server Service, TLS enabled, anonymous
access disabled, and authenticated users limited to read-only access unless an
RBAC rule grants more. Do not expose the server with a public LoadBalancer and
do not set `server.insecure: true`.

## Temporary administrator access

Use a workstation that can reach the OKE private API endpoint:

```bash
kubectl -n argocd port-forward service/argo-cd-argocd-server 8443:443
```

Open `https://localhost:8443`. Retrieve the one-time bootstrap password without
printing it into a shared terminal log:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 --decode
```

Change or remove the initial credential after configuring organizational SSO.

## Permanent private access

Publish Argo CD only through an existing private ingress or private gateway
with TLS termination and restricted network access. Keep the chart Service as
`ClusterIP`. The ingress, certificate, DNS name, and network policy are
environment-specific administrator resources and are not created by this
reference stack.

## Configure OCI Identity Domain OIDC

1. Register a confidential application in the OCI Identity Domain and configure
   its redirect URI as `https://<private-argocd-host>/auth/callback`.
2. Store the client secret outside Git, preferably in OCI Vault and an
   `ExternalSecret` that writes the key into `argocd-secret`.
3. Add the issuer, client ID, scopes, and RBAC group mappings to
   `platform/applications/argocd/values/90-user.yml`:

```yaml
configs:
  cm:
    url: https://<private-argocd-host>
    oidc.config: |
      name: OCI Identity Domain
      issuer: https://<identity-domain-issuer>
      clientID: <confidential-application-client-id>
      clientSecret: $oidc.oci.clientSecret
      requestedScopes: [openid, profile, email, groups]
  rbac:
    policy.default: role:readonly
    policy.csv: |
      g, <identity-domain-argocd-admin-group>, role:admin
      g, <identity-domain-argocd-operator-group>, role:readonly
    scopes: '[groups, email]'
```

Verify both an administrator and a read-only user before disabling the local
administrator:

```yaml
configs:
  cm:
    admin.enabled: "false"
```

Never disable the local administrator until SSO login and the administrator
group mapping have been tested in a separate browser session.

## Authorization boundaries

- `default` is restricted to the bootstrap adapter in the `argocd` namespace.
- `platform` owns cluster-administrator resources on the hub.
- `applications` accepts only `apps-config` and forbids cluster-scoped objects.
- `fleet` owns fleet-administrator resources on registered managed clusters.

All normal authenticated users are read-only by default. Grant sync or
administrative rights through reviewed group mappings rather than individual
local accounts.
