# New tenancy setup

This procedure establishes the smallest trusted boundary needed to deploy the
official OCI Landing Zone Operating Entities blueprint. Bootstrap readiness is
read-only; Terraform starts at OP00.

## 1. Verify administrator access

Use an approved OCI administrator identity only for the initial runner, state
bucket, dynamic group, and policy. A short-lived OCI CLI security-token session
keeps that credential out of GitHub:

```bash
export OCI_REGION=eu-frankfurt-1
export TARGET_TENANCY_OCID='<target-tenancy-ocid>'
oci session authenticate --profile-name lz-bootstrap-session \
  --region "$OCI_REGION"
oci session validate --profile lz-bootstrap-session --auth security_token
oci iam tenancy get --profile lz-bootstrap-session --auth security_token \
  --tenancy-id "$TARGET_TENANCY_OCID" \
  --query 'data.{name:name,id:id,home_region_key:"home-region-key"}' \
  --output table
```

Stop if the returned tenancy is not the intended target or authentication
fails. Never copy the session credential into GitHub, a runner configuration,
Terraform, or a handoff.

## 2. Create the private state and runner boundary

Create one private Object Storage bucket:

```bash
export STATE_BUCKET=mccp-oci-lz-tfstate
export OCI_NAMESPACE=$(oci os ns get --profile lz-bootstrap-session \
  --auth security_token --query data --raw-output)

oci os bucket create --profile lz-bootstrap-session --auth security_token \
  --compartment-id "$TARGET_TENANCY_OCID" \
  --namespace-name "$OCI_NAMESPACE" \
  --name "$STATE_BUCKET" \
  --public-access-type NoPublicAccess \
  --region "$OCI_REGION"
```

Create a dedicated Linux ARM64 foundation runner using your standard OCI
Compute procedure. It is an unavoidable trust-bootstrap resource and is not
managed by the Landing Zone it deploys. Require:

- No public IP address.
- A private subnet with outbound HTTPS through a NAT Gateway and access to OCI
  services through a Service Gateway.
- OCI Bastion or another approved private administrator path.
- A dedicated operating-system account and GitHub runner service.
- Git, `jq`, Jsonnet, OCI CLI, `rg`, Python 3, `curl`, `tar`, and `unzip`.
- Repository-scoped GitHub registration with the `mccp-foundation` label.

In the private foundation repository, use **Settings → Actions → Runners →
New self-hosted runner** and follow GitHub's generated Linux ARM64 commands.
The registration token is short-lived and authenticates only runner
registration; it is not an OCI credential. Configure the runner as a service.

Bind the runner identity to its exact instance OCID:

```bash
export FOUNDATION_RUNNER_INSTANCE_OCID='<foundation-runner-instance-ocid>'
export FOUNDATION_DYNAMIC_GROUP=dg-mccp-foundation-runner
export FOUNDATION_POLICY=pcy-mccp-foundation-runner

oci iam dynamic-group create \
  --profile lz-bootstrap-session --auth security_token \
  --name "$FOUNDATION_DYNAMIC_GROUP" \
  --description 'Dedicated MCCP foundation runner' \
  --matching-rule \
    "ALL {instance.id = '$FOUNDATION_RUNNER_INSTANCE_OCID'}"

oci iam policy create \
  --profile lz-bootstrap-session --auth security_token \
  --compartment-id "$TARGET_TENANCY_OCID" \
  --name "$FOUNDATION_POLICY" \
  --description 'MCCP foundation automation' \
  --statements \
    "[\"allow dynamic-group $FOUNDATION_DYNAMIC_GROUP to manage all-resources in tenancy\"]"
```

The foundation policy is intentionally privileged because OP00 and OP01 manage
tenancy-wide IAM and shared foundation resources. Exact-instance matching,
private networking, repository isolation, branch protection, runner patching,
and audit monitoring are mandatory controls. Project workloads use the
separate, narrower OP03 runner identity.

