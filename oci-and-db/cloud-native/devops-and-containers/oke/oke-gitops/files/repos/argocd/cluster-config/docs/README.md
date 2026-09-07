# Bootstrap security and access

Use these pages before the first `bootstrap-gitops-agent` run. They separate the
security setup from the day-to-day cluster administration guide.

For normal GitOps changes, start with the repository [README](../README.md),
[use-case catalog](use-cases.md), and [operations guide](operations.md).

## Reading order

1. [Create the IAM identities and policies](iam.md)
2. [Create the OCI Vault secrets](runtime-secrets.md)
3. [Configure secure Argo CD access](argocd-access.md)
4. Return to the [cluster bootstrap guide](../README.md#2-install-argo-cd)

## What the pipeline does

The Resource Manager `auth_token` seeds the three base OCI DevOps repositories
and the optional `fleet-config` repository. It is not installed in Kubernetes.
At deployment time, the
`prepare-gitops-agent` stage reads two different JSON secrets from OCI Vault:

| Secret | Used for | Kubernetes objects |
|---|---|---|
| Git reader | Read `cluster-config`, `apps-config`, and optional `fleet-config` | `oci-devops-git-credentials` |
| OCIR reader | Pull mirrored charts and images | `ocir-oci-repo`, `ocirsecret` |

Only the Vault Secret OCIDs are pipeline parameters. Usernames and tokens are
never Terraform values or pipeline parameters.

## Related operations

- [Rotate or replace either runtime credential](runtime-secrets.md#rotate-a-credential)
- [Configure private Argo CD access, OIDC, and RBAC](argocd-access.md)
- [Recover an existing installation that uses one shared token](runtime-secrets.md#migrate-an-existing-shared-token-installation)
- [Return to the cluster administrator guide](../README.md)
