# Deployment runbook

This runbook uses standard file, Git, `jq`, and Perl commands. Run it from a
clean clone of this asset; no custom deployment program is required.

## 1. Prepare the shared repositories

```bash
export STAGE=/tmp/control-plane
export CUSTOMER_ORG=example-enterprise
export PROJECT_STATE_BUCKET=example-project-state
export MCCP_RELEASE=v2.1.0
export OCI_ORCHESTRATOR_REF=fcf1d7f02c0b4faa1ff55f1776c396452dd51761
export AZURE_ORCHESTRATOR_REF=mccp-v2.1.0
export GCP_ORCHESTRATOR_REF=mccp-v2.1.0
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

find "$STAGE" -type d \( -name tests -o -name __pycache__ \) \
  -prune -exec rm -rf {} +

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g' {} +
```

`PROJECT_STATE_BUCKET` must name a dedicated private Object Storage bucket
with versioning enabled. Do not reuse the OCI Landing Zone foundation-state
bucket. When the Landing Zone asset creates the OP03 runner identity, its
`PROJECT_STATE_BUCKET` repository variable and this value must match exactly.

`OCI_ORCHESTRATOR_REF` pins OCI Landing Zones Orchestrator
[`release-2.1.4`](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator/tree/release-2.1.4).
The workflow uses its immutable commit; release-branch names remain recorded
as provenance in the deployment contract.

Create and tag Platform CI first because project workflows pin that internal
MCCP release tag:

```bash
git -C "$STAGE/platform-ci" init -b main
git -C "$STAGE/platform-ci" add -A
git -C "$STAGE/platform-ci" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare Platform CI'
git -C "$STAGE/platform-ci" tag -a "$MCCP_RELEASE" \
  -m "MCCP $MCCP_RELEASE"
export PLATFORM_CI_REF="$MCCP_RELEASE"

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
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__PROJECT_TEMPLATE_REF__/$ENV{PROJECT_TEMPLATE_REF}/g; s/__PRODUCTION_PROJECT_TEMPLATE_REF__/$ENV{PRODUCTION_PROJECT_TEMPLATE_REF}/g; s/__CATALOGS_REF__/$ENV{CATALOGS_REF}/g; s/__PROJECT_STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g; s/__PLATFORM_OWNER__/$ENV{PLATFORM_OWNER}/g; s/__ENVIRONMENT_OWNER__/$ENV{ENVIRONMENT_OWNER}/g; s/__PROD_OWNER__/$ENV{PROD_OWNER}/g' {} +
```

Treat `MCCP_RELEASE` and both external adapter release tags as immutable;
never move an existing release tag. Official GitHub Actions use their reviewed
major release tags.

The MVP uses the fixed `repository-secrets` profile on GitHub Free. Each
enabled environment receives its own repository secret bundle and readiness
variable; the reviewed pull request remains the human deployment gate. See the
[security model](security.md) and the separate
[final-environment hardening guide](final-environment-hardening.md) before
adding paid-plan controls.
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

If the Codex app assistant is required, package it with the rendered installation
contract and install that staged directory through the approved plugin process:

```bash
cp -R plugins/project-gitops "$STAGE/project-gitops"
cp contracts/deployment-contract.template.json \
  "$STAGE/project-gitops/deployment-contract.json"
perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g;
   s/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g;
   s/__PROJECT_TEMPLATE_REF__/$ENV{PROJECT_TEMPLATE_REF}/g;
   s/__PRODUCTION_PROJECT_TEMPLATE_REF__/$ENV{PRODUCTION_PROJECT_TEMPLATE_REF}/g;
   s/__CATALOGS_REF__/$ENV{CATALOGS_REF}/g;
   s/__PROJECT_STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g;
   s/__PLATFORM_OWNER__/$ENV{PLATFORM_OWNER}/g;
   s/__ENVIRONMENT_OWNER__/$ENV{ENVIRONMENT_OWNER}/g;
   s/__PROD_OWNER__/$ENV{PROD_OWNER}/g' \
  "$STAGE/project-gitops/deployment-contract.json"
if rg -n '__[A-Z0-9_]+__' "$STAGE/project-gitops/deployment-contract.json"
then
  echo 'Unresolved deployment-contract placeholders remain' >&2
  exit 1
fi
```

The assistant remains optional and is not required by any workflow.

Verify that no mutable shared-workflow reference or local test content is
present:

