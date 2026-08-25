# OKE GitOps Solution with OCI DevOps

This OCI Resource Manager stack gives one existing OKE cluster a simple GitOps
operating model. Users change Kubernetes configuration in Git; Argo CD or Flux
CD continuously makes the cluster match that configuration.

The default model is deliberately single-cluster. It does not require cluster
types, profiles, variants, or fleet selectors. The optional fleet model is
engine-specific: Argo CD uses a central hub with native ApplicationSets and
cluster registration, while Flux is deliberately decentralized. The stack
installs Flux only on its selected OKE cluster. Administrators add another
member by manually creating a private OCI DevOps OKE environment and a
dedicated installation pipeline; every member then pulls only its own
activation root from the shared `fleet-config` repository. Flux has no hub
mode and does not use Sveltos.

## Documentation

- Stable repository contract: [contract v1](REPOSITORY-CONTRACT.md).
- Current release: [2.0.0 release notes](RELEASE-NOTES.md).
- This README: stack deployment and the one-time GitOps handoff.
- Bootstrap access:
  - [Argo CD IAM and Vault guide](repos/argocd/cluster-config/docs/README.md)
  - [Flux CD IAM and Vault guide](repos/fluxcd/cluster-config/docs/README.md)
- Cluster administration:
  - [Argo CD cluster guide](repos/argocd/cluster-config/README.md)
  - [Flux CD cluster guide](repos/fluxcd/cluster-config/README.md)
- Application teams:
  - [Argo CD developer guide](repos/argocd/apps-config/docs/README.md)
  - [Flux CD developer guide](repos/fluxcd/apps-config/docs/README.md)
- Architecture details: [Argo CD](argocd-solution.md) and
  [Flux CD](flux-solution.md).
- Complete change maps:
  - [Argo CD use cases and impacted files](argocd-use-cases.md)
  - [Flux CD use cases and impacted files](flux-use-cases.md)
- Portable Argo CD automation:
  [install the OKE agent skill](repos/argocd/cluster-config/docs/install-agent-skill.md).
- Portable Flux automation:
  [install the OKE agent skill](repos/fluxcd/cluster-config/docs/install-agent-skill.md).
- Stack-author IAM reference: [policies.md](policies.md).
- Optional fleet administration:
  [Argo CD fleet guide](repos/fleet-config/argocd/README.md) or
  [Flux CD fleet guide](repos/fleet-config/fluxcd/README.md).

## What the stack creates

- One OCI DevOps project.
- A `pipelines` repository for mirroring charts and images into OCIR.
- A `cluster-config` repository for GitOps bootstrap and platform resources.
- An `apps-config` repository for application workloads.
- When `enable_multicluster = true`, a `fleet-config` repository for native
  Argo CD fleet descriptors or decentralized Flux cluster roots and profiles.
- A `bootstrap-gitops-agent` build pipeline that mirrors and performs the
  initial installation.
- A `mirror-gitops-agent` build pipeline that mirrors only, for self-managed
  upgrades.
- An underlying `install-gitops-agent` deployment pipeline triggered only by
  the bootstrap pipeline.
- Logging, notifications, and optional IAM resources.

Choose one GitOps engine when creating the stack:

- `argocd`: Argo CD with ApplicationSets for normal platform applications and
  logical parent Applications for environment-aware Kustomize or Git-hosted
  umbrella Helm applications.
- `fluxcd`: Flux Operator with ResourceSets and Flux Kustomizations.

Both choices provide the same user workflow and repository boundaries.
The environment-aware Kustomize and umbrella Helm references use the same
application catalog with both agents. Only the controller-specific activation
objects differ: Argo CD uses Applications/ApplicationSets, while Flux uses
Kustomizations/ResourceSets/HelmReleases.
The deployment pipeline installs the selected engine once. After bootstrap,
Argo CD or Flux Operator manages its own Helm release from the editable
`cluster-config/platform/applications/<engine>/` descriptor and ordered
`values/` files stored in Git.

## The operating model

| Repository | Owners | Put these changes here |
|---|---|---|
| `pipelines` | Platform team | Artifact-mirroring build specifications |
| `cluster-config` | Cluster administrators | GitOps bootstrap, operators, policies, and cluster-wide platform services |
| `apps-config` | Application teams | Reusable components, images, and dev/staging/production overlays |
| `fleet-config` (optional) | Cluster administrators | Native Argo CD placement or decentralized Flux per-cluster activation and shared profiles |

