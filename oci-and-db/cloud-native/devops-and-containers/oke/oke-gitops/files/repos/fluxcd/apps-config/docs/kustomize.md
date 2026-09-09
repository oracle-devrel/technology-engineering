# Develop a Kustomize application

Use one reusable base and three component-local environment overlays. Each
component/environment overlay is an independent GitOps deployment unit.

## Directory contract

```text
applications/<app>/kustomize/components/<component>/
  base/
    kustomization.yml
    deployment.yml
    service.yml
  environments/
    dev/
      kustomization.yml
      deployment-patch.yml
    staging/
      kustomization.yml
      deployment-patch.yml
    production/
      kustomization.yml
      deployment-patch.yml
```

## What goes in the base

The base owns configuration shared by every environment of that component:

- the Deployment, Service, ConfigMap, and similar workload resources;
- the image repository and a valid default tag;
- ports and probes;
- security context;
- resource requests and limits;
- stable application and component labels.

The base must not create a Namespace, ResourceQuota, LimitRange, or shared
NetworkPolicy. Those are administrator-owned application infrastructure.

## What goes in an environment overlay

The component's environment overlay owns:

- `namespace: <app>`;
- `nameSuffix: -<environment>`;
- the deployed image tag;
- application instance and environment labels;
- environment-specific Deployment or configuration patches.

Example `environments/dev/kustomization.yml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: payments
nameSuffix: -dev

resources:
  - ../../base

images:
  - name: docker.io/example/frontend
    newTag: 1.4.7

labels:
  - includeSelectors: true
    pairs:
      app.kubernetes.io/instance: payments-dev
      app.kubernetes.io/environment: dev

patches:
  - path: deployment-patch.yml
```

For a routine release, change only `images[].newTag` in the selected
component/environment overlay. A base change affects every active environment
of that component; an overlay change affects only that one deployment unit.

## Add a component

1. Add the component base.
2. Add `dev`, `staging`, and `production` overlays even if some will remain
   inactive.
3. Ensure the rendered names are `<component>-<environment>`.
4. Render the base and every overlay.
5. Ask the administrator to add the required pairs to the target cluster's
   Argo CD ApplicationSet or Flux ResourceSet.

There is no application-level environment aggregator and no repository-root
activation Kustomization.

## Validate

```bash
kubectl kustomize applications/<app>/kustomize/components/<component>/base
kubectl kustomize applications/<app>/kustomize/components/<component>/environments/dev
kubectl kustomize applications/<app>/kustomize/components/<component>/environments/staging
kubectl kustomize applications/<app>/kustomize/components/<component>/environments/production
```

Confirm that environments sharing the application namespace do not render
duplicate resource identities.
