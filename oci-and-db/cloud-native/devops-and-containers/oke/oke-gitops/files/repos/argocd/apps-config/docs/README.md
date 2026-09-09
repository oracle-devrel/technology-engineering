# Developer documentation

Use this documentation to build and release applications through GitOps. This
repository contains reusable application code and configuration; it does not
choose which OKE cluster receives an application.

## Choose a guide

| Task | Guide |
|---|---|
| Understand every developer use case and its impacted files | [Use-case table](use-cases.md) |
| Build or modify a Kustomize component | [Kustomize applications](kustomize.md) |
| Build an umbrella Helm application or decide where values belong | [Helm applications and values](helm.md) |
| Request deployment, release a component, verify, or roll back | [Delivery workflow](delivery.md) |

## The short version

For Kustomize, put reusable resources in a component `base/` and put the image
and environment-specific patches in that component's
`environments/<environment>/` overlay.

For Helm, values have three scopes:

| Scope | Location | Example content |
|---|---|---|
| Component defaults, shared by all environments | `applications/<app>/helm/charts/<component>/values.yaml` | Default port, probes, resource requests, image repository |
| Application globals, shared by all components/environments | `applications/<app>/helm/values.yaml` | Application identity and all subcharts disabled by default |
| Component release values for one environment | `applications/<app>/helm/values/<environment>/<component>.yml` | Enable that component, image tag, replicas, environment configuration |

For a routine Helm release, developers normally change only:

```text
applications/<app>/helm/values/<environment>/<component>.yml
```

For example, the dev frontend image belongs in:

```text
applications/reference-helm-app/helm/values/dev/frontend.yml
```

Never put a password, token, private key, or other secret value in any of these
files. Use OCI Vault and an `ExternalSecret` reference.

The application catalog remains identical whether the cluster administrator
selects Argo CD or Flux. Controller-specific placement and reconciliation
objects belong in `cluster-config` or `fleet-config`, never here.
