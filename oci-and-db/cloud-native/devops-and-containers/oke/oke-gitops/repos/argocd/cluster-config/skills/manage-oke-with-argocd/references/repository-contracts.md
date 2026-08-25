# Repository contracts

## Local cluster descriptors

Store all descriptors under `cluster-config/platform/applications/<name>/`.

Namespaced Kustomize, filename `kustomize.application.yaml`:

```yaml
name: <unique-name>
namespace: <namespace>
resourcesPath: platform/applications/<directory>/resources
```

External Helm/OCI chart, filename `helm-repository.application.yaml`:

```yaml
name: <unique-name>
namespace: <namespace>
helm:
  repository: <repository-url>
  chart: <chart>
  version: <pinned-version>
  releaseName: <release>
  valueFiles:
    - values/00-base.yml
    - values/90-user.yml
resourcesPath: platform/applications/<directory>/resources
```

Git-hosted chart, filename `helm-git.application.yaml`:

```yaml
name: <unique-name>
namespace: <namespace>
helm:
  path: platform/applications/<directory>/chart
  releaseName: <release>
  valueFiles:
    - values/00-base.yml
    - values/90-user.yml
resourcesPath: platform/applications/<directory>/resources
```

Helm value files are explicit and ordered; later entries win for map keys and
lists normally replace. Keep `resources/kustomization.yml` even when empty.
Argo creates the namespace with `CreateNamespace=true`; do not add a Namespace
manifest.

## Logical developer application placement

```text
cluster-config/platform/applications/<app>/
  application.yaml
  kustomization.yml
  infrastructure/
    application.yml              # wave -10, project platform
    resources/kustomization.yml  # quota, limits, shared policy
  components.application-set.yml # wave 0, project applications
```

The parent is discovered by `platform-applications`. Infrastructure must become
Healthy before the component ApplicationSet is applied. Each list element
creates one component/environment Application. Components have no ordering
dependency.

## Controller safety defaults

Preserve `ServerSideApply=true`, `ApplyOutOfSyncOnly=true`,
`FailOnSharedResource=true`, and `PruneLast=true`. Namespaced delivery also uses
`CreateNamespace=true` and normally `SkipDryRunOnMissingResource=true`.
Do not weaken AppProjects or these options to hide a design or ownership error.
