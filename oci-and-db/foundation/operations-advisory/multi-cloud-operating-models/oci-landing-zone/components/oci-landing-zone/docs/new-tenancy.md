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

Use the browser flow above to create a session or replace an expired session.
Do not add `--no-browser` when the existing profile contains only an expired
session token. Oracle's no-browser flow must itself authenticate with an API
key or a still-valid session token; otherwise token generation fails with
`401 NotAuthenticated`. See
[Token-based Authentication for the CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm).

Stop if the returned tenancy is not the intended target or authentication
fails. Never copy the session credential into GitHub, a runner configuration,
Terraform, or a handoff.

## 2. Create the private state and runner boundary

Choose non-overlapping bootstrap values and create one private, versioned Object
Storage bucket:

```bash
export STATE_BUCKET=mccp-oci-lz-tfstate
export FOUNDATION_REPOSITORY='<organization>/<foundation-repository>'
export BOOTSTRAP_VCN_CIDR=10.255.0.0/24
export BOOTSTRAP_SUBNET_CIDR=10.255.0.0/28
export SSH_PUBLIC_KEY_FILE="$HOME/.ssh/id_ed25519.pub"
export OCI_NAMESPACE=$(oci os ns get --profile lz-bootstrap-session \
  --auth security_token --query data --raw-output)

oci os bucket create --profile lz-bootstrap-session --auth security_token \
  --compartment-id "$TARGET_TENANCY_OCID" \
  --namespace-name "$OCI_NAMESPACE" \
  --name "$STATE_BUCKET" \
  --public-access-type NoPublicAccess \
  --versioning Enabled \
  --region "$OCI_REGION"

oci os bucket get --profile lz-bootstrap-session --auth security_token \
  --namespace-name "$OCI_NAMESPACE" --name "$STATE_BUCKET" \
  --region "$OCI_REGION" \
  --query 'data.{access:"public-access-type",versioning:versioning}'
```

Both values must be `NoPublicAccess` and `Enabled`. Never reuse another
application's state bucket.

Create a dedicated bootstrap VCN. It remains outside Landing Zone Terraform and
must not be attached to the Landing Zone DRG:

```bash
export BOOTSTRAP_VCN_OCID=$(
  oci network vcn create \
    --profile lz-bootstrap-session --auth security_token \
    --compartment-id "$TARGET_TENANCY_OCID" \
    --cidr-block "$BOOTSTRAP_VCN_CIDR" \
    --display-name vcn-mccp-foundation-bootstrap \
    --dns-label mccpboot --is-ipv6-enabled false \
    --query data.id --raw-output
)

export BOOTSTRAP_ROUTE_TABLE_OCID=$(
  oci network vcn get \
    --profile lz-bootstrap-session --auth security_token \
    --vcn-id "$BOOTSTRAP_VCN_OCID" \
    --query 'data."default-route-table-id"' --raw-output
)
export BOOTSTRAP_SECURITY_LIST_OCID=$(
  oci network vcn get \
    --profile lz-bootstrap-session --auth security_token \
    --vcn-id "$BOOTSTRAP_VCN_OCID" \
    --query 'data."default-security-list-id"' --raw-output
)

export NAT_GATEWAY_OCID=$(
  oci network nat-gateway create \
    --profile lz-bootstrap-session --auth security_token \
    --compartment-id "$TARGET_TENANCY_OCID" \
    --vcn-id "$BOOTSTRAP_VCN_OCID" \
    --display-name nat-mccp-foundation-bootstrap \
    --query data.id --raw-output
)

services="$(
  oci network service list \
    --profile lz-bootstrap-session --auth security_token --all
)"
test "$(jq '[.data[] | select(.name | startswith("All "))] | length' \
  <<< "$services")" -eq 1
export OCI_SERVICES_OCID=$(
  jq -er '.data[] | select(.name | startswith("All ")) | .id' \
    <<< "$services"
)
export OCI_SERVICES_CIDR=$(
  jq -er '.data[] | select(.name | startswith("All ")) | ."cidr-block"' \
    <<< "$services"
)

export SERVICE_GATEWAY_OCID=$(
  oci network service-gateway create \
    --profile lz-bootstrap-session --auth security_token \
    --compartment-id "$TARGET_TENANCY_OCID" \
    --vcn-id "$BOOTSTRAP_VCN_OCID" \
    --display-name sgw-mccp-foundation-bootstrap \
    --services "[{\"serviceId\":\"$OCI_SERVICES_OCID\"}]" \
    --query data.id --raw-output
)

route_rules="$(
  jq -cn \
    --arg nat "$NAT_GATEWAY_OCID" \
    --arg service_gateway "$SERVICE_GATEWAY_OCID" \
    --arg service_cidr "$OCI_SERVICES_CIDR" '
    [
      {
        destination: "0.0.0.0/0",
        destinationType: "CIDR_BLOCK",
        networkEntityId: $nat,
        description: "Outbound HTTPS through NAT"
      },
      {
        destination: $service_cidr,
        destinationType: "SERVICE_CIDR_BLOCK",
        networkEntityId: $service_gateway,
        description: "Private OCI service access"
      }
    ]'
)"
oci network route-table update \
  --profile lz-bootstrap-session --auth security_token \
  --rt-id "$BOOTSTRAP_ROUTE_TABLE_OCID" \
  --route-rules "$route_rules" --force

oci network security-list update \
  --profile lz-bootstrap-session --auth security_token \
  --security-list-id "$BOOTSTRAP_SECURITY_LIST_OCID" \
  --ingress-security-rules \
    "[{\"source\":\"$BOOTSTRAP_VCN_CIDR\",\"sourceType\":\"CIDR_BLOCK\",\"protocol\":\"6\",\"isStateless\":false,\"tcpOptions\":{\"destinationPortRange\":{\"min\":22,\"max\":22}},\"description\":\"SSH from OCI Bastion in bootstrap VCN\"},{\"source\":\"0.0.0.0/0\",\"sourceType\":\"CIDR_BLOCK\",\"protocol\":\"1\",\"isStateless\":false,\"icmpOptions\":{\"type\":3,\"code\":4},\"description\":\"Path MTU discovery\"}]" \
  --egress-security-rules \
    '[{"destination":"0.0.0.0/0","destinationType":"CIDR_BLOCK","protocol":"all","isStateless":false,"description":"Runner outbound through controlled routes"}]' \
  --force

export BOOTSTRAP_SUBNET_OCID=$(
  oci network subnet create \
    --profile lz-bootstrap-session --auth security_token \
    --compartment-id "$TARGET_TENANCY_OCID" \
    --vcn-id "$BOOTSTRAP_VCN_OCID" \
    --cidr-block "$BOOTSTRAP_SUBNET_CIDR" \
    --display-name sn-mccp-foundation-runner \
    --dns-label runner \
    --route-table-id "$BOOTSTRAP_ROUTE_TABLE_OCID" \
    --security-list-ids "[\"$BOOTSTRAP_SECURITY_LIST_OCID\"]" \
    --prohibit-public-ip-on-vnic true \
    --prohibit-internet-ingress true \
    --query data.id --raw-output
)
```

