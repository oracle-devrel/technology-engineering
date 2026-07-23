# Deployment runbook

This runbook uses standard file, Git, and Perl commands. Run it from a clean
clone of this asset; no installation program or custom deployment service is
required.

## 1. Prepare the foundation repository

```bash
export STAGE=/tmp/oci-landing-zone
export CUSTOMER_ORG=example-customer
export FOUNDATION_REPOSITORY=oci-landing-zone
export ENVIRONMENT=prod
export OCI_REGION=eu-frankfurt-1
: "${NONPROD_TEMPLATE_REF:?Set the approved non-production template commit}"
: "${PROD_TEMPLATE_REF:?Set the approved production template commit}"

mkdir -p "$STAGE"
cp -R components/oci-landing-zone "$STAGE/$FOUNDATION_REPOSITORY"
cp LICENSE "$STAGE/$FOUNDATION_REPOSITORY/LICENSE"
```

Edit the copied repository and replace every example OCID, region-specific
image, CIDR, name, tenancy reference, and SSH key. The bundled configuration is
Frankfurt-based; review every regional value if you deploy elsewhere.

Confirm that the workflows retain the approved OCI orchestrator commit and that
no local test content exists:

```bash
rg 'git -C ORCH checkout 34202e837e9df015ddaaa4fce0ab62bb6e3883de' \
  "$STAGE/$FOUNDATION_REPOSITORY/.github/workflows"
find "$STAGE/$FOUNDATION_REPOSITORY" -type d -name tests
```

The `find` command must return no output.

## 2. Create the local Git repository

```bash
git -C "$STAGE/$FOUNDATION_REPOSITORY" init -b main
git -C "$STAGE/$FOUNDATION_REPOSITORY" add -A
git -C "$STAGE/$FOUNDATION_REPOSITORY" \
  -c user.name='Landing Zone Administrator' \
  -c user.email='landing-zone@invalid' \
  commit -m 'Prepare OCI landing zone'
export FOUNDATION_REF=$(git -C "$STAGE/$FOUNDATION_REPOSITORY" rev-parse HEAD)
cp contracts/deployment-contract.template.json "$STAGE/deployment-contract.json"
find "$STAGE/deployment-contract.json" -type f -exec perl -pi -e \
  's/__CUSTOMER_ORG__/$ENV{CUSTOMER_ORG}/g; s/__FOUNDATION_REPOSITORY__/$ENV{FOUNDATION_REPOSITORY}/g; s/__FOUNDATION_REF__/$ENV{FOUNDATION_REF}/g; s/__NONPROD_TEMPLATE_REF__/$ENV{NONPROD_TEMPLATE_REF}/g; s/__PROD_TEMPLATE_REF__/$ENV{PROD_TEMPLATE_REF}/g; s/__ENVIRONMENT__/$ENV{ENVIRONMENT}/g; s/__OCI_REGION__/$ENV{OCI_REGION}/g' {} +
git -C "$STAGE/$FOUNDATION_REPOSITORY" status --short
```

The final command must return no output. Create a private GitHub repository with
the same name, set the installation gate to `false`, and then publish this
prepared `main` branch through your approved Git process:

```bash
gh repo create "$CUSTOMER_ORG/$FOUNDATION_REPOSITORY" --private
gh variable set FOUNDATION_AUTOMATION_READY --body false \
  --repo "$CUSTOMER_ORG/$FOUNDATION_REPOSITORY"
```

## 3. Configure GitHub and OCI

Protect `main`, require independent approval and a successful Terraform plan,
and restrict workflows to trusted runners. Configure these repository
variables:

| Variable | Purpose |
|---|---|
| `OCI_TF_STATE_BUCKET` | OCI Object Storage state bucket |
| `OCI_TF_STATE_NAMESPACE` | Object Storage namespace |
| `REGION` | State bucket region |
| `OCI_TENANCY_OCID` | Tenancy used to validate the OP02 handoff |
| `FOUNDATION_AUTOMATION_READY` | Set to `false` during installation; set to `true` only after the runner and backend are verified |

### Bootstrap administrator authentication preflight

Before creating the state bucket or the temporary runner, verify the local OCI
administrator profile against the target tenancy. This is a hard gate: do not
continue after an authentication error.

```bash
export OCI_CLI_PROFILE=cloudopstenancy
export TARGET_TENANCY_OCID='<target-tenancy-ocid>'
oci iam tenancy get --profile "$OCI_CLI_PROFILE" \
  --tenancy-id "$TARGET_TENANCY_OCID" \
  --query 'data.{name:name,id:id,home_region_key:"home-region-key"}' \
  --output table
```

The command must return the intended tenancy. A `401 NotAuthenticated` result
means that the API-key profile, its fingerprint, or its private key does not
match the OCI user; repair that administrative access before creating any
resource. The API key is only for out-of-band setup of the state bucket and
temporary runner boundary. Never place its private key or profile in GitHub
Actions secrets, repository variables, Git, or handoff files.

Bootstrap creates the permanent runner, so its first apply needs a temporary
trusted Linux **self-hosted runner** with Git, outbound HTTPS, and an Instance
Principal identity authorized for Bootstrap and state access. The workflow
installs its pinned Terraform release. Use a short-lived GitHub runner
registration token only to register that runner; it does not authenticate to
OCI. Create the state bucket first, review the Bootstrap plan, apply it through
the temporary runner, register the permanent runner, verify Instance Principal
access, and retain the temporary state until recovery is tested.

All foundation jobs are skipped while `FOUNDATION_AUTOMATION_READY` is missing
or not exactly `true`. Set it explicitly to `false` before publishing the
initial `main` branch. This makes the initial repository push safe: it cannot
queue or apply Bootstrap, OP00, OP01, OP02, OP03, or OP04. After repository
variables, the trusted runner, and backend access are verified, set it to
`true`, open one focused pull request per phase, and use the normal plan then
merge gate. Do not set it to `true` merely to make an initial push run.

## 4. Establish the foundation

Deploy OP00, OP01, OP02, optional OP03, and OP04 in order. Use one focused pull
request per phase, review its Terraform plan, obtain approval, merge, and verify
the OCI outcome.

OP02 is complete when `project-onboarding-environment.json` identifies the
expected environment, VCN, and role-based subnets. Commit the reviewed artifact
to the protected path named by `.github/project-onboarding-contract.json` before
allowing OP04 onboarding for that environment. Repeat this for every enabled
`dev`, `test`, `uat`, or `prod` foundation; absent evidence fails closed.

OP04 is complete when the workflow produces `project-foundation-handoff.json`
and `environment_information.md` with the expected project, target repository,
environment-aware handoff path, and provenance.

Provide the JSON handoff to the Control Plane administrator. Do not add
credentials or secrets to either handoff file.
