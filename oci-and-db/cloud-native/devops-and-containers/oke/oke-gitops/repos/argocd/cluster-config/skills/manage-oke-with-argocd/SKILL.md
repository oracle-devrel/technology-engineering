---
name: manage-oke-with-argocd
description: Manage Oracle Kubernetes Engine clusters through this solution's Argo CD GitOps repositories. Use for bootstrapping or observing Argo CD, changing cluster-scoped or namespaced resources, deploying Helm charts, managing environment-aware Kustomize or umbrella-Helm applications, releasing one component, handling OCI Vault ExternalSecrets, registering or configuring private-endpoint spoke clusters, validating changes, analyzing pruning impact, troubleshooting reconciliation, and rolling back through Git in cluster-config, apps-config, or fleet-config repositories.
---

# Manage OKE with Argo CD

Operate OKE through Git. Treat Git as desired state and Kubernetes/Argo CD as
observation surfaces. Do not repair managed objects directly.

## Start every task

1. Locate the repository and run `scripts/preflight.sh [path]`.
2. Identify the target cluster, namespace, application, component, and
   environment. Do not guess a missing target that changes placement.
3. Classify the request with [references/use-cases.md](references/use-cases.md).
4. Read [references/repository-contracts.md](references/repository-contracts.md).
5. Read only the task-specific reference:
   - local platform or developer application:
     [references/applications.md](references/applications.md);
   - managed spoke: [references/fleet.md](references/fleet.md);
   - failure or rollback:
     [references/operations.md](references/operations.md).
6. Apply [references/safety.md](references/safety.md) before editing or running
   a command that changes external state.

## Repository ownership

- `cluster-config`: bootstrap, Argo configuration, cluster resources (including
  every resource rendered into `kube-system`), namespace infrastructure, and
  local placement. Owned by cluster administrators.
- `apps-config`: reusable developer components and `dev`, `staging`, and
  `production` variants. It never selects a cluster.
- `fleet-config`: optional registered-spoke objects, profiles, and per-cluster
  placement. Spokes run no local GitOps controller.
- `pipelines`: OCI DevOps artifact mirroring. Do not place Kubernetes desired
  state here.

If a requested change crosses repositories, make and validate one coherent
change per repository and state the required merge order.

## Change workflow

1. Update the clone from `main` without discarding user changes.
2. Inspect existing descriptors and every referenced path.
3. Prefer the supported descriptor or application-parent contract over editing
   generated ApplicationSets.
4. Make the smallest coherent change. Preserve component/environment as the
   release and rollback boundary.
5. Run `scripts/validate.sh [repository-root]`.
6. Run `scripts/impact.sh [repository-root] [base-ref]` and review every delete,
   descriptor removal, list-element removal, namespace change, and target
   change.
7. Compare before/after rendered output for each changed deployment unit:
   - Kustomize: `scripts/diff-kustomize.sh <repo> <overlay-path> [base-ref]`;
   - umbrella Helm: `scripts/diff-helm-selection.sh <repo> <app> <component> <environment> [base-ref]`.
   Do not call every object in a render “changed.”
8. Show the user the planned resources and pruning impact before destructive or
   externally mutating operations.
9. Commit through the repository's normal review workflow. Do not push, merge,
   run a pipeline, apply bootstrap, or change a live cluster unless the user
   authorized that action.
10. After merge, observe the generated Application and workload. Fix or revert
   Git when desired state is wrong.

## Validation rules

- Render every changed Kustomize root with `kubectl kustomize`.
- For umbrella Helm, lint and template every affected component/environment
  using global values first and the selected values file last.
- Inspect rendered names, namespaces, labels, images, resource requests, and
  duplicate identities.
- Verify a Helm environment file enables exactly one subchart.
- Never render or print secret values into logs.
- Use server-side dry-run only when cluster access exists and the user permits
  live read/API interaction. Local rendering remains mandatory.

## Observe Argo CD

Run on the hub:

```bash
kubectl -n argocd get applicationsets,applications
kubectl -n argocd describe application <application>
```

For a spoke, confirm the generated Application destination is the registered
private API endpoint. Then inspect the workload namespace. Expect `Synced` and
`Healthy`; read conditions and events before acting on other states.

## Report every result

Include:

- target cluster, namespace, application, component, and environment;
- repository and every created, modified, or deleted file;
- validation commands and outcomes;
- Applications and Kubernetes resources proven by before/after rendering to
  change or be pruned; list unchanged rendered resources separately only when
  useful;
- external actions performed or still requiring authorization;
- exact Git revert or rollback procedure.

Use templates in `assets/` only as starting points. Replace every `__TOKEN__`,
inspect the result, and adapt it to existing repository conventions before
committing. Read [references/templates.md](references/templates.md) before
copying an asset.
