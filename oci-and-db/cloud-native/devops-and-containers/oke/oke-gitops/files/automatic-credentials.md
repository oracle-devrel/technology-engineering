# Automatic Runtime Credentials

Enable **Create OCI Vault and Credentials** to create the runtime identities
used by Argo CD or Flux. The feature is optional and disabled by default.

## Resources

- A Git reader user and group with read-only access to this stack's
  `cluster-config`, optional `apps-config`, and optional `fleet-config`.
- A separate OCIR reader user and group with pull-only access below
  `ocir_repo_path_prefix` in the DevOps project compartment.
- An auth token for each account. Console access, passwords and API keys are
  disabled; no activation email is sent.
- A regional OCI Vault, AES-256 key, and two username/password JSON secrets.
- A runtime-reader access policy in the DevOps project compartment, named
  `<project>-gitops-credentials-<random7>` with a stable random suffix.

The Vault, key and secrets always use the actual DevOps project compartment,
including when an existing project is selected. The Automation Domain
Compartment only filters the identity-domain picker; it is not Vault placement.
Git usernames use the tenancy name; OCIR usernames use the Object Storage
namespace. Both include the selected identity-domain name.

## Bootstrap

The stack sets `git_read_credentials_secret_ocid` and
`registry_pull_secret_ocid` defaults on both `bootstrap-gitops-agent` and
`install-gitops-agent`. Run bootstrap without overriding them. Secret payloads
match the existing bootstrap JSON contract; no controller manifests change.

The Resource Manager user's supplied `auth_token` remains required for initial
repository seeding. Generated Git reader credentials cannot push repository
content and are never used for seeding.

## IAM Boundaries

**Create DevOps IAM policies and dynamic group** independently controls build
and installation execution permissions. Its DevOps domain selector is separate
from the automation accounts' domain selector. With execution IAM disabled,
those permissions must already exist. Automatic runtime-reader policies are
still created whenever automatic credentials are enabled.

The applying identity needs permission to create users, groups and auth tokens
in the selected Identity Domain, and Vaults, keys, secrets and policies in the
DevOps project compartment. Reader access is scoped to the stack repositories
and registry prefix; resources outside those scopes need separately configured
permissions.

## Manual Mode And Lifecycle

When disabled, no automation resources are created and pipeline secret defaults
remain `CHANGE_ME`. Supply your own two Vault JSON secret OCIDs as before.
Existing customer-owned repositories are not overwritten by either mode.

Auth tokens and secret contents are sensitive Terraform state. Restrict state
access. Outputs expose only resource references. Disabling the feature on an
existing deployment destroys the generated users, tokens and policy and
schedules Vault resources for deletion; installed controllers need replacement
credentials before that change. OCI enforces a retention period for Vault
deletion.
