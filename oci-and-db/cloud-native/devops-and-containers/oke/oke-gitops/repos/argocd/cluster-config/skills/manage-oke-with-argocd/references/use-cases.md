# Use-case router

| Request | Repository | Contract or file |
|---|---|---|
| Start reconciliation after installation | `cluster-config` | Apply existing `bootstrap/argocd-bootstrap.yml` once |
| Configure, upgrade, or pin Argo CD | `cluster-config` | `platform/applications/argocd/values/90-user.yml` and its Helm descriptor |
| Add cluster-wide YAML | `cluster-config` | `platform/cluster-resources/<group>/` plus root `kustomization.yml` |
| Add namespaced administrator YAML | `cluster-config` | `<app>/kustomize.application.yaml` plus `resources/` |
| Add external Helm/OCI chart | `cluster-config` | `<app>/helm-repository.application.yaml`, `values/`, `resources/` |
| Add chart stored in Git | `cluster-config` | `<app>/helm-git.application.yaml`, `chart/`, `values/`, `resources/` |
| Combine Helm and YAML | `cluster-config` | Helm descriptor plus its `resources/` source |
| Install operator and custom resources | `cluster-config` | One multi-source app; dependent resources use later sync waves |
| Share a namespace across independent tools | `cluster-config` | One descriptor per tool, same namespace, unique object ownership |
| Add application namespace quota/limits/policy | `cluster-config` | `<app>/infrastructure/resources/`; never `namespace.yaml` |
| Add Kustomize developer application/component | `apps-config`, then placement repo | Component base plus all three environment overlays |
| Add umbrella Helm application/component | `apps-config`, then placement repo | Umbrella chart, disabled subcharts, one values file per component/environment |
| Release one Kustomize component | `apps-config` | Component's environment `kustomization.yml` image tag |
| Release one Helm component | `apps-config` | `helm/values/<environment>/<component>.yml` |
| Activate environment/component locally | `cluster-config` | Application's `components.application-set.yml` list |
| Use OCI Vault workload secret | payload repo plus administrator setup | Sanitized `ExternalSecret`; workload identity and IAM stay outside secret data |
| Register spoke | runtime hub Secret plus `fleet-config` | Private API cluster Secret and `clusters/<cluster>/cluster.yaml` |
| Add spoke cluster resources | `fleet-config` | Profile cluster root plus cluster's `clusterResourcesPath` |
| Add spoke Kustomize/Helm tool | `fleet-config` | Profile payload plus per-cluster descriptor |
| Place developer app on spoke | `fleet-config` | Parent, infrastructure, and component ApplicationSet under cluster app folder |
| Share config across spokes | `fleet-config` | Reusable `profiles/<profile>/` referenced by several clusters |
| Add one-cluster exception | `fleet-config` | Dedicated `profiles/<cluster>-specific/` |
| Stop or delete deployment | placement repo | Remove selection/binding first; infrastructure and catalog last |
| Diagnose or roll back | repository containing desired state | Observe Argo, fix or `git revert`; never use Helm/kubectl rollback |

For descriptor fields and paths, read `repository-contracts.md`. For developer
value placement and activation, read `applications.md`.
