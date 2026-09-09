# Develop reusable custom applications

This repository is a developer-owned application catalog. It does not select a
cluster and has no root reconciliation object. Cluster administrators deploy
catalog entries through bindings in `cluster-config` or `fleet-config`.

## Start here

1. Open the [developer documentation index](docs/README.md).
2. Read the [application use-case and file-impact table](docs/use-cases.md).
3. Follow the [Kustomize](docs/kustomize.md) or
   [Helm and values](docs/helm.md) guide.
4. Use the [delivery workflow](docs/delivery.md) to request placement, release,
   verify, and roll back a component.

For a normal Helm release, put the environment-specific values and image tag
in exactly this file:

```text
applications/<app>/helm/values/<environment>/<component>.yml
```

Component defaults shared by all environments belong in
`helm/charts/<component>/values.yaml`. Values genuinely shared by the complete
application belong in `helm/values.yaml`. See the Helm guide for precedence and
copyable examples.

## Ownership model

| Repository | Owner | Responsibility |
|---|---|---|
| `apps-config` | Application developers | Components, images, and environment overlays |
| `cluster-config` | Cluster administrators | Application infrastructure and local-cluster activation |
| `fleet-config` | Fleet administrators | Application infrastructure and managed-cluster activation |

The supported environments are exactly `dev`, `staging`, and
`production`. Several environments may run in the application's one
same-named namespace.

## Catalog layout

```text
applications/
  reference-app/
    kustomize/
      components/
        frontend/
          base/
          environments/{dev,staging,production}/
        api/
          base/
          environments/{dev,staging,production}/
  reference-helm-app/
    helm/
      Chart.yaml
      values.yaml
      charts/{frontend,api}/
      values/
        dev/{frontend,api}.yml
        staging/{frontend,api}.yml
        production/{frontend,api}.yml
examples/
```

A component base contains resources shared by every environment. Each component
environment overlay references only that component base, owns its image version
and environment-specific patches, adds `-<environment>` to resource names,
targets namespace `reference-app`, and adds application, component, instance,
and environment labels.

There is no application-level environment aggregator. Each component overlay
is an independent deployment unit. Administrator-owned activation selects the
required component/environment combinations.

`reference-helm-app` provides the equivalent workflow for Helm. Its `helm/`
directory contains the umbrella chart, vendored subcharts, the sole global
`values.yaml`, and one obvious component values file under each environment.
Every component reconciliation loads global values first and then
`values/<environment>/<component>.yml`, which enables exactly one subchart.
This preserves each component/environment pair as a sync and rollback boundary.

The complete placement-independent values precedence is:

1. `helm/charts/<component>/values.yaml`: component defaults;
2. `helm/values.yaml`: application globals and every component disabled;
3. `helm/values/<environment>/<component>.yml`: enable one component and apply
   its environment-specific release values.

## Validate the catalog

There is intentionally no repository-root `kustomization.yml`. Render the
reusable units directly:

```bash
kubectl kustomize applications/reference-app/kustomize/components/frontend/base
kubectl kustomize applications/reference-app/kustomize/components/api/base
kubectl kustomize applications/reference-app/kustomize/components/frontend/environments/dev
kubectl kustomize applications/reference-app/kustomize/components/api/environments/dev
kubectl kustomize applications/reference-app/kustomize/components/frontend/environments/production
helm dependency list ./applications/reference-helm-app/helm
helm lint ./applications/reference-helm-app/helm \
  -f applications/reference-helm-app/helm/values.yaml \
  -f applications/reference-helm-app/helm/values/dev/frontend.yml
helm template reference-helm-app-frontend-dev ./applications/reference-helm-app/helm \
  --namespace reference-helm-app \
  -f applications/reference-helm-app/helm/values.yaml \
  -f applications/reference-helm-app/helm/values/dev/frontend.yml
```

Every environment must render unique `<component>-<environment>` identities.
Application repositories must not contain Namespace, ResourceQuota, LimitRange,
or shared NetworkPolicy resources.

## Change one component image

The dev frontend image is owned by:

```text
applications/reference-app/kustomize/components/frontend/environments/dev/kustomization.yml
```

Change only `images[].newTag`, render that component overlay, review,
and push:

```bash
kubectl kustomize applications/reference-app/kustomize/components/frontend/environments/dev
git diff
git add applications/reference-app/kustomize/components/frontend/environments/dev/kustomization.yml
git commit -m "Update reference frontend in dev"
git push
```

Normal GitOps object-level diffing updates only `Deployment/frontend-dev`.
Other component Deployments retain their pod templates. Every cluster binding
that selects this same dev catalog path receives the update; use a separate
reviewed overlay when clusters intentionally require different desired state.

For Helm, change the selected component image tag in
`helm/values/<environment>/<component>.yml`. Argo CD syncs only that generated
Application. Flux may refresh each HelmRelease chart artifact because the
shared Git source revision changed, but unchanged rendered Deployments retain
their pod templates; only the selected component rolls out.

## Request a local-cluster deployment

Before placement, the cluster administrator defines the application's
same-named namespace, quota, limits, shared NetworkPolicies, and selected
component/environment pairs together in `cluster-config`.

The included application parent is:

```text
cluster-config/platform/applications/reference-app/
```

Argo CD uses an infrastructure child at sync wave `-10` and a component
ApplicationSet at wave `0`. Flux uses an infrastructure Kustomization and one
dependent component Kustomization per selected pair. Pairs may be added or
removed without changing catalog content.

```bash
kubectl -n argocd get application,applicationset
kubectl -n flux-system get resourceset,kustomization,helmrelease
kubectl -n reference-app get deployments,pods,services
```

## Request a managed-cluster deployment

For Argo CD, the fleet administrator creates:

```text
fleet-config/clusters/<cluster>/applications/<application>/
  application.yaml
  infrastructure/application.yml
  components.application-set.yml
```

The parent selects the registered cluster. Its infrastructure child reads the
selected fleet profile and its component ApplicationSet points to this repository.
Repeating the application folder for another cluster reuses the same catalog
content and preserves infrastructure-first ordering. For decentralized Flux,
the equivalent placement is a local ResourceSet in a reusable fleet profile;
every member reconciles the same catalog through its own
`GitRepository/apps-config`.

## Add an application or component

1. Use `applications/<application>/kustomize/` for Kustomize components and
   `applications/<application>/helm/` for umbrella Helm components.
2. Add Kustomize overlays or Helm values files for all three standard
   environments.
3. Let administrators select the required component/environment combinations.
4. Render every base and component environment overlay.
5. Ask administrators to add one application folder containing infrastructure
   and the required component/environment selections.

Keep Services as `ClusterIP` unless a reviewed ingress design says otherwise.
Specify small resource requests and limits, use architecture-compatible images,
and do not add PVCs to examples.

Both Argo CD and decentralized Flux preserve one reconciliation and rollback
boundary per Helm component/environment pair.

## Rollback and pruning

Revert a faulty application commit in this repository to roll every binding
back to the previous desired state:

```bash
git log --oneline
git revert <bad-commit-sha>
git push
```

Removing a local or fleet binding is an administrator action and prunes only
that environment from that target cluster. Namespace infrastructure should be
removed only after every binding and retained workload has been handled.

## Secrets

Never commit Secret values, including base64-encoded values. Store secrets in
OCI Vault and commit only sanitized External Secrets references after the
administrator installs and configures External Secrets Operator. See
`examples/external-secret.yml` and `oci-secret.sh`.
