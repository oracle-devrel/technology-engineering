# Developer applications

## Kustomize catalog

```text
apps-config/applications/<app>/kustomize/components/<component>/
  base/
  environments/{dev,staging,production}/
```

The base owns resources common to all environments. Each component environment
overlay references its base, targets namespace `<app>`, adds suffix
`-<environment>`, owns the image tag and local patches, and adds application,
component, instance, and environment labels. There is no application-level
environment aggregator.

A base change affects every active environment of that component. An overlay
change affects only that component/environment.

## Umbrella Helm catalog

```text
apps-config/applications/<app>/helm/
  Chart.yaml
  values.yaml
  charts/<component>/{Chart.yaml,values.yaml,templates/}
  values/{dev,staging,production}/<component>.yml
```

Value placement and precedence:

1. `charts/<component>/values.yaml`: defaults for that component in every
   environment, including image repository, ports, probes, and resources.
2. `helm/values.yaml`: application globals and every subchart disabled.
3. `helm/values/<environment>/<component>.yml`: enable exactly one component;
   own the deployed image tag and environment-specific release values.

Argo passes files 2 and 3 in that order. Helm first loads subchart defaults.
Later map keys win; lists normally replace. If adding another values layer,
update every relevant component ApplicationSet explicitly and preserve order.

## Placement handoff

Developers provide application, components, environments, resource needs,
network needs, secrets/workload identity needs, and private image requirements.
Administrators own namespace infrastructure and select pairs in
`components.application-set.yml` locally or below a fleet cluster.

Application repositories never own Namespace, ResourceQuota, LimitRange, or
shared NetworkPolicy objects. Standard environments are exactly `dev`,
`staging`, and `production`; several can coexist in the same application
namespace.

## Secrets

Never commit Secret values, including base64. Commit only a sanitized
`ExternalSecret` after an administrator configures External Secrets Operator,
an OCI Vault SecretStore, workload identity, and IAM policy.
