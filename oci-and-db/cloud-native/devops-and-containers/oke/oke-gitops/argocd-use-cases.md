# Argo CD use-case and file-impact reference

This is the complete change map for operating OKE with the Argo CD variant of
the stack. Use it to decide which generated repository owns a change before
editing files. Paths are relative to the named repository.

## Repository ownership

| Repository | Primary owner | Responsibility |
|---|---|---|
| `pipelines` | Platform engineering | Mirror Argo CD, Helm charts, and container images into OCIR |
| `cluster-config` | Cluster administrators | Bootstrap, Argo CD configuration, cluster resources, namespace infrastructure, and hub placement |
| `apps-config` | Application developers | Reusable application components and the `dev`, `staging`, and `production` variants |
| `fleet-config` | Fleet administrators | Optional spoke registration metadata, reusable profiles, and per-cluster placement |

## Complete use-case matrix

`Create` lists new files or directories. `Modify` lists existing control files
that must reference or activate the change. A dash means no file change is
normally required.

| Use case | Repository | Create | Modify |
|---|---|---|---|
| Install Argo CD for the first time | none; OCI DevOps operation | Vault secrets described in `cluster-config/docs/runtime-secrets.md` | Pipeline parameters only; no Git file |
| Start Git reconciliation | `cluster-config` | — | Apply, but do not edit, `bootstrap/argocd-bootstrap.yml` |
| Access the Argo CD UI temporarily | none; workstation operation | — | Port-forward the Argo CD server `ClusterIP`; no Git file |
| Configure private UI access, OIDC, and RBAC | `cluster-config` | Environment-specific private ingress/certificate and an external secret for the OIDC client secret | `platform/applications/argocd/values/90-user.yml`; verify administrator and read-only mappings before disabling local admin |
| Rotate the Git or OCIR runtime reader | none; Vault and OCI DevOps operation | A new secret version or credential | Run the `prepare-gitops-agent` deployment stage with both current Secret OCIDs; no Git file |
| Change Argo CD configuration | `cluster-config` | Optional additional file below `platform/applications/argocd/values/` | `platform/applications/argocd/values/90-user.yml`; add any new file to `helm.valueFiles` in `platform/applications/argocd/helm-repository.application.yaml` |
| Upgrade or pin Argo CD | `pipelines`, then `cluster-config` | Mirror the required chart version through `mirror-gitops-agent` | To pin, change `helm.version` in `platform/applications/argocd/helm-repository.application.yaml` |
| Mirror another public Helm chart and its images | `pipelines` | `mirroring/<application>.yaml`, copied from `mirror_helm.yaml` | Create an OCI DevOps Managed Build stage that uses the new build spec |
| Mirror an explicit image list | `pipelines` | `mirroring/<group>.yaml`, copied from `mirror_images.yaml` | Create an OCI DevOps Managed Build stage that uses the new build spec |
| Add cluster-wide Kustomize resources | `cluster-config` | `platform/cluster-resources/<group>/kustomization.yml` and manifests | `platform/cluster-resources/kustomization.yml` |
| Add namespaced administrator resources | `cluster-config` | `platform/applications/<name>/kustomize.application.yaml`, `resources/kustomization.yml`, and manifests | — |
| Install a chart from a Helm or OCI repository | `cluster-config` | `platform/applications/<name>/helm-repository.application.yaml`, `values/*.yml`, and `resources/kustomization.yml` | — |
| Install a Helm chart stored in Git | `cluster-config` | `platform/applications/<name>/helm-git.application.yaml`, `chart/`, `values/*.yml`, and `resources/kustomization.yml` | — |
| Apply several ordered Helm values files | `cluster-config` or `fleet-config` | Additional files under the application's `values/` directory | The descriptor's `helm.valueFiles` array; later entries win |
| Combine Helm and Kustomize | `cluster-config` | Add manifests below the Helm application's `resources/` | That application's `resources/kustomization.yml` |
| Install an operator and its custom resources | `cluster-config` | Operator Helm descriptor, values, `resources/kustomization.yml`, and custom resources | Add `argocd.argoproj.io/sync-wave` annotations to dependent resources |
| Run independent tools in one namespace | `cluster-config` | One application directory and descriptor per tool/component | Set the same `namespace` in each descriptor; never generate the same Kubernetes object twice |
| Onboard a Kustomize application | `apps-config`, then `cluster-config` | Component bases and three environment overlays; matching parent/infrastructure/component files under `platform/applications/<app>/` | List active component/environment pairs in `components.application-set.yml` |
| Onboard a Git-hosted umbrella Helm application | `apps-config`, then `cluster-config` | `applications/<app>/helm/{Chart.yaml,values.yaml,charts/,values/<environment>/}`; matching parent/infrastructure/component files in `cluster-config` | List active pairs in `components.application-set.yml`; each generated Application loads global values then one environment/component file |
| Deploy more than one environment in one cluster | `cluster-config` | — | Add each required component/environment pair to the application's `components.application-set.yml` |
| Change one Kustomize component image | `apps-config` | — | `applications/<app>/kustomize/components/<component>/environments/<environment>/kustomization.yml` |
| Change one Helm component image | `apps-config` | — | `applications/<app>/helm/values/<environment>/<component>.yml` |
| Add or remove an application component | `apps-config`, then placement repository | New or removed Kustomize component tree, Helm subchart, and all three environment variants | The local or fleet `components.application-set.yml` selections |
| Add application namespace quota, limits, or shared policies | `cluster-config` | Manifests under `platform/applications/<app>/infrastructure/resources/` | Its `kustomization.yml`; do not add `namespace.yaml` |
| Reference a workload secret from OCI Vault | `apps-config` or `cluster-config` | An `ExternalSecret` manifest with no secret value | The owning Kustomization; configure External Secrets and OCI workload identity/IAM outside the application payload |
| Roll back a bad deployment | repository containing the bad change | A Git revert commit | — |
| Stop deploying one component/environment | `cluster-config` or `fleet-config` | — | Remove its list element from `components.application-set.yml`; pruning deletes that deployment on that target |
| Delete an application | placement repository, then catalog if unused | — | First remove component selections, then parent/infrastructure activation; delete catalog content only when no cluster uses it |
| Enable native Argo CD fleet management | `cluster-config` and `fleet-config` | Runtime Argo cluster Secret outside Git; fleet cluster/profile directories | Add and review `gitops/argocd/fleet.yml` if it was not seeded initially |
| Register a spoke | runtime cluster plus `fleet-config` | Runtime `argocd` cluster Secret; `clusters/<cluster>/cluster.yaml` | The Secret label must be `fleet.oke.oracle.com/cluster=<cluster>` and its server must be the private API endpoint |
| Add spoke cluster-wide resources | `fleet-config` | `profiles/<profile>/cluster-resources/kustomization.yml` and manifests | `clusters/<cluster>/cluster.yaml` `clusterResourcesPath` |
| Add a spoke namespaced Kustomize application | `fleet-config` | Profile resources plus `clusters/<cluster>/applications/<binding>/kustomize.application.yaml` | — |
| Add a spoke repository Helm application | `fleet-config` | Profile values/resources plus `clusters/<cluster>/applications/<binding>/helm-repository.application.yaml` | — |
| Add a spoke Git-hosted Helm application | `fleet-config` | Profile chart/values/resources plus `clusters/<cluster>/applications/<binding>/helm-git.application.yaml` | — |
| Place a developer application on a spoke | `fleet-config` plus existing `apps-config` catalog | Parent, infrastructure child, and component ApplicationSet below `clusters/<cluster>/applications/<app>/` | Select pairs in that component ApplicationSet |
| Share one configuration across spokes | `fleet-config` | One `profiles/<profile>/` tree | Point each cluster object and binding at that profile |
| Apply a cluster-specific exception | `fleet-config` | A clearly named dedicated `profiles/<cluster>-specific/` tree | Point only that cluster's object or bindings at it |
| Validate before merge | repository being changed | — | Render every changed Kustomize root or Helm combination; inspect `git diff` |
| Diagnose failed reconciliation | none | — | Inspect ApplicationSet generation, Application conditions/diff, repository access, destination connectivity, then workload events |

## Safety invariants

- Git is the desired-state authority after bootstrap. Do not repair managed
  objects with `kubectl edit`.
- Never commit a token, password, private key, kubeconfig, or populated
  Kubernetes `Secret`.
- Do not add `namespace.yaml` for local Argo applications. Use
  `CreateNamespace=true`; application infrastructure owns quota, limits, and
  shared policies.
- Review every descriptor or list-element deletion as a destructive change.
  Automated pruning is enabled.
- Spoke cluster credentials exist only as runtime Argo CD Secrets and always
  use the private Kubernetes API endpoint.
- Render the smallest affected unit before committing. A component/environment
  pair is the application deployment and rollback boundary.

For copyable manifests, start with the
[cluster administrator guide](repos/argocd/cluster-config/README.md), the
[application developer guide](repos/argocd/apps-config/docs/README.md), or the
[optional fleet guide](repos/fleet-config/argocd/README.md).
