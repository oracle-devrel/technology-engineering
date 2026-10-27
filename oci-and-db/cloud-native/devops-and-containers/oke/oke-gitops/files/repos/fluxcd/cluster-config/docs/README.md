# Bootstrap access guide

Use these pages before the first `bootstrap-gitops-agent` run. They separate the
security setup from the day-to-day cluster administration guide.

## Reading order

1. [Create the IAM identities and policies](iam.md)
2. [Create the OCI Vault secrets](runtime-secrets.md)
3. Return to the [cluster bootstrap guide](../README.md#2-install-flux-operator)

## What the pipeline does

The Resource Manager `auth_token` seeds the three base OCI DevOps repositories
and the optional `fleet-config` repository. It is not installed in Kubernetes.
At deployment time, the
`prepare-gitops-agent` stage reads two different JSON secrets from OCI Vault:

| Secret | Used for | Kubernetes objects |
|---|---|---|
| Git reader | Read `cluster-config`, `apps-config`, and optional `fleet-config` | `git-token-auth` |
| OCIR reader | Pull mirrored charts and images | `ocirsecret` |

Only the Vault Secret OCIDs are pipeline parameters. Usernames and tokens are
never Terraform values or pipeline parameters.

## Related operations

- [Choose a Flux delivery pattern](use-cases.md)
- [Operate and troubleshoot Flux after bootstrap](operations.md)
- [Install the portable Flux administration skill](install-agent-skill.md)
- [AI-assisted cluster administration](agent-guide.md)
- [Rotate or replace either runtime credential](runtime-secrets.md#rotate-a-credential)
- [Deliver application secrets from OCI Vault](external-secrets.md)
- [Recover an existing installation that uses one shared token](runtime-secrets.md#migrate-an-existing-shared-token-installation)
- [Return to the cluster administrator guide](../README.md)
