# Day-two Argo CD operations

Use Git for desired-state changes and use Argo CD and Kubernetes for
observation. The hub cluster is the default target unless an Application
explicitly names a registered spoke.

## Before every change

```bash
git switch main
git pull --ff-only
git status --short
git switch -c <short-change-name>
```

Choose the pattern in [the use-case catalog](use-cases.md), inspect the
existing application directory, and render the smallest affected unit before
committing.

## Observe reconciliation

```bash
kubectl -n argocd get applicationsets,applications
kubectl -n argocd get application <name> \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision
kubectl -n argocd describe application <name>
```

An Application should become `Synced` and `Healthy`. `Progressing` can be
normal during rollout. Read conditions and resource health before taking
action on `Degraded` or persistent `Unknown`.

For an environment-aware application, verify the complete chain:

```text
platform-applications ApplicationSet
  -> application parent
     -> infrastructure Application (wave -10)
     -> component ApplicationSet (wave 0)
        -> one Application per selected component/environment
```

## Argo CD UI access

Keep the server as a TLS-enabled `ClusterIP`. Access it temporarily:

```bash
kubectl -n argocd port-forward service/<argocd-server-service> 8443:443
```

Open `https://localhost:8443`. Retrieve the initial local-admin password only
when local admin is still enabled:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o go-template='{{index .data "password" | base64decode}}{{"\n"}}'
```

For shared or production use, configure OIDC and reviewed group mappings as
described in [Secure Argo CD access](argocd-access.md). Do not expose the UI by
changing the Service to `LoadBalancer` as an access shortcut.

## Roll back

Prefer a Git revert so the desired-state history remains auditable:

```bash
git log --oneline
git revert <bad-commit-sha>
git push origin main
```

For a Helm rollback, make sure the previous chart version still exists in the
repository or OCIR, then revert the version or values change in Git. Do not use
`helm rollback` against an Argo-managed release; Argo CD would restore Git's
version.

## Delete safely

Automated pruning is enabled. Removing a resource from a referenced
Kustomization, deleting a discovered descriptor, or removing a component list
element is a deletion request.

For an environment-aware application:

1. Remove component/environment selections and verify workload pruning.
2. Remove the parent activation only after no workload remains.
3. Remove namespace infrastructure last.
4. Remove catalog content only after checking every hub and fleet binding.

## Troubleshooting order

1. **Discovery:** confirm the descriptor filename and path match the relevant
   ApplicationSet generator.
2. **Generation:** inspect the ApplicationSet conditions and generated
   Application.
3. **Repository access:** inspect Application conditions and the repository
   credential in `argocd`. Rotate it through the deployment pipeline; never
   commit it.
4. **Rendering:** reproduce the failing Kustomize or Helm render locally with
   the same ordered values.
5. **Destination:** confirm the Application targets the expected cluster and
   namespace. A spoke must resolve to its private API endpoint.
6. **Ownership:** investigate `FailOnSharedResource` errors before changing
   ownership. Do not disable the safety option to hide overlap.
7. **Kubernetes health:** inspect workload status and recent events.

Useful commands:

```bash
kubectl -n argocd get applicationset <name> -o yaml
kubectl -n argocd get application <name> -o yaml
kubectl -n <namespace> get events --sort-by=.lastTimestamp
kubectl -n <namespace> describe pod <pod>
```

Common causes:

| Symptom | Check |
|---|---|
| No generated Application | Descriptor filename, generator path, required fields, ApplicationSet conditions |
| `ComparisonError` | Repository credential, revision, source path, Helm values paths |
| `SharedResourceWarning` or failed sync | Two Applications producing the same object |
| `ImagePullBackOff` | Fully qualified image, architecture, namespace-specific OCIR pull secret |
| CR dry-run failure | CRD availability, `SkipDryRunOnMissingResource`, and sync-wave placement |
| Spoke connection failure | Cluster Secret label, credentials, DNS/routing, and private API reachability from hub pods |
| Immediate reversion of a manual fix | Expected self-healing; make or revert the change in Git |
