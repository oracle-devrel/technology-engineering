# OCI WIF example setup

This guide describes the OCI and GitHub configuration used by the
[reference examples](./README.md). Use it as a basis for your own setup.
The examples use OCI Workload Identity Federation with ephemeral resource
principal session tokens. Each demo creates one private
Object Storage bucket and deletes it in the same run. Terraform uses native
provider WIF; Ansible uses the OCI collection's resource principal authentication.

## 1. Prerequisites

You need:

- An OCI administrator who can create an Identity Domain, configure its
  applications and trusts, and create IAM policies.
- A compartment and region for the demo buckets.
- A GitHub repository containing these workflows, permission to set its Actions
  secrets, and permission to run workflows.
- Bash, OCI CLI, `jq`, and GitHub CLI (`gh`), authenticated to your repository.
  OCI session authentication opens a browser for sign-in; no OCI Console
  configuration is required.

Choose the executing repository before configuring policies. The OIDC
`repository` claim is its actual `owner/repository`; a fork needs its own name
in the policy and its own Actions secrets.

Use a dedicated Identity Domain for the reference. OCI requires issuer
uniqueness within a domain. The Resource trust needs no runtime service user
or group membership.

## 2. Create the Identity Domain

Run the blocks in order in the same Bash session. Replace the region, tenancy,
compartment, and repository values below. Use an administrator with access to
the new domain. Keep shell tracing and debug logging disabled.

```bash
set -euo pipefail
oci session authenticate --region eu-frankfurt-1 --profile-name rpst-admin
export RPST_BOOTSTRAP_PROFILE=rpst-admin
export OCI_REGION=eu-frankfurt-1
export OCI_TENANCY='<tenancy_ocid>'
export RPST_COMPARTMENT_ID='<compartment_ocid>'
export RPST_REPOSITORY='<owner>/<repo>'
export RPST_DOMAIN_NAME=github-rpst
export RPST_APPLICATION_NAME=github-rpst-client
export RPST_TRUST_NAME=github-rpst-trust
export RPST_POLICY_NAME=github-rpst-buckets
gh auth status
```

A profile name is a label; permissions come from the authenticated identity.
If the OCI session expires, authenticate again with the same profile. The
administrator configures OCI; the runtime application needs no admin roles.

Create a Free domain, hidden on the sign-in page, and wait for its work request:

```bash
oci iam domain create \
  --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token --region "$OCI_REGION" \
  --compartment-id "$RPST_COMPARTMENT_ID" --display-name "$RPST_DOMAIN_NAME" \
  --description 'GitHub Actions RPST reference' --home-region "$OCI_REGION" \
  --license-type free --is-hidden-on-login true \
  --wait-for-state SUCCEEDED --wait-interval-seconds 10 --query data.id --raw-output
domain="$(oci iam domain list --compartment-id "$RPST_COMPARTMENT_ID" --all \
  --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token --output json --query data |
  jq -ce --arg name "$RPST_DOMAIN_NAME" \
    '[.[] | select(."display-name" == $name)] |
     if length == 1 then .[0] else error("Expected exactly one domain") end')"
RPST_DOMAIN_ID="$(jq -er '.id' <<< "$domain")"
domain="$(oci iam domain get --domain-id "$RPST_DOMAIN_ID" \
  --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token --output json --query data)"
jq -e '."lifecycle-state" == "ACTIVE"' <<< "$domain" > /dev/null
RPST_DOMAIN_URL="$(jq -er '.url | rtrimstr("/")' <<< "$domain")"
export RPST_DOMAIN_URL
unset domain
```

The base URL must not include `/admin/v1` or `/oauth2/v1/token`. Use the domain's
home region for these demo buckets; additional domains are not automatically
replicated to every subscribed region. Run creation blocks once. Before retrying
after an interruption, check whether their resources already exist.
[OCI CLI domain creation](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/iam/domain/create.html).

## 3. Create the runtime OAuth application

Create an active confidential client with only the Client Credentials grant.
The response contains its credentials: capture it in memory and never run this
request without the assignment. No administrative role grants are created.

