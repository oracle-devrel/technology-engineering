# Argo CD use-case catalog

This catalog is the entry point for choosing how to manage OKE. All examples
use existing ApplicationSets; administrators normally add a small descriptor
and payload rather than writing an Argo CD Application.

## Decision table

| Requirement | Pattern | Detailed example |
|---|---|---|
| Cluster-scoped Kubernetes YAML | Singleton cluster-resource Kustomization | [Cluster-wide example](../README.md#use-case-1-cluster-wide-kustomize-resources) |
| Namespace-scoped administrator YAML | Kustomize descriptor | [Namespaced example](../README.md#use-case-2-namespaced-infrastructure-with-kustomize) |
| Helm or OCI repository chart | Repository Helm descriptor | [Repository Helm example](../README.md#chart-from-a-helm-or-oci-repository) |
| Helm chart stored in Git | Git Helm descriptor | [Git Helm example](../README.md#chart-stored-directly-in-this-git-repository) |
| Helm with dashboards, policy, or other YAML | Helm descriptor plus `resources/` | [Multi-source example](../README.md#helm-plus-additional-kustomize-resources) |
| Operator followed by its custom resources | One multi-source Application with sync waves | [Operator example](../README.md#operator-plus-custom-resources) |
| Independently managed tools sharing a namespace | One descriptor per tool, same destination namespace | [Shared namespace example](../README.md#multiple-components-in-one-namespace) |
| Kustomize developer application with environments | Parent, infrastructure child, component ApplicationSet, `apps-config` catalog | [`reference-app`](../platform/applications/reference-app/application.yaml) |
| Umbrella Helm developer application with environments | Same parent model; one generated Application per enabled subchart/environment | [`reference-helm-app`](../platform/applications/reference-helm-app/application.yaml) |
| Modify one component only | Edit only its environment overlay or values file | The `apps-config` README |
| Self-manage or upgrade Argo CD | Mirrored chart plus editable ordered values | [Self-management guide](../README.md#configure-the-self-managed-argo-cd-application) |
| Temporary UI access or permanent OIDC/RBAC | Private port-forward or private ingress plus reviewed identity mappings | [Secure Argo CD access](argocd-access.md) |
| Rotate Git or OCIR runtime credentials | OCI Vault rotation and the preparation deployment stage | [Credential rotation](runtime-secrets.md#rotate-a-credential) |
| Runtime workload secret | OCI Vault plus External Secrets | `apps-config/examples/external-secret.yml` and `oci-secret.sh` |
| Rollback, deletion, or diagnosis | Git revert, ordered removal, controller observation | [Operations guide](operations.md) |
| Deliver any supported pattern to a spoke | Native Argo CD fleet adapter | The `fleet-config` README |

## Descriptor contracts

### Namespaced Kustomize

```yaml
name: <unique-application-name>
namespace: <destination-namespace>
resourcesPath: platform/applications/<directory>/resources
```

Filename: `kustomize.application.yaml`.

### Chart from a repository

```yaml
name: <unique-application-name>
namespace: <destination-namespace>
helm:
  repository: <https-or-oci-repository>
  chart: <chart-name>
  version: <pinned-version>
  releaseName: <release-name>
  valueFiles:
    - values/00-base.yml
    - values/90-user.yml
resourcesPath: platform/applications/<directory>/resources
```

Filename: `helm-repository.application.yaml`.

### Chart stored in this repository

```yaml
name: <unique-application-name>
namespace: <destination-namespace>
helm:
  path: platform/applications/<directory>/chart
  releaseName: <release-name>
  valueFiles:
    - values/00-base.yml
    - values/90-user.yml
resourcesPath: platform/applications/<directory>/resources
```

Filename: `helm-git.application.yaml`.

The `valueFiles` array is explicit and ordered. Later files win for the same
map key, while lists normally replace. All Helm descriptors include a
Kustomize source at `resourcesPath`; keep an empty `kustomization.yml` when no
additional manifests are needed yet.

## Environment-aware application contract

An administrator-owned local binding has this shape:

```text
platform/applications/<app>/
  application.yaml
  kustomization.yml
  infrastructure/
    application.yml
    resources/kustomization.yml
  components.application-set.yml
```

The infrastructure Application uses wave `-10`, creates the same-named
namespace, and owns quota, limits, and shared policies. The component
ApplicationSet uses wave `0` and explicitly selects component/environment
pairs from `apps-config`. Valid standard environments are `dev`, `staging`,
and `production`; several may coexist in the application's one namespace.

Kustomize catalog paths are:

```text
applications/<app>/kustomize/components/<component>/base
applications/<app>/kustomize/components/<component>/environments/<environment>
```

Umbrella Helm catalog paths are:

```text
applications/<app>/helm
applications/<app>/helm/values.yaml
applications/<app>/helm/values/<environment>/<component>.yml
```

Each Helm component Application loads exactly the global file and its selected
environment/component file. All subcharts are disabled globally; the selected
file enables exactly one.

## Which files are impacted?

Use this catalog together with the directory examples and report every created,
modified, and deleted file in the change review. The application catalog and
optional fleet repository contain their own scoped file-impact tables because
they are independently generated repositories.
