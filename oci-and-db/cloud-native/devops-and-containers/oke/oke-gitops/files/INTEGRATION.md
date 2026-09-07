# OCI DevOps and GitOps integration modes

The OCI DevOps starter and this GitOps stack are independent building blocks.
They do not read each other's Terraform state, invoke each other's pipelines,
or modify each other's repositories.

## Supported combinations

| Application delivery | Cluster administration | Configuration |
|---|---|---|
| OCI DevOps pipelines | OCI DevOps pipelines | Use the OCI DevOps starter by itself. |
| OCI DevOps pipelines | GitOps | Use the OCI DevOps starter for applications and select `cluster_admin` here. |
| GitOps | GitOps | Select `build_only` in the OCI DevOps starter and `applications_and_cluster` here. |

The two stacks may create separate OCI DevOps projects or reuse the same
project. When they share a project, their pipeline repositories remain
distinct: the OCI DevOps starter uses `devops-pipelines`, while this stack uses
`gitops-pipelines` by default.

## Use an image built by OCI DevOps

The handoff is an ordinary image reference in Git. After CI publishes an image,
record its immutable OCIR repository and tag in `apps-config` through a reviewed
pull request.

For Kustomize, update the environment overlay:

```yaml
images:
  - name: invoice
    newName: fra.ocir.io/example/oke-devops-starter/shop/invoice
    newTag: a1b2c3d
```

For umbrella Helm, update the selected component values:

```yaml
image:
  repository: fra.ocir.io/example/oke-devops-starter/shop/invoice
  tag: a1b2c3d
```

Render and review the change, then merge it to `main`. Argo CD or Flux performs
the release and retains Git as the auditable source of desired state. No direct
communication between the stacks is required.

## Scope boundaries

`cluster_admin` does not mean cluster-scoped objects only. Administrators can
still manage namespaced configuration such as ResourceQuota, LimitRange,
NetworkPolicy, Secrets backed by an external secret provider, and tool-specific
resources. The scope merely leaves developer component placements inactive.

`applications_and_cluster` adds those placements. GitOps then owns application
namespace infrastructure and component releases as well as cluster
administration.
