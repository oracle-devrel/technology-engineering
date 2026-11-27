# Upgrading To 1.2.0

This minor release adds optional Vault-backed automation credentials, tighter
pipeline identity scopes, and structured Resource Manager application/tool forms.

## Credentials And IAM

Repository seeding always uses your supplied OCI auth token. **Create OCI Vault
and Credentials** creates automation users/groups/tokens and their scoped Git/pull
policy, plus a Vault, AES key and secrets in the resolved DevOps project compartment.
The policy uses `<project>-automation-credentials-<random7>` naming with a stable
suffix. Sensitive tokens still enter Terraform state; restrict state/job access.

**Create DevOps IAM Policies And Dynamic Group** independently controls pipeline
execution permissions. With it disabled, those permissions must already exist.
Select the DevOps domain for the dynamic group and automation domain for users
separately; they can be the same domain. See [Automatic Credentials](automatic-credentials.md).

## Existing Resource Manager Inputs

Applications now use a structured list with nested components. Cluster
administration exposes a tool list directly. Terraform accepts native values and
legacy JSON strings/objects, but the Console cannot render an object as a list.

Before opening the new form, convert the saved `cluster_administration` variable
from `{ "tools": [...] }` to `[...]`. For legacy `noprod.tools`, extract that list.
Use the Resource Manager API/CLI and preserve all other saved variables. This
representation-only change needs no apply and preserves the tools' configuration.
Do not expose auth tokens when exporting variables.

Existing Terraform inputs without `pipeline_iam_domain_id` retain the old
`devops_iam_domain_id` fallback. In the new form, select the existing dynamic
group's domain in the separate DevOps domain picker before applying.

## Review The Plan

- Dynamic groups match exact generated execution-resource OCIDs rather than
  every DevOps resource in the compartment.
- Bootstrap secret reads are limited to bootstrap identities and, in automatic
  mode, the generated pull-token secret.
- Vault placement and secret-read scope follow the actual project compartment.
  Deprecated compartment overrides no longer apply; migrate external bootstrap
  secrets where necessary.
- Credential policies are always created in the project compartment. Existing
  policy names/locations may require replacement; allow IAM propagation.

Exact identity scopes do not isolate pipeline roles: execution permissions remain
a shared trust boundary. Review executable pipeline changes accordingly.
Release archives preserve customized starter resources and add-only seeding.
Do not use development-mode archives for production.

## Verification

Amsterdam testing exercised two components through PR, dev, staging and production,
automatic bootstrap credentials, cluster tools, image digests, negative access
checks and credential stability. Later form/policy refinements passed local
validation and mocked plans. The child-domain comparison was blocked by
domain-creation permissions; no unverified domain-placement rule is enforced.
