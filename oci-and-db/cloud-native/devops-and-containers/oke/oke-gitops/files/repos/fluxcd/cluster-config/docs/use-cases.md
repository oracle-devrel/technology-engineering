# Flux CD use-case catalog

Use this catalog to choose the correct Flux pattern before creating resources.
The repository root README contains complete copyable examples; this page is
the short routing guide.

## Decision table

| Requirement | Flux pattern | Detailed example |
|---|---|---|
| Cluster-scoped Kubernetes YAML | Root platform Kustomization | [Cluster-wide example](../README.md#use-case-1-cluster-wide-kustomize-resources) |
| Namespace-scoped administrator YAML | ResourceSet owning a Namespace and Kustomization | [Namespaced example](../README.md#use-case-2-namespaced-infrastructure-with-kustomize) |
| Helm repository chart | ResourceSet generating HelmRepository, ordered values, and HelmRelease | [Repository Helm example](../README.md#chart-from-a-helm-repository) |
| OCI repository chart | ResourceSet generating OCIRepository, ordered values, and a HelmRelease `chartRef` | [`flux-operator` reference](../platform/applications/flux-operator/resourceset.yml) |
| Helm chart stored in Git | ResourceSet generating a HelmRelease from `GitRepository/flux-system` | [Git Helm example](../README.md#chart-stored-directly-in-this-git-repository) |
| Helm with dashboards, policy, or other YAML | One ResourceSet generating a HelmRelease and Kustomization | [Composition example](../README.md#helm-plus-additional-kustomize-resources) |
| Operator followed by custom resources | HelmRelease health gate plus dependent Kustomization | [Operator example](../README.md#operator-plus-custom-resources) |
| Independently managed tools sharing a namespace | One ResourceSet per tool and one Namespace owner | [Shared namespace example](../README.md#multiple-components-in-one-namespace) |
| Kustomize developer application with environments | Infrastructure ResourceSet plus component ResourceSet and `apps-config` catalog | [`reference-app`](../platform/applications/reference-app/) |
| Umbrella Helm developer application with environments | Infrastructure ResourceSet plus one generated HelmRelease per selected component/environment | [`reference-helm-app`](../platform/applications/reference-helm-app/) |
| Modify one component only | Edit only its environment overlay or values file | `apps-config/docs/README.md` |
| Self-manage or configure Flux Operator | Mirrored chart plus editable ordered values | [Self-management guide](../README.md#configure-the-self-managed-flux-operator-application) |
| Rotate Git or OCIR runtime credentials | OCI Vault rotation and preparation deployment stage | [Credential rotation](runtime-secrets.md#rotate-a-credential) |
| Runtime workload secret | External Secrets Operator, OCI Vault, and OKE Workload Identity | [External Secrets guide](external-secrets.md) |
| Rollback, removal, or diagnosis | Git revert, ordered pruning, and local Flux observation | [Operations guide](operations.md) |
| Deliver any supported pattern to another member | Independent Flux installation plus explicit fleet profile activation | The generated `fleet-config` repository README |

## Local application contracts

### Namespaced Kustomize

```text
platform/applications/<name>/
  kustomization.yml
  resourceset.yml
  resources/
    kustomization.yml
    <manifests>.yml
```

The ResourceSet creates the Namespace and a Flux Kustomization targeting the
`resources/` path. Do not add `namespace.yaml` below `resources/`.

### Chart from a Helm or OCI repository

```text
platform/applications/<name>/
  kustomization.yml
  resourceset.yml
  values/
    00-base.yml
    90-user.yml
  resources/                  # optional related Kustomize payload
```

The ResourceSet generates the source and HelmRelease. It exposes the ordered
value files through a stable ConfigMap and lists its keys under
`spec.inputs[].valuesFrom`. Later files have higher precedence for the same
map key; lists normally replace.

### Chart stored in this repository

Use the same contract and add `chart/`. The HelmRelease references
`GitRepository/flux-system` and the chart path in this repository instead of
creating a HelmRepository or OCIRepository.

### Chart from an OCI repository

Use the same ordered values contract. Generate an `OCIRepository` with its
`url`, `secretRef`, and pinned tag or semantic-version constraint, then replace
`HelmRelease.spec.chart` with `HelmRelease.spec.chartRef` pointing to that
OCIRepository. The self-managed
[`flux-operator` ResourceSet](../platform/applications/flux-operator/resourceset.yml)
is the included working reference for this pattern.

## Environment-aware application contract

An administrator-owned local placement has this shape:

```text
platform/applications/<app>/
  kustomization.yml
  infrastructure/
    kustomization.yml
    resourceset.yml
    resources/kustomization.yml
  components/
    kustomization.yml
    resourceset.yml
```

The infrastructure ResourceSet creates the same-named Namespace and owns
quota, limits, and shared policies. The component ResourceSet explicitly lists
the selected component/environment pairs and depends on infrastructure
readiness. It generates one Kustomization or HelmRelease per pair, preserving
an independent reconciliation, pruning, and rollback boundary.

Valid environments are exactly `dev`, `staging`, and `production`. Several may
coexist in the application's single namespace.

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

Each HelmRelease loads the global file first and the selected
environment/component file second. All subcharts are disabled globally and
the selected file enables exactly one.

## Which files are impacted?

The decision table and contracts above cover this repository. The generated
`apps-config/docs/use-cases.md` and `fleet-config/docs/use-cases.md` pages
contain the corresponding scoped file-impact tables for application and fleet
owners. The stack source also publishes one combined `flux-use-cases.md`
reference across all four repositories.