```bash
application="$(
  jq -n --arg name "$RPST_APPLICATION_NAME" '{
    "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:App"],
    "displayName": $name,
    "basedOnTemplate": {"value": "CustomWebAppTemplateId"},
    "isOAuthClient": true,
    "clientType": "confidential",
    "allowedGrants": ["client_credentials"],
    "active": true
  }' |
    oci raw-request --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
      --http-method POST \
      --target-uri "$RPST_DOMAIN_URL/admin/v1/Apps?attributes=id,name,clientSecret" \
      --request-body file:///dev/stdin --output json --query '{id:id,name:name,clientSecret:clientSecret}' |
    jq -ce 'if (.status | startswith("2")) then .data
            else error("Application creation failed: " + .status) end'
)"
RPST_APP_ID="$(printf '%s' "$application" | jq -er '.id')"
test -n "$RPST_APP_ID"
RPST_CLIENT_ID="$(printf '%s' "$application" | jq -er '.name')"
RPST_CLIENT_SECRET="$(printf '%s' "$application" | jq -er '.clientSecret')"
unset application
```

Keep the client ID and secret as unexported shell variables until section 6
transfers them directly to GitHub. Do not print them or save them to a file.
The runtime client only performs token exchange.
[Oracle application creation API](https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-admin-v1-apps-post.html).

## 4. Create the Resource trust

Use these fields:

| Field | Value |
| --- | --- |
| `name` | `github-rpst-trust` |
| `type` | `JWT` |
| `issuer` | `https://token.actions.githubusercontent.com` |
| `publicKeyEndpoint` | `https://token.actions.githubusercontent.com/.well-known/jwks` |
| `subjectType` | `Resource` |
| `allowImpersonation` | `true` |
| `impersonatingResource` | `github_terraform` |
| `claimPropagations` | `["ext_repository", "ext_workflow_ref"]` |
| `oauthClients` | Array containing the runtime application's client ID |
| `active` | `true` |
| `schemas` | `["urn:ietf:params:scim:schemas:oracle:idcs:IdentityPropagationTrust"]` |