## 3. Configure and generate the official blueprint

Edit `config/customer.jsonnet` and replace every customer token. Keep
`config/projects.json` empty during foundation creation. For the initial
low-cost topology, use Hub E and one development project VCN.

Generate the committed phase configuration from the pinned OE release:

```bash
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

Only the exact OP02 dependency marker tested above may remain. It is not a
customer value: the OP02 workflow reads the unique spokes route-table OCID from
protected OP01 state, replaces the marker in a temporary copy, and fails closed
before Terraform if it cannot resolve it. Do not edit generated files manually.
The protected workflow regenerates changed phases from OE `v3.1.0` and rejects
drift.

## 4. Configure GitHub and run readiness

Set these repository variables:

```bash
gh variable set FOUNDATION_RUNNER_LABELS \
  --body '["self-hosted","linux","arm64","mccp-foundation"]' \
  --repo '<organization>/<foundation-repository>'
gh variable set OCI_TF_STATE_BUCKET --body "$STATE_BUCKET" \
  --repo '<organization>/<foundation-repository>'
gh variable set OCI_TF_STATE_NAMESPACE --body "$OCI_NAMESPACE" \
  --repo '<organization>/<foundation-repository>'
gh variable set REGION --body "$OCI_REGION" \
  --repo '<organization>/<foundation-repository>'
gh variable set OCI_TENANCY_OCID --body "$TARGET_TENANCY_OCID" \
  --repo '<organization>/<foundation-repository>'
gh variable set FOUNDATION_AUTOMATION_READY --body false \
  --repo '<organization>/<foundation-repository>'
```

Protect `main`, require review and successful checks, and keep the repository
private. Run **OCI Bootstrap readiness** manually. It must verify the runner
tools, Instance Principal tenancy identity, private bucket, and read-only object
access. Only after it succeeds:

```bash
gh variable set FOUNDATION_AUTOMATION_READY --body true \
  --repo '<organization>/<foundation-repository>'
```

## 5. Deploy the multi-stack foundation

Use one focused pull request per step. Review the exact Terraform plan, obtain
approval, merge, and verify the apply before continuing:

1. Set OP00 `operation.json` to `"enabled": true`.
2. Set OP01 to `"enabled": true, "stage": "core"`.
3. Set the selected OP02 environment to `"enabled": true`.
4. Download the successful OP02
   `project-onboarding-<environment>-<commit>` artifact, review it, and commit
   it to the protected blueprint path in
   `.github/project-onboarding-contract.json`.
5. Move OP01 to `"stage": "pre"`.
6. Move OP01 to `"stage": "final"`.
7. If MCPP execution is hosted in this tenancy, deploy OP03 first with
   `"stage": "infrastructure"`, register its new private runner, then replace
   the OP03 identity placeholders and move to `"stage": "identity"`.
8. Add one project name to `config/projects.json`, generate
   `op04:<environment>-<project>`, and submit the two-file OP04 request.

OP04 uses the official OE `v3.1.0` project model: one project compartment,
one administrator group, and the OE policies. The MCPP runner policies are the
only project-IAM extension. The resulting handoff repeats the same project
compartment OCID in its three workload-role fields for compatibility.

For a later environment, first add it to `customer.jsonnet` without activating
it, generate and deploy its OP02 stack, commit its protected blueprint, then add
it to `activated_environments` and run the OP01 `pre` and `final` updates.

## 6. Hand off the project

After OP04 applies, validate both artifacts:

- `project-foundation-handoff.json` for machine processing.
- `environment_information.md` for people.

The Cloud Operator flow creates or reuses the contract-selected private project
repository and publishes the exact environment handoff through a reviewed pull
request. It never merges that pull request, runs Terraform locally, or places
credentials in the handoff.

If any apply fails, stop and compare OCI with the owning Terraform state before
submitting a corrective pull request. Never edit state manually or bypass the
review gate.
