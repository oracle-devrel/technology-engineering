# Application developer use cases

This repository is a reusable catalog. It never chooses a cluster. A cluster
or fleet administrator activates catalog units from `cluster-config` or
`fleet-config`.

Start with the [developer documentation index](README.md). Detailed examples
are in the [Kustomize guide](kustomize.md), [Helm values guide](helm.md), and
[delivery workflow](delivery.md).

| Developer task | Create | Modify | Validate |
|---|---|---|---|
| Add a Kustomize application | `applications/<app>/kustomize/components/<component>/base/` and `environments/{dev,staging,production}/` for every component | Ask an administrator to add placement; do not add a root activation here | `kubectl kustomize` every base and overlay |
| Add a Kustomize component | One base plus all three environment overlays | Administrator-owned component ApplicationSet selections | Render the new base and overlays; check unique resource identities |
| Change one Kustomize component image | — | The selected component's `environments/<environment>/kustomization.yml` | Render that overlay and inspect the Deployment image |
| Add an umbrella Helm application | `applications/<app>/helm/Chart.yaml`, `values.yaml`, vendored `charts/`, and `values/{dev,staging,production}/<component>.yml` | Ask an administrator to add placement | Dependency list, lint, and template every component/environment pair |
| Add a Helm component | One disabled-by-default vendored subchart and one values file per environment | Parent dependencies/global disable map and administrator placement | Confirm each render contains only its selected subchart |
| Change one Helm component image | — | `applications/<app>/helm/values/<environment>/<component>.yml` | Template with global values first and selected values second |
| Add environment-specific configuration | Kustomize patch or fields in the existing Helm component values file | The environment overlay or `helm/values/<environment>/<component>.yml` | Render only that component/environment and inspect the diff |
| Reference an OCI Vault secret | Sanitized `ExternalSecret` manifest | The owning Kustomization | Schema validation; confirm no secret value is present |
| Remove a component | — | Remove administrator placements first; delete catalog files only when unused everywhere | Verify pruning on each target before catalog deletion |
| Roll back | A Git revert commit | — | Render the reverted unit and observe its controller reconciliation object |

## Kustomize contract

- A base contains common resource definitions.
- Each of exactly `dev`, `staging`, and `production` has a component-local
  overlay.
- Resources use `<component>-<environment>` names and the application's
  same-named namespace.
- Every overlay adds application, component, instance, and environment labels.
- A base change affects every active environment of that component. An overlay
  change affects only that component/environment.

## Helm contract

- `helm/values.yaml` is the sole global values file and disables every
  subchart.
- `helm/values/<environment>/<component>.yml` enables exactly one component
  and owns its environment configuration and image.
- Argo CD and Flux load exactly those two files in that order; the selected
  file wins.
- Each component/environment pair is an independent reconciliation, release,
  sync, and rollback boundary.

Applications do not own Namespace, ResourceQuota, LimitRange, or shared
NetworkPolicy resources. Request those from the cluster administrator before
placement.
