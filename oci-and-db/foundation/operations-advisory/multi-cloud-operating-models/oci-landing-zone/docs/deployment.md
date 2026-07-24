# Deployment runbook

This runbook publishes a customer foundation repository and deploys the current
official OE blueprint through reviewed GitHub pull requests. It uses no custom
installer or local Terraform apply.

## 1. Confirm the supported release set

The asset currently pins:

| Upstream | Release | Immutable revision |
|---|---|---|
| OCI Landing Zone Operating Entities | `v3.1.0` | `172809932c53467ab20ec6d1b44290a487211b36` |
| OCI Landing Zones Orchestrator | `release-2.1.4` | `fcf1d7f02c0b4faa1ff55f1776c396452dd51761` |
| OCI Exadata modules | `release-1.2.0` | `55eeee14808f864e450db550530d760f9e0b0105` |
| Terraform CLI | `1.15.8` | Installed by the workflow action |

These were the newest stable official OE tag and release branches verified on
July 23, 2026.

The release names provide readable provenance; the SHAs are the executable
supply-chain locks. Upgrade each release name and SHA together, regenerate all
phases, and rerun the contract tests. Do not follow a mutable branch at
execution time.

The Orchestrator declares Terraform `>= 1.5.0` because that is its OCI Resource
Manager compatibility floor. This installation executes with Terraform CLI
`1.15.8`, pinned independently in every workflow. The upstream floor therefore
does not limit the newer CLI used by this GitHub Actions path.

OE `v3.1.0` is the hierarchy source of truth. It creates one compartment per
project. This asset does not recreate the application/database/infrastructure
child compartments used by older OE `v2.x` examples.

## 2. Prepare the foundation repository

From a clean clone of this publication asset:

```bash
export STAGE=/tmp/mccp-installation
export CUSTOMER_ORG=example-customer
export FOUNDATION_REPOSITORY=oci-landing-zone
export OCI_REGION=eu-frankfurt-1
export ENVIRONMENT=dev
: "${NONPROD_TEMPLATE_REF:?Set the approved non-production template commit}"
: "${PROD_TEMPLATE_REF:?Set the approved production template commit}"

mkdir -p "$STAGE"
cp -R components/oci-landing-zone "$STAGE/$FOUNDATION_REPOSITORY"
cp LICENSE "$STAGE/$FOUNDATION_REPOSITORY/LICENSE"
find "$STAGE/$FOUNDATION_REPOSITORY" -type d \
  \( -name tests -o -name __pycache__ \) -prune -exec rm -rf {} +
```

Tests remain in the publication source and are not copied to the customer
foundation repository.

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

The generator needs Git, `jq`, and Jsonnet plus outbound HTTPS to GitHub. Do not
edit `generated/*.json` directly. The single OP02 token shown above is an
internal dependency marker, not customer input: the OP02 workflow replaces it
at runtime with the unique spokes route-table OCID read from protected OP01
state and fails closed if the dependency is missing or ambiguous.

## 3. Create the protected GitHub repository

Create the local repository while every operation remains disabled:

```bash
git init -b main
git add -A
git -c user.name='Landing Zone Administrator' \
  -c user.email='landing-zone@invalid' \
  commit -m 'Prepare OCI landing zone'
export FOUNDATION_REF=$(git rev-parse HEAD)

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
creates a separate, narrower MCPP runner for project workload automation.

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
3. OP02: enable exactly one environment.
4. Review and commit that OP02 run's environment-blueprint artifact to the
   protected path declared by `.github/project-onboarding-contract.json`.
5. OP01: change `stage` to `pre`.
6. OP01: change `stage` to `final`.
7. OP03, when MCPP runs in this tenancy: deploy `infrastructure`, create the
   restricted Bastion path, then deploy `identity` with the exact runner
   instance OCID and the separate project-state bucket name. Validate Instance
   Principal before registration.
8. OP04: add one project to `config/projects.json` and generate its official
   project declaration.
9. On paid GitHub plans, register the OP03 runner in a
   repository-restricted organization runner group. On GitHub Free, wait until
   the project repository exists and register the runner to that repository
   only.

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

## 6. Create the deployment contract

After the foundation and both project templates have immutable commits, render
the local contract used by the packaged Cloud Operator skill:

```bash
export FOUNDATION_REF=$(gh api \
  "repos/$CUSTOMER_ORG/$FOUNDATION_REPOSITORY/commits/main" \
  --jq .sha)
