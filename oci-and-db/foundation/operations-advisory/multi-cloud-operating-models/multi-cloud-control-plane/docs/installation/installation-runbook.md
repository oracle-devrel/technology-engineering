# Installation runbook

> **Audience:** Cloud Operations<br>
> **Outcome:** Shared repositories, trusted runners, and one accepted project
> repository ready for Project Team requests.<br>
> **Scope:** This runbook does not provision the state bucket, runner hosts,
> cloud foundation, or customer identities.

It establishes the shared control plane, prepares one project for use, and then
optionally adds request interfaces.

## Installation path

1. [Prepare the installation inputs](#1-prepare-the-installation-inputs): a
   clean source clone, GitHub organization access, state backend, runner hosts,
   and a completed project foundation.
2. [Publish the shared repositories](#2-publish-the-shared-repositories).
3. [Register and verify trusted runners](#3-register-and-verify-trusted-runners).
4. [Hand off the first project repository](#4-hand-off-the-first-project-repository).
5. [Accept the first project](#5-accept-the-first-project).
6. Complete the [optional interface setup](optional-interfaces.md) only if the
   customer selected the Multi-Cloud Plane UI or Codex plugin.

Stop at any stage whose success condition is not met; do not move a Project Team
into a repository that has not been handed off and accepted. The GitHub
interface is available as soon as the project acceptance check succeeds and
needs no additional MCCP component.

Run the source commands from the `multi-cloud-control-plane` directory of a
clean clone. No custom installation program is required. The
[repository source index](../../repository-sources/README.md) describes the
technical contract of each repository the runbook publishes.

## 1. Prepare the installation inputs

Before starting, have all of the following:

- A customer GitHub organization where you can create private repositories,
  configure Actions, and register organization runners.
- A clean MCCP source clone, with Git, GitHub CLI (`gh`), `jq`, `rg`, and Perl.
- A dedicated, private, versioned OCI Object Storage state bucket. Know its
  namespace and region; do not reuse a foundation-state bucket.
- Separate trusted Linux runner hosts for non-production and production. Their
  cloud identities and network access must already be approved.
- A completed project-foundation handoff for the first project. It provides the
  approved cloud, environment, region, network, and execution references.

Authenticate `gh` to the intended customer organization, then check the source
clone:

```bash
gh auth status
git status --short
```

**Continue only when:** `gh auth status` shows the intended account and
`git status --short` has no output. Use a new clone if the current one contains
unrelated work.

## 2. Publish the shared repositories

Stage the four shared sources and set the customer values and immutable
orchestrator pins:

```bash
export STAGE="$(mktemp -d)"
export CUSTOMER_ORG=example-enterprise
export PROJECT_STATE_BUCKET=example-project-state
export OCI_ORCHESTRATOR_REF=fcf1d7f02c0b4faa1ff55f1776c396452dd51761
export AZURE_ORCHESTRATOR_REF=8f3718211f98b8cc22ff0538dbd7080f12294c50
export GCP_ORCHESTRATOR_REF=ff64cb3534f11de7ae2693d5ab5dabbab479003c

mkdir -p "$STAGE"
cp -R repository-sources/platform-ci "$STAGE/platform-ci"
cp -R repository-sources/nonprod-project-template "$STAGE/nonprod-project-template"
cp -R repository-sources/prod-project-template "$STAGE/prod-project-template"
cp -R repository-sources/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/nonprod-project-template/LICENSE"
cp LICENSE "$STAGE/prod-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g' {} +
```

`STAGE` is a local build directory, not a Git repository or secret store. Keep
it accessible only to the installation operator. `PROJECT_STATE_BUCKET` is
rendered into the project workflow templates.

The OCI pin is [Orchestrator release-2.1.4](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator/tree/release-2.1.4).
The Azure and Google Cloud pins are the reviewed `mccp-v2.1.0`
[Azure](https://github.com/oci-clickops/clickops-orchestrator-azure/commit/8f3718211f98b8cc22ff0538dbd7080f12294c50)
and [Google Cloud](https://github.com/oci-clickops/clickops-orchestrator-gcp/commit/ff64cb3534f11de7ae2693d5ab5dabbab479003c)
orchestrator commits. Do not replace any of these commits with a mutable tag.

Create Platform CI first, then prepare the templates and catalog:

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

Keep Platform CI private, restrict its write access to Cloud Operations, and
protect `main` when the customer GitHub plan supports it. `PLATFORM_CI_COMMIT`
is installation evidence. Project repositories intentionally call the
Cloud Operations-controlled `platform-ci` `main` branch at runtime; its changes
remain a Cloud Operations review responsibility. Official GitHub Actions use
their reviewed major release tags. The fixed `repository-secrets` profile gives
an enabled environment a secret bundle only when a workload needs matching
runtime placeholders; the pull request remains the human deployment gate. See
the [security guidance](../reference/security.md) and do not add untested
paid-plan controls to this release.

Verify the staged sources, publish them, and enable the project templates:

```bash
rg '__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__|__PROJECT_STATE_BUCKET__' "$STAGE"

for repository in platform-ci nonprod-project-template prod-project-template gitops-templates; do
  gh repo create "$CUSTOMER_ORG/$repository" \
    --private --source "$STAGE/$repository" --remote origin --push
done

gh repo edit "$CUSTOMER_ORG/nonprod-project-template" --template
gh repo edit "$CUSTOMER_ORG/prod-project-template" --template
test "$(gh api "repos/$CUSTOMER_ORG/nonprod-project-template" --jq '.is_template')" = true
test "$(gh api "repos/$CUSTOMER_ORG/prod-project-template" --jq '.is_template')" = true
```

The command above must return no output. In the published `platform-ci`
repository, set **Settings → Actions → General → Access** to
**Accessible from repositories in the organization**, then verify it and record
the published commits:

```bash
test "$(gh api "repos/$CUSTOMER_ORG/platform-ci/actions/permissions/access" \
  --jq '.access_level')" = organization

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

**Continue only when:** all commands that use `test` return exit code zero and
the four commit values are recorded as installation evidence.

## 3. Register and verify trusted runners

Register each existing host as an organization runner using GitHub's
[self-hosted runner instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).
Use the host-specific registration and service instructions from GitHub; never
copy a registration token into this runbook.

| Boundary | Required labels | Required software and configuration |
| --- | --- | --- |
| Resolver | `self-hosted`, `control-plane-resolver` | Linux, Bash, Git, `jq`, and `rg`; outbound access to GitHub Actions. |
| Non-production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), selected environment (`dev`, `test`, or `uat`) | Linux, Bash, Git, Python 3.11 or later with `pip`, `curl`, and `sha256sum`; outbound HTTPS to GitHub Actions, HashiCorp, PyPI, and Ansible Galaxy. |
| Production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), `prod` | The same execution requirements, on a separate runner instance and identity. |

Execution runners need `STATE_NAMESPACE`, `STATE_REGION`, and
`OCI_CLI_AUTH=instance_principal`. Their identity may access only the state
bucket and the required workload services. For Azure, add Azure CLI and the
approved `ARM_*` service-principal values. For Google Cloud, use
`GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default
Credentials. Keep every credential outside Git. The workflow installs Terraform
1.12.1.

When available, use separate organization runner groups restricted to the
approved repositories. The supplied baseline can run every selected cloud from
OCI hosts, whose dynamic-group policies must cover only the state bucket and
the required workload compartments and services. Use separate non-production
and production SSH key pairs. OCI Compute manifests use
`/home/github-runner/.ssh/oci_vm_key.pub`; supported Ansible operations use the
matching private key at `/home/github-runner/.ssh/oci_vm_key`, readable only by
the `github-runner` account.

On each resolver runner, verify the required programs:

```bash
for program in bash git jq rg; do
  command -v "$program" >/dev/null || { echo "Missing $program"; exit 1; }
done
```

On each execution runner, verify the required programs and non-secret settings:

```bash
for program in bash git python3.11 curl sha256sum; do
  command -v "$program" >/dev/null || { echo "Missing $program"; exit 1; }
done
for variable in STATE_NAMESPACE STATE_REGION OCI_CLI_AUTH; do
  test -n "${!variable:-}" || { echo "Missing $variable"; exit 1; }
done
```

From the administrator workstation, confirm that every required runner is
online with the intended labels:

```bash
gh api "orgs/$CUSTOMER_ORG/actions/runners" --paginate \
  --jq '.runners[] | [.name, .status, (.labels | map(.name) | join(","))] | @tsv'
```

**Continue only when:** all checks succeed, every required runner is online,
and every identity has the intended state and workload access.

## 4. Hand off the first project repository

Create a project repository only after its project-foundation handoff is
complete. Use `nonprod-project-template` for the shared `dev`, `test`, and
`uat` model, or `prod-project-template` for the isolated `prod` model.

```bash
export PROJECT_REPOSITORY=nonprod-example-project
gh repo create "$CUSTOMER_ORG/$PROJECT_REPOSITORY" \
  --private --template "$CUSTOMER_ORG/nonprod-project-template"
```

Before giving the Project Team access:

1. Complete `environments/<environment>/environment_information.md` for each
   enabled cloud; blank values are not valid. The OCI references are published
   into that file by the Landing Zone project-foundation handoff (the OP04 phase
   that creates the project compartments, groups, and policies), so do not
   hand-write them. Complete the Azure and Google Cloud sections yourself in a
   separate reviewed pull request. Use the
   [OCI Landing Zone](../../../../../landing-zones/README.md) if the foundation
   does not exist yet.
2. Configure Project Team access and reviewed ownership from
   `.github/CODEOWNERS.template`.
3. Confirm the project's runners, identities, state boundary, and any required
   `GITOPS_SECRET_VALUES_<ENVIRONMENT>` secret bundle. Add that bundle only
   when supported workload placeholders require it.
4. Confirm the request surface is within the [supported MVP scope](../reference/support.md).

**Continue only when:** the handoff is complete. The Project Team then starts
with the [Project Team guide](../usage/README.md), not with platform setup.

## 5. Accept the first project

Run the [environment secret-isolation check](../reference/verify-secret-isolation.md)
after handoff and before the first workload request. It reaches Terraform plan
but does not deploy infrastructure.

**Complete when:** the published commits and Platform CI access are verified,
all required runners are online with the intended labels and authority, and the
first project passes that check. Retain the commits, repository settings,
runner labels, identity boundaries, handoff, and successful checks as
installation evidence. Remove the temporary staging directory only after
recording that evidence.
