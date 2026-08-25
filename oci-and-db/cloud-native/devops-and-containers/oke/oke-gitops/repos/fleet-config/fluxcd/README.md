# Decentralized Flux fleet

Every participating cluster runs its own Flux controllers and reconciles one
explicit activation root below `clusters/`. There is no central Flux hub,
remote kubeconfig, hub-to-spoke API connection, or Sveltos installation.

```text
bootstrap/                 generated member template; copy once per additional cluster
clusters/<cluster>/        profiles activated on exactly one cluster
profiles/common/           shared cluster resources and administrator tools
profiles/development/      shared developer application activation
profiles/flux-operator/    self-management for additional Flux members
```

The primary stack cluster continues to use its normal `cluster-config` and
also reconciles `clusters/<primary-name>`. Resource Manager does not know
about additional clusters. For each additional member, an administrator
creates its OCI DevOps environment and installation pipeline, copies
`bootstrap/member-template.yml` to `bootstrap/<cluster>.yml`, and creates that
cluster's activation root.

Start with:

1. [Architecture](docs/architecture.md)
2. [Cluster and profile naming](docs/naming.md)
3. [Supported use cases](docs/use-cases.md)
4. [Operations and validation](docs/operations.md)
5. [OCI Vault secrets with External Secrets Operator](docs/external-secrets.md)
6. [Add another Flux member](docs/add-member.md)

## Bootstrap each member

Run `bootstrap-gitops-agent` once in OCI DevOps for the stack's selected
cluster. Its triggered deployment installs Flux Operator and prepares the
Vault-backed Git and OCIR credentials through that cluster's private OKE API
endpoint. Additional members use their own manually created environment and
deployment pipeline; Resource Manager never adds stages to the primary
pipeline.

After that deployment succeeds, perform the explicit Git handoff once per
cluster:

```bash
# Primary cluster, from a cluster-config clone and its kubeconfig.
kubectl apply -f bootstrap/flux-bootstrap.yml

# Additional member, after copying and editing member-template.yml.
kubectl apply -f bootstrap/<cluster>.yml
```

Verify the local reconciliation graph on each cluster:

```bash
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepository,kustomization,helmrelease
```

The primary bootstrap retains its normal `cluster-config` source and adds its
fleet root. An additional bootstrap has no `cluster-config` source: it creates
only the local `fleet-config` and `apps-config` sources required by that
member. Reapplying a completed member bootstrap file is idempotent.

Never commit Git passwords, registry credentials, kubeconfigs, OCI tokens, or
workload secrets. OCI DevOps prepares `git-token-auth` and `ocirsecret` in
each member's `flux-system` namespace from OCI Vault.
Application secrets should use External Secrets Operator with OKE Workload
Identity; each member receives its own narrowly scoped IAM policy statement.