export PROJECT_STATE_BUCKET=example-project-state
export NONPROD_SECURITY_PROFILE=repository-secrets
export PROD_SECURITY_PROFILE=repository-secrets
export PLATFORM_OWNER='@example-platform-owner'
export DEV_OWNER="$PLATFORM_OWNER"
export TEST_OWNER="$PLATFORM_OWNER"
export UAT_OWNER="$PLATFORM_OWNER"
export PROD_OWNER="$PLATFORM_OWNER"
cd '<publication asset>/oci-landing-zone'
cp -R plugins/cloud-operator-gitops \
  "$STAGE/cloud-operator-gitops"
cp contracts/deployment-contract.template.json \
  "$STAGE/cloud-operator-gitops/deployment-contract.json"
perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g;
   s/__FOUNDATION_REPOSITORY__/$ENV{FOUNDATION_REPOSITORY}/g;
   s/__FOUNDATION_REF__/$ENV{FOUNDATION_REF}/g;
   s/__NONPROD_TEMPLATE_REF__/$ENV{NONPROD_TEMPLATE_REF}/g;
   s/__PROD_TEMPLATE_REF__/$ENV{PROD_TEMPLATE_REF}/g;
   s/__NONPROD_SECURITY_PROFILE__/$ENV{NONPROD_SECURITY_PROFILE}/g;
   s/__PROD_SECURITY_PROFILE__/$ENV{PROD_SECURITY_PROFILE}/g;
   s/__PLATFORM_OWNER__/$ENV{PLATFORM_OWNER}/g;
   s/__DEV_OWNER__/$ENV{DEV_OWNER}/g;
   s/__TEST_OWNER__/$ENV{TEST_OWNER}/g;
   s/__UAT_OWNER__/$ENV{UAT_OWNER}/g;
   s/__PROD_OWNER__/$ENV{PROD_OWNER}/g;
   s/__PROJECT_STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g;
   s/__ENVIRONMENT__/$ENV{ENVIRONMENT}/g;
   s/__OCI_REGION__/$ENV{OCI_REGION}/g' \
  "$STAGE/cloud-operator-gitops/deployment-contract.json"
jq -e . \
  "$STAGE/cloud-operator-gitops/deployment-contract.json" >/dev/null
if rg -n '__[A-Z0-9_]+__' \
  "$STAGE/cloud-operator-gitops/deployment-contract.json"
then
  echo 'Unresolved deployment-contract placeholders remain' >&2
  exit 1
fi
```

The contract is installation policy, not a secret. Keep it with the approved
operator configuration. Install the staged
`$STAGE/cloud-operator-gitops` package, not the unrendered publication
directory. The skill reads `deployment-contract.json` from that package before
it performs any onboarding action.

Use `repository-secrets` for GitHub Free. Use `github-environments` for the
recommended paid-plan profile. Every owner must be an existing `@user` or
`@organization/team` with write access to the project repository. It is valid
to use the same platform owner for all environments during an isolated
acceptance test, but production installations should use separate environment
reviewer teams.

## 7. Onboard and hand off a project

Add one lowercase project name to the selected array in
`config/projects.json`, then generate only that OP04 declaration:

```bash
scripts/generate_foundation.sh op04:dev-payments
```

A new-project pull request must contain exactly `config/projects.json` and the
generated OP04 `iam.json`. A later adapter or policy reconciliation for an
existing registered project must contain exactly that project's generated
`iam.json`; the protected workflow rejects any project-list change in this
maintenance mode. In both cases the workflow regenerates the file from the
protected default-branch adapter and pinned OE `v3.1.0`, plans one separate
OP04 state, applies after merge, and publishes:

- `project-foundation-handoff.json`
- `environment_information.md`

The three workload-role compartment fields in the machine handoff intentionally
contain the same official OE project compartment OCID. Network subnet fields
remain role-specific.

The Cloud Operator skill validates the artifacts, creates or reuses the
contract-selected private project repository, and opens the handoff pull
request. For a new repository, that same reviewed request must replace
`nonprod-__PROJECT__` or `prod-__PROJECT__`, select the contract security
profile, render an active `.github/CODEOWNERS`, remove
`.github/CODEOWNERS.template`, and publish the selected environment handoff.
Validation rejects any unresolved placeholder or additional path. The skill
never merges, calls OCI directly, or runs Terraform.
