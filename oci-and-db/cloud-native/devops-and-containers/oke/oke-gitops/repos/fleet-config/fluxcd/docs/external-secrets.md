# OCI Vault secrets on fleet members

Each Flux member runs its own ESO controller and authenticates independently
with OKE Workload Identity. There is no hub credential and no static OCI
credential Secret.

Before activating `profiles/advanced` on a member:

1. Confirm the member is an enhanced OKE cluster.
2. Replace the Vault, region, and secret-name placeholders under
   `profiles/advanced/applications/external-secrets/resources/`.
3. Add the three least-privilege policy statements from the generated
   `cluster-config/docs/external-secrets.md`, using this member's cluster OCID.
4. Commit the profile changes and its activation under
   `clusters/<cluster>/`.
5. Wait for ResourceSet `fleet-external-secrets`, HelmRelease
   `external-secrets`, Kustomization `fleet-external-secrets-resources`, the
   SecretStore, and the ExternalSecret to become Ready.

The ResourceSet uses native ordered steps. ESO and all CRDs become healthy in
the first step; Flux creates the provider custom resources only in the second.
The reference creates `Secret/vault-proof` in `eso-demo`. Rename the namespace,
objects, and secret keys for a real workload.

## Safe removal

ResourceSet steps guarantee installation order, but Kubernetes resources have
no reverse termination-order guarantee. The two example Namespaces therefore
use `fluxcd.controlplane.io/prune: disabled`: they remain while Flux finalizes
the ExternalSecret Kustomization and uninstalls the ESO Helm release.

Deactivate the advanced profile, wait until `fleet-external-secrets`, its
generated Kustomization, and HelmRelease are gone, and only then delete the
empty `eso-demo` and `external-secrets` Namespaces. Remove the exact IAM policy
statements and OCI Vault test secret last. Do not force-remove ExternalSecret
finalizers while the ESO controller is still available.

Use a separate policy statement for every member because a workload identity
is the tuple of cluster OCID, namespace, and ServiceAccount. A profile shared
by several clusters does not imply shared OCI authorization.
