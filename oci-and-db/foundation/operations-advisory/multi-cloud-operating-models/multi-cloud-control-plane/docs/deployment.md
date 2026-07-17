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
cp -R components/oe-nonprod-project-template "$STAGE/oe-nonprod-project-template"
cp -R components/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/oe-nonprod-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"

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

find "$STAGE/oe-nonprod-project-template" -type f -exec perl -pi -e \
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__OCI_ORCHESTRATOR_REF__/$ENV{OCI_ORCHESTRATOR_REF}/g; s/__AZURE_ORCHESTRATOR_REF__/$ENV{AZURE_ORCHESTRATOR_REF}/g; s/__GCP_ORCHESTRATOR_REF__/$ENV{GCP_ORCHESTRATOR_REF}/g' {} +

for repository in oe-nonprod-project-template gitops-templates; do
  git -C "$STAGE/$repository" init -b main
  git -C "$STAGE/$repository" add -A
  git -C "$STAGE/$repository" -c user.name='Platform Administrator' \
    -c user.email='platform@invalid' commit -m "Prepare $repository"
done

export PROJECT_TEMPLATE_REF=$(git -C "$STAGE/oe-nonprod-project-template" rev-parse HEAD)
export CATALOGS_REF=$(git -C "$STAGE/gitops-templates" rev-parse HEAD)
cp contracts/deployment-contract.template.json "$STAGE/deployment-contract.json"
find "$STAGE/deployment-contract.json" -type f -exec perl -pi -e \
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g; s/__PROJECT_TEMPLATE_REF__/$ENV{PROJECT_TEMPLATE_REF}/g; s/__CATALOGS_REF__/$ENV{CATALOGS_REF}/g' {} +
```

If the optional UI is required, copy `components/multi-cloud-plane`, replace
`__CUSTOMER_ORG__`, and initialize it in the same way. If the Codex app assistant
is required, copy `plugins/project-gitops`, replace `__CUSTOMER_ORG__`, and
install it through your approved Codex plugin process. Both remain optional.

Verify that no mutable workflow reference or local test content is present:

```bash
rg '@main|__CUSTOMER_ORG__|__PLATFORM_CI_REF__|__.*_ORCHESTRATOR_REF__|__STATE_BUCKET__' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the matching private GitHub
repositories and publish each prepared `main` branch through your approved Git
process. Protect `main`, require independent approval and successful plan/check
results, and allow the project repositories to call Platform CI workflows at
**Organization settings → Actions → General → Access → Accessible from
repositories in the organization**.

Before granting Project Team access, replace every `__PROJECT__-<environment>-approvers`
owner in the generated `CODEOWNERS` with an existing team for that project and
environment. Keep platform ownership for `.github`, `control-plane.json`, and
`environments`; only workload subtrees are delegated. Require code-owner review
and the plan/check status in the `main` branch-protection rule.

## 2. Configure trusted runners

| Setting | Purpose |
|---|---|
| `STATE_NAMESPACE` | OCI Object Storage namespace |
| `STATE_REGION` | Region of the OCI state bucket |
| `OCI_CLI_AUTH=instance_principal` | OCI state and inventory authentication |
| `REGION` | Optional workload-region fallback |

Runners need Terraform 1.12 or later, Python 3.11 or later, and `rg` for
validation. Put runners in organization runner groups and grant each group only
to the repositories that need it. OCI runner instances must belong to an OCI
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
export PROJECT_TOKEN=${PROJECT_REPOSITORY#oe-nonprod-}

jq -e '
  .schema_version == 2 and .repository_layout == "shared-nonprod-v2" and .cloud == "oci" and
  (.source_commit | test("^[0-9a-f]{40}$")) and
  (.source_run | test("^[0-9]+$")) and
  ((.subnets | keys | sort) == ["app","database","infrastructure","web"])
' "$HANDOFF"

cp -R "$STAGE/oe-nonprod-project-template" "$PROJECT_OUTPUT"
rm -rf "$PROJECT_OUTPUT/.git"
test "$PROJECT_REPOSITORY" = "oe-nonprod-$PROJECT_TOKEN"
find "$PROJECT_OUTPUT" -type f -exec perl -pi -e \
  's/__PROJECT__/$ENV{PROJECT_TOKEN}/g' {} +
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

## 4. Confirm the installation

Open one non-production manifest pull request. The installation is working when
the expected plan is tied to the current commit, independent approval is
required, the trusted runner completes the merged change, and state is stored
under the expected project/cloud/environment/region key.

## 5. Verify environment-secret isolation

Run this check before permitting real requests. It verifies that the reusable
workflow receives secrets only from the GitHub Environment declared in its own
job; no caller uses `secrets: inherit`.

1. In `dev`, set `READINESS_MARKER` and a JSON `GITOPS_SECRET_VALUES` mapping
   for one synthetic placeholder in a disposable OCI/dev manifest. Do not set
   that placeholder mapping in `uat`.
2. Open a dev-only pull request and confirm its Terraform plan passes variable
   preparation without printing the secret value.
3. Submit the same placeholder in UAT. Confirm **Prepare variables** fails
   closed with an unresolved-placeholder error. Do not merge either test PR.
4. Confirm the runs select their respective GitHub Environment, runner labels,
   and state-key environment segment. Delete the test branches and secret values.