```bash
rg '@main|__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__|__PROJECT_STATE_BUCKET__' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the matching private GitHub
repositories and publish each prepared `main` branch through your approved Git
process. Publish the `platform-ci` release tag at the same time and verify that
it resolves to the reviewed Platform CI commit. In the published `platform-ci`
repository, allow project repositories to call its reusable workflows at
**Settings → Actions → General → Access → Accessible from repositories in the
organization**.

Before recording the published component commits in the deployment contract,
clone the four component repositories into one temporary directory and run the
release parity gate against the same rendered staging values. The substitutions
file contains only non-secret rendered values such as immutable release tags,
commits, and bucket names; do not put credentials or secret values in it.

```bash
python3.11 scripts/verify-release-parity.py \
  --manifest contracts/release-parity-manifest.template.json \
  --published-root /tmp/published-components \
  --customer-org "$CUSTOMER_ORG" \
  --substitutions /secure/non-secret-release-substitutions.json
```

The command must return exit code zero. It fails for a missing, unexpected, or
different regular file, including a stale project-level policy file, or an
unrendered release-owned token declared in the manifest. Project and catalog
runtime tokens (for example `__ADB_DISPLAY_NAME__`) remain intentionally in
the published templates. Runtime foundation, project, and disposable acceptance
repositories are validated by their pinned source commits and handoff contracts,
not by copying their tenancy-specific files into this release bundle.

Keep `platform-ci` private. Reusable-workflow access alone does not authorize
the caller's `GITHUB_TOKEN` to check out private Platform CI files at runtime.
For a new GitHub organization, an organization owner must first enable deploy
keys at **Organization → Settings → Member privileges → Deploy keys → Enabled**.
Create one read-only SSH deploy key on `platform-ci` and store its private half
as the repository secret `PLATFORM_CI_DEPLOY_KEY` in every project repository.
The workflows pass that secret explicitly only to the release-tag-pinned
Platform CI checkout; they never use `secrets: inherit`.

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

For the paid-plan enforcement model, apply this branch-protection
baseline to every project repository after rendering valid CODEOWNERS. It
requires an independent
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
[Shared non-production](shared-nonproduction.md).

## 2. Configure trusted runners

| Setting | Purpose |
|---|---|
| `STATE_NAMESPACE` | OCI Object Storage namespace |
| `STATE_REGION` | Region of the OCI state bucket |
| `OCI_CLI_AUTH=instance_principal` | OCI state and inventory authentication |
| `REGION` | Optional workload-region fallback |

Resolver runners need Git, `jq`, and `rg`. Execution runners need Git and
Python 3.11 or later; the workflow installs its pinned Terraform 1.12.1
runtime. On GitHub Free, use an organization runner group restricted to the
selected project repositories. Keep non-production and production in separate
groups, and add a repository only after its handoff is complete. GitHub Team
and Enterprise use the same model; Enterprise can also scope runner groups
across organizations. OCI runner instances must belong to an OCI dynamic group
with policies for Object Storage state access and only the
compartments/services required by their workload. Azure and Google runners need
equivalent workload-scoped identities. Azure additionally needs its approved
service-principal environment values. Google needs `GOOGLE_CREDENTIALS`,
`GOOGLE_APPLICATION_CREDENTIALS`, or Application Default Credentials. Keep
credentials outside Git.

The OP03 add-on creates one SSH key pair for each project-runner boundary. OCI
Compute manifests use only the public key at
`/home/github-runner/.ssh/oci_vm_key.pub`; supported Ansible operations use the
matching private key at `/home/github-runner/.ssh/oci_vm_key`. Project Teams do
not create, store, or rotate this key. Before enabling project automation,
verify as `github-runner` that both files exist and that the private key is
readable only by that service account. Non-production and production runners
must have separate key pairs.

## 3. Onboard an OCI project

Validate the handoff before copying the project template:

The canonical field contract is
`contracts/project-foundation-handoff.schema.json`.

```bash
export HANDOFF=/secure/project-foundation-handoff.json
export PROJECT_OUTPUT=/tmp/project-repository
export PROJECT_REPOSITORY=$(jq -r .target_repository "$HANDOFF")
export PROJECT_TOKEN=${PROJECT_REPOSITORY#nonprod-}

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

Keep `.github` and `environments` under platform ownership; only workload
subtrees are delegated. This GitHub Free MVP has a fixed
`repository-secrets` profile, and runner labels are derived from the request
cloud and environment. Record a human review and verify the plan/check on the
current commit before merging; private-repository branch protection and
enforced CODEOWNERS review are not claimed as technical controls in this MVP.

Configure repository bundles and readiness variables for enabled environments:

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
CODEOWNERS, handoff files, selected secret and readiness pairs, runner routing,
and manual-review process are verified, enable it once:

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

Complete the mandatory [repository-secret end-to-end verification](repository-secret-e2e.md).
Do not allow workload requests until it passes. The paid-plan enforcement
model is documented separately in [final-environment-hardening.md](final-environment-hardening.md).
