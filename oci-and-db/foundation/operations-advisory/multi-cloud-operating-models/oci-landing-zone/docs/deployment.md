# Deployment runbook

This runbook publishes a customer foundation repository and deploys the current
official OE blueprint through reviewed GitHub pull requests. It uses no custom
installer or local Terraform apply.

## 1. Confirm the supported release set

The asset currently pins:

| Upstream | Release | Immutable revision |
|---|---|---|
| OCI Landing Zone Operating Entities | `master` (reviewed) | `dab13856ba6701c45baafc163780bb76562c039a` |
| OCI Landing Zones Orchestrator | `release-2.1.4` | `fcf1d7f02c0b4faa1ff55f1776c396452dd51761` |
| Terraform CLI | `1.15.8` | Installed by the workflow action |

The release names provide readable provenance; the SHAs are the executable
supply-chain locks. Do not follow a mutable branch at execution time.

The reviewed OE `master` revision and its official TBAC add-on are the hierarchy
source of truth. Each project has a root plus Application, Database, and
Infrastructure child compartments; schema-3 handoffs contain distinct workload
targets.

## 2. Prepare the foundation repository

From a clean clone of this publication asset:

`NONPROD_TEMPLATE_REPOSITORY`/`NONPROD_TEMPLATE_REVISION` and
`PROD_TEMPLATE_REPOSITORY`/`PROD_TEMPLATE_REVISION` are the approved immutable
GitHub repository-and-commit pairs for the project templates created from the
sibling [Multi-Cloud Control Plane](../../multi-cloud-control-plane/README.md)
asset. They are required later when rendering the Cloud Operator installation
file; never use branch names or discover a repository from its SHA.

```bash
export ASSET_ROOT="$PWD"
export STAGE=/tmp/mccp-installation
export CUSTOMER_ORG=example-customer
export FOUNDATION_REPOSITORY=oci-landing-zone
export OCI_REGION=eu-frankfurt-1
export ENVIRONMENT=dev
: "${NONPROD_TEMPLATE_REPOSITORY:?Set the approved non-production template repository}"
: "${NONPROD_TEMPLATE_REVISION:?Set the approved non-production template commit}"
: "${PROD_TEMPLATE_REPOSITORY:?Set the approved production template repository}"
: "${PROD_TEMPLATE_REVISION:?Set the approved production template commit}"

mkdir -p "$STAGE"
cp -R components/oci-landing-zone "$STAGE/$FOUNDATION_REPOSITORY"
find "$STAGE/$FOUNDATION_REPOSITORY" -type d \
  \( -name tests -o -name __pycache__ \) \
  -prune -exec rm -rf {} +
```

Publication validation tests and Python caches are not needed by the customer
foundation repository and are removed from the staged copy.

Edit `$STAGE/$FOUNDATION_REPOSITORY/config/customer.jsonnet` and replace every
placeholder. Keep `config/projects.json` empty for the initial foundation. The
default source describes one low-cost Hub E topology and one development
project VCN.

Generate the official phase JSON:

```bash
cd "$STAGE/$FOUNDATION_REPOSITORY"
scripts/generate_foundation.sh all
if rg -n '__[A-Z0-9_]+__' \
  config/customer.jsonnet config/projects.json \
  op00_manage_global_landing_zone \
  op01_manage_landing_zone_environment
then
  echo 'Unresolved placeholders remain' >&2
  exit 1
fi
test "$(
  rg -o --no-filename '__[A-Z0-9_]+__' op02_manage_environment |
    sort -u
)" = '__DRG_SPOKES_ROUTE_TABLE_OCID__'
```

The generator needs Git, `jq`, Jsonnet, and ripgrep (`rg`) plus outbound HTTPS
to GitHub. Do not edit `generated/*.json` directly. The single OP02 token shown
above is an internal dependency marker, not customer input: the OP02 workflow
replaces it at runtime with the unique spokes route-table OCID read from
protected OP01 state and fails closed if the dependency is missing or
ambiguous.

Before continuing, record the reviewed deployment decisions alongside the pull
request: customer organization, foundation repository, OCI region, hub and
environment CIDRs, foundation and project state-bucket names, first
environment, first project, and whether MCCP is hosted in this tenancy. These
are customer inputs; do not turn them into hand-edited generated JSON.

## 3. Create the protected GitHub repository

Create the local repository while every operation remains disabled:

