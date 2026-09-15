# Operator and custom resources

Copy this directory to
`platform/applications/kube-prometheus-stack/`. The ApplicationSet discovers
the descriptor, installs the Helm chart at sync wave `0`, waits for it to
become healthy, and then applies the `PrometheusRule` at wave `1`.

The descriptor's ordered `helm.valueFiles` list defines Helm precedence. Later
files override earlier files; directory or filename sorting is not used.

Pin and test the chart version before production use.
