# Platform applications

Create one directory per application. "Infrastructure" and "custom" describe
ownership, not different Git directory types. A tool directory normally
contains a ResourceSet and
an optional `resources/` Kustomize source. Every Helm application also keeps an
explicit ordered set of files under `values/`; the local Kustomization renders
them into the ConfigMap consumed by the HelmRelease. The ResourceSet's
`inputs.valuesFrom` list determines precedence.

Add the application directory to this folder's `kustomization.yml`. The
ResourceSet creates the destination Namespace and the Flux reconciliation
objects. Do not add a standalone `namespace.yml`.

`flux-operator/` is the bootstrap-created self-managed Flux Operator
application. Its ResourceSet and `values/` files are administrator-owned after
the first repository seed.

`reference-app/` keeps namespace infrastructure and component activation in
one application folder. Its `infrastructure` ResourceSet creates namespace
`reference-app` and reconciles quota, limits, and shared NetworkPolicies. The
`components` ResourceSet generates one Kustomization per selected
component/environment pair. Every generated Kustomization depends on
`Kustomization/reference-app-infrastructure`. Components have no ordering
dependency. Production overlays exist in the catalog but are intentionally
inactive.

`reference-helm-app/` uses the same infrastructure/components boundary for
the shared umbrella Helm catalog. Its component ResourceSet generates one
HelmRelease per selected component/environment pair, loading
`helm/values.yaml` first and the selected
`helm/values/<environment>/<component>.yml` second. Dev and staging are active;
production remains renderable but inactive.

See the repository root README for complete Kustomize, Helm repository, and
Git-hosted Helm examples.
The copyable operator-readiness example is under
`examples/advanced/operator-and-custom-resources/`.