```bash
git init -b main
git add -A
git -c user.name='Landing Zone Administrator' \
  -c user.email='landing-zone@invalid' \
  commit -m 'Prepare OCI landing zone'

gh repo create "$CUSTOMER_ORG/$FOUNDATION_REPOSITORY" --private
gh variable set FOUNDATION_AUTOMATION_READY --body false \
  --repo "$CUSTOMER_ORG/$FOUNDATION_REPOSITORY"
```

Publish the prepared `main` branch through the organization's approved Git
process. Protect `main`, require independent approval and successful checks,
disallow force pushes and deletion, and restrict writes to the Cloud Operator
team. Keep the repository private.

GitHub Free cannot enforce branch protection on a private repository. For an
acceptance installation on Free, keep automation disabled by default, restrict
repository administration, record the independent review procedurally, and
enable only the reviewed phase. Paid plans remain the recommended production
profile because these controls are enforced technically.

## 4. Establish the bootstrap boundary

Follow the repository's
[`docs/new-tenancy.md`](../components/oci-landing-zone/docs/new-tenancy.md)
procedure to:

1. Authenticate an approved administrator with a short-lived OCI CLI session.
2. Create separate private Object Storage buckets for foundation and project
   state.
3. Create and register one dedicated private foundation runner.
4. Bind its dynamic group to the exact instance OCID.
5. Configure the repository variables.
6. Run the read-only **OCI Bootstrap readiness** workflow.

The readiness workflow creates nothing and has no Terraform state. The
foundation runner remains the privileged execution identity for OP00–OP04. OP03
creates a separate, narrower MCCP runner for project workload automation.

Required repository variables are:

| Variable | Purpose |
|---|---|
| `FOUNDATION_RUNNER_LABELS` | JSON array selecting only the foundation runner |
| `OCI_TF_STATE_BUCKET` | Private Object Storage foundation-state bucket |
| `PROJECT_STATE_BUCKET` | Separate private Object Storage project-state bucket |
| `OCI_TF_STATE_NAMESPACE` | Object Storage namespace |
| `REGION` | State and deployment region |
| `OCI_TENANCY_OCID` | Exact target tenancy |
| `FOUNDATION_AUTOMATION_READY` | `false` until readiness succeeds |

Set `FOUNDATION_AUTOMATION_READY=true` only after readiness succeeds.

## 5. Deploy the official multi-stack sequence

Use one focused pull request per transition:

1. OP00: set `enabled` to `true`.
2. OP01: set `enabled` to `true` and keep `stage` as `core`.
3. OP03, when MCCP runs in this tenancy: deploy `infrastructure`, create the
   restricted Bastion path, then deploy `identity` with the exact runner
   instance OCID and the separate project-state bucket name. OCI must resolve
   the resulting dynamic group before OP02 can create its runner policies.
4. OP02: enable exactly one environment.
5. Review and commit that OP02 run's environment-blueprint artifact to the
   protected path declared by `.github/project-onboarding-contract.json`.
6. OP01: change `stage` to `pre`.
7. OP01: change `stage` to `final`.
8. OP04: add one project to `config/projects.json` and generate its official
   project declaration.
9. After the project repository exists, register the OP03 runner in an
   organization runner group restricted to the selected project repositories.
   This selected-repository scope is the GitHub Free MVP default. A paid plan
   can add the environment protection and reviewer controls described in the
   hardening guide.

For every pull request, confirm the generated-contract check and Terraform plan
succeed, review replacements/deletions/IAM/routes, obtain independent approval,
merge, and verify the apply before starting the next phase.

State remains isolated:

| Phase | State key |
|---|---|
| OP00 | `op00_manage_global_landing_zone/terraform.tfstate` |
| OP01 | `op01_manage_landing_zone_environment/terraform.tfstate` |
| OP02 | `op02_manage_environment/<environment>/terraform.tfstate` |
| OP03 | `op03_manage_platform_gitops/terraform.tfstate` |
| OP04 | `op04_manage_project/<environment>/<environment>-<project>/terraform.tfstate` |

## 6. Create the Cloud Operator installation file

After both project templates have immutable repository-and-commit pairs, render
the small local file used by the packaged Cloud Operator skill. The schema 3 contract contains
the customer organization, exact current foundation repository,
`project_templates`, enabled environments, and CODEOWNERS identities. Paths and the fixed
`repository-secrets` profile are part of this published MVP implementation.

