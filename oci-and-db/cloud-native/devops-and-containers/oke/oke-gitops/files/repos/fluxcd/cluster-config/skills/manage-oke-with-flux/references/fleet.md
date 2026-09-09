# Decentralized Flux fleet

There is no Flux hub. Every member has local Flux controllers, local Git/OCIR
credentials, and one `fleet-config/clusters/<cluster>` activation root. No
cluster stores another member's kubeconfig or calls another Kubernetes API.

## Repository model

```text
fleet-config/
  bootstrap/member-template.yml
  bootstrap/<cluster>.yml
  clusters/<cluster>/{kustomization,flux-operator,common,...}.yml
  profiles/<profile>/
    cluster-resources/
    applications/
```

The primary may reconcile `cluster-config` plus its fleet root. Additional
members reconcile only `fleet-config` and `apps-config`. A profile may be
shared or dedicated to one cluster. Activation is explicit: each file below
`clusters/<cluster>/` points to one profile and its root lists the file.

## Add a member

Read the repository's `docs/add-member.md` completely. Resource Manager manages
only the primary environment/pipeline. An administrator creates a private OKE
deployment environment and dedicated installer pipeline for every later
member, using a unique `deployment_nonce` per run. Prepare Git activation,
install Flux Operator through OCI DevOps, then apply the sanitized
`bootstrap/<cluster>.yml` once. Each external mutation requires authorization.

After handoff, verify the root path and Ready sources, ResourceSets,
Kustomizations, HelmReleases, and workloads locally on that member. A member
failure must not block another cluster.
