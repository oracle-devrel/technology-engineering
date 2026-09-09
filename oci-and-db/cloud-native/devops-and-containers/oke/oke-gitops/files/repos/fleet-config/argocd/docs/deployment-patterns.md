# Cluster and profile deployment patterns

The fleet adapter exposes the same delivery forms as the single-cluster
`platform.yml`.

| Need | Fleet declaration |
|---|---|
| Cluster-wide Kustomize resources | `cluster.yaml` → one `clusterResourcesPath` |
| Namespaced Kustomize infrastructure | `applications/<binding>/kustomize.application.yaml` |
| Helm chart from a repository | `applications/<binding>/helm-repository.application.yaml` |
| Helm chart stored in Git | `applications/<binding>/helm-git.application.yaml` |
| Environment-aware application | `applications/<name>/application.yaml` |

Cluster resources are not an application in the repository model. Each
cluster selects exactly one Kustomize root, normally
`profiles/<profile>/cluster-resources`. The adapter internally generates the
Argo CD object required to reconcile it.

Repository and Git Helm applications also include `resourcesPath`, so Helm plus
Kustomize, an operator plus its custom resources, and shared namespaces use
the same composition as the normal cluster platform.

## Reusable profile binding

This descriptor installs the reusable KEDA profile on one cluster:

```yaml
application: keda
cluster: oke-2
namespace: keda
resourcesPath: profiles/standard/applications/keda/resources
helm:
  repository: https://kedacore.github.io/charts
  chart: keda
  version: 2.20.1
  releaseName: keda
  valueFiles:
    - profiles/standard/applications/keda/values/00-base.yml
    - profiles/standard/applications/keda/values/90-overrides.yml
```

The ordered values list is explicit and may contain any number of files. Helm
processes it from top to bottom; a later file wins for the same key.

## Reusable environment-aware application

Developer workloads stay in `apps-config`; fleet-owned infrastructure and
placement converge in one application folder:

```yaml
application: reference-app
cluster: oke-2
resourcesPath: clusters/oke-2/applications/reference-app
```

The folder's `infrastructure/application.yml` points to the profile-owned quota,
limits, and policies and uses wave `-10`.
`components.application-set.yml` uses wave `0` and explicitly lists the
component/environment pairs read from the developer catalog. Put the same
structure beneath another cluster object to reuse the selection while
preserving infrastructure readiness ordering.

`reference-helm-app` demonstrates the same parent convention for a Git-hosted
umbrella Helm chart. The example activates frontend/dev and api/dev. Each
generated Application renders one subchart with ordered application,
component, environment, and override files. Application names append the
cluster name, while Helm release names stay
`reference-helm-app-<component>-<environment>`.

## Profile dedicated to one cluster

A profile is an organizational and reuse boundary, not a promise that several
clusters use it. A cluster may point to a dedicated profile:

```yaml
# clusters/oke-2/cluster.yaml
cluster: oke-2
clusterResourcesPath: profiles/oke-2-specific/cluster-resources
```

Its application descriptors can reference paths such as:

```yaml
application: monitoring
cluster: oke-2
namespace: monitoring
resourcesPath: profiles/oke-2-specific/applications/monitoring/resources
```

Choose this when the cluster has a complete configuration set that should stay
together. Use the same dedicated-profile pattern for smaller exceptions so the
fleet has one consistent payload model.

## Cluster-specific binding

Store cluster-specific payloads in a dedicated profile and point a normal
descriptor at them:

```yaml
application: oke-2-local-settings
cluster: oke-2
namespace: cluster-settings
resourcesPath: profiles/oke-2-specific/applications/settings/resources
```

Prefer reusable profiles when several clusters need the same desired state.
Document why a dedicated profile belongs to one cluster and when it can be
removed.

## Advanced composition

- Operator and custom resources: one Helm descriptor references the operator
  chart plus the profile's `resources/`; add sync waves when CR ordering needs
  them. `profiles/example/applications/queue-worker` is a standalone example.
  It must replace, not accompany, the plain KEDA application because both
  install the same cluster-scoped operator resources.
- Shared namespace: use independent bindings with unique application names and
  the same namespace.
- Autoscaling: omit `spec.replicas` when HPA, KEDA, or another controller owns
  the replica count.