```bash
export PLATFORM_OWNER='@example-platform-owner'
export DEV_OWNER="$PLATFORM_OWNER"
export TEST_OWNER="$PLATFORM_OWNER"
export UAT_OWNER="$PLATFORM_OWNER"
export PROD_OWNER="$PLATFORM_OWNER"
cd "$ASSET_ROOT"
cp -R plugins/cloud-operator-gitops \
  "$STAGE/cloud-operator-gitops"
cp contracts/cloud-operator-installation.template.json \
  "$STAGE/cloud-operator-gitops/cloud-operator-installation.json"
perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g;
   s/__FOUNDATION_REPOSITORY__/$ENV{FOUNDATION_REPOSITORY}/g;
   s/__NONPROD_TEMPLATE_REPOSITORY__/$ENV{NONPROD_TEMPLATE_REPOSITORY}/g;
   s/__NONPROD_TEMPLATE_REVISION__/$ENV{NONPROD_TEMPLATE_REVISION}/g;
   s/__PROD_TEMPLATE_REPOSITORY__/$ENV{PROD_TEMPLATE_REPOSITORY}/g;
   s/__PROD_TEMPLATE_REVISION__/$ENV{PROD_TEMPLATE_REVISION}/g;
   s/__PLATFORM_OWNER__/$ENV{PLATFORM_OWNER}/g;
   s/__DEV_OWNER__/$ENV{DEV_OWNER}/g;
   s/__TEST_OWNER__/$ENV{TEST_OWNER}/g;
   s/__UAT_OWNER__/$ENV{UAT_OWNER}/g;
   s/__PROD_OWNER__/$ENV{PROD_OWNER}/g;
   s/__ENVIRONMENT__/$ENV{ENVIRONMENT}/g;
   s/__OCI_REGION__/$ENV{OCI_REGION}/g' \
  "$STAGE/cloud-operator-gitops/cloud-operator-installation.json"
jq -e . \
  "$STAGE/cloud-operator-gitops/cloud-operator-installation.json" >/dev/null
if rg -n '__[A-Z0-9_]+__' \
  "$STAGE/cloud-operator-gitops/cloud-operator-installation.json"
then
  echo 'Unresolved Cloud Operator installation placeholders remain' >&2
  exit 1
fi
```

The installation file is not a secret. Keep it with the approved operator
configuration. Install the staged
`$STAGE/cloud-operator-gitops` package, not the unrendered publication
directory. The skill reads `cloud-operator-installation.json` from that package
before it performs any onboarding action.

### Exact project-template repository creation

After the Cloud Operator has shown the separate repository-creation preview and
received confirmation, derive `TEMPLATE_REPOSITORY` and `TEMPLATE_REVISION`
from the selected `project_templates` object. Create an empty private target,
push that exact source commit as `main`, and prove both commit and tree identity
before rendering the handoff branch:

```bash
SOURCE_DIR="$(mktemp -d)"
TARGET_DIR="$(mktemp -d)"
trap 'rm -rf "$SOURCE_DIR" "$TARGET_DIR"' EXIT

gh repo create "$TARGET_REPOSITORY" --private --disable-wiki
git clone --no-checkout "https://github.com/$TEMPLATE_REPOSITORY.git" "$SOURCE_DIR"
git -C "$SOURCE_DIR" checkout --detach "$TEMPLATE_REVISION"
git -C "$SOURCE_DIR" remote add target "https://github.com/$TARGET_REPOSITORY.git"
git -C "$SOURCE_DIR" push target "$TEMPLATE_REVISION:refs/heads/main"
git clone "https://github.com/$TARGET_REPOSITORY.git" "$TARGET_DIR"
test "$(git -C "$SOURCE_DIR" rev-parse "$TEMPLATE_REVISION^{commit}")" = "$(git -C "$TARGET_DIR" rev-parse "origin/main^{commit}")"
test "$(git -C "$SOURCE_DIR" rev-parse "$TEMPLATE_REVISION^{tree}")" = "$(git -C "$TARGET_DIR" rev-parse "origin/main^{tree}")"
```

Fail closed if either check differs. Never create a repository from a default
branch, a GitHub template action, a redirect, or a SHA-only repository search.

### Breaking installation update

Schema 3 deliberately rejects every earlier Cloud Operator installation. Do not
retain a compatibility path or infer a template repository from an old SHA.
Render a new staged package with explicit repository-and-commit pairs, use
`jq -e` and the placeholder scan above to verify it, then install that package
through the approved process.