The Service Gateway route destination must be the returned service
`cidr-block` label, such as
`all-fra-services-in-oracle-services-network`; its display name is invalid in
a route rule.

Create the restricted Bastion and select a reviewed Oracle Linux 9 ARM64 image:

```bash
export CLIENT_IP="$(curl -4 --fail --silent https://api.ipify.org)"
oci bastion bastion create \
  --profile lz-bootstrap-session --auth security_token \
  --bastion-type standard \
  --compartment-id "$TARGET_TENANCY_OCID" \
  --target-subnet-id "$BOOTSTRAP_SUBNET_OCID" \
  --name bst-mccp-foundation-runner \
  --max-session-ttl 10800 \
  --client-cidr-list "[\"$CLIENT_IP/32\"]" \
  --wait-for-state SUCCEEDED

oci compute image list \
  --profile lz-bootstrap-session --auth security_token \
  --compartment-id "$TARGET_TENANCY_OCID" \
  --shape VM.Standard.A1.Flex \
  --operating-system 'Oracle Linux' \
  --sort-by TIMECREATED --sort-order DESC --limit 10 \
  --query 'data[?\"operating-system-version\"==`9`].{name:"display-name",id:id,created:"time-created"}'

export FOUNDATION_IMAGE_OCID='<reviewed-oracle-linux-9-arm64-image-ocid>'
export FOUNDATION_RUNNER_INSTANCE_OCID=$(
  oci compute instance launch \
    --profile lz-bootstrap-session --auth security_token \
    --availability-domain '<availability-domain>' \
    --compartment-id "$TARGET_TENANCY_OCID" \
    --shape VM.Standard.A1.Flex \
    --shape-config '{"ocpus":1,"memoryInGBs":6}' \
    --image-id "$FOUNDATION_IMAGE_OCID" \
    --subnet-id "$BOOTSTRAP_SUBNET_OCID" \
    --assign-public-ip false \
    --display-name vm-mccp-foundation-runner \
    --hostname-label mccp-foundation \
    --ssh-authorized-keys-file "$SSH_PUBLIC_KEY_FILE" \
    --user-data-file docs/foundation-runner-cloud-init.yaml \
    --boot-volume-size-in-gbs 50 \
    --is-pv-encryption-in-transit-enabled true \
    --agent-config \
      '{"areAllPluginsDisabled":false,"isManagementDisabled":false,"isMonitoringDisabled":false,"pluginsConfig":[{"name":"Bastion","desiredState":"ENABLED"},{"name":"OS Management Service Agent","desiredState":"ENABLED"}]}' \
    --query data.id --raw-output
)
```

Wait for the instance, cloud-init, and Bastion plugin to become ready before
registering GitHub Actions. The supplied cloud-init pins and verifies ripgrep
`15.2.0`, go-jsonnet `0.22.0`, and GitHub Actions runner `2.336.0`; OCI CLI is
installed from Oracle's OL9 package repository. The workflows disable the
optional `hashicorp/setup-terraform` wrapper, so the runner does not require a
separate system Node.js installation.

In the private foundation repository, use **Settings → Actions → Runners →
New self-hosted runner**. Run the generated repository-scoped Linux ARM64
configuration through a time-limited OCI Bastion managed SSH session, name the
runner `mccp-foundation-<region>`, add only the `mccp-foundation` custom label,
and configure it as the `github-runner` system service. The registration token
is short-lived and is not an OCI credential. Never store it in cloud-init,
GitHub secrets, shell history, or the repository.

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

The protected adapter also omits OE `v3.1.0`'s child-specific shared-network
Security Zone target. This is a narrow workaround for the upstream template:
OCI rejects a platform Compute instance in the parent CIS zone when its subnet
is in the child zone. The shared network and platform hierarchies therefore
inherit the same parent CIS Level 1 zone, while environment zones remain
unchanged. Review the OP01 final plan to confirm that no parent or environment
Security Zone is removed.

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
tools, Instance Principal tenancy identity, private versioned bucket, and
read-only object access.

GitHub Free does not enforce branch protection on private repositories; its API
returns HTTP 403 for this configuration. A Free-plan acceptance installation
must keep `FOUNDATION_AUTOMATION_READY=false`, restrict repository
administration, record independent review procedurally, and enable automation
only for the reviewed phase. Paid plans are recommended because they enforce
the branch and review controls technically.

Only after readiness succeeds:

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
