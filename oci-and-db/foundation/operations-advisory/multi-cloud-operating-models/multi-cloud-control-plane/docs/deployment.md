# Deployment runbook

This runbook uses standard file, Git, `jq`, and Perl commands. Run it from a
clean clone of this asset; no custom deployment program is required.

## 1. Prepare the shared repositories

```bash
export STAGE=/tmp/control-plane
export CUSTOMER_ORG=example-enterprise
export PROJECT_STATE_BUCKET=example-project-state
export OCI_ORCHESTRATOR_REF=fcf1d7f02c0b4faa1ff55f1776c396452dd51761
export AZURE_ORCHESTRATOR_REF=2d0b532f7639212f1b7c2708cd15b71d80b217fe
export GCP_ORCHESTRATOR_REF=c434e0697a3ca4daa8f8c7903afd4c6c7be287f9
export NONPROD_SECURITY_PROFILE=github-environments
export PROD_SECURITY_PROFILE=github-environments
export PLATFORM_OWNER='@example-platform-owner'
export ENVIRONMENT_OWNER="$PLATFORM_OWNER"
export PROD_OWNER="$PLATFORM_OWNER"

mkdir -p "$STAGE"
cp -R components/platform-ci "$STAGE/platform-ci"
cp -R components/nonprod-project-template "$STAGE/nonprod-project-template"
cp -R components/prod-project-template "$STAGE/prod-project-template"
cp -R components/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/nonprod-project-template/LICENSE"
cp LICENSE "$STAGE/prod-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"
rm -rf "$STAGE/platform-ci/tests"

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/gitops-state-bucket/$ENV{PROJECT_STATE_BUCKET}/g; s/__STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g' {} +
```

`PROJECT_STATE_BUCKET` must name a dedicated private Object Storage bucket
with versioning enabled. Do not reuse the OCI Landing Zone foundation-state
bucket. When the Landing Zone asset creates the OP03 runner identity, its
`PROJECT_STATE_BUCKET` repository variable and this value must match exactly.

