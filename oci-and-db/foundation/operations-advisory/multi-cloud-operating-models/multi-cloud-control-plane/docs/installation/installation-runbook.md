# Installation runbook

Cloud Operations uses this runbook to publish the shared repositories, connect trusted runners and verify the first project. Start with an existing cloud foundation, state bucket, runner hosts and customer identities.

## Installation path

| Stage | Checkpoint |
| --- | --- |
| [1. Prepare the inputs](#1-prepare-the-installation-inputs) | The source clone, GitHub access and cloud prerequisites are ready. |
| [2. Publish the repositories](#2-publish-the-shared-repositories) | Four private repositories are published at the verified commits. |
| [3. Verify trusted runners](#3-register-and-verify-trusted-runners) | Runners are online with the required labels, access and secret configuration. |
| [4. Hand off the first project](#4-hand-off-the-first-project-repository) | The project repository has its reviewed scope, access and merge controls. |
| [5. Accept the first project](#5-accept-the-first-project) | The first intended plan or check passes on the customer runners. |

Run the commands from the `multi-cloud-control-plane` directory of a clean clone. Continue when the current stage's checkpoint passes. After acceptance, Project Teams can use GitHub directly. If selected, complete the [optional interface setup](optional-interfaces.md).

## 1. Prepare the installation inputs

Before starting, confirm these inputs and retain the indicated evidence:

| Input | Owner | Evidence before publication |
| --- | --- | --- |
| Customer GitHub organization with private-repository, Actions, and organization-runner administration | Cloud Operations with the customer organization administrator | `gh auth status` identifies the intended account. |
| Clean MCCP source clone with Git, GitHub CLI (`gh`), `jq`, `rg`, and Perl | Installation operator | `git status --short` is empty and all required tools are available. |
| Dedicated, private, versioned OCI Object Storage state bucket, including namespace and region | Cloud Operations | Approved bucket details; it is not a foundation-state bucket. |
| Separate trusted Linux runner hosts for non-production and production | Cloud Operations | Approved cloud identities and network access. |
| Existing environment foundation for the first project | Cloud Operations | Approved environment and OCI region, foundation compartments and network, shared workload Vault and runner policies. OP04 supplies the project compartments, key and handoff in step 4. Azure uses existing foundation inputs in the resource JSON and a configured runner. |

Authenticate `gh` to the intended customer organization, then check the source clone:

```bash
gh auth status
git status --short
```

**Continue only when:** `gh auth status` shows the intended account and `git status --short` has no output. Use a new clone if the current one contains unrelated work.

Terraform state always uses this OCI Object Storage bucket, including for Azure-only and Google Cloud-only deployments.

## 2. Publish the shared repositories

### 2.1 Render and validate the sources

Stage the four shared sources and set the customer values and reviewed orchestrator commits:

```bash
export STAGE="$(mktemp -d)"
export CUSTOMER_ORG=example-enterprise
export STATE_BUCKET=example-project-state
export OCI_ORCHESTRATOR_REF=d162f24e81b0720803a9c26db2bc96e271cefa09
export AZURE_ORCHESTRATOR_REF=791d46865e096cb58613b3b5319f0c5eee301e95
export GCP_ORCHESTRATOR_REF=ff64cb3534f11de7ae2693d5ab5dabbab479003c

: "${CUSTOMER_ORG:?set CUSTOMER_ORG}"
if ! [[ "$CUSTOMER_ORG" =~ ^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$ ]] || \
  [ "${#CUSTOMER_ORG}" -gt 39 ]; then
  echo 'Set CUSTOMER_ORG to a valid GitHub organization name.' >&2
  exit 1
fi
: "${STATE_BUCKET:?set STATE_BUCKET}"
: "${OCI_ORCHESTRATOR_REF:?set OCI_ORCHESTRATOR_REF}"
: "${AZURE_ORCHESTRATOR_REF:?set AZURE_ORCHESTRATOR_REF}"
: "${GCP_ORCHESTRATOR_REF:?set GCP_ORCHESTRATOR_REF}"

cp -R repository-sources/platform-ci "$STAGE/platform-ci"
cp -R repository-sources/nonprod-project-template "$STAGE/nonprod-project-template"
cp -R repository-sources/prod-project-template "$STAGE/prod-project-template"
cp -R repository-sources/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/nonprod-project-template/LICENSE"
cp LICENSE "$STAGE/prod-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__STATE_BUCKET__/$ENV{STATE_BUCKET}/g; s/__OCI_ORCHESTRATOR_REF__/$ENV{OCI_ORCHESTRATOR_REF}/g; s/__AZURE_ORCHESTRATOR_REF__/$ENV{AZURE_ORCHESTRATOR_REF}/g; s/__GCP_ORCHESTRATOR_REF__/$ENV{GCP_ORCHESTRATOR_REF}/g' {} +
```

`STAGE` is a local build directory, not a Git repository or secret store. Keep it accessible only to the installation operator. `STATE_BUCKET` is rendered into the project workflow templates where the token is `__STATE_BUCKET__`.

The OCI pin selects the official [Orchestrator v2.3.0 release commit](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator/commit/d162f24e81b0720803a9c26db2bc96e271cefa09), which supports native ADB Vault references. The Azure pin selects the [connectivity-aware adapter](https://github.com/oci-clickops/clickops-orchestrator-azure/commit/791d46865e096cb58613b3b5319f0c5eee301e95), which supports private and public mTLS profiles. The Google Cloud pin selects the reviewed [Google Cloud adapter](https://github.com/oci-clickops/clickops-orchestrator-gcp/commit/ff64cb3534f11de7ae2693d5ab5dabbab479003c). Keep these reviewed commits for a repeatable installation; upgrades follow their own review and validation.

Verify the rendered sources before creating their local repository commits:

```bash
if rg --hidden --glob '!.git' \
  '__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__' "$STAGE"; then
  echo 'Unrendered installation placeholder found.' >&2
  exit 1
fi
```

The command above must return no output.

### 2.2 Create the local repository commits

Create Platform CI first, then prepare the templates and catalog:

```bash
git -C "$STAGE/platform-ci" init -b main
git -C "$STAGE/platform-ci" add -A
git -C "$STAGE/platform-ci" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare Platform CI'
export PLATFORM_CI_COMMIT=$(git -C "$STAGE/platform-ci" rev-parse HEAD)

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

### 2.3 Publish, configure, and record evidence

Keep Platform CI private, grant write access to Cloud Operations and review changes to its `main`. Project workflows call that branch at runtime. Record `PLATFORM_CI_COMMIT` as installation evidence. Follow the [security controls](../reference/security.md#required-controls) when reviewing Action releases and configuring repositories.

Publish the staged sources and enable the project templates:

```bash
for repository in platform-ci nonprod-project-template prod-project-template gitops-templates; do
  gh repo create "$CUSTOMER_ORG/$repository" \
    --private --source "$STAGE/$repository" --remote origin --push
done

gh repo edit "$CUSTOMER_ORG/nonprod-project-template" --template
gh repo edit "$CUSTOMER_ORG/prod-project-template" --template
test "$(gh api "repos/$CUSTOMER_ORG/nonprod-project-template" --jq '.is_template')" = true
test "$(gh api "repos/$CUSTOMER_ORG/prod-project-template" --jq '.is_template')" = true
```

In the published `platform-ci` repository, set **Settings → Actions → General → Access** to **Accessible from repositories in the organization**, then verify it and record the published commits:

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

**Continue only when:** all commands that use `test` return exit code zero and the four commit values are recorded as installation evidence.

To resume an interrupted publication, recreate and verify the staging output if needed. Check which repositories exist and inspect their published `main` commits before retrying. Repair the push only for the intended partial repository, or follow the approved recovery process if it differs. Publish the missing repositories and repeat the commit checks for all four.

## 3. Register and verify trusted runners

Register each existing host as an organization runner using GitHub's [self-hosted runner instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners). Use the host-specific registration and service instructions from GitHub; never copy a registration token into this runbook.

| Boundary | Required labels | Required software and configuration |
| --- | --- | --- |
| Resolver | `self-hosted`, `control-plane-resolver` | Linux, Bash, Git, `jq`, and `rg`; outbound access to GitHub Actions. |
| Non-production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), selected environment (`dev`, `test`, or `uat`) | Linux, Bash, Git, `jq`, `rg`, OCI CLI, Python 3.11 available as `python3.11`, with `pip`, `curl`, and `sha256sum`; outbound HTTPS to GitHub Actions, HashiCorp, PyPI, and Ansible Galaxy. |
| Production execution | `self-hosted`, selected cloud (`oci`, `azure`, or `gcp`), `prod` | The same execution requirements, on a separate runner instance and identity. |

### Execution runner preflight

Set the following values in the runner service environment, such as the runner service `.env` file, not only in an operator shell. Keep every credential outside Git.

| Scope | Required configuration |
| --- | --- |
| Every execution runner | `STATE_NAMESPACE`, `STATE_REGION`, and `OCI_CLI_AUTH=instance_principal`; the runner identity may access only the state bucket and required workload services. This is required even for Azure-only and Google Cloud-only deployments because Terraform state uses OCI Object Storage. |
| Azure execution runner | `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`, and a protected PFX at `ARM_CLIENT_CERTIFICATE_PATH`; set `ARM_CLIENT_CERTIFICATE_PASSWORD` for an encrypted PFX. Platform CI authenticates AzureRM directly with the certificate. Existing Azure CLI and `ARM_CLIENT_SECRET` installations remain supported. Keep certificate files and credential values outside Git. |
| Google Cloud execution runner | `GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default Credentials. |
| Workflow runtime | The workflow installs Terraform `1.12.1`. |

Use separate organization runner groups restricted to the approved repositories. The supplied baseline can run every selected cloud from OCI hosts, whose dynamic-group policies must cover only the approved state, workload and Vault scope. A shared dev runner may serve several approved project repositories. Its identity is shared too: labels select jobs but do not isolate permissions between projects. Use separate identities and runner groups when the customer needs that stronger boundary. Use separate non-production and production SSH key pairs. OCI Compute manifests use `/home/github-runner/.ssh/oci_vm_key.pub`; supported Ansible operations use the matching private key at `/home/github-runner/.ssh/oci_vm_key`, readable only by the `github-runner` account.

On each resolver runner, verify the required programs:

```bash
for program in bash git jq rg; do
  command -v "$program" >/dev/null || { echo "Missing $program"; exit 1; }
done
```

On each execution runner, verify the required programs and non-secret settings:

```bash
for program in bash git jq rg oci python3.11 curl sha256sum; do
  command -v "$program" >/dev/null || { echo "Missing $program"; exit 1; }
done
python3.11 -m pip --version >/dev/null || { echo 'Missing pip for python3.11'; exit 1; }
for variable in STATE_NAMESPACE STATE_REGION OCI_CLI_AUTH; do
  test -n "${!variable:-}" || { echo "Missing $variable"; exit 1; }
done
```

From the administrator workstation, confirm that every required runner is online with the intended labels:

```bash
gh api "orgs/$CUSTOMER_ORG/actions/runners" --paginate \
  --jq '.runners[] | [.name, .status, (.labels | map(.name) | join(","))] | @tsv'
```

**Continue only when:** all checks succeed, every required runner is online, and every identity has the intended state and workload access.

### Prepare workload-secret delivery

Before onboarding, Cloud Operations prepares and administers the shared workload Vault and configures the runner policies for the intended project scope. After step 4 delivers the version 5 handoff, use it to identify the shared Vault, project HSM key and Database compartment and verify the runner's required read access. The Project Team then creates and rotates the database secrets; a new installation does not need project secrets or a project handoff before OP04.

| Request | Secret input |
| --- | --- |
| OCI ADB | One Vault secret per database in the approved project scope and deployment region. Use its OCID in `admin_password_secret_id`. |
| Azure ADB | One Vault secret per database in the approved project scope. Use its OCID in `admin_password_secret_id` and the OCI region in the trusted handoff for the secret. |
| Google Cloud ADB | The provider-native reference from the catalog. |

After handoff, verify access through the first intended request that uses a secret. Use the approved SSH public key directly in Azure and Google VM manifests. Keep credentials outside Git and replace all catalog placeholders before submitting a request. The [secret-delivery reference](../reference/security.md#secret-delivery) explains the trusted revision, metadata checks and native secret resolution.

## 4. Hand off the first project repository

The [OCI Landing Zone project-onboarding workflow](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities), known as OP04, prepares the OCI project foundation. It creates the project and its Application, Database and Infrastructure compartments, their admin groups, and one AES-256 HSM key in Database linked to the shared DEFAULT workload Vault. Cloud Operations prepares the environment foundation, shared Vault and runner policies in advance.

Complete steps 2 and 3 before starting automatic project delivery: the configured project template must be published and enabled, Platform CI must be accessible to the organization, and the required runners must be ready.

1. **Verify or obtain the project handoff.** If a valid handoff already exists for the intended project, environment and region, verify its schema, scope and published references through the governed Cloud Operations process and reuse it. Do not repeat onboarding. Otherwise, submit the reviewed OP04 onboarding and verify its successful apply and delivery. The configured automation can create an absent private `nonprod-<project>` repository from template `main` and deliver the dev handoff. Validate `project-foundation-handoff.json` and `environment_information.md` from that exact successful workflow run, then compare the published environment handoff with those artifacts. Use the non-production or production template for the intended boundary. If delivery is incomplete, follow [handoff recovery](#handoff-recovery) before continuing.
2. **Check the cloud inputs.** Use the generated OCI references in `environments/<environment>/environment_information.md`. For Google Cloud, verify the approved handoff references. Azure uses the existing resource group, location, network references where required and a dedicated secret for ADB. Supply these in the request or its JSON. The existing runner supplies `ARM_*` settings, and Azure entries in the handoff are optional context.
3. **Set access and review controls.** Give Project Team access. The Project Team can turn `.github/CODEOWNERS.template` into `.github/CODEOWNERS` as described in the project template. On Team or Enterprise Cloud, configure an active ruleset for `main` requiring a pull request and at least one approval, with no direct-push bypass. On GitHub Free private repositories, restrict direct access and record independent review through the [procedural control](../reference/security.md#github-plan-controls).
4. **Check readiness for the first request.** Verify the project's runner, state, identity and Vault scope. Check the [reference capabilities](../reference/support.md) and the inputs required for the first request with the Project Team.

**Continue only when:** the handoff is complete, Project Team has the intended access and review path, and all runner permissions and resource inputs for the selected cloud are ready. Use the [Project Team guide](../usage/README.md) to prepare the first request for acceptance.

### Handoff recovery

Keep incomplete delivery unverified and retain its workflow link. Use the governed Cloud Operations recovery procedure with validated artifacts from an eligible successful run. If no such evidence exists, stop before handoff publication; artifacts from a failed run are not eligible. A separate recovery write needs its own preview and confirmation. Inspect any existing target repository before recovery, preserve a valid handoff and ownership layout, and create an absent repository only through the configured GitHub template mechanism. Verify the recovered handoff against the validated artifacts before resuming. Do not repeat project creation or silently rerun the workflow.

## 5. Accept the first project

Use the [first-project check](../reference/verify-secret-isolation.md) on the first intended request in an enabled cloud. Confirm the expected runner, state and any secret references using the plan or lifecycle check before workload deployment.

For GitHub Team and GitHub Enterprise Cloud, also inspect the active `main` ruleset after configuring it:

```bash
export PROJECT_REPOSITORY=nonprod-orders

gh api "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/rulesets" --paginate \
  --jq '.[] | select(.target == "branch" and .enforcement == "active") | .id' |
while read -r ruleset_id; do
  gh api "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/rulesets/$ruleset_id" --jq \
    '{name, conditions, bypass_actors, rules}'
done
```

Set `PROJECT_REPOSITORY` to the handed-off repository name, without the organization prefix. For example, use `prod-orders` for a production project repository.

Confirm that the output contains the active rule targeting `main`, its required pull-request rule with at least one approval, and no direct-push bypass. GitHub Free installations do not run this plan-specific check.

**Complete when:** the published commits and Platform CI access are verified, all required runners are online with the intended labels and authority, and the first project passes that check. For plans that support private repository rulesets, retain the verified ruleset configuration with the installation evidence. Retain the commits, repository settings, runner labels, identity boundaries, handoff, and successful checks as installation evidence. Remove the temporary staging directory only after recording that evidence.
