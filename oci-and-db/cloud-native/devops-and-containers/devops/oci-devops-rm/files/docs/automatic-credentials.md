# Automatic Credentials

Set `create_automatic_credentials=true` to create credentials without supplying
a personal repository-seeding auth token. The default remains false, preserving
existing manual installations.

## Configure

1. Enable **Create Automatic Credentials** in the OCI DevOps section.
2. Select the existing identity domain and its compartment in the IAM section.
3. Select the compartment for the generated Vault/key/secrets and provide a
   contact email required by identity domains.
4. Enable **Create IAM** unless your organization supplies permissions externally.
5. Apply the stack, then run each application's bootstrap pipeline.

No network infrastructure is created or changed. Both OKE targets continue
using private endpoints, the selected worker subnets and optional NSGs.

## Created Resources

| Resource | Purpose |
| --- | --- |
| Bootstrap service account and group | Git access to only repositories created by this stack |
| Pull service account and group | Read-only access to the component image repositories; full delivery only |
| One auth token per account | Bootstrap Git authentication or Kubernetes image pulls |
| Regional Vault and AES key | Encrypt the generated credential secrets |
| One token secret per account | Store the auth token without exposing it in outputs |

Names derive from the resolved project name plus a short hash of its OCID,
avoiding collisions between equally named projects. Tokens are stable across
ordinary applies; rotation is explicit, not scheduled by this stack.

Build and release scripts continue using resource-principal authentication.
The generated bootstrap user is not a pipeline administrator. The pull user
cannot push images or write source repositories.

In build-only mode, only the bootstrap account is created. Application delivery
adds the pull account and presets new bootstrap pipelines with its registry
username and Vault token-secret OCID. The pipeline still creates the namespace
and Kubernetes pull secret when run, not during Terraform apply.

## Independent IAM Selection

| Automatic credentials | Create IAM | Behavior |
| --- | --- | --- |
| Off | Off | Supply personal seeding token and externally managed permissions |
| Off | On | Supply seeding token; stack creates pipeline dynamic group/policies |
| On | Off | Stack creates accounts/groups/Vault/secrets; supply IAM permissions externally |
| On | On | Stack also grants scoped Git/pull permissions and pipeline access |

With external IAM, configure access for the derived groups before repository
seeding can succeed. Merely creating users does not authorize them. Inspect
`credentials.tf` for the generated policy templates. With IAM enabled, seeding
waits for policy creation and retries initial Git access for up to ten minutes
while authorization propagates.

If permissions cannot be prepared until the new group OCIDs exist, the initial
apply can fail at repository seeding. Grant the external policies, then reapply;
the already created credentials are retained. Enable both flags for an
unattended first installation.

Generated dynamic-group membership matches exact pipeline/repository/trigger
OCIDs instead of all resources in the project compartment. Vault read access is
limited to the application bootstrap pipeline identities.
Automatic mode additionally restricts that access to the generated pull-token
secret; manually supplied secrets remain scoped to the selected compartment.
New pipelines created outside Terraform are not automatically added to this
allowlist. Grant their execution identities explicitly through your approved
IAM process. Group and policy propagation can temporarily delay the first Git
operation or pipeline run; retry after propagation rather than widening grants.

The pipeline group still shares the stack's compartment-scoped execution
permissions. An exact identity allowlist is not isolation between pipeline
roles: treat executable pipeline code as trusted, and review changes accordingly.

## Security And Upgrade Boundaries

The applying identity must be authorized to manage identity-domain users,
groups, auth tokens, Vaults, keys and secrets, and policies when enabled.
Identity resources use the tenancy home-region provider; Vault resources use
the stack region. No console password or activation email is created.
The accounts are ordinary identity-domain users with console and other
credential capabilities disabled; only OCI auth tokens are enabled. They are
not Identity Domains `serviceUser` accounts, which disable auth tokens.
Tokens are created through the selected identity domain endpoint. A short
Vault readiness delay allows its dedicated KMS DNS records to propagate
before creating the key; retry the apply if regional propagation takes longer.

Auth tokens are stored in Terraform state as well as Vault. Sensitive values
are redacted, not removed from state: restrict Resource Manager state and job
access. The `automatic_credentials` output contains only references, usernames
and group IDs. Tokens never enter generated repository files or Helm values.

Security resources remain Terraform-managed. Disabling this option or
destroying the stack can revoke tokens and schedule Vault/key/secret deletion.
Review the plan and migrate consumers first. Existing Kubernetes pull secrets
are not automatically rotated when the Vault token changes; rerun bootstrap
after rotating credentials.

Release-mode pipeline customization is preserved. Enabling this feature on an
existing stack does not overwrite old bootstrap pipeline defaults: pass the
generated username and secret OCID when running it, or update its defaults
explicitly. Existing repository files are not reseeded or overwritten.
