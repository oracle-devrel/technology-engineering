# Deployment runbook

This runbook uses standard file, Git, `jq`, and Perl commands. Run it from a
clean clone of this asset; no custom deployment program is required.

## 1. Prepare the shared repositories

```bash
export STAGE=/tmp/control-plane
export CUSTOMER_ORG=example-enterprise
export STATE_BUCKET=example-control-plane-state
export OCI_ORCHESTRATOR_REF=34202e837e9df015ddaaa4fce0ab62bb6e3883de
export AZURE_ORCHESTRATOR_REF=2d0b532f7639212f1b7c2708cd15b71d80b217fe
export GCP_ORCHESTRATOR_REF=c434e0697a3ca4daa8f8c7903afd4c6c7be287f9

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
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/gitops-state-bucket/$ENV{STATE_BUCKET}/g; s/__STATE_BUCKET__/$ENV{STATE_BUCKET}/g' {} +
```

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
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__PROJECT_TEMPLATE_REF__/$ENV{PROJECT_TEMPLATE_REF}/g; s/__PRODUCTION_PROJECT_TEMPLATE_REF__/$ENV{PRODUCTION_PROJECT_TEMPLATE_REF}/g; s/__CATALOGS_REF__/$ENV{CATALOGS_REF}/g' {} +
```

If the optional UI is required, copy `components/multi-cloud-plane`, replace
`__CUSTOMER_ORG__`, remove its `tests/` directory and `test_github_api.py`, and
initialize it in the same way. If the Codex app assistant
is required, copy `plugins/project-gitops`, replace `__CUSTOMER_ORG__`, and
install it through your approved Codex plugin process. Both remain optional.

Verify that no mutable workflow reference or local test content is present:

```bash
rg '@main|__CUSTOMER_ORG__|__[A-Z_]+_REF__|__STATE_BUCKET__' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the matching private GitHub
repositories and publish each prepared `main` branch through your approved Git
process. In the published `platform-ci` repository, allow project repositories
to call its reusable workflows at **Settings → Actions → General → Access → Accessible from
repositories in the organization**.

On paid plans, protect `main` and require independent approval plus successful
plan/check results. GitHub Free private repositories cannot enforce the same
branch and code-owner controls; restrict administration and direct pushes,
record a human PR review, and follow the limitations in
[Shared non-production](shared-nonproduction.md#github-free-security-profile).

Before granting Project Team access, replace every `__PROJECT__-<environment>-approvers`
owner in the generated `CODEOWNERS` with an existing team for that project and
environment. Keep platform ownership for `.github`, `control-plane.json`, and
`environments`; only workload subtrees are delegated. On a paid plan, require
code-owner review and the plan/check status in the `main` branch-protection rule.

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
boundaries. On paid plans, use organization runner groups and grant each group
only to the repositories that need it. OCI runner instances must belong to an OCI
dynamic group with policies for Object Storage state access and only the
compartments/services required by their workload. Azure and Google runners need
equivalent workload-scoped identities. Azure additionally
needs its approved service-principal environment values. Google needs
`GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default
Credentials. Keep credentials outside Git.

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
