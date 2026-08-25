# Operate this cluster with Argo CD

This repository is the cluster administrator's source of truth for one OKE
cluster. A commit merged to `main` is a request for Argo CD to change the
cluster.

For normal tools, you do not need to write Argo CD Applications: the stack
installs ApplicationSets that discover small descriptors under
`platform/applications/`. An environment-aware application is the deliberate
exception. Its parent is generated from a descriptor, while its folder keeps
the infrastructure child and component ApplicationSet together so sync waves
can enforce readiness.

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

Do not add `namespace.yaml`. The generated Argo CD Application uses
`CreateNamespace=true`.

Application workloads owned by development teams belong in the separate
`apps-config` catalog. Administrators keep namespace infrastructure and the
explicit component/environment selections together under
`platform/applications/<name>/`. Fleet
activation follows the same application folder under
`fleet-config/clusters/<cluster>/applications/<name>/`.

## Documentation map

- [First-time bootstrap](#first-time-bootstrap)
- [Choose a supported use case](docs/use-cases.md)
- [Daily operations, rollback, and troubleshooting](docs/operations.md)
- [Guide for AI-assisted administration](docs/agent-guide.md)
- [Install the portable OKE Argo CD agent skill](docs/install-agent-skill.md)
- [Bootstrap security and access](docs/README.md)
  - [IAM identities and policies](docs/iam.md)
  - [Vault secrets and credential rotation](docs/runtime-secrets.md)
- [Secure Argo CD UI and RBAC access](docs/argocd-access.md)
- [Configure the self-managed Argo CD application](#configure-the-self-managed-argo-cd-application)
- [Optional native Argo CD fleet](#optional-native-argo-cd-fleet)

New administrators should complete bootstrap, read the use-case catalog, and
then use this README's copyable examples. An AI agent should read
`docs/agent-guide.md` before proposing a change. For a self-contained package
that can be installed into a local agent, use
`skills/manage-oke-with-argocd/` and follow the installation guide.

## Repository layout

```text
bootstrap/                         Generated bootstrap recovery manifests
gitops/argocd/                     Initially generated Argo CD adapter
  fleet.yml                        Optional native fleet adapter
platform/
  cluster-resources/               Cluster-scoped Kustomize resources
  applications/
    argocd/
      helm-repository.application.yaml
      values/
        00-bootstrap.yml           Initial private-registry settings
        90-user.yml                Administrator overrides
    <application>/
      *.application.yaml           One Argo CD discovery descriptor
      values/                      Ordered Helm values files
      chart/                       Optional Helm chart stored directly in Git
      resources/
        kustomization.yml          Additional namespaced Kustomize resources
    <environment-aware-app>/
      application.yaml             Parent discovery descriptor
      infrastructure/              Wave -10 child and namespace prerequisites
      components.application-set.yml Active wave 0 component selection
```

The stack provisions an initial repository template only. After the first
seed, every file—including `bootstrap/`, `gitops/argocd/`, and the Argo CD
self-management descriptor—is administrator-owned Git configuration.
Subsequent Resource Manager applies preserve repository content and prefer
customer Git changes.

## Optional native Argo CD fleet

`gitops/argocd/fleet.yml` is the optional native fleet adapter. This README
documents it even when `enable_multicluster = false` and the file is absent.
When enabled during initial provisioning, the stack creates `fleet-config` and
seeds `fleet.yml` with the normal platform delivery ApplicationSets plus a
logical-application parent ApplicationSet:

- cluster-wide Kustomize resources;
- namespaced Kustomize infrastructure;
- repository Helm plus optional Kustomize resources;
- Git-hosted Helm plus optional Kustomize resources;
- reusable component/environment deployments from `apps-config`, ordered
  after their infrastructure.

The fleet repository contains one directory per cluster object and one per
reusable umbrella profile. `cluster.yaml` selects exactly one cluster-resource
Kustomization; it is not an application descriptor. Bindings under
`clusters/<cluster>/applications/<binding>/` apply the profile's namespaced or
Helm payloads. An environment-aware application directory under
`clusters/<cluster>/applications/<name>/` contains its infrastructure and an
ApplicationSet listing the selected developer-owned component/environment
pairs. Argo CD selects the runtime cluster Secret with
`fleet.oke.oracle.com/cluster=<cluster>`.

Profiles may be shared across clusters or intentionally dedicated to one
cluster. All cluster-specific configuration, including small exceptions, uses
a dedicated profile so the fleet has one consistent payload model.

Finish this cluster's normal bootstrap first. Then follow the README in the
cloned `fleet-config` repository to register private managed-cluster endpoints
as Argo CD cluster Secrets and activate descriptors. Do not install Sveltos on
an Argo CD hub. Managed clusters run neither Argo CD nor Flux CD.

Keep hub-local configuration in this repository. Put only desired state
delivered to managed clusters in `fleet-config`. If fleet support was disabled
initially and is enabled later, review the proposed `fleet.yml` before adding
it; existing Git files remain customer-owned.

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

### 2. Install Argo CD

In the OCI DevOps project, run `bootstrap-gitops-agent` and set
`git_read_credentials_secret_ocid` to the Git Secret OCID and
`registry_pull_secret_ocid` to the OCIR Secret OCID. Leave
`chart_version=LATEST` or set an exact chart version. The pipeline:

1. mirrors the Argo CD chart and images into private OCIR;
2. starts `install-gitops-agent`;
3. creates the `argocd` namespace, the shared
   `oci-devops-git-credentials` `repo-creds` Secret, the `ocir-oci-repo` Helm
   repository Secret, and the `ocirsecret` image-pull Secret from OCI Vault;
4. installs Argo CD with the native OKE Helm stage.

The pipeline is idempotent and safely updates its generated Secrets. Do not run
a second deployment while the triggered deployment is active. It does not
apply the GitOps bootstrap Application.

`ocirsecret` is created only in `argocd` for the mirrored controller images.
Application namespaces do not inherit it. If an application pulls from private
OCIR, provision a separate namespace-scoped pull Secret for that application;
never copy the Git reader credential into an application namespace.

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

kubectl -n argocd get pods
```

OCI DevOps uses an OCI Git username and auth token. Keep the token in a
credential manager, not in the clone URL.

### 4. Start Git reconciliation

From the root of this clone, apply the generated bootstrap Application:

```bash
kubectl apply -f bootstrap/argocd-bootstrap.yml
```

This is the only bootstrap manifest that an administrator normally applies
directly. It is safe to apply again: Kubernetes updates the same
`Application/argocd-bootstrap`. The other credential manifests in
`bootstrap/` are sanitized recovery references; the installation pipeline has
already created the real Secrets from OCI Vault.

Wait for reconciliation and inspect any reported conditions:

```bash
kubectl -n argocd get applications,applicationsets
kubectl -n argocd describe application argocd-bootstrap
```

Expected controller objects include:

- `Application/argocd-bootstrap`
- `Application/argocd`
- `ApplicationSet/platform-cluster-resources`, which generates
  `Application/platform-cluster-resources`
- `ApplicationSet/platform-applications`, which generates parent
  `Application/reference-app`; that parent owns its infrastructure child and
  `ApplicationSet/reference-app-components` in sync-wave order
- `Application/reference-helm-app`, whose component ApplicationSet renders one
  selected umbrella subchart per component/environment with ordered value files
- Three additional `platform-*` ApplicationSets for platform applications

Argo CD also reconciles four authorization boundaries: restricted `default`
for bootstrap, `platform` for cluster administrators, `applications` for
developer-owned namespaced workloads, and optional `fleet` for managed
clusters. See [Secure Argo CD access](docs/argocd-access.md) for access and RBAC
configuration.

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

Review the branch and merge it to `main`. Argo CD then generates or updates the
Application and reconciles the cluster. Do not use `kubectl edit` for a managed
resource; make the correction in Git.

## Configure the self-managed Argo CD application

The deployment pipeline performs only the initial Helm installation. After
bootstrap, `Application/argocd` manages that same release from Git.

Both installation and self-management use the chart mirrored under the
stack's private OCIR `charts` repository. The generated descriptor uses
`version: "*"`, so it selects the newest chart version currently available in
that private repository. To upgrade safely, run the separate
`mirror-gitops-agent` pipeline with `chart_version=LATEST` or an exact version.
Wait for chart and image mirroring to succeed. That pipeline does not trigger
`install-gitops-agent`; Argo CD reconciliation upgrades the release. The build
parameter does not edit Git. To pin or roll back, mirror the exact version and
set `helm.version` to that version in
`platform/applications/argocd/helm-repository.application.yaml`.

Put normal changes in:

```text
platform/applications/argocd/values/90-user.yml
```

For example:

```yaml
server:
  service:
    type: ClusterIP

controller:
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
```

Commit and merge the change normally. Argo CD reads the file through its Git
values source and reconciles itself:

```bash
kubectl -n argocd get application argocd
kubectl -n argocd get pods
```

The ordered list is in
`platform/applications/argocd/helm-repository.application.yaml`:

```yaml
helm:
  valueFiles:
    - values/00-bootstrap.yml
    - values/90-user.yml
```

To add another layer, create the file and place it exactly where it should be
applied in this list. Argo CD passes the files to Helm in this order. Helm
recursively combines maps, later files override earlier files, and lists are
normally replaced rather than merged. The list is authoritative; filenames are
not sorted automatically.

The stack generated only `00-bootstrap.yml` initially. It does not own
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

Add the directory to `platform/cluster-resources/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - storage
```

Validate with:

```bash
kubectl kustomize platform/cluster-resources
```

## Use case 2: namespaced infrastructure with Kustomize

The following application creates namespace `team-platform` through Argo CD and
deploys administrator-owned resources into it.

Create
`platform/applications/team-platform/kustomize.application.yaml`:

```yaml
name: team-platform
namespace: team-platform
resourcesPath: platform/applications/team-platform/resources
```

Create `platform/applications/team-platform/resources/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - resource-quota.yml
```

Create `platform/applications/team-platform/resources/resource-quota.yml`:

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

The ApplicationSet detects the descriptor and generates
`Application/team-platform`. All manifests produced by this Kustomization are
deployed into `team-platform` unless a manifest explicitly sets another
namespace.

## Use case 3: a Helm application

### Chart from a Helm or OCI repository

This example deploys the upstream `kube-prometheus-stack` chart and additional
Kustomize resources as one Argo CD Application in namespace `monitoring`.

Create
`platform/applications/kube-prometheus-stack/helm-repository.application.yaml`:

```yaml
name: kube-prometheus-stack
namespace: monitoring
helm:
  repository: https://prometheus-community.github.io/helm-charts
  chart: kube-prometheus-stack
  version: 87.19.1
  releaseName: kube-prometheus-stack
  valueFiles:
    - values/00-base.yml
    - values/90-overrides.yml
resourcesPath: platform/applications/kube-prometheus-stack/resources
```

Create
`platform/applications/kube-prometheus-stack/values/00-base.yml`:

```yaml
grafana:
  enabled: true
prometheus:
  prometheusSpec:
    retention: 7d
```

Create
`platform/applications/kube-prometheus-stack/values/90-overrides.yml`:

```yaml
prometheus:
  prometheusSpec:
    retention: 15d
```

The effective retention is `15d` because `90-overrides.yml` is last in
`helm.valueFiles`.

Create
`platform/applications/kube-prometheus-stack/resources/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

# Add NetworkPolicies, dashboards, alert rules, or other related resources.
resources: []
```

The generated Application has three sources: the chart, this Git repository as
the values source, and `resources/` as the Kustomize source. Keep related
resources together; if they need an independent lifecycle or permissions,
create another platform application.

`gitops/argocd/platform.yml` uses `templatePatch` because Go templating cannot
render the variable-length `helm.valueFiles` array inside the normal
ApplicationSet template. The patch repeats all three sources intentionally.
ApplicationSet applies a merge patch, and arrays such as `spec.sources` are
replaced as one value rather than merged item by item. Patching only the chart
source would therefore remove the `$values` source and the Kustomize
`resourcesPath` source. The repeated entries preserve the full multi-source
Application while adding the ordered values list.

For a tool whose namespace matches its name, use the same value for both:

```yaml
name: keda
namespace: keda
helm:
  repository: https://kedacore.github.io/charts
  chart: keda
  version: 2.20.1
  releaseName: keda
  valueFiles:
    - values/00-base.yml
resourcesPath: platform/applications/keda/resources
```

### Chart stored directly in this Git repository

Put the chart below the application directory and use a Git descriptor:

```text
platform/applications/internal-tool/
  helm-git.application.yaml
  values/00-base.yml
  chart/Chart.yaml
  chart/templates/
  resources/kustomization.yml
```

`helm-git.application.yaml`:

```yaml
name: internal-tool
namespace: internal-tool
helm:
  path: platform/applications/internal-tool/chart
  releaseName: internal-tool
  valueFiles:
    - values/00-base.yml
resourcesPath: platform/applications/internal-tool/resources
```

## Advanced patterns

These patterns reuse the three use cases above. They do not introduce another
folder type.

### Helm plus additional Kustomize resources

Every generated Helm Application already includes `resources/` as a third
source. Use it for resources that belong to the same lifecycle as the chart,
such as dashboards, alert rules, or NetworkPolicies. Keep the directory with an
empty `kustomization.yml` until it is needed.

### Operator plus custom resources

Keep the operator chart and its custom resources in the same platform
application. Helm resources use the default sync wave `0`. Annotate resources
that require the operator CRDs with a later wave:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: platform-alerts
  annotations:
    argocd.argoproj.io/sync-wave: "1"
spec:
  groups: []
```

Argo CD waits for wave `0` to become healthy before applying wave `1`.
Generated Applications also use `SkipDryRunOnMissingResource=true`, allowing
the first sync to render custom resources before their CRDs exist.

Use consecutive waves when more stages are required:

```text
-1  prerequisites that must exist first
 0  chart and normal resources
 1  custom resources that require the operator
 2  configuration that requires those custom resources
```

Do not use sync waves to join unrelated tools. If a dependent resource has a
different owner, permissions boundary, or rollback lifecycle, keep it in a
separate application and accept that Argo CD will retry it until its dependency
is healthy.

### Multiple components in one namespace

Give every independently upgraded component its own application directory and
unique Argo CD Application name, but set the same namespace:

```text
platform/applications/
  monitoring-metrics/     name: monitoring-metrics, namespace: monitoring
  monitoring-logs/        name: monitoring-logs, namespace: monitoring
  monitoring-traces/      name: monitoring-traces, namespace: monitoring
```

This provides independent health, upgrades, rollback, and pruning while keeping
the logical platform in namespace `monitoring`. Never let two Applications
produce the same Kubernetes object.

### Explicit dependency boundaries

Argo CD does not provide a general `dependsOn` relationship between independent
Applications. Use one of these designs:

1. Same lifecycle: put the Helm source and dependent Kustomize resources in one
   multi-source Application and use sync waves.
2. Independent lifecycle: use separate Applications and make the dependent
   manifests safe to retry until the prerequisite exists.
3. Hard cross-application orchestration: require an explicit higher-level
   design rather than hiding the dependency in directory order.

See `examples/advanced/operator-and-custom-resources/` for a copyable pattern.

## Validate and verify

Render every Kustomize directory you changed:

```bash
kubectl kustomize platform/cluster-resources
kubectl kustomize platform/applications/<name>/resources
```

After merge:

```bash
kubectl -n argocd get applications,applicationsets
kubectl -n argocd describe application <name>
kubectl -n <namespace> get all
```

If the Application is not generated, check that the descriptor has exactly one
of the supported filenames and that every required field is present.

## Rollback and deletion

Revert the Git commit:

```bash
git switch main
git pull --ff-only
git revert <bad-commit-sha>
git push origin main
```

Pruning is enabled. Removing a descriptor deletes its generated Application and
the resources managed by that Application. Review such changes carefully.

## Security and troubleshooting

- Never commit tokens, passwords, kubeconfig files, or private keys.
- Prefer OCI Vault with External Secrets, or another encrypted secret workflow.
- Require administrator review for changes to `cluster-config`.
- A repository authentication error usually means the corresponding Secret in
  `argocd` must be refreshed. After rotating the Vault secret, run the
  `prepare-gitops-agent` stage as a single-stage deployment with both current
  Secret OCIDs. Mirroring does not update runtime credentials.
- For `ImagePullBackOff`, inspect the Pod and verify `ocirsecret`.
- For `OutOfSync` or `Degraded`, inspect the Application diff, conditions, and
  the unhealthy Kubernetes resource.
