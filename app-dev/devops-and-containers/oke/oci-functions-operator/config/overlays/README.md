# Kustomize Overlays

OKE deployment overlays are deprecated. Helm is the supported OKE installation
path and owns controller image, RBAC, CRDs, service account, and OCI auth
environment configuration.

Keep the generated Kubebuilder directories under `config/crd`, `config/rbac`,
`config/manager`, `config/default`, and `config/samples` for controller
development. Do not mix Helm and Kustomize resources for the same cluster
install.