Resource Manager populates each repository only when it is empty. After the
initial seed, every file belongs to the repository's users—including bootstrap
and GitOps adapter files. Later stack applies preserve existing Git content;
users update templates through normal Git commits, and customer Git wins over
new stack defaults.

The normal change flow is:

```text
Edit YAML → render locally → commit → review → merge to main
    → Argo CD or Flux detects the commit → OKE is reconciled
```

After bootstrap, do not use `kubectl apply` for normal managed resources.
Direct cluster edits create drift and the GitOps controller will normally
reverse them. Fix or revert the configuration in Git instead.

## Before deployment

You need:

- An existing OKE cluster and permission to manage it.
- An OCI compartment where the stack can create DevOps resources.
- Git, `kubectl`, and access to the cluster kubeconfig.
- A bootstrap auth token that Resource Manager can use to seed the OCI DevOps
  repositories.
- A dedicated non-human identity with read-only access to `cluster-config` and
  `apps-config`.
- A different non-human identity with read-only access to the required OCIR
  repositories.
- Two OCI Vault secrets containing the runtime identities as JSON.
- A subnet from which OCI DevOps Shell stages can reach the OKE API endpoint
  and OCI services.
- IAM permissions from [policies.md](./policies.md), or `create_iam = true`.

### Prepare bootstrap access

The sensitive Resource Manager `auth_token` is used only to seed the hosted
repositories. Runtime Git and OCIR access uses two dedicated read-only users
and two OCI Vault secrets.

Follow the bootstrap access guide for the selected engine:

- [Argo CD bootstrap access](repos/argocd/cluster-config/docs/README.md)
- [Flux CD bootstrap access](repos/fluxcd/cluster-config/docs/README.md)

The guides include Console navigation, exact least-privilege policy statements,
username formats, Vault JSON, pipeline parameter mapping, verification,
rotation, and migration from the deprecated shared token.

Select a bootstrap runner subnet with outbound access to OCI services and to
the OKE **private** API endpoint. Bootstrap always uses the private endpoint,
even if the OKE cluster also exposes a public endpoint. Attach an NSG if your
network policy requires one.

## Deploy and bootstrap

1. Deploy `stack.zip` through OCI Resource Manager.
2. Set `gitops_agent` to `argocd` or `fluxcd`.
   Leave `enable_multicluster` disabled for a normal cluster. With Argo CD,
   enable it when the target is the hub. With Flux, enable it to create the
   shared `fleet-config` repository and activate this stack's selected cluster;
   it does not provision or connect additional clusters.
3. Wait for the Resource Manager apply job to succeed.
4. In the created OCI DevOps project, run `bootstrap-gitops-agent` and set:

   - `git_read_credentials_secret_ocid` to the Git reader Secret OCID;
   - `registry_pull_secret_ocid` to the OCIR reader Secret OCID.

   Leave `chart_version` as `LATEST` or set an exact chart version.

5. Wait for that build and its automatically triggered `install-gitops-agent`
   deployment to succeed.
6. Configure `kubectl` for the OKE private API endpoint, then clone
   `cluster-config`.
7. Apply the one generated bootstrap root for the selected engine:

   ```bash
   # Run from the cluster-config clone.
   kubectl apply -f bootstrap/argocd-bootstrap.yml
   # OR
   kubectl apply -f bootstrap/flux-bootstrap.yml
   ```

   Apply only the file for the selected `gitops_agent`. This is the one-time
   handoff from agent installation to Git reconciliation.
8. Follow the cloned repository README, which is the authoritative operating
   guide:
   - [Argo CD cluster bootstrap](./repos/argocd/cluster-config/README.md)
   - [Flux CD cluster bootstrap](./repos/fluxcd/cluster-config/README.md)
9. When bootstrap is healthy, clone `apps-config` and follow its README:
   - [Argo CD application workflow](./repos/argocd/apps-config/README.md)
   - [Flux CD application workflow](./repos/fluxcd/apps-config/README.md)