`OCI_ORCHESTRATOR_REF` pins OCI Landing Zones Orchestrator
[`release-2.1.4`](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator/tree/release-2.1.4).
That release consumes
[`terraform-oci-modules-exadata` `release-1.2.0`](https://github.com/oci-landing-zones/terraform-oci-modules-exadata/tree/release-1.2.0)
for both `autonomous_databases_configuration` and
`cloud_exadata_database_configuration`. The workflow uses the immutable
Orchestrator commit; the release-branch names remain recorded as provenance in
the deployment contract.

Create the Platform CI commit first because project workflows pin that exact
commit:

```bash
git -C "$STAGE/platform-ci" init -b main
git -C "$STAGE/platform-ci" add -A
git -C "$STAGE/platform-ci" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare Platform CI'
export PLATFORM_CI_REF=$(git -C "$STAGE/platform-ci" rev-parse HEAD)

find "$STAGE/nonprod-project-template" "$STAGE/prod-project-template" -type f -exec perl -pi -e \
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__OCI_ORCHESTRATOR_REF__/$ENV{OCI_ORCHESTRATOR_REF}/g; s/__AZURE_ORCHESTRATOR_REF__/$ENV{AZURE_ORCHESTRATOR_REF}/g; s/__GCP_ORCHESTRATOR_REF__/$ENV{GCP_ORCHESTRATOR_REF}/g' {} +

for repository in nonprod-project-template prod-project-template gitops-templates; do
  git -C "$STAGE/$repository" init -b main
  git -C "$STAGE/$repository" add -A
  git -C "$STAGE/$repository" -c user.name='Platform Administrator' \
    -c user.email='platform@invalid' commit -m "Prepare $repository"
done

export PROJECT_TEMPLATE_REF=$(git -C "$STAGE/nonprod-project-template" rev-parse HEAD)
export PRODUCTION_PROJECT_TEMPLATE_REF=$(git -C "$STAGE/prod-project-template" rev-parse HEAD)
export CATALOGS_REF=$(git -C "$STAGE/gitops-templates" rev-parse HEAD)
cp contracts/deployment-contract.template.json "$STAGE/deployment-contract.json"
find "$STAGE/deployment-contract.json" -type f -exec perl -pi -e \
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__PROJECT_TEMPLATE_REF__/$ENV{PROJECT_TEMPLATE_REF}/g; s/__PRODUCTION_PROJECT_TEMPLATE_REF__/$ENV{PRODUCTION_PROJECT_TEMPLATE_REF}/g; s/__CATALOGS_REF__/$ENV{CATALOGS_REF}/g; s/__PROJECT_STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g; s/__NONPROD_SECURITY_PROFILE__/$ENV{NONPROD_SECURITY_PROFILE}/g; s/__PROD_SECURITY_PROFILE__/$ENV{PROD_SECURITY_PROFILE}/g; s/__PLATFORM_OWNER__/$ENV{PLATFORM_OWNER}/g; s/__ENVIRONMENT_OWNER__/$ENV{ENVIRONMENT_OWNER}/g; s/__PROD_OWNER__/$ENV{PROD_OWNER}/g' {} +
```

The example defaults to the recommended paid-plan `github-environments`
profile. For private repositories on GitHub Free, set both profile variables
to `repository-secrets`. Do not mix profiles inside one project repository.
See the [GitHub plan capability matrix](security.md#github-plan-capability-matrix).
Owner values must be existing `@user` or `@organization/team` identities with
write access. An isolated Free-plan acceptance test may use the same owner for
every path; production deployments should use separate environment reviewer
teams.

After pushing the prepared template repositories to the customer organization,
mark both of them as GitHub template repositories. Private templates remain
private; this setting is required before a Cloud Operator can create a project
repository from either template in the GitHub UI or API.

```bash
gh repo edit "$CUSTOMER_ORG/nonprod-project-template" --template
gh repo edit "$CUSTOMER_ORG/prod-project-template" --template
gh api "repos/$CUSTOMER_ORG/nonprod-project-template" --jq '.is_template'
gh api "repos/$CUSTOMER_ORG/prod-project-template" --jq '.is_template'
```

If the optional UI is required, copy `components/optional-ui`, replace
`__CUSTOMER_ORG__`, remove its `tests/` directory and `test_github_api.py`, and
initialize it in the same way. If the Codex app assistant
is required, copy `plugins/project-gitops`, replace `__CUSTOMER_ORG__`, and
install it through your approved Codex plugin process. Both remain optional.

Verify that no mutable workflow reference or local test content is present:

```bash
rg '@main|__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__|__PROJECT_STATE_BUCKET__' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the matching private GitHub
repositories and publish each prepared `main` branch through your approved Git
process. In the published `platform-ci` repository, allow project repositories
to call its reusable workflows at **Settings → Actions → General → Access → Accessible from
repositories in the organization**.

Keep `platform-ci` private. Reusable-workflow access alone does not authorize
the caller's `GITHUB_TOKEN` to check out private Platform CI files at runtime.
For a new GitHub organization, an organization owner must first enable deploy
keys at **Organization → Settings → Member privileges → Deploy keys → Enabled**.
Create one read-only SSH deploy key on `platform-ci` and store its private half
as the repository secret `PLATFORM_CI_DEPLOY_KEY` in every project repository.
The workflows pass that secret explicitly only to the SHA-pinned Platform CI
checkout; they never use `secrets: inherit`.

```bash
ssh-keygen -t ed25519 -f /secure/platform-ci-readonly-deploy-key -N '' \
  -C 'platform-ci readonly workflow checkout'
gh repo deploy-key add /secure/platform-ci-readonly-deploy-key.pub \
  --repo "$CUSTOMER_ORG/platform-ci" --title 'project workflow read-only checkout'
gh secret set PLATFORM_CI_DEPLOY_KEY --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY" \
  < /secure/platform-ci-readonly-deploy-key
```

Do not enable write access for the deploy key. Protect and rotate the key like
any other repository secret; it authorizes read-only access to Platform CI code
only, not cloud access or GitHub writes. Do not commit it, add it to the JSON
secret bundles, or expose it in a workflow log.

On paid plans, apply this branch-protection baseline to every project
repository after rendering valid CODEOWNERS. It requires an independent
approval, CODEOWNERS review, approval of the latest push, resolved
conversations, and administrator enforcement:

```bash
export PROTECTED_REPOSITORY="$CUSTOMER_ORG/$PROJECT_REPOSITORY"
jq -n '{
  required_status_checks: null,
  enforce_admins: true,
  required_pull_request_reviews: {
    dismiss_stale_reviews: true,
    require_code_owner_reviews: true,
    required_approving_review_count: 1,
    require_last_push_approval: true
  },
  restrictions: null,
  allow_force_pushes: false,
  allow_deletions: false,
  required_conversation_resolution: true
}' | gh api --method PUT \
  "repos/$PROTECTED_REPOSITORY/branches/main/protection" --input -
gh api "repos/$PROTECTED_REPOSITORY/branches/main/protection"
```

The baseline deliberately does not register a static status-check context.
Terraform and Ansible use mutually exclusive path-filtered workflows; GitHub
leaves a required path-filtered workflow pending when that workflow is not
selected. Reviewers must verify the successful plan/check attached to the
current commit before merge. An organization that requires technical status
enforcement must first provide one stable, always-running aggregate gate and
then add only that context to `required_status_checks`.

GitHub Free private repositories cannot enforce the same branch and code-owner
controls; restrict administration and direct pushes, record a human PR review,
verify the current plan/check, and follow the limitations in
[Shared non-production](shared-nonproduction.md#github-free-fallback-repository-secrets).

## 2. Configure trusted runners

| Setting | Purpose |
|---|---|
| `STATE_NAMESPACE` | OCI Object Storage namespace |
| `STATE_REGION` | Region of the OCI state bucket |
| `OCI_CLI_AUTH=instance_principal` | OCI state and inventory authentication |
| `REGION` | Optional workload-region fallback |

Runners need Terraform 1.12 or later, Python 3.11 or later, and `rg` for
validation. On GitHub Free, use repository-level self-hosted runners and
dedicated environment labels; do not share one runner identity across security
boundaries. On GitHub Team or Enterprise, use organization runner groups and
grant each group only to the repositories that need it. Enterprise runner
groups may also be scoped across organizations. OCI runner instances must
belong to an OCI dynamic group with policies for Object Storage state access
and only the compartments/services required by their workload. Azure and
Google runners need equivalent workload-scoped identities. Azure additionally
needs its approved service-principal environment values. Google needs
`GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default
Credentials. Keep credentials outside Git.

For the optional non-production ExaCS out-of-place patch operation, use a
dedicated runner dynamic group and scope it to the registered database
compartment. The OCI Database API move requires Database and Database Home
permissions. Name the dynamic group after the repository and bind it to the
single runner instance, not its whole compartment. For example, a project
named `orders` uses `mcp-exacs-orders-runner-dg` and the following matching
rule:

```text
ALL {instance.id = '<exacs-runner-instance-ocid>'}
```

On OCI tenancies that use identity domains, create the dynamic group in
**Identity & Security → Domains → Default → Dynamic Groups**. Use `Default`
unless a platform administrator has deliberately established another domain
for runner identities. A group in `Default` is referenced by its unqualified
name in a policy; a group in another domain must use the qualified form
`'<domain-name>'/'<group-name>'`.

Create a tenancy policy named `mcp-exacs-orders-runner-policy` with the
following statement. Use the database compartment OCID so a renamed or
similarly named compartment cannot broaden the permission:

```text
Allow dynamic-group mcp-exacs-orders-runner-dg to manage database-family in compartment id <project-database-compartment-ocid>
```

Do not grant this policy at tenancy scope. Route the operation only to that
dedicated runner group by registering it with the additional
`exacs-database-operations` label. Register only approved databases and target
homes, and keep the generic project runner outside this dynamic group.

### Oracle Linux 9 ExaCS runner bootstrap

Use a repository-scoped runner for a non-production ExaCS test or project
repository. Do not reuse it for another repository or register it at
organization scope. Confirm the architecture before downloading the matching
GitHub Actions package:

```bash
uname -m # aarch64 selects actions-runner-linux-arm64; x86_64 selects linux-x64
sudo dnf config-manager --set-enabled ol9_developer_EPEL
sudo dnf install -y git ripgrep python3.11 python3.11-pip
```

The VM must have outbound HTTPS (TCP 443) access to GitHub Actions before
registration. At minimum, allow `github.com`, `api.github.com`, and
`*.actions.githubusercontent.com`; the runner also needs `codeload.github.com`
to download actions, `results-receiver.actions.githubusercontent.com` and
`*.blob.core.windows.net` for job logs/artifacts, and the GitHub release/object
domains for runner updates. Use GitHub's current self-hosted-runner domain list
when configuring a firewall or proxy because the published endpoint set can
change. A VM that can install Oracle Linux packages but cannot reach GitHub
cannot register or accept Actions jobs.

For Ansible operations, also permit outbound HTTPS to `pypi.org`,
`files.pythonhosted.org`, and `galaxy.ansible.com`. The workflow installs the
pinned Ansible runtime and Oracle OCI collection before it reads a lifecycle
manifest; block that traffic and the workflow fails before contacting OCI.
If the runner uses an outbound proxy, configure it as a URI, for example
`HTTP_PROXY=http://proxy.example:8080` and
`HTTPS_PROXY=http://proxy.example:8080`. The workflow normalizes a legacy
scheme-less value for its own Ansible bootstrap, but the runner service should
use the URI form so all tools behave consistently. Do not disable TLS
certificate verification; install the enterprise CA bundle if the proxy
intercepts TLS.

Download the current matching runner package from GitHub's runner release page,
verify its published SHA-256 checksum, unpack it under a dedicated directory,
and run its dependency installer. Generate a short-lived registration token in
the repository's **Settings → Actions → Runners → New self-hosted runner**
page; never paste a token into a ticket, pull request, terminal history, or
committed file.

```bash
mkdir -p "$HOME/actions-runner-exacs" && cd "$HOME/actions-runner-exacs"
# Download and checksum-verify the package selected for uname -m.
tar xzf actions-runner-linux-<architecture>-<version>.tar.gz
sudo ./bin/installdependencies.sh
./config.sh --unattended \
  --url "https://github.com/<organization>/nonprod-<project>" \
  --token '<short-lived-registration-token>' \
  --name 'exacs-<project>-<hostname>' \
  --labels 'oci,dev,control-plane-resolver,exacs-database-operations' \
  --work _work
sudo ./svc.sh install <runner-user>
sudo ./svc.sh start
sudo ./svc.sh status
```

`control-plane-resolver` is required only for the caller's secret-free path
resolver. With repository registration it cannot receive jobs from another
repository. `exacs-database-operations` is appended only for the governed
out-of-place patch operation, so that job cannot run on a generic OCI runner.
The VM's OCI dynamic group must have the database-family policy above; its
scope is the approved database compartment, never the tenancy.

## 3. Onboard an OCI project

Validate the handoff before copying the project template:

The canonical field contract is
`contracts/project-foundation-handoff.schema.json`.

```bash
export HANDOFF=/secure/project-foundation-handoff.json
export PROJECT_OUTPUT=/tmp/project-repository
export PROJECT_REPOSITORY=$(jq -r .target_repository "$HANDOFF")
export PROJECT_TOKEN=${PROJECT_REPOSITORY#nonprod-}
export SECURITY_PROFILE=github-environments

jq -e '
  .schema_version == 2 and .repository_layout == "shared-nonprod-v2" and .cloud == "oci" and
  (.source_commit | test("^[0-9a-f]{40}$")) and
  (.source_run | test("^[0-9]+$")) and
  ((.subnets | keys | sort) == ["app","database","infrastructure","web"])
' "$HANDOFF"

cp -R "$STAGE/nonprod-project-template" "$PROJECT_OUTPUT"
rm -rf "$PROJECT_OUTPUT/.git"
test "$PROJECT_REPOSITORY" = "nonprod-$PROJECT_TOKEN"
find "$PROJECT_OUTPUT" -type f -exec perl -pi -e \
  's/__PROJECT__/$ENV{PROJECT_TOKEN}/g' {} +
case "$SECURITY_PROFILE" in
  github-environments|repository-secrets) ;;
  *) echo "Unsupported SECURITY_PROFILE" >&2; exit 1 ;;
esac
jq --arg profile "$SECURITY_PROFILE" '.security_profile = $profile' \
  "$PROJECT_OUTPUT/control-plane.json" > "$PROJECT_OUTPUT/control-plane.json.tmp"
mv "$PROJECT_OUTPUT/control-plane.json.tmp" "$PROJECT_OUTPUT/control-plane.json"
{
  printf '# Project Environment Information\n\n```json\n'
  jq --sort-keys . "$HANDOFF"
  printf '\n```\n'
} > "$PROJECT_OUTPUT/environments/dev/environment_information.md"