### Project-repository bootstrap on GitHub Free

GitHub Free private repositories cannot access organization secrets or
variables. This MVP therefore uses the fixed `repository-secrets` profile and
requires a deliberate manual bootstrap in each handed-off project repository.
For every enabled environment, a repository administrator must configure the
selected `GITOPS_SECRET_VALUES_<ENVIRONMENT>` JSON secret, the matching
`CONTROL_PLANE_READY_<ENVIRONMENT>=true` variable. The organization
administrator must configure private `platform-ci` Actions access for
organization repositories and verify it with `gh api
repos/OWNER/platform-ci/actions/permissions/access`; the expected access level
is `organization`. GitHub then downloads the directly referenced private
composite action at its immutable SHA, never a branch. Never put secret values in
a manifest, handoff, installation JSON, terminal history, or chat. Set
`PROJECT_AUTOMATION_READY=true` only after the handoff, CODEOWNERS, runner
routing, native Actions access, and all enabled-environment secret and
readiness pairs have been verified. The project template runbook contains the
manual commands and ordering.

Every owner must be an existing `@user` or `@organization/team` with write
access to the project repository. It is valid to use the same platform owner
for all environments during an isolated acceptance test, but production
installations should use separate environment reviewer teams.

### Paid-plan profile

A paid-plan profile adds branch protection, CODEOWNERS review, GitHub
Environments, and required reviewers after validating those controls in the
customer organization. Native private Actions access and the immutable
workflow SHA are used in both profiles; workload secret bundles remain
repository-and-environment scoped for least privilege.

## 7. Onboard and hand off a project

Add one lowercase project name to the selected array in
`config/projects.json`, then generate only that OP04 declaration:

```bash
scripts/generate_foundation.sh op04:dev-payments
```

A new-project pull request is a two-file OP04 request. It must contain exactly
`config/projects.json` and the generated OP04 `iam.json`. For a later adapter or
policy reconciliation, leave `config/projects.json` unchanged and submit only
the regenerated `iam.json`. The protected workflow regenerates it from the
default-branch adapter and the pinned reviewed OE `master` revision,
validates the submitted files, plans one separate OP04 state, applies after
merge, and publishes:

- `project-foundation-handoff.json`
- `environment_information.md`

OP02 creates the fixed MVP runner policies once per environment. They cover
the `PROJECTS` subtree, shared `NETWORK`, and shared `SECURITY` for Compute,
ADB, and project NSGs. OP04 creates no runner policy; it contains only the
official TBAC project structure.
Keep these generated scopes unchanged.

The schema-3 machine handoff contains one project-root OCID and three distinct
official TBAC child-compartment OCIDs: Application, Database, and
Infrastructure. Compute is restricted to Application, ADB and ADB lifecycle to
Database, and NSGs to Infrastructure. Network subnet fields remain
role-specific.

The Cloud Operator skill validates the artifacts, creates or reuses the
contract-selected private project repository, and opens the handoff pull
request. For a new repository, that same reviewed request must replace
`nonprod-__PROJECT__` or `prod-__PROJECT__`, select the contract security
profile, render an active `.github/CODEOWNERS`, remove
`.github/CODEOWNERS.template`, and publish the selected environment handoff.
Validation rejects any unresolved placeholder or additional path. The skill
never merges, calls OCI directly, or runs Terraform.

### Required GitHub Free bootstrap before Project GitOps

After the handoff pull request has merged, the project repository is not yet
ready for a workload request. GitHub Free private repositories cannot use
organization secrets or variables, so a repository administrator must complete
the manual project bootstrap in the [MCCP OCI project onboarding
runbook](../../multi-cloud-control-plane/docs/deployment.md#3-onboard-an-oci-project).
For a non-production project, follow the focused
[shared non-production checklist](../../multi-cloud-control-plane/docs/shared-nonproduction.md)
for only the environments that were handed off. It requires verified
`platform-ci` Actions access at organization scope, the selected
`GITOPS_SECRET_VALUES_<ENVIRONMENT>` bundle, and
`CONTROL_PLANE_READY_<ENVIRONMENT>=true`; set
`PROJECT_AUTOMATION_READY=true` last.

Do not submit a Project GitOps workload request until this checklist has been
completed and the repository-secret end-to-end verification has passed. On a
paid plan, use the separately documented hardening profile; workload secrets
remain scoped to repository and environment.
