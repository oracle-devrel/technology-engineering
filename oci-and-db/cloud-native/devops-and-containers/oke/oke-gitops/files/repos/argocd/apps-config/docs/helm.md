# Develop an umbrella Helm application

Use this model when one application contains several components implemented as
subcharts. The delivery adapter deploys each selected component/environment
pair separately, so a frontend release does not roll out the API.

## Directory contract

```text
applications/<app>/helm/
  Chart.yaml
  values.yaml
  charts/
    <component>/
      Chart.yaml
      values.yaml
      templates/
  values/
    dev/
      <component>.yml
    staging/
      <component>.yml
    production/
      <component>.yml
```

The supported environment names are exactly `dev`, `staging`, and
`production`.

## Where values belong

### Component defaults

Put settings that are valid for one component in every environment in:

```text
helm/charts/<component>/values.yaml
```

Typical component defaults are:

- image repository and pull policy;
- container and Service ports;
- health probe defaults;
- safe CPU and memory requests and limits;
- common feature defaults.

Example:

```yaml
enabled: false
replicaCount: 1
image:
  repository: docker.io/example/frontend
  tag: 1.0.0
  pullPolicy: IfNotPresent
service:
  port: 80
resources:
  requests:
    cpu: 50m
    memory: 64Mi
```

Do not put a dev or production image tag here unless every environment must use
that exact tag. A change to this file affects every active environment of this
component that does not override the changed key.

### Application-wide global values

Put values shared across the application in:

```text
helm/values.yaml
```

Keep every component disabled here. This allows one generated reconciliation
object to render only its selected component:

```yaml
global:
  application: payments
  component: unset
  environment: unset
  instance: unset

frontend:
  enabled: false

api:
  enabled: false
```

Use Helm's `global` map only for data genuinely consumed by several subcharts.
Component-only values belong under that component or in its subchart defaults.

### Environment and release values

Put the final values for one component in one environment in:

```text
helm/values/<environment>/<component>.yml
```

This file must enable exactly one component. It normally owns the deployed
image tag and environment-specific settings:

```yaml
global:
  application: payments
  component: frontend
  environment: dev
  instance: payments-dev

frontend:
  enabled: true
  image:
    tag: 1.4.7
  replicaCount: 1
```

Do not enable `api`, `worker`, or another component in this file. Doing so would
make two generated reconciliation objects capable of owning the same objects.

## Effective precedence

Helm computes the selected release in this order:

1. `charts/<component>/values.yaml` supplies the subchart defaults.
2. `helm/values.yaml` supplies umbrella application defaults and disables all
   components.
3. `helm/values/<environment>/<component>.yml` enables one component and
   supplies the final environment overrides.

Later values win for the same map key. Maps merge recursively; lists normally
replace rather than merge.

The controller adapter explicitly passes the last two files in this order.
Argo CD uses `helm.valueFiles`; Flux uses
`HelmRelease.spec.chart.spec.valuesFiles`:

```yaml
helm:
  valueFiles:
    - $values/applications/<app>/helm/values.yaml
    - $values/applications/<app>/helm/values/{{ .environment }}/{{ .component }}.yml
```

The order in the ApplicationSet or ResourceSet-generated HelmRelease is
authoritative. Filenames are not automatically sorted. The reference contract
deliberately uses one global file and one final component/environment file. If
the application truly needs another layer, add it at the intended position in
every relevant controller binding.

## Add a component

1. Add the component dependency to the umbrella `Chart.yaml` with an
   `enabled` condition:

   ```yaml
   dependencies:
     - name: worker
       version: 0.1.0
       repository: file://charts/worker
       condition: worker.enabled
   ```

2. Add `charts/worker/` with its chart metadata, defaults, and templates.
3. Add `worker.enabled: false` to the umbrella `values.yaml`.
4. Add `values/dev/worker.yml`, `values/staging/worker.yml`, and
   `values/production/worker.yml`; each enables only `worker`.
5. Render all three combinations.
6. Ask the administrator to add only the required pairs to the appropriate
   Argo CD ApplicationSet or Flux ResourceSet.

## Validate

From the repository root:

```bash
helm dependency list applications/<app>/helm

helm lint applications/<app>/helm \
  -f applications/<app>/helm/values.yaml \
  -f applications/<app>/helm/values/dev/<component>.yml

helm template <app>-<component>-dev applications/<app>/helm \
  --namespace <app> \
  -f applications/<app>/helm/values.yaml \
  -f applications/<app>/helm/values/dev/<component>.yml
```

Inspect the rendered result and confirm:

- only the selected component is present;
- resource names include component and environment;
- labels identify application, component, instance, and environment;
- the namespace is the application name;
- Services are appropriate for the platform exposure design;
- resource requests and limits are present;
- no secret value is rendered.

Repeat lint and template for every component across all three environments.

## Release one component

To release only frontend in dev, change only:

```text
applications/<app>/helm/values/dev/frontend.yml
```

Render it, review the diff, and merge. Every cluster whose administrator has
activated frontend/dev will reconcile that catalog change. The API and other
component reconciliation objects receive no desired-state change.

With Flux and a GitRepository chart source, `reconcileStrategy: Revision`
packages a new chart artifact for every Git revision. Helm controller may
therefore record no-op upgrades for the other component HelmReleases. Their
rendered manifests and Deployment pod templates remain unchanged; only the
component whose values changed receives a new ReplicaSet. A chart-source change
correctly affects every selected component because the umbrella chart is shared.