# Generic templates deliberately ship CODEOWNERS.template, not active rules.
# Every owner must already exist and have repository write access.
export PLATFORM_OWNERS='@example-platform-admin'
export DEV_OWNERS='@example-dev-approver'
export TEST_OWNERS='@example-test-approver'
export UAT_OWNERS='@example-uat-approver'
cp "$PROJECT_OUTPUT/.github/CODEOWNERS.template" \
  "$PROJECT_OUTPUT/.github/CODEOWNERS"
find "$PROJECT_OUTPUT/.github/CODEOWNERS" -type f -exec perl -pi -e \
  's/__PLATFORM_OWNERS__/$ENV{PLATFORM_OWNERS}/g; s/__DEV_OWNERS__/$ENV{DEV_OWNERS}/g; s/__TEST_OWNERS__/$ENV{TEST_OWNERS}/g; s/__UAT_OWNERS__/$ENV{UAT_OWNERS}/g' {} +
! rg '__[A-Z_]+__' "$PROJECT_OUTPUT/.github/CODEOWNERS"

git -C "$PROJECT_OUTPUT" init -b main
git -C "$PROJECT_OUTPUT" add -A
git -C "$PROJECT_OUTPUT" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare project repository'
git -C "$PROJECT_OUTPUT" status --short
```

The final command must return no output. Repeat the verified handoff for each
enabled environment under `environments/<environment>/environment_information.md`.
Confirm the project, environment,
region, compartments, VCN, subnets, workflow run, commit, and state keys against
the approved onboarding record. Then create the private project repository,
apply the same protections, and grant the Project Team access.

Keep `.github`, `control-plane.json`, and `environments` under platform
ownership; only workload subtrees are delegated. On a paid plan, require
code-owner review and the plan/check status in the `main` branch-protection rule.

Configure exactly one security profile for the entire repository. Do not
configure both sources.

For the recommended paid-plan `github-environments` profile, create two GitHub
Environments for every enabled logical environment. The base Environment
(`dev`, `test`, or `uat`) is used by plan/check and has no required reviewers.
The matching apply Environment (`dev-apply`, `test-apply`, or `uat-apply`) is
used by apply/execute; configure its required reviewers and prevention of
self-review where the plan supports those controls. Store identical copies of
the two environment secrets in each pair. These commands prompt for secret
values:

```bash
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/dev"
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/dev-apply"
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/test"
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/test-apply"
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/uat"
gh api --method PUT "repos/$CUSTOMER_ORG/$PROJECT_REPOSITORY/environments/uat-apply"
gh secret set GITOPS_SECRET_VALUES --env dev --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env dev --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES --env dev-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env dev-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES --env test --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env test --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES --env test-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env test-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES --env uat --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env uat --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES --env uat-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set READINESS_MARKER --env uat-apply --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
printf '{"INVALID":"true"}\n' | gh secret set GITOPS_SECRET_VALUES --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
printf 'false\n' | gh secret set READINESS_MARKER --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
```

The last two repository secrets are non-sensitive, invalid sentinels required
by GitHub's reusable-workflow secret channel. They must remain exactly
`{"INVALID":"true"}` and `false`; never store real values in them. The invalid
member cannot pass any environment-qualified secret-name check. When the called job declares the
selected Environment, its same-named secrets override the sentinels. A missing
or misspelled Environment or secret therefore fails readiness or placeholder
resolution instead of falling back to repository credentials. Keep every
base/apply secret pair synchronized and verify both copies after rotation.

For the GitHub Free `repository-secrets` fallback, use the repository bundles
and readiness variables:

```bash
gh secret set GITOPS_SECRET_VALUES_DEV --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES_TEST --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh secret set GITOPS_SECRET_VALUES_UAT --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh variable set CONTROL_PLANE_READY_DEV --body true --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh variable set CONTROL_PLANE_READY_TEST --body true --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
gh variable set CONTROL_PLANE_READY_UAT --body true --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
```

Only configure enabled environments. Every JSON member name must begin with
the corresponding uppercase environment. Never place multiple environments in
one bundle.

Project automation is disabled by default. Only after the rendered contract,
CODEOWNERS, handoff files, selected-profile secrets and readiness markers,
runner routing, and `main` branch protection are verified, enable it once:

```bash
gh variable set PROJECT_AUTOMATION_READY --body true \
  --repo "$CUSTOMER_ORG/$PROJECT_REPOSITORY"
```

Do not set this variable while publishing or rendering a generic template. A
missing or any value other than `true` skips every project workflow before it
can allocate a runner.

## 4. Confirm the installation

Open one non-production manifest pull request. The installation is working when
the expected plan is tied to the current commit, a human review is recorded,
the trusted runner completes the merged change, and state is stored
under the expected project/cloud/environment/region key.

## 5. Verify secret isolation

For `github-environments`, complete the mandatory
[GitHub Environment end-to-end verification](environment-secret-e2e.md). For
`repository-secrets`, complete the mandatory
[repository-secret end-to-end verification](repository-secret-e2e.md). Do not
allow workload requests until the selected profile passes its procedure.
