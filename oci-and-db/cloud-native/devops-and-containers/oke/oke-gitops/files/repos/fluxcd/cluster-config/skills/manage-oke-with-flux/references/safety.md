# Safety contract

- Inspect before editing and preserve unrelated or uncommitted user changes.
- Never commit tokens, passwords, private keys, kubeconfigs, populated Secrets,
  or plaintext/base64 secret values.
- Never silently select a cluster, profile, namespace, application, component,
  or environment when ambiguity changes the outcome.
- Never create the same Kubernetes identity from two ResourceSets or inputs.
- Never remove an input, Kustomization resource, profile activation, or source
  without stating what Flux pruning can delete.
- Never apply ordinary managed desired state directly with kubectl. The
  generated initial bootstrap manifest is the explicit exception.
- Never push/merge Git, run a pipeline, apply bootstrap, rotate credentials,
  modify IAM/Vault, or mutate a cluster without user authorization.
- Additional members use a private OKE DevOps environment. Do not automate
  extra environments/pipelines into Resource Manager or invent a Flux hub.
- Prefer workload identity, dedicated read-only runtime credentials, least
  privilege, bounded resources, and ClusterIP Services unless approved.
- Validate locally before mutation. Report missing tools instead of claiming
  validation succeeded.
