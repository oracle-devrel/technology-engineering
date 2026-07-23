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

## 4. Establish the bootstrap boundary

Follow the repository's
[`docs/new-tenancy.md`](../components/oci-landing-zone/docs/new-tenancy.md)
procedure to:

1. Authenticate an approved administrator with a short-lived OCI CLI session.
2. Create the private Object Storage state bucket.
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
| `OCI_TF_STATE_BUCKET` | Private Object Storage state bucket |
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
7. OP03, when MCPP runs in this tenancy: deploy `infrastructure`, register the
   new runner, then deploy `identity` with its exact instance OCID and state
   bucket name.
8. OP04: add one project to `config/projects.json` and generate its official
   project declaration.

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
cd '<publication asset>/oci-landing-zone'
cp contracts/deployment-contract.template.json \
  "$STAGE/deployment-contract.json"
perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g;
   s/__FOUNDATION_REPOSITORY__/$ENV{FOUNDATION_REPOSITORY}/g;
   s/__FOUNDATION_REF__/$ENV{FOUNDATION_REF}/g;
   s/__NONPROD_TEMPLATE_REF__/$ENV{NONPROD_TEMPLATE_REF}/g;
   s/__PROD_TEMPLATE_REF__/$ENV{PROD_TEMPLATE_REF}/g;
   s/__ENVIRONMENT__/$ENV{ENVIRONMENT}/g;
   s/__OCI_REGION__/$ENV{OCI_REGION}/g' \
  "$STAGE/deployment-contract.json"
jq -e . "$STAGE/deployment-contract.json" >/dev/null
```

The contract is installation policy, not a secret. Keep it with the approved
operator configuration.

## 7. Onboard and hand off a project

Add one lowercase project name to the selected array in
`config/projects.json`, then generate only that OP04 declaration:

```bash
scripts/generate_foundation.sh op04:dev-payments
```

The pull request must contain exactly `config/projects.json` and the generated
OP04 `iam.json`. The workflow regenerates the file from protected OE `v3.1.0`,
plans one separate OP04 state, applies after merge, and publishes:

- `project-foundation-handoff.json`
- `environment_information.md`

The three workload-role compartment fields in the machine handoff intentionally
contain the same official OE project compartment OCID. Network subnet fields
remain role-specific.

The Cloud Operator skill validates the artifacts, creates or reuses the
contract-selected private project repository, and opens the handoff pull
request. It never merges, calls OCI directly, or runs Terraform.
