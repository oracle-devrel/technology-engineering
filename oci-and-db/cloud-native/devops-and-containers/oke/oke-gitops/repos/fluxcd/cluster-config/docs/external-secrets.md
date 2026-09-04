# Application secrets from OCI Vault

[Documentation index](README.md) · [Cluster administrator guide](../README.md)

External Secrets Operator (ESO) is the standard workload-secret integration.
Secret values remain in OCI Vault. Git contains only an OCI Vault reference,
and ESO materializes the Kubernetes Secret at reconciliation time.

Use OKE Workload Identity. Do not create an OCI user, API key, auth token, or
static OCI credential Secret for ESO. Workload Identity requires an enhanced
OKE cluster and identifies the caller by cluster OCID, namespace, and Service
Account.

## 1. Install ESO before its custom resources

Create an administrator-owned application folder for `external-secrets`. Pin
the official chart from `https://charts.external-secrets.io`, install its
CRDs, and force the controller ServiceAccount name:

```yaml
values:
  installCRDs: true
  serviceAccount:
    create: true
    name: external-secrets
```

Use ResourceSet `steps`: the first step creates namespace `external-secrets`
and waits for the ESO HelmRelease; the second creates the `SecretStore` and
`ExternalSecret` reconciliation. Do not use an empty Kustomization as a
readiness gate because it can become Ready before an external HelmRelease.
The fleet reference at
`profiles/advanced/applications/external-secrets/resourceset.yml` is directly
copyable into a local platform application.

## 2. Grant the ESO workload access

Record the OKE cluster OCID, Vault OCID, secret OCID, and compartment OCID.
Add these narrowly scoped statements to an existing policy in a parent
compartment; a new policy object is not required:

```text
Allow any-user to use vaults in compartment id <compartment-ocid> where all {request.principal.type = 'workload', request.principal.namespace = 'external-secrets', request.principal.service_account = 'external-secrets', request.principal.cluster_id = '<cluster-ocid>', target.vault.id = '<vault-ocid>'}
Allow any-user to inspect secrets in compartment id <compartment-ocid> where all {request.principal.type = 'workload', request.principal.namespace = 'external-secrets', request.principal.service_account = 'external-secrets', request.principal.cluster_id = '<cluster-ocid>', target.vault.id = '<vault-ocid>'}
Allow any-user to read secret-bundles in compartment id <compartment-ocid> where all {request.principal.type = 'workload', request.principal.namespace = 'external-secrets', request.principal.service_account = 'external-secrets', request.principal.cluster_id = '<cluster-ocid>', target.secret.id = '<secret-ocid>'}
```

Add one `read secret-bundles` statement per allowed secret, or deliberately
broaden the target only after a security review. `use vaults` is required
because the provider validates the selected Vault with `GetVault`; it does not
grant ESO permission to create or modify Vault secrets.

For a fleet, repeat the statements with each member's cluster OCID. A policy
for one member does not authorize ESO running on another member.

## 3. Commit the references

Create a namespaced `SecretStore` in the application namespace:

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: oci-vault
spec:
  provider:
    oracle:
      vault: <vault-ocid>
      region: <region>
      principalType: Workload
```

Do not set `serviceAccountRef` when ESO itself should authenticate. The Oracle
provider then uses the projected token of
`external-secrets/external-secrets`, matching the IAM policy.

Create one `ExternalSecret` for the Kubernetes Secret required by the
application:

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: application-runtime
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: SecretStore
    name: oci-vault
  target:
    name: application-runtime
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: <oci-vault-secret-name>
```

The application consumes `Secret/application-runtime` normally. It must not
own the generated Secret manifest.

## 4. Verify without exposing values

```bash
kubectl -n external-secrets get deployment,serviceaccount
kubectl -n <application-namespace> get secretstore,externalsecret
kubectl -n <application-namespace> get secret <generated-secret> \
  -o custom-columns=NAME:.metadata.name,TYPE:.type,KEYS:'length(.data)'
```

Expect the SecretStore and ExternalSecret Ready conditions to be `True` and
the ExternalSecret status to be `SecretSynced`. Verify hashes rather than
printing or decoding secret values in routine logs.

## Rotation and removal

Create a new OCI Vault secret version; ESO refreshes the Kubernetes Secret on
its next interval. Application Pods reload it only if the application supports
live Secret updates; otherwise roll the affected Deployment.

Before removing ESO, remove dependent ExternalSecrets and wait for their
finalizers to complete. Keep both the operator and application Namespaces
until the ExternalSecret Kustomization and ESO HelmRelease are gone; annotate
Namespaces with `fluxcd.controlplane.io/prune: disabled` when one ResourceSet
owns the whole lifecycle. Delete the now-empty Namespaces afterward, then
remove the exact IAM statements. Never delete unrelated statements from a
shared OCI policy.
