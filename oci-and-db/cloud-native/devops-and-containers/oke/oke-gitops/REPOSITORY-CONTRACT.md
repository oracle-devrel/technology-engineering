# Repository contract v1

This contract is frozen for the `oke-gitops-2.0.0` release. It defines where
users and automation place desired state. Controller-specific manifests may
differ, but repository ownership and the application catalog remain stable.

## Repository ownership

| Repository | Owner | Contract |
|---|---|---|
| `cluster-config` | Cluster administrators | Bootstrap one primary cluster, self-manage its selected GitOps agent, own cluster-scoped resources, namespace infrastructure, administrator tools, and local application placement |
| `apps-config` | Application teams | Store reusable Kustomize and umbrella-Helm application components; never select a cluster or own shared namespace infrastructure |
| `fleet-config` | Fleet administrators | Optionally store reusable profiles and explicit per-cluster placement |
| `pipelines` | Platform administrators | Mirror public artifacts into OCIR and install the selected GitOps agent; never store Kubernetes desired state |

## Application model

- A namespace normally represents one application and has the same name.
- Administrator tools have no environment layer. Exceptions may share a
  purpose-specific namespace such as `monitoring` when ownership is explicit.
- Developer environments are exactly `dev`, `staging`, and `production`.
- One developer application may run several environments in its single
  namespace.
- An application contains one or more components. Each component/environment
  pair is an independent reconciliation and rollback boundary.
- Application repositories never own Namespace, ResourceQuota, LimitRange, or
  shared NetworkPolicy objects.

## Shared developer catalog

Both Argo CD and Flux consume the same `apps-config` structure:

```text
applications/<app>/
  kustomize/components/<component>/
    base/
    environments/{dev,staging,production}/
  helm/
    Chart.yaml
    values.yaml
    charts/<component>/
    values/{dev,staging,production}/<component>.yml
```

Kustomize environment overlays own component image changes and patches. For
Helm, `helm/values.yaml` is loaded first and disables all subcharts; the
selected environment/component file is loaded last and enables exactly one
component.

## Controller and fleet contracts

- Argo CD uses Applications and ApplicationSets. Optional fleet management is
  centralized: the hub reaches registered spokes through private Kubernetes
  API endpoints.
- Flux uses Flux Operator ResourceSets, Kustomizations, and HelmReleases.
  Optional fleet management is decentralized: every member runs local Flux,
  pulls its own activation root, and stores no other member's kubeconfig.
- Resource Manager provisions connectivity and installation for one OKE
  cluster only. Additional Flux members use manually created private OCI
  DevOps environments and dedicated installation pipelines.
- Normal desired state is changed through Git. Direct `kubectl apply` is
  limited to the documented one-time bootstrap handoff.

## Seed ownership

The stack creates an initial template only. After a repository contains user
content, Resource Manager applies preserve it unchanged. The hidden
`development_overwrite_repositories` flag is absent from the schema, defaults
to `false`, and is reserved for controlled stack development.

The portable `manage-oke-with-argocd` and `manage-oke-with-flux` skills encode
this same contract for AI-assisted administration.
