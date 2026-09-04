# Operate this cluster with Flux CD

This repository is the cluster administrator's source of truth for one OKE
cluster. A commit merged to `main` is a request for Flux to change the cluster.

Flux Operator ResourceSets compose each platform application. A ResourceSet can
create the destination namespace, a Helm release, and a Flux Kustomization for
additional manifests while keeping them one administrator-owned application.

For AI-assisted administration, install the self-contained
`skills/manage-oke-with-flux/` package using
[the installation guide](docs/install-agent-skill.md).

## Where a change belongs

Cluster administrators normally have three use cases:

| Use case | Location |
|---|---|
| Cluster-wide, non-namespaced Kustomize resources | `platform/cluster-resources/` |
| Namespace-wide infrastructure manifests | `platform/applications/<name>/resources/` |
| Helm charts from a repository or from Git | `platform/applications/<name>/` |

A namespace normally represents one application. A pre-packaged infrastructure
tool has no environment layer and normally uses its own name as its namespace.
For example, KEDA is deployed to `keda`. When a package contains several
closely-related components, choose a clearer application namespace; for
example, deploy `kube-prometheus-stack` to `monitoring`.

Do not add `namespace.yaml` to the application resources. The application's
ResourceSet creates the namespace.

Application workloads owned by development teams belong in the separate
`apps-config` catalog. Administrators keep namespace infrastructure and the
explicit component/environment selections together under
`platform/applications/<name>/`; decentralized fleet placement uses equivalent
local ResourceSet profiles in `fleet-config`.

## Documentation map

