---
name: manage-oke-with-flux
description: Manage Oracle Kubernetes Engine clusters through this solution's decentralized Flux GitOps repositories. Use for bootstrapping or observing Flux, changing cluster-scoped or namespaced resources, deploying Helm charts, managing environment-aware Kustomize or umbrella-Helm applications, releasing one component, using OCI Vault ExternalSecrets, onboarding or configuring independent fleet members, validating changes, analyzing pruning impact, troubleshooting reconciliation, and rolling back through Git in cluster-config, apps-config, or fleet-config.
---

# Manage OKE with Flux

Operate OKE through Git. Treat Git as desired state and Flux/Kubernetes as
observation surfaces. Do not repair managed objects directly.

## Start every task

1. Locate the repository and run `scripts/preflight.sh [path]`.
2. Identify the target cluster, namespace, application, component, and
   environment. Do not guess when ambiguity changes placement.
3. Classify the request with [references/use-cases.md](references/use-cases.md).
4. Read [references/repository-contracts.md](references/repository-contracts.md).
5. Read only the task-specific reference:
   - local platform or developer application:
     [references/applications.md](references/applications.md);
   - decentralized member or profile:
     [references/fleet.md](references/fleet.md);
   - failure, pruning, or rollback:
     [references/operations.md](references/operations.md).
6. Apply [references/safety.md](references/safety.md) before editing or running
   a command that changes external state.

## Repository ownership

- `cluster-config`: one primary cluster's bootstrap, Flux self-management,
  cluster resources, namespace infrastructure, and local placement.
- `apps-config`: reusable developer components and exactly `dev`, `staging`,
  and `production` variants. It never selects a cluster.
- `fleet-config`: optional shared profiles and explicit per-cluster activation.
  Every member runs its own Flux controllers and pulls Git independently.
- `pipelines`: OCI DevOps mirroring and agent installation. Do not place
  Kubernetes desired state here.

If a request crosses repositories, make one coherent change per repository,
validate each independently, and state the required merge order.

## Change workflow

1. Update the clone from `main` without discarding user changes.
2. Inspect the relevant ResourceSet, Kustomization, HelmRelease, source, and
   every referenced path.
3. Prefer the existing ResourceSet/input contract. Do not bypass it with
   unrelated controller objects or direct workload application.
4. Make the smallest coherent change. Preserve component/environment as the
   reconciliation and rollback boundary.
5. Run `scripts/validate.sh [repository-root]`.
6. Run `scripts/impact.sh [repository-root] [base-ref]`. Review deletions,
   ResourceSet input removals, Kustomization reference removals, namespace
   changes, source changes, and profile activation changes.
7. Compare each changed deployment unit:
   - Kustomize: `scripts/diff-kustomize.sh <repo> <overlay-path> [base-ref]`;
   - umbrella Helm: `scripts/diff-helm-selection.sh <repo> <app> <component> <environment> [base-ref]`.
   An object appearing in a complete render is not proof that it changed.
8. Show planned resources and pruning impact before destructive or externally
   mutating operations.
9. Do not push, merge, run a pipeline, apply bootstrap, modify IAM, or mutate a
   cluster unless the user authorized it.
10. After merge, observe the local Flux graph and workload. Correct or revert
    Git when desired state is wrong.

## Validation rules

- Render every changed Kustomize root with `kubectl kustomize`.
- For umbrella Helm, lint and template every affected component/environment
  using global values first and the selected values file last.
- Inspect names, namespaces, labels, images, requests, and duplicate identities.
- Verify each Helm environment file enables exactly one subchart.
- Never render, decode, or print secret values into logs.
- A live dry-run is optional; local rendering remains mandatory.

## Observe Flux

Run against the target cluster, not an assumed hub:

```bash
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepository,kustomization,helmrelease
kubectl -n flux-system describe kustomization <name>
```

Expect every relevant object to report `Ready=True`. Additional members have
only `fleet-config` and `apps-config` sources; the primary also has
`cluster-config`. Read conditions and events before changing Git.

## Report every result

Include the target cluster, namespace, application, component and environment;
all created/modified/deleted files; validation results; proven changed and
pruned Kubernetes identities; external actions performed or still requiring
authorization; and the exact Git revert procedure.

Use `assets/` only as starting points. Replace every `__TOKEN__`, inspect the
result, and adapt it before committing. Read
[references/templates.md](references/templates.md) first.
