# Automatic Credentials

Set `create_automatic_credentials=true` to create automation credentials.
Repository seeding always requires the current user's supplied auth token,
including in automatic mode. The default remains false, preserving existing
manual installations.

## Configure

1. Supply your repository-seeding auth token and enable **Create OCI Vault and Credentials** in the IAM section.
2. Select the existing identity domain and its compartment in the IAM section.
3. Identity Domains receives the placeholder email `automation@example.com`;
   no email input is required in the form. The generated Vault, key and secrets
   always use the resolved DevOps project compartment, including
   when an existing project is reused. No separate Vault compartment is selected.
4. Enable **Create IAM** unless your organization supplies permissions externally.
5. Apply the stack, then run each application's bootstrap pipeline.

No network infrastructure is created or changed. Both OKE targets continue
using private endpoints, the selected worker subnets and optional NSGs.

## Created Resources

| Resource | Purpose |
| --- | --- |
| Bootstrap service account and group | Git access to only repositories created by this stack |
| Pull service account and group | Read-only access to the component image repositories; full delivery only |
| One auth token per account | Automation Git authentication or Kubernetes image pulls; not Terraform repository seeding |
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
| On | Off | Supply seeding token; stack creates accounts/groups/Vault/secrets and their Git/pull access policy; pipeline permissions remain external |
| On | On | Supply seeding token; stack also grants scoped Git/pull permissions and pipeline access |

The supplied seeding token must belong to the current OCI user and have access
to the generated repositories. It is never replaced by a generated token.
Initial Git access retries for up to ten minutes while authorization propagates.
Automatic credentials always include the generated groups' Git/pull access policy
in the resolved DevOps project compartment, independently of **Create IAM**.
Its name is `<project>-automation-credentials-<random7>`; the suffix is generated
once and retained in Terraform state. **Create IAM** controls only the pipeline
dynamic group and execution policies. With it disabled, those pipeline
permissions must already exist externally. Inspect `credentials.tf` for the
generated policy templates.

Generated dynamic-group membership matches exact pipeline/repository/trigger
OCIDs instead of all resources in the project compartment. Vault read access is
limited to the application bootstrap pipeline identities.
Automatic mode additionally restricts that access to the generated pull-token
secret; manually supplied bootstrap secrets must also be in the DevOps project
compartment. Legacy Vault-compartment input values are retained for compatibility
but no longer override credential placement or secret-read policy scope.
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
60-second Vault readiness delay allows its dedicated KMS DNS records to propagate
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
