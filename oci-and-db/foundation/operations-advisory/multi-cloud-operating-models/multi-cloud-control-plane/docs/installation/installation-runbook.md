# Installation runbook

> **Audience:** Cloud Operations<br>
> **Before you begin:** Administrative access to a private GitHub organization,
> existing trusted runner hosts, and a dedicated OCI Object Storage state
> bucket.<br>
> **Outcome:** Prepared shared repositories, configured execution prerequisites,
> and verified automation controls.<br>
> **Next step:** [Prepare the shared repositories](#1-prepare-the-shared-repositories).

This runbook uses Git, GitHub CLI (`gh`), `jq`, `rg`, and Perl. Authenticate
`gh` to an account that can create and configure private repositories in the
customer organization. Run the commands from a clean clone of this asset; no
custom deployment program is required.

```bash
gh auth status
git status --short
```

`gh auth status` must confirm the intended GitHub account. `git status` must
return no output before staging the publication.

## 1. Prepare the shared repositories

```bash
export STAGE="$(mktemp -d)"
export CUSTOMER_ORG=example-enterprise
export PROJECT_STATE_BUCKET=example-project-state
export OCI_ORCHESTRATOR_REF=fcf1d7f02c0b4faa1ff55f1776c396452dd51761
export AZURE_ORCHESTRATOR_REF=mccp-v2.1.0
export GCP_ORCHESTRATOR_REF=mccp-v2.1.0

mkdir -p "$STAGE"
cp -R repository-sources/platform-ci "$STAGE/platform-ci"
cp -R repository-sources/nonprod-project-template "$STAGE/nonprod-project-template"
cp -R repository-sources/prod-project-template "$STAGE/prod-project-template"
cp -R repository-sources/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/nonprod-project-template/LICENSE"
cp LICENSE "$STAGE/prod-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"

find "$STAGE" -type d \( -name tests -o -name __pycache__ -o -name .venv \) \
  -prune -exec rm -rf {} +
find "$STAGE" -type f -name mccp-installation.json -delete

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g' {} +
```

`STAGE` is a local build directory, not a Git repository or secret store. Use a
directory accessible only to the installation operator, keep credentials and
runtime secrets outside it, and remove it after the published repositories have
been verified.

`PROJECT_STATE_BUCKET` must name a dedicated private OCI Object Storage bucket
with versioning enabled. MCCP uses this backend for project Terraform state for
all supported target clouds. Do not reuse a foundation-state bucket. The
value is rendered into the project workflow templates during this runbook.

`OCI_ORCHESTRATOR_REF` pins OCI Landing Zones Orchestrator
[`release-2.1.4`](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator/tree/release-2.1.4).
The workflow uses that immutable commit.

`AZURE_ORCHESTRATOR_REF` and `GCP_ORCHESTRATOR_REF` name the reviewed
`mccp-v2.1.0` releases published by the external
[Azure adapter](https://github.com/oci-clickops/clickops-orchestrator-azure/tree/mccp-v2.1.0)
and [GCP adapter](https://github.com/oci-clickops/clickops-orchestrator-gcp/tree/mccp-v2.1.0).
Confirm that they resolve to the reviewed adapter commits before installation.

Create Platform CI first. Project workflows and its composite actions use its
review-controlled `main` branch directly:

```bash
git -C "$STAGE/platform-ci" init -b main
git -C "$STAGE/platform-ci" add -A
git -C "$STAGE/platform-ci" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare Platform CI'
export PLATFORM_CI_COMMIT=$(git -C "$STAGE/platform-ci" rev-parse HEAD)

find "$STAGE/nonprod-project-template" "$STAGE/prod-project-template" -type f -exec perl -pi -e \
  's/__OCI_ORCHESTRATOR_REF__/$ENV{OCI_ORCHESTRATOR_REF}/g; s/__AZURE_ORCHESTRATOR_REF__/$ENV{AZURE_ORCHESTRATOR_REF}/g; s/__GCP_ORCHESTRATOR_REF__/$ENV{GCP_ORCHESTRATOR_REF}/g' {} +

for repository in nonprod-project-template prod-project-template gitops-templates; do
  git -C "$STAGE/$repository" init -b main
  git -C "$STAGE/$repository" add -A
  git -C "$STAGE/$repository" -c user.name='Platform Administrator' \
    -c user.email='platform@invalid' commit -m "Prepare $repository"
done

export PROJECT_TEMPLATE_REF=$(git -C "$STAGE/nonprod-project-template" rev-parse HEAD)
export PRODUCTION_PROJECT_TEMPLATE_REF=$(git -C "$STAGE/prod-project-template" rev-parse HEAD)
export CATALOGS_REF=$(git -C "$STAGE/gitops-templates" rev-parse HEAD)
```

Keep the Platform CI repository private and restrict write access to Cloud
Operations. Protect `main` when the customer GitHub plan supports protection
for private repositories. Official GitHub Actions use their reviewed major
release tags.

The MVP uses the fixed `repository-secrets` profile on GitHub Free. An enabled
environment receives its own repository secret bundle only when a workload
manifest contains matching runtime placeholders; the reviewed pull request
remains the human deployment gate. See the
[security and GitHub controls](../reference/security.md). Do not add untested
paid-plan controls to this release.

Verify that no unresolved release placeholder or local test content is present:

```bash
rg '__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__|__PROJECT_STATE_BUCKET__' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the four private repositories and
publish their prepared `main` branches:

```bash
for repository in platform-ci nonprod-project-template prod-project-template gitops-templates; do
  gh repo create "$CUSTOMER_ORG/$repository" \
    --private --source "$STAGE/$repository" --remote origin --push
done
```

Mark both project repositories as templates, then confirm the setting:

```bash
gh repo edit "$CUSTOMER_ORG/nonprod-project-template" --template
gh repo edit "$CUSTOMER_ORG/prod-project-template" --template
test "$(gh api "repos/$CUSTOMER_ORG/nonprod-project-template" --jq '.is_template')" = true
test "$(gh api "repos/$CUSTOMER_ORG/prod-project-template" --jq '.is_template')" = true
```

In the published `platform-ci` repository, allow project repositories to call
its reusable workflows at
**Settings → Actions → General → Access → Accessible from repositories in the
organization**. Confirm the resulting access level:

```bash
test "$(gh api "repos/$CUSTOMER_ORG/platform-ci/actions/permissions/access" \
  --jq '.access_level')" = organization
```

Record the exact prepared commits, then confirm that every published branch
resolves to those commits:

```bash
printf '%s  %s\n' \
  "$PLATFORM_CI_COMMIT" platform-ci \
  "$PROJECT_TEMPLATE_REF" nonprod-project-template \
  "$PRODUCTION_PROJECT_TEMPLATE_REF" prod-project-template \
  "$CATALOGS_REF" gitops-templates

test "$(git ls-remote "https://github.com/$CUSTOMER_ORG/platform-ci.git" \
  refs/heads/main | cut -f1)" = "$PLATFORM_CI_COMMIT"
test "$(git ls-remote "https://github.com/$CUSTOMER_ORG/nonprod-project-template.git" \
  refs/heads/main | cut -f1)" = "$PROJECT_TEMPLATE_REF"
test "$(git ls-remote "https://github.com/$CUSTOMER_ORG/prod-project-template.git" \
  refs/heads/main | cut -f1)" = "$PRODUCTION_PROJECT_TEMPLATE_REF"
