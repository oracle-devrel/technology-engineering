# Deployment runbook

This runbook uses standard file, Git, `jq`, and Perl commands. Run it from a
clean clone of this asset; no custom deployment program is required.

## 1. Prepare the shared repositories

```bash
export STAGE=/tmp/control-plane
export CUSTOMER_ORG=example-enterprise
export STATE_BUCKET=example-control-plane-state

mkdir -p "$STAGE"
cp -R components/platform-ci "$STAGE/platform-ci"
cp -R components/oe-env-project-template "$STAGE/oe-env-project-template"
cp -R components/gitops-templates "$STAGE/gitops-templates"
cp LICENSE "$STAGE/platform-ci/LICENSE"
cp LICENSE "$STAGE/oe-env-project-template/LICENSE"
cp LICENSE "$STAGE/gitops-templates/LICENSE"

find "$STAGE" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/gitops-state-bucket/$ENV{STATE_BUCKET}/g' {} +
```

Create the Platform CI commit first because project workflows pin that exact
commit:

```bash
git -C "$STAGE/platform-ci" init -b main
git -C "$STAGE/platform-ci" add -A
git -C "$STAGE/platform-ci" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare Platform CI'
export PLATFORM_CI_REF=$(git -C "$STAGE/platform-ci" rev-parse HEAD)

find "$STAGE/oe-env-project-template" -type f -exec perl -pi -e \
  's/__PLATFORM_CI_REF__/$ENV{PLATFORM_CI_REF}/g' {} +

for repository in oe-env-project-template gitops-templates; do
  git -C "$STAGE/$repository" init -b main
  git -C "$STAGE/$repository" add -A
  git -C "$STAGE/$repository" -c user.name='Platform Administrator' \
    -c user.email='platform@invalid' commit -m "Prepare $repository"
done

export PROJECT_TEMPLATE_REF=$(git -C "$STAGE/oe-env-project-template" rev-parse HEAD)
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
rg '@main|__CUSTOMER_ORG__|__PLATFORM_CI_REF__|gitops-state-bucket' "$STAGE"
find "$STAGE" -type d -name tests
```

Both commands must return no output. Create the matching private GitHub
repositories and publish each prepared `main` branch through your approved Git
process. Protect `main`, require independent approval and successful plan/check
results, and allow the project repositories to call Platform CI workflows.

## 2. Configure trusted runners

| Setting | Purpose |
|---|---|
| `STATE_NAMESPACE` | OCI Object Storage namespace |
| `STATE_REGION` | Region of the OCI state bucket |
| `OCI_CLI_AUTH=instance_principal` | OCI state and inventory authentication |
| `REGION` | Optional workload-region fallback |

Runners need Terraform 1.12 or later and Python 3.11 or later. Azure additionally
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

jq -e '
  .schema_version == 1 and .cloud == "oci" and
  (.source_commit | test("^[0-9a-f]{40}$")) and
  (.source_run | test("^[0-9]+$")) and
  ((.subnets | keys | sort) == ["app","database","infrastructure","web"])
' "$HANDOFF"

cp -R "$STAGE/oe-env-project-template" "$PROJECT_OUTPUT"
rm -rf "$PROJECT_OUTPUT/.git"
{
  printf '# Project Environment Information\n\n```json\n'
  jq --sort-keys . "$HANDOFF"
  printf '\n```\n'
} > "$PROJECT_OUTPUT/enviroment_information.md"

git -C "$PROJECT_OUTPUT" init -b main
git -C "$PROJECT_OUTPUT" add -A
git -C "$PROJECT_OUTPUT" -c user.name='Platform Administrator' \
  -c user.email='platform@invalid' commit -m 'Prepare project repository'
git -C "$PROJECT_OUTPUT" status --short
```

The final command must return no output. Confirm the project, environment,
region, compartments, VCN, subnets, workflow run, commit, and state keys against
the approved onboarding record. Then create the private project repository,
apply the same protections, and grant the Project Team access.

## 4. Confirm the installation

Open one non-production manifest pull request. The installation is working when
the expected plan is tied to the current commit, independent approval is
required, the trusted runner completes the merged change, and state is stored
under the expected project/cloud/region key.
