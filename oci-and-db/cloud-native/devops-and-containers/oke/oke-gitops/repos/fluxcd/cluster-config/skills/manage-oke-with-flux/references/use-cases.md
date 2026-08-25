# Use-case router

| Request | Repository | Contract or file |
|---|---|---|
| Start primary reconciliation | `cluster-config` | Apply `bootstrap/flux-bootstrap.yml` once after pipeline success |
| Configure, upgrade, or pin Flux Operator | `cluster-config` | Operator values and ResourceSet; mirror first, then Git reconciles |
| Add cluster-wide YAML | `cluster-config` | `platform/cluster-resources/<group>/` plus root Kustomization |
| Add namespaced administrator YAML | `cluster-config` | Application ResourceSet plus `resources/` |
| Add repository/OCI Helm chart | `cluster-config` | ResourceSet, source, ordered values, HelmRelease |
| Add Git-hosted Helm chart | `cluster-config` | ResourceSet, `chart/`, ordered `values/`, existing Git source |
| Combine Helm and YAML | `cluster-config` | ResourceSet generating HelmRelease and Kustomization |
| Install operator then custom resources | placement repo | Helm health gate plus dependent Kustomization |
| Share a namespace across tools | placement repo | Unique identities; one Namespace owner |
| Add namespace quota/limits/policy | placement repo | Infrastructure ResourceSet and `resources/` |
| Add Kustomize developer app/component | `apps-config`, then placement | Base plus all three component overlays |
| Add umbrella Helm app/component | `apps-config`, then placement | Umbrella chart, disabled subcharts, values per pair |
| Release one Kustomize component | `apps-config` | Component environment image |
| Release one Helm component | `apps-config` | `helm/values/<environment>/<component>.yml` |
| Activate pair on primary | `cluster-config` | Component ResourceSet `inputs` |
| Use OCI Vault workload secret | payload plus admin setup | Sanitized ExternalSecret; OKE WI/IAM outside data |
| Add decentralized member | `fleet-config` plus OCI DevOps | Cluster root, private pipeline, bootstrap copy |
| Activate/share/dedicate profile | `fleet-config` | Explicit cluster-root Kustomization reference |
| Add fleet cluster resources or tool | `fleet-config` | Profile ResourceSet and payload |
| Place developer app on member | `fleet-config` | Infrastructure and component ResourceSets |
| Stop one deployment | placement repo | Remove one input/activation; review pruning |
| Diagnose or roll back | desired-state repo | Observe local Flux, fix or Git revert |

Read `repository-contracts.md` for ResourceSet rules, `applications.md` for
catalog placement, and `fleet.md` for member onboarding.