test "$(git ls-remote "https://github.com/$CUSTOMER_ORG/gitops-templates.git" \
  refs/heads/main | cut -f1)" = "$CATALOGS_REF"
```

Each `test` command must return exit code zero. Record the commits as
installation evidence. This release bundle contains only the shared control
plane sources; tenant-specific runtime artifacts remain outside it.

Keep `platform-ci` private and configure its Actions access for organization
repositories. A private reusable workflow invokes its directly referenced
composite action on `main` with GitHub's scoped temporary token; project
repositories do not need a deploy key or other Platform CI source credential.

## 2. Configure trusted runners

This runbook configures existing self-hosted runner hosts; it does not provision
runner machines. Register each runner with the customer GitHub organization and
assign only the labels required by the published workflows.

| Setting | Purpose |
|---|---|
| `STATE_NAMESPACE` | OCI Object Storage namespace |
| `STATE_REGION` | Region of the OCI state bucket |
| `OCI_CLI_AUTH=instance_principal` | OCI state and inventory authentication |

Resolver runners need Git, `jq`, and `rg`. Execution runners need Git and
Python 3.11 or later; the workflow installs its pinned Terraform 1.12.1
runtime. Use separate runner instances and labels for non-production and
production. When the customer GitHub plan supports additional organization
runner groups, place those instances in separate groups restricted to the
approved repositories.

Register runner labels that match the supplied workflows:

| Job boundary | Required labels |
|---|---|
| Request resolver | `self-hosted`, `control-plane-resolver` |
| Non-production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), selected environment (`dev`, `test`, or `uat`) |
| Production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), `prod` |

The supplied baseline can use OCI runner instances for every selected cloud.
Those instances must belong to an OCI dynamic group with policies for the
Object Storage state bucket and only the compartments and services required by
their workload. Azure additionally needs Azure CLI and its approved
service-principal `ARM_*` values. Google needs `GOOGLE_CREDENTIALS`,
`GOOGLE_APPLICATION_CREDENTIALS`, or Application Default Credentials. Keep
credentials outside Git.

Cloud Operations provisions one SSH key pair for each OCI runner boundary. OCI
Compute manifests use only the public key at
`/home/github-runner/.ssh/oci_vm_key.pub`; supported Ansible operations use the
matching private key at `/home/github-runner/.ssh/oci_vm_key`. Verify as
`github-runner` that both files exist and that the private key is readable only
by that service account. Non-production and production runners must have
separate key pairs.

## 3. Confirm the installation

The organization installation is complete when:

- the four published repository commits match the recorded values;
- Platform CI Actions access is available to organization repositories;
- resolver and execution runners have the required labels; and
- each runner identity has the intended state and workload access.

Retain the commits, repository settings, runner labels, identity boundaries,
and successful checks as installation evidence.

At this point the shared MCCP installation is complete. Project repository
creation and handoff are separate Cloud Operations activities.

## 4. Complete first-project acceptance

After Cloud Operations creates and hands off the first project repository,
complete the mandatory
[environment secret isolation test](verify-secret-isolation.md)
before the Project Team submits workload requests. This verifies a real project
boundary but is not part of publishing the shared repositories.
