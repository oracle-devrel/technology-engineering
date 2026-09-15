# Guide for AI-assisted Argo CD administration

This repository is designed so an AI agent can propose safe OKE changes using
the same Git workflow as a human administrator. The agent must treat Git as the
authority and Kubernetes as an observation surface.

For a portable copy containing these rules, references, templates, and
validators, install `skills/manage-oke-with-argocd/` as described in
[the skill installation guide](install-agent-skill.md).

## Read before changing anything

Read these files in order:

1. The repository [README](../README.md) for ownership, bootstrap, and the
   normal workflow.
2. The [use-case catalog](use-cases.md) to select the supported pattern.
3. The [Argo CD adapter guide](../gitops/argocd/README.md) before changing an
   ApplicationSet or AppProject.
4. The [platform application guide](../platform/applications/README.md) for
   application-parent and sync-wave rules.
5. The README and manifests in the application directory being changed.

If the task changes developer-owned workloads, also read the `apps-config`
README. If it targets a managed cluster, read the `fleet-config` README and its
registration, naming, deployment-pattern, and operations guides.

## Deterministic workflow

1. Identify the target: hub cluster or registered spoke, application,
   namespace, component, and environment.
2. Classify the change with the [use-case catalog](use-cases.md).
3. Inspect the existing descriptor and every referenced path. Do not infer a
   path from its name alone.
4. Confirm ownership. Cluster and namespace infrastructure belongs here;
   reusable developer workloads belong in `apps-config`; spoke placement
   belongs in `fleet-config`.
5. Make the smallest coherent Git change. Do not modify generated adapter files
   unless the requested behavior cannot be expressed by a supported descriptor.
6. Render every changed Kustomize root and Helm values combination.
7. Inspect the Git diff for secrets, unintended deletions, namespace changes,
   ownership overlap, public endpoints, `LoadBalancer` Services, PVCs, and
   unbounded resource requests.
8. Commit through a reviewed branch. After merge, observe Argo CD and the
   target workload. Do not force-sync around a bad desired state.
9. If reconciliation fails, diagnose in the order documented in
   [operations guide](operations.md). Fix or revert Git.

## Pattern selection

| Desired outcome | Use |
|---|---|
| Non-namespaced resources for the hub | `platform/cluster-resources/` |
| Administrator-owned namespaced YAML | `kustomize.application.yaml` |
| External Helm/OCI chart | `helm-repository.application.yaml` |
| Chart stored in `cluster-config` | `helm-git.application.yaml` |
| Helm plus related YAML | Either Helm descriptor plus its `resources/` source |
| Operator plus custom resources | One multi-source Helm Application and sync waves |
| Developer component/environment workload | Logical application parent plus component ApplicationSet reading `apps-config` |
| Same application on a spoke | Equivalent parent under `fleet-config/clusters/<cluster>/applications/` |

## Required checks

For Kustomize:

```bash
kubectl kustomize <changed-root>
```

For Git-hosted Helm:

```bash
helm dependency list <chart-path>
helm lint <chart-path> -f <global-values> -f <selected-values>
helm template <release> <chart-path> \
  --namespace <namespace> \
  -f <global-values> \
  -f <selected-values>
```

After merge:

```bash
kubectl -n argocd get applicationsets,applications
kubectl -n argocd describe application <application>
kubectl -n <namespace> get deploy,sts,ds,pod,svc
kubectl -n <namespace> get events --sort-by=.lastTimestamp
```

For a spoke, run the Argo commands on the hub. Confirm the generated
Application destination is the registered spoke's private API endpoint.

## Non-negotiable constraints

- Never commit credentials or a populated cluster Secret.
- Never use a spoke public API endpoint in Argo CD.
- Never add a `Namespace` manifest to a local Argo application; namespace
  creation comes from `CreateNamespace=true`.
- Never allow two Applications to own the same Kubernetes object.
- Never silently change an application, namespace, component, environment, or
  target cluster because a value is missing. Stop and report the ambiguity.
- Never delete a descriptor, list item, or Kustomize resource reference without
  stating what Argo CD will prune.
- Preserve explicit Helm values order. Later files win; lists normally replace
  rather than merge.
- Keep `dev`, `staging`, and `production` as the only standard application
  environments.
- Keep every component/environment pair independently reconcilable.

## Change report

Every proposed change should report:

- target cluster, namespace, application, component, and environment;
- files created, modified, and deleted;
- rendered roots and validation results;
- expected Argo CD Applications affected;
- resources expected to be created, updated, or pruned;
- rollback commit or exact Git revert procedure.
