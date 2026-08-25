# Flux CD use-case and file-impact reference

This is the complete change map for operating OKE with the decentralized Flux
variant of the stack. Use it to decide which generated repository owns a
change before editing files. Paths are relative to the named repository.

Every participating cluster runs its own Flux controllers and pulls Git
independently. There is no Flux hub or remote spoke kubeconfig.

## Repository ownership

| Repository | Primary owner | Responsibility |
|---|---|---|
| `pipelines` | Platform engineering | Mirror Flux Operator, Helm charts, and container images into OCIR |
| `cluster-config` | Cluster administrators | Primary-cluster bootstrap, Flux configuration, cluster resources, namespace infrastructure, and local placement |
| `apps-config` | Application developers | Reusable application components and the `dev`, `staging`, and `production` variants |
| `fleet-config` | Fleet administrators | Optional shared profiles and explicit per-cluster activation for independent Flux members |

## Complete use-case matrix

`Create` lists new files or directories. `Modify` lists existing control files
that must reference or activate the change. A dash means no file change is
normally required.

| Use case | Repository | Create | Modify |
|---|---|---|---|
| Install Flux Operator on the primary cluster | none; OCI DevOps operation | Vault secrets described in `cluster-config/docs/runtime-secrets.md` | Pipeline parameters only; no Git file |
| Start primary-cluster Git reconciliation | `cluster-config` | — | Apply, but do not edit, `bootstrap/flux-bootstrap.yml` |
| Observe Flux reconciliation | none; target-cluster operation | — | Inspect local Flux sources, Kustomizations, ResourceSets, HelmReleases, and workload events; no Git file |
| Rotate the Git or OCIR runtime reader | none; Vault and OCI DevOps operation | A new secret version or credential | Run the preparation deployment stage with both current Secret OCIDs; no Git file |
| Change Flux Operator configuration | `cluster-config` | Optional additional file below `platform/applications/flux-operator/values/` | `platform/applications/flux-operator/values/90-user.yml`; add a new ConfigMap key and append it to `spec.inputs[].valuesFrom` in `resourceset.yml` |
| Upgrade or pin Flux Operator | `pipelines`, then `cluster-config` | Mirror the required chart version through `mirror-gitops-agent` | To pin, change `spec.inputs[].version` in `platform/applications/flux-operator/resourceset.yml` |
| Mirror another public Helm chart and its images | `pipelines` | `mirroring/<application>.yaml`, copied from `mirror_helm.yaml` | Create an OCI DevOps Managed Build stage that uses the new build spec |
| Mirror an explicit image list | `pipelines` | `mirroring/<group>.yaml`, copied from `mirror_images.yaml` | Create an OCI DevOps Managed Build stage that uses the new build spec |
| Add cluster-wide Kustomize resources | `cluster-config` | `platform/cluster-resources/<group>/kustomization.yml` and manifests | `platform/cluster-resources/kustomization.yml` |
| Add namespaced administrator resources | `cluster-config` | `platform/applications/<name>/resourceset.yml`, `kustomization.yml`, and `resources/` | `platform/applications/kustomization.yml` |
| Install a chart from a Helm or OCI repository | `cluster-config` | `platform/applications/<name>/resourceset.yml`, ordered `values/*.yml`, and optional `resources/` | `platform/applications/kustomization.yml` |
| Install a Helm chart stored in Git | `cluster-config` | `platform/applications/<name>/resourceset.yml`, `chart/`, ordered `values/`, and optional `resources/` | `platform/applications/kustomization.yml` |
| Apply several ordered Helm values files | `cluster-config` or `fleet-config` | Additional files below the application's `values/` directory | The stable values ConfigMap and ResourceSet `valuesFrom` list; later entries win |
| Combine Helm and Kustomize | placement repository | Add manifests below the application's `resources/` | Generate both a HelmRelease and Kustomization in its ResourceSet and add an explicit readiness dependency when required |
| Install an operator and its custom resources | placement repository | Operator ResourceSet, health-check Kustomization, and dependent custom-resource Kustomization | Express readiness with Kustomization `healthChecks`, `dependsOn`, or ResourceSet dependencies |
| Run independent tools in one namespace | placement repository | One ResourceSet/application directory per tool or component | Use one Namespace owner and unique generated Kubernetes identities |
| Onboard a Kustomize developer application | `apps-config`, then `cluster-config` | Component bases and all three environment overlays; matching `infrastructure/` and `components/` directories under `platform/applications/<app>/` | Add the application to `platform/applications/kustomization.yml` and active pairs to `components/resourceset.yml` |
| Onboard a Git-hosted umbrella Helm application | `apps-config`, then `cluster-config` | `applications/<app>/helm/{Chart.yaml,values.yaml,charts/,values/<environment>/}`; matching infrastructure and component ResourceSets | Add the application to `platform/applications/kustomization.yml`; list active pairs in `components/resourceset.yml` |
| Deploy more than one environment in one cluster | `cluster-config` | — | Add every required component/environment pair to the component ResourceSet `inputs` |
| Change one Kustomize component image | `apps-config` | — | `applications/<app>/kustomize/components/<component>/environments/<environment>/kustomization.yml` |
| Change one Helm component image | `apps-config` | — | `applications/<app>/helm/values/<environment>/<component>.yml` |
| Add or remove an application component | `apps-config`, then placement repository | New or removed Kustomize component tree, Helm subchart, and all three environment variants | The local or fleet component ResourceSet `inputs` |
| Add application namespace quota, limits, or shared policies | placement repository | Manifests below `infrastructure/resources/` | Its infrastructure `kustomization.yml`; the ResourceSet owns the Namespace |
| Reference a workload secret from OCI Vault | payload and placement repository | A sanitized `ExternalSecret` and `SecretStore` reference with no secret value | The owning Kustomization; configure ESO and OKE Workload Identity/IAM separately |
| Roll back a bad deployment | repository containing the bad change | A Git revert commit | — |
| Stop deploying one component/environment | `cluster-config` or `fleet-config` | — | Remove its component ResourceSet input; pruning deletes only that generated reconciliation unit on the target |
| Delete an application placement | placement repository, then catalog if unused | — | Remove component inputs first, then application activation and infrastructure; delete catalog content only when no cluster uses it |
| Enable the decentralized Flux fleet repository | `cluster-config` and `fleet-config` | Stack-generated primary activation root | Enable the stack feature flag; do not create a hub or remote cluster credential |
| Add another Flux member | `fleet-config` plus OCI DevOps | `clusters/<cluster>/`, `bootstrap/<cluster>.yml`, a private OKE environment, and a dedicated install pipeline | Select only that cluster's profiles in `clusters/<cluster>/kustomization.yml` |
| Start reconciliation on an additional member | `fleet-config` | A cluster-specific copy of `bootstrap/member-template.yml` | Apply the rendered `bootstrap/<cluster>.yml` once to that cluster; do not add `cluster-config` as a source |
| Add member cluster-wide resources | `fleet-config` | ResourceSet and Kustomize payload below `profiles/<profile>/cluster-resources/` | Profile and target-cluster Kustomizations |
| Add a member namespaced Kustomize application | `fleet-config` | ResourceSet and payload below `profiles/<profile>/applications/<app>/` | Profile and target-cluster Kustomizations |
| Add a member repository Helm application | `fleet-config` | ResourceSet, source, and ordered values below `profiles/<profile>/applications/<app>/` | Profile and target-cluster Kustomizations |
| Add a member Git-hosted Helm application | `fleet-config` | ResourceSet, chart, and ordered values below `profiles/<profile>/applications/<app>/` | Profile and target-cluster Kustomizations |
| Place a developer application on a member | `fleet-config` plus existing `apps-config` catalog | Infrastructure and component ResourceSets below `profiles/<profile>/applications/<app>/` | Select pairs in the component ResourceSet and activate the profile on that member |
| Share one configuration across members | `fleet-config` | One `profiles/<profile>/` tree | Reference the profile from every intended `clusters/<cluster>/kustomization.yml` |
| Apply a cluster-specific exception | `fleet-config` | A clearly named `profiles/<cluster>-specific/` tree | Reference it from only that cluster root |
| Validate before merge | repository being changed | — | Render every changed Kustomize root or Helm selection and inspect the Git and pruning diff |
| Diagnose failed reconciliation | none | — | Inspect the target cluster's source, root/profile Kustomization, ResourceSet, generated reconciliation, workload, and events in that order |

## Safety invariants

- Git is the desired-state authority after bootstrap. Do not repair managed
  objects with `kubectl edit`, `helm upgrade`, or `kubectl rollout undo`.
- Never commit a token, password, private key, kubeconfig, populated Secret, or
  secret value. Use OCI Vault and External Secrets Operator.
- Every Flux member is autonomous. Run observations and reconciliation against
  the intended cluster context; never assume a central cluster.
- A ResourceSet owns the destination Namespace. Do not add a second Namespace
  owner or generate the same Kubernetes identity from two inputs.
- Preserve pruning, readiness checks, bounded timeouts, and explicit
  dependencies. Review every ResourceSet input or profile activation removal
  as a deletion request.
- Render the smallest affected unit before committing. A
  component/environment/cluster tuple is the application deployment and
  rollback boundary.

For copyable manifests, start with the
[cluster administrator guide](repos/fluxcd/cluster-config/README.md), the
[application developer guide](repos/fluxcd/apps-config/docs/README.md), or the
[optional decentralized fleet guide](repos/fleet-config/fluxcd/README.md).
