# Developer delivery workflow

Developers own catalog content. Cluster administrators own namespace
infrastructure and placement. Argo CD or Flux owns reconciliation after a
reviewed commit reaches the configured branch.

## Request initial deployment

Give the administrator:

- application name and same-named namespace;
- technology: Kustomize or umbrella Helm;
- components to activate;
- one or more environments from `dev`, `staging`, and `production`;
- expected CPU, memory, storage, and object counts for quota design;
- required network ingress and egress;
- required OCI workload identity, Vault, or external service access;
- any private image-pull requirement.

With Argo CD, the administrator creates this structure in `cluster-config`:

```text
platform/applications/<app>/
  application.yaml
  kustomization.yml
  infrastructure/
    application.yml
    resources/
  components.application-set.yml
```

Infrastructure reconciles at wave `-10`. The component ApplicationSet
reconciles at wave `0` and lists the active component/environment pairs. A
fleet administrator uses the equivalent folder below
`fleet-config/clusters/<cluster>/applications/<app>/` for a spoke.

With Flux, the administrator creates the equivalent logical application under
`cluster-config/platform/applications/<app>/` or a decentralized fleet
profile. An infrastructure ResourceSet creates the namespace prerequisites;
the component ResourceSet creates one dependent Kustomization or HelmRelease
per selected pair.

Developers do not add cluster names or placement selectors to `apps-config`.

## Make a release

```bash
git switch main
git pull --ff-only
git switch -c release-<component>-<environment>
```

Change the smallest deployment unit:

| Technology | Normal release file |
|---|---|
| Kustomize | `applications/<app>/kustomize/components/<component>/environments/<environment>/kustomization.yml` |
| Helm | `applications/<app>/helm/values/<environment>/<component>.yml` |

Render the unit, review `git diff`, commit, push, and merge through normal code
review. Do not run `kubectl apply` or `helm upgrade` for a GitOps-managed
application.

## Verify after merge

In Argo CD, find:

```text
<app> parent
  <app>-infrastructure
  <app>-components ApplicationSet
    <app>-<component>-<environment>
```

The component Application should become `Synced` and `Healthy`. Check the
workload in the application's namespace. If only one component file changed,
the other component Deployments should retain their desired pod templates.

With Flux, verify the application ResourceSets and the selected component
Kustomizations or HelmReleases in `flux-system`; each must report Ready.

## Roll back

Revert the release commit:

```bash
git log --oneline
git revert <release-commit>
git push origin main
```

Do not use `kubectl rollout undo` or `helm rollback`; the GitOps controller
would restore the version still declared in Git.

## Secrets

Never commit a Kubernetes Secret value, even base64-encoded. Ask the
administrator to configure External Secrets Operator, an OCI Vault
`SecretStore`, workload identity, and required IAM policy. Commit only the
sanitized `ExternalSecret` resource that names the required Vault secret. See
`examples/external-secret.yml`.

## Remove a deployment

Removing a component/environment is an administrator placement change. The
administrator removes its list element from the controller-specific
ApplicationSet or ResourceSet, reviews pruning, and verifies deletion on every
target. Delete catalog files only after confirming that no cluster uses them.
