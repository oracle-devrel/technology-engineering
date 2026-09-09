# Operator and custom resources

Copy this directory to
`platform/applications/kube-prometheus-stack/`, then add that directory to
`platform/applications/kustomization.yml`.

The ResourceSet installs the chart, creates a readiness Kustomization that
checks the HelmRelease, and deploys the `PrometheusRule` only after that
readiness gate succeeds.

Edit the files under `values/` for normal chart configuration. The local
Kustomization renders them as separate keys in
`ConfigMap/kube-prometheus-stack-values`. The ordered `inputs.valuesFrom` list
in `resourceset.yml` defines precedence; later entries override earlier ones.

Pin and test the chart version before production use.
