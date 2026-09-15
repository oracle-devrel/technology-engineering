# Safety contract

- Inspect before editing. Preserve unrelated and uncommitted user changes.
- Never commit tokens, passwords, private keys, kubeconfigs, populated Secrets,
  or plaintext/base64 secret values.
- Never use a public spoke API endpoint in Argo CD.
- Never create the same Kubernetes object from two Applications.
- Never add a Namespace manifest to a local Argo application.
- Never silently choose a cluster, namespace, application, component, or
  environment when ambiguity changes the outcome.
- Never remove a descriptor, selection, or Kustomize reference without stating
  exactly what automated pruning can delete.
- Never run `kubectl apply` for normal managed desired state. The one generated
  bootstrap Application is the explicit exception.
- Never run a pipeline, push/merge Git, rotate credentials, modify IAM, register
  a cluster, or mutate a live cluster without user authorization.
- Prefer private endpoints, workload identity, dedicated read-only runtime
  credentials, least privilege, small bounded resources, and ClusterIP Services
  unless an approved exposure design requires otherwise.
- Validate locally before any external mutation. If validation cannot run,
  report the missing tool or dependency instead of claiming success.