The resource type is a free string. `impersonatingResource`, the exchange's
`res_type`, and `RPST_RESOURCE_TYPE` must match. All demos can use this same
trust and client. Two claims are propagated here; OCI allows up to three.
The RPST payload exposes them as `var_ext_repository` and `var_ext_workflow_ref`;
IAM conditions use `request.principal.ext_repository`.
[Oracle RPST requirements](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/token_exchange_grant_type_workload_id-federation.htm),
[A-Team configuration example](https://www.ateam-oracle.com/oci-workload-identity-federation-using-ephemeral-rpst).

The recipe uses the administrator's signed OCI CLI session, `jq`, and
`raw-request` to send the complete trust configuration.
[OCI CLI raw-request reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/raw-request.html).

The next block uses the client ID captured above, sends JSON through standard
input, checks the HTTP status, and prints only the trust ID. It needs no client
secret and creates no local credential or response file.

```bash
test -n "$RPST_CLIENT_ID"

jq -n --arg client_id "$RPST_CLIENT_ID" --arg name "$RPST_TRUST_NAME" '{
  "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:IdentityPropagationTrust"],
  "name": $name,
  "type": "JWT",
  "issuer": "https://token.actions.githubusercontent.com",
  "publicKeyEndpoint": "https://token.actions.githubusercontent.com/.well-known/jwks",
  "subjectType": "Resource",
  "allowImpersonation": true,
  "impersonatingResource": "github_terraform",
  "claimPropagations": ["ext_repository", "ext_workflow_ref"],
  "oauthClients": [$client_id],
  "active": true
}' |
  oci raw-request --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
    --http-method POST --target-uri "$RPST_DOMAIN_URL/admin/v1/IdentityPropagationTrusts" \
    --request-body file:///dev/stdin --output json --query id |
  jq -er 'if (.status | startswith("2")) then .data
          else error("Trust creation failed: " + .status) end'
```

Run once per domain. Before retrying after an interruption, check whether the
trust exists. If the session expires, authenticate again with the same profile.
Any administrator OAuth client used for setup must be separate from the runtime
client; its credentials do not belong in the repository secrets.

### Verify the application and trust

After creation, verify the stored configuration. Keep the administrator session
active and the profile, domain URL, and names configured above.

```bash
set -euo pipefail
domain_read() {
  oci raw-request --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
    --http-method GET --target-uri "$RPST_DOMAIN_URL/admin/v1/$1" --output json --query "$2" |
    jq -e 'if (.status | startswith("2")) then .data
           else error("Administrative read failed: " + .status) end'
}

app_filter="$(jq -rn --arg name "$RPST_APPLICATION_NAME" '"displayName eq " + ($name | tojson) | @uri')"
trust_filter="$(jq -rn --arg name "$RPST_TRUST_NAME" '"name eq " + ($name | tojson) | @uri')"
app="$(domain_read "Apps?attributes=id,name,active,clientType,isOAuthClient,allowedGrants&filter=$app_filter" '{count:totalResults,app:Resources[0].{id:id,name:name,active:active,clientType:clientType,isOAuthClient:isOAuthClient,allowedGrants:allowedGrants}}')"
trust="$(domain_read "IdentityPropagationTrusts?filter=$trust_filter" '{count:totalResults,trust:Resources[0].{active:active,subjectType:subjectType,type:type,issuer:issuer,publicKeyEndpoint:publicKeyEndpoint,allowImpersonation:allowImpersonation,impersonatingResource:impersonatingResource,claimPropagations:claimPropagations,oauthClients:oauthClients}}')"
jq -ne --argjson app "$app" --argjson trust "$trust" \
  'if $app.count == 1 and $trust.count == 1 then true
   else error("Expected exactly one application and one trust") end' > /dev/null
app_id="$(jq -r '.app.id' <<< "$app")"
grant_filter="$(jq -rn --arg id "$app_id" '"grantee.value eq " + ($id | tojson) | @uri')"
grants="$(domain_read "Grants?filter=$grant_filter" totalResults)"

jq -ne --argjson app "$app" --argjson trust "$trust" --argjson grants "$grants" '
  $app.app as $a | $trust.trust as $t | {
    app_active: ($a.active == true),
    confidential_client: ($a.clientType == "confidential" and $a.isOAuthClient == true),
    client_credentials_only: ($a.allowedGrants == ["client_credentials"]),
    no_admin_roles: ($grants == 0),
    active_resource_trust: ($t.active == true and $t.subjectType == "Resource"),
    jwt_type: ($t.type == "JWT"),
    issuer: ($t.issuer == "https://token.actions.githubusercontent.com"),
    jwks: ($t.publicKeyEndpoint == "https://token.actions.githubusercontent.com/.well-known/jwks"),
    impersonation: ($t.allowImpersonation == true and $t.impersonatingResource == "github_terraform"),
    claim_propagations: ($t.claimPropagations == ["ext_repository", "ext_workflow_ref"]),
    client_binding: ($t.oauthClients == [$a.name])
  } | ., (if all(.[]; . == true) then empty else error("Correct the failed settings") end)'
unset app trust grants app_id app_filter trust_filter grant_filter
unset -f domain_read
```

All checks must be `true`; a failed check returns a nonzero exit status. The
application request selects its required fields with the API's `attributes`
parameter, excluding the client secret. The CLI then selects the fields used
by each check, keeps their values in shell variables, and prints only the
check results. Client IDs and full responses are not printed.
[Oracle application attributes parameter](https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-admin-v1-apps-get.html).

The CLI recipe was executed on macOS with OCI CLI **3.83.0**, `jq` **1.7.1**,
and GitHub CLI. The stored application and trust returned all eleven checks as
`true`. These checks also passed against the domain used by the three bucket
demos.

## 5. Create IAM policies

Create a policy in the tenancy root with the two statements below. The bucket
rule uses the compartment OCID, including when the compartment is nested.

```bash
policy_statements="$(jq -cn \
  --arg namespace_policy "Allow any-user to read objectstorage-namespaces in tenancy where all {request.principal.type='identityfederateddomainapp', request.principal.ext_repository='$RPST_REPOSITORY'}" \
  --arg bucket_policy "Allow any-user to manage buckets in compartment id $RPST_COMPARTMENT_ID where all {request.principal.type='identityfederateddomainapp', request.principal.ext_repository='$RPST_REPOSITORY'}" \
  '[$namespace_policy, $bucket_policy]')"
RPST_POLICY_ID="$(oci iam policy create \
  --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
  --compartment-id "$OCI_TENANCY" --name "$RPST_POLICY_NAME" \
  --description 'GitHub Actions RPST bucket access' --statements "$policy_statements" \
  --wait-for-state ACTIVE --query data.id --raw-output)"
unset policy_statements
```

The first statement grants namespace access in the tenancy. The second grants
bucket access only in the selected compartment. For this repository, the value is
`dgutierrezcolodra/oci-terraform-github-actions-wif-example`.
Allow time for IAM propagation. Token issuance alone does not grant bucket access.
[Oracle policy syntax](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm).

Read back the domain and policy using the captured OCIDs:

```bash
oci iam domain get --domain-id "$RPST_DOMAIN_ID" --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
  --query 'data.{name:"display-name",state:"lifecycle-state",url:url,region:"home-region",compartment:"compartment-id"}'
oci iam policy get --policy-id "$RPST_POLICY_ID" --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
  --query 'data.{name:name,state:"lifecycle-state",compartment:"compartment-id",statements:statements}'
```

Confirm the domain is `ACTIVE`, the region and compartment are the ones you
selected, and the policy is `ACTIVE` in the tenancy root with exactly the two
statements above, using your repository and bucket compartment. The application,
trust, zero role grants, domain, and policy checks were performed against the
OCI configuration used by this reference.


## 6. Set GitHub repository secrets

All workflows use the same six secrets:

| Secret | Value |
| --- | --- |
| `RPST_DOMAIN_BASE_URL` | Domain HTTPS base URL without trailing slash |
| `RPST_CLIENT_ID` | Runtime application's client ID |
| `RPST_CLIENT_SECRET` | Runtime application's client secret |
| `RPST_RESOURCE_TYPE` | `github_terraform`, matching the trust |
| `RPST_COMPARTMENT_ID` | Bucket compartment OCID |
| `OCI_REGION` | Bucket region; use the domain's home region |

The Orchestrator demo also needs `OCI_TENANCY`, containing your tenancy OCID.
This supplies the upstream `tenancy_ocid` input; it is not an API credential.

Transfer the values through standard input. The client secret is never exported,
written to a file, or placed in an external command's arguments. The `printf`
output goes directly to `gh`, not to the terminal:

```bash
printf '%s' "$RPST_DOMAIN_URL" | gh secret set RPST_DOMAIN_BASE_URL --repo "$RPST_REPOSITORY"
printf '%s' "$RPST_CLIENT_ID" | gh secret set RPST_CLIENT_ID --repo "$RPST_REPOSITORY"
printf '%s' "$RPST_CLIENT_SECRET" | gh secret set RPST_CLIENT_SECRET --repo "$RPST_REPOSITORY"
printf '%s' 'github_terraform' | gh secret set RPST_RESOURCE_TYPE --repo "$RPST_REPOSITORY"
printf '%s' "$RPST_COMPARTMENT_ID" | gh secret set RPST_COMPARTMENT_ID --repo "$RPST_REPOSITORY"
printf '%s' "$OCI_REGION" | gh secret set OCI_REGION --repo "$RPST_REPOSITORY"
printf '%s' "$OCI_TENANCY" | gh secret set OCI_TENANCY --repo "$RPST_REPOSITORY"
unset RPST_CLIENT_ID RPST_CLIENT_SECRET RPST_APP_ID
gh secret list --repo "$RPST_REPOSITORY"
```

The list shows secret names, not values. Never put credentials, JWTs, RPSTs, or
private keys in commits, screenshots, logs, or job summaries.

## 7. Run the demos

GitHub requires the workflow file on the repository's default branch for manual
dispatch. In a customer repository, place the reference files on that branch.
[GitHub manual workflow requirements](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

### Terraform simple

1. Open **Actions → Demo Terraform RPST Bucket → Run workflow**.
2. Select the branch and `plan`. The raw exchange checks OCI configuration;
   Terraform then plans one bucket using its own RPST and key.
3. Expect HTTP 200, claim names, selected diagnostic values, lifetime, and a plan
   for one private bucket. Payload inspection does not verify its signature.
4. Run again with `apply-and-destroy`. Check both outcomes in the summary and
   confirm the bucket is absent from the compartment.

### Terraform OCI LZ Orchestrator

1. Set the additional `OCI_TENANCY` repository secret.
2. Open **Actions → Demo Terraform OCI LZ Orchestrator RPST Bucket → Run workflow**.
3. Select the branch and `plan`. The workflow fetches the official Orchestrator
   commit, fills its bucket inputs, and checks that the plan creates exactly one
   private bucket. No other configuration family is enabled.
4. Run again with `apply-and-destroy`. Check plan, apply, and destroy in the
   summary and confirm bucket absence in OCI.

The [Orchestrator instructions](./examples/terraform/orchestrator/README.md)
describe the selected upstream commit and input format.

### Ansible

1. Open **Actions → Demo Ansible RPST Bucket → Run workflow**.
2. Select the branch and run. It exchanges credentials, reads the namespace,
   creates a private bucket, obtains fresh credentials, and deletes the bucket.
3. Check create and delete outcomes in the summary and confirm bucket absence.

### Confirm bucket deletion

Use the workflow's numeric run ID from its URL. The administrator CLI lists
matching demo buckets and fails if any remain; successful deletion returns `[]`.

```bash
RPST_RUN_ID='<run_id>'
RPST_NAMESPACE="$(oci os ns get --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
  --region "$OCI_REGION" --query data --raw-output)"
oci os bucket list --profile "$RPST_BOOTSTRAP_PROFILE" --auth security_token \
  --region "$OCI_REGION" --namespace-name "$RPST_NAMESPACE" \
  --compartment-id "$RPST_COMPARTMENT_ID" --all --query 'data[].name' --output json |
  jq -e --arg id "$RPST_RUN_ID" \
    'map(select(. == ("rpst-terraform-" + $id) or
                . == ("rpst-orchestrator-" + $id) or
                . == ("rpst-ansible-" + $id))) |
     ., (if length == 0 then empty else error("Demo bucket still exists") end)'
```

## 8. Diagnose failures

| Observation | What to check |
| --- | --- |
| Manual dispatch unavailable | The workflow must exist on the default branch. |
| Input validation fails | All six shared secrets must exist; Orchestrator also needs `OCI_TENANCY`. |
| Raw exchange or Ansible exchange fails | Domain URL, active client, credentials, trust issuer uniqueness, JWKS endpoint, and matching `res_type`. |
| Raw exchange passes; Terraform authentication fails | Provider or SDK RPST handling; check the `tenant` claim. |
| Exchange passes; Object Storage access denied | IAM propagation, both policies, repository claim, compartment, and region. |
| Terraform checksum error | Check the committed lock; keep checksum validation enabled. |
| Delete or destroy fails after creation | Find the run's bucket in the compartment and remove it manually. |

The raw Terraform exchange uses `continue-on-error`; inspect its result and
Terraform's result separately. The raw exchange prints only HTTP status, permitted
error fields, claim names, selected diagnostic claims, and token lifetime.
The workflows do not request `rpst_exp`. Observe the issued lifetime; the recorded
Terraform execution received 1,200 seconds. These short demos obtain fresh
credentials before operations and do not require a background refresh process.
