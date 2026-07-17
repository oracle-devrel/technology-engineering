# Deployment runbook

This runbook uses standard file, Git, and Perl commands. Run it from a clean
clone of this asset; no installation program or custom deployment service is
required.

## 1. Prepare the foundation repository

```bash
export STAGE=/tmp/oci-landing-zone
export FOUNDATION_REPOSITORY=oci-landing-zone
export ENVIRONMENT=prod
export OCI_REGION=eu-frankfurt-1

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
  's/__FOUNDATION_REPOSITORY__/$ENV{FOUNDATION_REPOSITORY}/g; s/__FOUNDATION_REF__/$ENV{FOUNDATION_REF}/g; s/__ENVIRONMENT__/$ENV{ENVIRONMENT}/g; s/__OCI_REGION__/$ENV{OCI_REGION}/g' {} +
git -C "$STAGE/$FOUNDATION_REPOSITORY" status --short
```

The final command must return no output. Create a private GitHub repository with
the same name and publish this prepared `main` branch through your approved Git
process.

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

Bootstrap creates the permanent runner, so its first apply needs a temporary
trusted Linux execution host with Terraform 1.12.1 and an approved OCI
administrative identity. Create the state bucket first, review the Bootstrap
plan, apply it, register the permanent runner, verify Instance Principal access,
and retain the temporary state until recovery is tested.

## 4. Establish the foundation

Deploy OP00, OP01, OP02, optional OP03, and OP04 in order. Use one focused pull
request per phase, review its Terraform plan, obtain approval, merge, and verify
the OCI outcome.

OP02 is complete when `project-onboarding-environment.json` identifies the
expected environment, VCN, and role-based subnets. OP04 is complete when the
workflow produces `project-foundation-handoff.json` and
`enviroment_information.md` with the expected project and provenance.

Provide the JSON handoff to the Control Plane administrator. Do not add
credentials or secrets to either handoff file.