If optional multi-cluster support is enabled, follow the cloned `fleet-config`
README after the installation pipeline succeeds. For Argo CD, bootstrap the
hub and register spokes natively. For Flux, create each additional private OKE
environment and installation pipeline manually, copy and edit
`fleet-config/bootstrap/member-template.yml`, and create that member's explicit
`fleet-config/clusters/<cluster>` activation root. The primary cluster still
uses `cluster-config/bootstrap/flux-bootstrap.yml`. Every Flux member then runs
local controllers and reconciles only its own root. No cluster stores another
cluster's kubeconfig, and failure of one member does not block the others.

The bootstrap pipeline stops after mirroring artifacts, creating the controller
namespace and Vault-backed credentials, and installing the chart. It does not
apply or wait for the GitOps reconciliation root. The administrator owns that
explicit `kubectl apply` handoff. Do not start a second bootstrap while one is
active.

After GitOps takes ownership, use `mirror-gitops-agent` for upgrades. Its
`chart_version` parameter defaults to `LATEST` and also accepts an exact chart
version. It mirrors the chart and images into OCIR and never triggers
`install-gitops-agent`; Argo CD or Flux reconciles the new private chart from
Git. The parameter selects only what is mirrored; it never edits Git. The
generated wildcard selects the highest mirrored semantic version. Pin or roll
back the self-managed release by committing an exact version in
`cluster-config` after that version exists in OCIR.

### Upgrade an existing stack to the split pipelines

Existing `pipelines` repositories are customer-owned and are not overwritten
by Resource Manager. When upgrading an existing stack, merge the new
`mirror_argocd.yaml` or `mirror_flux_operator.yaml` into that repository and
push it to `main`, then apply the updated stack. Do not run either pipeline
during this short migration window.

After the apply, verify:

- `bootstrap-gitops-agent` has the three credential parameters plus
  `chart_version`, and its final stage triggers `install-gitops-agent`;
- `mirror-gitops-agent` has only `chart_version`, defaults it to `LATEST`, and
  has no deployment-trigger stage.

### Upgrade an existing stack to separated credentials

Resource Manager does not overwrite any existing customer-owned repository
during this upgrade. Update the Resource Manager stack so the deployment
pipeline exposes the two parameters. Run `bootstrap-gitops-agent` with both
new Secret OCIDs for a fresh installation. For an existing installation, run
`prepare-gitops-agent` as a single-stage deployment with both new Secret OCIDs,
then verify repository and registry access before revoking the former personal
token.

`auth_token_secret_ocid` remains available for one release as a deprecated
fallback. It is intended only to keep existing installations recoverable while
their pipeline repository is migrated.

## What success looks like

For Argo CD:

```bash
kubectl get pods -n argocd
kubectl get applications -n argocd
```

Expected Applications include `argocd-bootstrap`, `argocd`,
`platform-cluster-resources`, parent `reference-app`, and its infrastructure,
and component/environment children such as `reference-app-frontend-dev`,
`reference-app-api-dev`, `reference-app-frontend-staging`, and
`reference-app-api-staging`. Four delivery ApplicationSets use the standardized names `platform-cluster-resources`,
`platform-kustomize`, `platform-helm-repository`, and `platform-helm-git`.
The last three discover administrator-owned applications under
`cluster-config/platform/applications/`. `platform-applications` separately
discovers logical application parents and uses child sync waves for readiness ordering.

For Flux CD:

```bash
kubectl get pods -n flux-system
kubectl get fluxinstances,resourcesets -n flux-system
kubectl get gitrepositories,kustomizations,helmreleases -n flux-system
```

Expected Kustomizations include `flux-platform`, `platform`,
`reference-app-infrastructure`, `reference-app-frontend-dev`, and
`reference-app-api-staging`.

## Daily GitOps rules

1. Start from the latest `main`.
2. Create a short-lived branch.
3. Change one logical thing.
4. Render the affected Kustomize root locally.
5. Commit and push the branch.
6. Review the diff and merge it to `main`.
7. Check the GitOps controller and the workload status.

Removing a resource from a referenced `kustomization.yml` is a deletion:
pruning is enabled for normal platform and application reconciliation.
Review deletions with the same care as infrastructure changes.

## Deploy the stack

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/technology-engineering/releases/download/oke-gitops-2.0.0/stack.zip)
