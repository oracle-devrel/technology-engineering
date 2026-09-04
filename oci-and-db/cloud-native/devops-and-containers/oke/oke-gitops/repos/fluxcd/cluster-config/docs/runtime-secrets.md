# Create and operate the runtime Vault secrets

[Previous: IAM identities and policies](iam.md) · [Documentation index](README.md)

Create two OCI Vault secrets after the two users and auth tokens exist. The
pipeline accepts Secret OCIDs; it never accepts the token values as pipeline
parameters.

## 1. Verify the Vault prerequisites

You need:

- an OCI Vault;
- a symmetric master encryption key in that Vault;
- permission to create secrets in the chosen compartment;
- `read secret-bundles` permission for the DevOps dynamic group, as shown in
  [the IAM guide](iam.md#4-verify-the-devops-resource-principal-policy).

An asymmetric key cannot encrypt an imported secret. You may reuse an existing
Vault and symmetric key that follow your organization's security policy.

## 2. Create the Git reader secret

In OCI Console:

1. Open **Identity & Security → Vault → Secrets**.
2. Select **Create secret**.
3. Choose the secret compartment, Vault, and symmetric encryption key.
4. Use a descriptive name such as `oke-gitops-git-read`.
5. Select manual secret generation and enter this JSON as plain text:

   ```json
   {"username":"<tenancy-name>/<domain-name>/<git-reader-username>","password":"<git-reader-auth-token>"}
   ```

6. Create the secret and copy its Secret OCID.

The Console encodes the plaintext for OCI Vault. Do not base64-encode the JSON
before pasting it into the Console.

## 3. Create the OCIR reader secret

Repeat the same procedure with a different secret, for example
`oke-gitops-ocir-pull`, and this JSON:

```json
{"username":"<tenancy-namespace>/<domain-name>/<ocir-reader-username>","password":"<ocir-reader-auth-token>"}
```

Copy the second Secret OCID. Do not reuse the Git username or token.

## 4. Run the installer

Open **Developer Services → DevOps → Projects**, select the project created by
the stack, and run `bootstrap-gitops-agent` with:

| Build parameter | Value |
|---|---|
| `git_read_credentials_secret_ocid` | Git reader Secret OCID |
| `registry_pull_secret_ocid` | OCIR reader Secret OCID |
| `chart_version` | `LATEST` or an exact initial chart version |

Always supply both parameters. Supplying only one intentionally fails before
the cluster is changed. The build automatically triggers
`install-gitops-agent`; do not start a duplicate deployment manually.

After both runs succeed, verify:

```bash
kubectl -n flux-system get secret git-token-auth
kubectl -n flux-system get secret ocirsecret
kubectl -n flux-system get deployments
```

Do not print or decode these Secrets during routine verification.

## Rotate a credential

Git and OCIR credentials rotate independently:

1. Generate a new auth token for the same dedicated user.
2. Open the corresponding Vault secret and create a new secret version
   containing the same username and the new token.
3. Run `prepare-gitops-agent` as a single-stage deployment with both current
   Secret OCIDs.
4. Wait for that deployment to succeed.
5. Verify both GitRepository objects and all Kustomizations remain Ready.
6. Only then revoke the previous auth token.

If verification fails, leave the previous token active, correct the new secret
version, and rerun the preparation stage.

## Migrate an existing shared-token installation

`auth_token_secret_ocid` is a deprecated one-release fallback for stacks that
previously used one personal token for Git and OCIR.

To migrate:

1. Create both dedicated identities and Vault secrets.
2. Update the stack so the deployment pipeline exposes both current Secret
   OCID parameters.
3. Run `prepare-gitops-agent` as a single-stage deployment with both new Secret
   OCIDs.
4. Verify Git reconciliation and private-registry access.
5. Revoke the former personal token.
6. Stop supplying `auth_token_secret_ocid`.

Never delete an active Vault secret or user while the cluster still references
it.

## OCI references

- [Creating a secret](https://docs.oracle.com/en-us/iaas/Content/secret-management/Tasks/create-secret.htm)
- [Getting a secret's contents](https://docs.oracle.com/en-us/iaas/Content/secret-management/Tasks/get-secrets-contents.htm)
- [OCI DevOps IAM policies](https://docs.oracle.com/en-us/iaas/Content/devops/using/devops_iampolicies.htm)

[Return to first-time bootstrap](../README.md#2-install-flux-operator)
