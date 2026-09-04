# Fleet use cases

| Need | Files to create or change | Included reference |
|---|---|---|
| Activate a profile on one cluster | `clusters/<cluster>/kustomization.yml` and one profile Kustomization file | Generated primary `common.yml`; additional members follow `docs/add-member.md` |
| Share a profile | Reference the same `profiles/<profile>` path from several cluster roots | `profiles/common/` |
| Cluster-specific configuration | Create `profiles/<cluster>-specific/` and reference it from one root | Naming and activation contract in `clusters/README.md` |
| Cluster-scoped Kustomize | Profile ResourceSet plus a Kustomization and payload directory | `profiles/common/cluster-resources/` |
| Namespaced Kustomize | Profile ResourceSet owning Namespace plus a Kustomization and payload | `profiles/common/applications/fleet-demo/` |
| Repository Helm chart | Profile ResourceSet owning Namespace, HelmRepository, ordered values, and HelmRelease | `profiles/common/applications/kube-state-metrics/` |
| Git-hosted Helm chart | Profile ResourceSet with the local GitRepository source and HelmRelease | `profiles/advanced/applications/git-tool/` |
| Ordered Helm values | List ConfigMap keys in base-to-override order; the last file wins | `git-tool/values/{00-base,90-overrides}.yml` |
| Helm plus Kustomize | Generate independent HelmRelease and Kustomization objects in one logical application folder | `profiles/advanced/applications/helm-plus-kustomize/` |
| Operator before custom resources | Use ordered ResourceSet steps: install and health-check the operator, then create its custom resources | `profiles/advanced/applications/external-secrets/` |
| OCI Vault workload secrets | Run ESO as the `external-secrets` ServiceAccount and commit only sanitized SecretStore/ExternalSecret references | `profiles/advanced/applications/external-secrets/` |
| Developer Kustomize application | Infrastructure ResourceSet plus one Kustomization per selected component/environment | `profiles/development/applications/reference-app/` |
| Developer umbrella Helm application | Infrastructure ResourceSet plus one HelmRelease per selected component/environment, using the shared `apps-config` chart | `profiles/development/applications/reference-helm-app/` |
| Developer Helm values precedence | Load `helm/values.yaml` first and `helm/values/<environment>/<component>.yml` second | `reference-helm-app/components/resourceset.yml` |
| Stop one deployment | Remove only its component/environment input or profile activation; review pruning first | Operational procedure below |

Application repositories remain cluster-neutral. Placement and namespace
infrastructure always belong to `fleet-config`.

The `advanced` profile is intentionally inactive in every cluster root. Before
activation, replace `<region>`, `<vault-ocid>`, and
`<vault-secret-name>` in its External Secrets manifests and create the exact
OKE Workload Identity policy described in `docs/external-secrets.md`.
