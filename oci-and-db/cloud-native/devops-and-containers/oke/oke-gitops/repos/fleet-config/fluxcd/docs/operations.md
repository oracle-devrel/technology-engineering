# Operations

Render repository roots before committing:

```bash
kubectl kustomize profiles/common >/dev/null
kubectl kustomize profiles/development >/dev/null
kubectl kustomize profiles/advanced >/dev/null
kubectl kustomize clusters/<cluster> >/dev/null
```

Validate the Git-hosted charts and ordered values:

```bash
helm lint profiles/advanced/applications/git-tool/chart \
  -f profiles/advanced/applications/git-tool/values/00-base.yml \
  -f profiles/advanced/applications/git-tool/values/90-overrides.yml

helm template git-tool profiles/advanced/applications/git-tool/chart \
  -f profiles/advanced/applications/git-tool/values/00-base.yml \
  -f profiles/advanced/applications/git-tool/values/90-overrides.yml
```

Before activating the ESO reference, replace all three placeholders and
confirm no placeholder remains:

```bash
rg '<region>|<vault-ocid>|<vault-secret-name>' \
  profiles/advanced/applications/external-secrets
```

After reconciliation, verify status without decoding the generated Secret:

```bash
kubectl -n flux-system get resourceset/fleet-external-secrets \
  helmrelease/external-secrets kustomization/fleet-external-secrets-resources
kubectl -n eso-demo get secretstore,externalsecret,secret
```

Inspect one member locally:

```bash
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepositories,kustomizations,helmreleases
kubectl get pods -A
```

A healthy member has Ready sources, Ready profile Kustomizations, Ready
ResourceSets, and Ready generated workload reconciliations. Failure on one
cluster does not block any other cluster.

Rollback by reverting the Git commit. Removing a profile, ResourceSet input,
Kustomization, or HelmRelease can prune workloads. Review the rendered diff
and target cluster before merging deletion changes.

For a controlled pruning test, first add a disposable profile containing only
a Namespace and ConfigMap. Activate it on one non-production cluster and wait
for Ready. Remove both its activation and profile in a second commit, then
verify that its Flux Kustomization and Namespace disappear. Revert that second
commit to prove restoration, and revert the rollback to leave the disposable
resources pruned. Never use a production application as the pruning fixture.