- [First-time bootstrap](#first-time-bootstrap)
- [Bootstrap access guide](docs/README.md)
  - [IAM identities and policies](docs/iam.md)
- [Vault secrets and credential rotation](docs/runtime-secrets.md)
- [Use-case catalog and pattern selection](docs/use-cases.md)
- [Day-two operations and troubleshooting](docs/operations.md)
- [Install the portable OKE Flux agent skill](docs/install-agent-skill.md)
- [AI-assisted administration contract](docs/agent-guide.md)
- [Configure the self-managed Flux Operator application](#configure-the-self-managed-flux-operator-application)
- [Platform configuration examples](#use-case-1-cluster-wide-kustomize-resources)
- [Security and troubleshooting](#security-and-troubleshooting)
- [Optional decentralized Flux fleet](#optional-decentralized-flux-fleet)

## Repository layout

```text
bootstrap/                         Generated bootstrap recovery manifests
gitops/fluxcd/                     Initially generated Flux adapter
platform/
  cluster-resources/               Cluster-scoped Kustomize resources
  applications/
    kustomization.yml              Registers platform ResourceSets
    flux-operator/
      values/
        00-bootstrap.yml           Initial private-registry settings
        90-user.yml                Administrator overrides
      kustomization.yml
      resourceset.yml
    <application>/
      kustomization.yml
      resourceset.yml              Namespace and reconciliation objects
      values/                      Ordered Helm values files
      chart/                       Optional Helm chart stored directly in Git
      resources/
        kustomization.yml          Additional namespaced Kustomize resources
    <environment-aware-app>/
      infrastructure/              Namespace prerequisites
      components/                  Selected component/environment reconciliations
```

The stack provisions an initial repository template only. After the first
seed, every file—including `bootstrap/`, `gitops/fluxcd/`, and the Flux
Operator self-management resources—is administrator-owned Git configuration.
Subsequent Resource Manager applies preserve repository content and prefer
customer Git changes.

## Optional decentralized Flux fleet

When the Resource Manager stack has `enable_multicluster = true`, it also
creates `fleet-config` and adds `gitops/fluxcd/fleet.yml`. That generated
GitRepository and Kustomization make this primary cluster reconcile only its
own `fleet-config/clusters/<name>` activation root.

The stack installs Flux Operator only on this selected cluster. Additional
members require a manually created private OCI DevOps OKE environment and
dedicated deployment pipeline. After that pipeline succeeds, copy and edit
`fleet-config/bootstrap/member-template.yml` and apply the resulting
`bootstrap/<cluster>.yml`. Every member then pulls the shared repositories
independently; there are no remote kubeconfigs or hub-to-spoke API calls. See
the fleet repository's `docs/add-member.md` for the complete procedure.

Keep primary-cluster-only configuration in this repository. Put reusable fleet
profiles and explicit per-cluster activation in `fleet-config`.

## First-time bootstrap

### 1. Verify the prerequisites

In OCI Console, open **Resource Manager → Stacks → Jobs**. The latest apply job
must be `Succeeded`. In the created DevOps project, confirm that repositories
named `pipelines`, `cluster-config`, and `apps-config` exist.

The Resource Manager inputs must include:

- the target OKE cluster;
- a bootstrap runner subnet with access to the OKE private API endpoint and
  OCI services.

Before running the pipeline, follow the
[bootstrap access guide](docs/README.md). It walks through the two dedicated
runtime identities, least-privilege policies, auth tokens, Vault secrets, and
rotation. Do not reuse the administrator token entered in Resource Manager;
that credential is only for initial repository seeding.

### 2. Install Flux Operator

In the OCI DevOps project, run `bootstrap-gitops-agent` and set
`git_read_credentials_secret_ocid` to the Git Secret OCID and
`registry_pull_secret_ocid` to the OCIR Secret OCID. Leave
`chart_version=LATEST` or set an exact chart version. The pipeline:

1. mirrors Flux Operator and its required images into private OCIR;
2. starts `install-gitops-agent`;
3. creates the `flux-system` namespace, `ocirsecret`, and `git-token-auth`
   from OCI Vault;
4. installs Flux Operator with the native OKE Helm stage.

The pipeline is idempotent and safely updates its generated Secrets. Do not run
a second deployment while the triggered deployment is active. It does not
apply the Flux bootstrap resources.

`ocirsecret` is created only in `flux-system` for the mirrored controller
images. Application namespaces do not inherit it. If an application pulls from
private OCIR, provision a separate namespace-scoped pull Secret for that
application; never copy the Git reader credential into an application
namespace.

For shared-token migration and independent Git or OCIR rotation, follow
[Vault secrets and credential rotation](docs/runtime-secrets.md). Never revoke
the previous token before the installer has applied and verified the
replacement.

### 3. Connect to the private OKE API and clone this repository

Run the following commands from an administrator workstation or jump host that
can route to the OKE private API endpoint. Replace the placeholders with the
cluster OCID and region shown by Resource Manager:

```bash
oci ce cluster create-kubeconfig \
  --cluster-id <oke-cluster-ocid> \
  --region <region> \
  --file "$HOME/.kube/config" \
  --token-version 2.0.0 \
  --kube-endpoint PRIVATE_ENDPOINT

git clone <cluster-config-https-url>
cd cluster-config
git status --short

kubectl -n flux-system get pods
```

OCI DevOps uses an OCI Git username and auth token. Keep the token in a
credential manager, not in the clone URL.

### 4. Start Git reconciliation

From the root of this clone, apply the generated Flux bootstrap resources:

```bash
kubectl apply -f bootstrap/flux-bootstrap.yml
```

This is the only bootstrap manifest that an administrator normally applies
directly. It is safe to apply again: Kubernetes updates the same
`FluxInstance/flux` and `ResourceSet/flux-bootstrap`. The credential manifest
in `bootstrap/` is a sanitized recovery reference; the installation pipeline
has already created the real Secret from OCI Vault.

Wait for reconciliation and inspect any reported conditions:

```bash
kubectl -n flux-system get fluxinstances,resourcesets
kubectl -n flux-system get gitrepositories,kustomizations,helmreleases
kubectl -n flux-system describe resourceset flux-bootstrap
```

Expected objects include `ResourceSet/flux-bootstrap`,
`Kustomization/flux-platform`, `Kustomization/platform`,
`GitRepository/apps-config`, and generated component Kustomizations such as
`reference-app-frontend-dev` and `reference-app-api-staging`.

## Normal Git workflow

```bash
git switch main
git pull --ff-only
git switch -c add-platform-change

# edit files, then validate as described below

git add platform
git commit -m "Add platform change"
git push -u origin HEAD
```

Review the branch and merge it to `main`. Flux then reconciles the cluster. Do
not use `kubectl edit` for a managed resource; make the correction in Git.

## Configure the self-managed Flux Operator application

The deployment pipeline performs only the initial Helm installation. After
bootstrap, `HelmRelease/flux-operator` manages that same release from Git.

Both installation and self-management use the chart mirrored under the
stack's private OCIR `charts` repository. To upgrade, run the separate
`mirror-gitops-agent` pipeline with `chart_version=LATEST` or an exact version
and wait for chart and image mirroring to succeed. That pipeline does not
trigger `install-gitops-agent`; Flux reconciliation upgrades the release. The
build parameter does not edit Git. To pin or roll back, mirror the exact version
and set `spec.inputs[0].version` in
`platform/applications/flux-operator/resourceset.yml`.

Put normal changes in:

```text
platform/applications/flux-operator/values/90-user.yml
```

For example:

```yaml
resources:
  limits:
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 128Mi
```

The local `kustomization.yml` renders the files into a stable ConfigMap. The
ResourceSet passes its ordered `inputs.valuesFrom` list to the HelmRelease.
Flux applies entries in list order, so the last reference has the highest
precedence:

```yaml
valuesFrom:
  - kind: ConfigMap
    name: flux-operator-values
    valuesKey: 00-bootstrap.yaml
  - kind: ConfigMap
    name: flux-operator-values
    valuesKey: 90-user.yaml
```

To add another layer, add the file to both `configMapGenerator.files` and the
exact position you want in `inputs.valuesFrom`. Helm recursively combines maps,
later files override earlier files, and lists are normally replaced rather
than merged. The `valuesFrom` list—not filenames or the ConfigMap generator
order—is authoritative.

The initially seeded adapter applies this administrator-owned application:

```bash
kubectl -n flux-system get kustomization flux-operator
kubectl -n flux-system get helmrelease flux-operator
kubectl -n flux-system get pods
```

The stack generated only the initial private-registry values. It does not own
subsequent edits in the seeded Git repository. A future destructive repository
reseed is a migration operation and must be reviewed separately.

## Use case 1: cluster-wide Kustomize resources

Use this for non-namespaced resources such as `StorageClass`, `ClusterRole`,
`ClusterIssuer`, or cluster policy.

Create `platform/cluster-resources/storage/storage-class.yml`:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: example-block
provisioner: blockvolume.csi.oraclecloud.com
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

Create `platform/cluster-resources/storage/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - storage-class.yml
```

Add `storage` to `platform/cluster-resources/kustomization.yml`, then validate:

```bash
kubectl kustomize platform/cluster-resources
```

## Use case 2: namespaced infrastructure with Kustomize

The following ResourceSet creates namespace `team-platform` and a Flux
Kustomization that deploys administrator-owned resources into it.

Create `platform/applications/team-platform/resourceset.yml`:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: team-platform
  namespace: flux-system
spec:
  inputs:
    - name: team-platform
      namespace: team-platform
      resourcesPath: ./platform/applications/team-platform/resources
  resources:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: << inputs.namespace >>

    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 5m
        sourceRef:
          kind: GitRepository
          name: flux-system
        path: << inputs.resourcesPath >>
        targetNamespace: << inputs.namespace >>
        prune: true
        wait: true
        timeout: 3m
```

Create `platform/applications/team-platform/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - resourceset.yml
```

Create
`platform/applications/team-platform/resources/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - resource-quota.yml
```

Create `resources/resource-quota.yml`:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-limits
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
```

Finally add `team-platform` to
`platform/applications/kustomization.yml`.

## Use case 3: a Helm application

### Chart from a Helm repository

This ResourceSet deploys the upstream `kube-prometheus-stack` chart and an
additional Kustomize source as one platform application in `monitoring`.

Create
`platform/applications/kube-prometheus-stack/resourceset.yml`:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: kube-prometheus-stack
  namespace: flux-system
spec:
  dependsOn:
    - apiVersion: v1
      kind: ConfigMap
      name: kube-prometheus-stack-values
      namespace: flux-system
  inputs:
    - name: kube-prometheus-stack
      namespace: monitoring
      chart: kube-prometheus-stack
      version: 87.19.1
      repository: https://prometheus-community.github.io/helm-charts
      valuesFrom:
        - kind: ConfigMap
          name: kube-prometheus-stack-values
          valuesKey: 00-base.yaml
        - kind: ConfigMap
          name: kube-prometheus-stack-values
          valuesKey: 90-overrides.yaml
      resourcesPath: ./platform/applications/kube-prometheus-stack/resources
  resources:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: << inputs.namespace >>

    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 30m
        url: << inputs.repository >>

    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 30m
        releaseName: << inputs.name >>
        targetNamespace: << inputs.namespace >>
        chart:
          spec:
            chart: << inputs.chart >>
            version: << inputs.version | quote >>
            sourceRef:
              kind: HelmRepository
              name: << inputs.name >>
        valuesFrom: << inputs.valuesFrom | toYaml | nindent 10 >>

    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: << inputs.name >>-resources
        namespace: flux-system
      spec:
        interval: 5m
        sourceRef:
          kind: GitRepository
          name: flux-system
        path: << inputs.resourcesPath >>
        targetNamespace: << inputs.namespace >>
        prune: true
        wait: true
        timeout: 3m
```

Put base chart configuration in
`platform/applications/kube-prometheus-stack/values/00-base.yml`:

```yaml
grafana:
  enabled: true

prometheus:
  prometheusSpec:
    retention: 7d
```

Put cluster-specific overrides in
`platform/applications/kube-prometheus-stack/values/90-overrides.yml`:

```yaml
prometheus:
  prometheusSpec:
    retention: 15d
```

Create `platform/applications/kube-prometheus-stack/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - resourceset.yml

configMapGenerator:
  - name: kube-prometheus-stack-values
    namespace: flux-system
    files:
      - 00-base.yaml=values/00-base.yml
      - 90-overrides.yaml=values/90-overrides.yml

generatorOptions:
  disableNameSuffixHash: true
```

The stable ConfigMap name lets the HelmRelease consume both files through
`valuesFrom`. The ResourceSet waits for the ConfigMap before creating the
release. The effective retention is `15d` because `90-overrides.yaml` is the
last entry in `inputs.valuesFrom`.

Create `resources/kustomization.yml` as shown in use case 2, then add
`kube-prometheus-stack` to `platform/applications/kustomization.yml`. The
`resources/` directory can hold NetworkPolicies, dashboards, alert rules, or
other related manifests.

For KEDA, use `name: keda` and `namespace: keda`, repository
`https://kedacore.github.io/charts`, chart `keda`, and a pinned chart version.

### Chart stored directly in this Git repository

Put the chart in `platform/applications/internal-tool/chart/`. In the
HelmRelease above, remove the HelmRepository resource and replace `chart.spec`
with:

```yaml
chart:
  spec:
    chart: ./platform/applications/internal-tool/chart
    sourceRef:
      kind: GitRepository
      name: flux-system
      namespace: flux-system
```

Keep the ResourceSet, destination Namespace, HelmRelease, and optional
Kustomization together in the application directory.

## Advanced patterns

These patterns reuse the three use cases above. They do not introduce another
folder type.

### Helm plus additional Kustomize resources

A Helm ResourceSet can create both the HelmRelease and a Kustomization for
`resources/`. Use this for dashboards, alert rules, NetworkPolicies, or other
resources that share the release lifecycle.

### Operator plus custom resources

Do not apply custom resources until the HelmRelease that installs their CRDs
and controller is ready. Add a small readiness Kustomization:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: kube-prometheus-stack-ready
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./platform/applications/kube-prometheus-stack/ready
  prune: true
  wait: true
  healthChecks:
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: kube-prometheus-stack
      namespace: flux-system
```

Then make the custom-resource Kustomization depend on it:

```yaml
spec:
  dependsOn:
    - name: kube-prometheus-stack-ready
  path: ./platform/applications/kube-prometheus-stack/resources
  targetNamespace: monitoring
```

The `ready/` directory contains an empty `kustomization.yml`; its purpose is to
make the HelmRelease health check an explicit dependency gate.

### Multiple components in one namespace

Give every independently upgraded component its own ResourceSet and controller
object names, but use the same destination namespace:

```text
platform/applications/
  monitoring-metrics/     ResourceSet monitoring-metrics -> monitoring
  monitoring-logs/        ResourceSet monitoring-logs    -> monitoring
  monitoring-traces/      ResourceSet monitoring-traces  -> monitoring
```

This provides independent health, upgrades, rollback, and pruning. Only one
ResourceSet should create the shared Namespace, or all Namespace templates must
be identical. Never let two ResourceSets produce the same Kubernetes object.

### Explicit dependency boundaries

For a dependency between ResourceSets, use the dependent ResourceSet's
`spec.dependsOn`:

```yaml
spec:
  dependsOn:
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: cert-manager
      namespace: flux-system
```

Use a health-check Kustomization when dependent custom resources must wait for a
HelmRelease. Use ResourceSet `dependsOn` when the whole ResourceSet must wait
for another ready Kubernetes object.

See `examples/advanced/operator-and-custom-resources/` for a copyable pattern.

## Validate and verify

Render the platform and every resources directory you changed:

```bash
kubectl kustomize platform
kubectl kustomize platform/applications/<name>/resources
```

After merge:

```bash
flux reconcile kustomization platform --with-source
flux get kustomizations
kubectl -n flux-system get resourcesets,helmreleases,kustomizations
kubectl -n <namespace> get all
```

Without the Flux CLI, use `kubectl describe` on the ResourceSet,
Kustomization, HelmRelease, or source that is not ready.

## Rollback and deletion

Revert the Git commit:

```bash
git switch main
git pull --ff-only
git revert <bad-commit-sha>
git push origin main
```

Pruning is enabled. Removing an application from the platform Kustomization can
delete its ResourceSet and the resources produced from it. Review such changes
carefully.

## Security and troubleshooting

- Never commit tokens, passwords, kubeconfig files, or private keys.
- Use OCI Vault with External Secrets Operator and OKE Workload Identity for
  workload secrets; follow `docs/external-secrets.md`.
- Require administrator review for changes to `cluster-config`.
- A `GitRepository` authentication error usually means `git-token-auth` must be
  refreshed in `flux-system`. After rotating the Vault secret, run the
  `prepare-gitops-agent` stage as a single-stage deployment with both current
  Secret OCIDs. Mirroring does not update runtime credentials.
- For `ImagePullBackOff`, inspect the Pod and verify `ocirsecret`.
- A non-ready ResourceSet, Kustomization, or HelmRelease exposes the render or
  apply error in its status and Events.
