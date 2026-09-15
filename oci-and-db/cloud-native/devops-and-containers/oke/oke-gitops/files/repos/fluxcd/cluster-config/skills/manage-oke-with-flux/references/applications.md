# Applications

## Administrator-owned tools

Use a single application folder and ResourceSet for namespace creation plus
its related delivery objects. A namespaced Kustomize tool creates a
Kustomization targeting `<app>`. Repository or OCI Helm creates the matching
source and HelmRelease; a Git-hosted chart uses the existing cluster-config
GitRepository. Helm plus YAML creates both HelmRelease and Kustomization.

For an operator and custom resources, install the HelmRelease first, gate on
its health with a small readiness Kustomization, and make the custom-resource
Kustomization depend on that gate. Never rely on incidental reconciliation
order.

## Developer Kustomize catalog

```text
apps-config/applications/<app>/kustomize/components/<component>/
  base/
  environments/{dev,staging,production}/
```

Each component overlay references its base, targets namespace `<app>`, adds
suffix `-<environment>`, owns its image and patches, and adds application,
component, instance, and environment labels. A base change affects each active
environment of that component; an overlay change affects one pair.

## Developer umbrella Helm catalog

```text
apps-config/applications/<app>/helm/
  Chart.yaml
  values.yaml
  charts/<component>/{Chart.yaml,values.yaml,templates/}
  values/{dev,staging,production}/<component>.yml
```

Subchart values hold component defaults. Global `helm/values.yaml` disables
all components. The selected environment/component file enables exactly one
subchart and owns its image and environment settings. Flux loads those two
files in that order through HelmRelease `chart.spec.valuesFiles`.

## Placement and secrets

The catalog never selects a cluster or owns Namespace, ResourceQuota,
LimitRange, or shared NetworkPolicy. Administrators select pairs locally or in
a fleet profile. Commit no Secret values or populated Secrets. Use sanitized
ExternalSecret references only after ESO, OCI Vault, OKE Workload Identity,
and least-privilege IAM are configured.
