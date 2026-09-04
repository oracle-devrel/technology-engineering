# Fleet repository seeds

This directory is stack source, not a repository seed itself. Terraform
selects exactly one child directory according to `gitops_agent`:

- `argocd/` becomes the complete `fleet-config` repository for an Argo CD hub.
- `fluxcd/` becomes the shared catalog consumed independently by decentralized
  Flux members; it does not create a Flux hub.

Do not place generated-repository content at this level. Engine-specific
documentation, examples, manifests, and helper scripts belong entirely below
the corresponding child directory. This prevents customers from receiving
instructions or resources for an engine they did not select.
