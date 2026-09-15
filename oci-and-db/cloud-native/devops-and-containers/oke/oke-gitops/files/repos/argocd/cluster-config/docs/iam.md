# Create the bootstrap IAM identities and policies

[Documentation index](README.md) · [Next: create the Vault secrets](runtime-secrets.md)

Create two non-human users. Do not use the administrator who ran the Resource
Manager stack and do not give either user an administrator role.

| Identity | Suggested group | Required access |
|---|---|---|
| Git reader | `oke-gitops-git-readers` | Read OCI DevOps repositories |
| OCIR reader | `oke-gitops-ocir-readers` | Pull from OCIR repositories |

The users may be shared by clusters only when those clusters are intentionally
allowed to read the same repositories. Separate users make revocation and
auditing easier.

## 1. Record the compartments and identity domain

Before creating anything, record:

- the identity domain containing the two users;
- the compartment OCID containing the OCI DevOps project;
- the compartment OCID containing the OCIR repositories;
- the compartment OCID containing the Vault secrets;
- the OKE, worker subnet, and optional NSG compartment OCIDs.

Several of these can be the same compartment. Policy examples below use OCIDs
so that duplicate compartment names are not ambiguous.

## 2. Create the groups and users

In OCI Console:

1. Open **Identity & Security → Domains** and select the intended domain.
2. Under **Groups**, create `oke-gitops-git-readers` and
   `oke-gitops-ocir-readers`.
3. Under **Users**, create `oke-gitops-git-reader` and
   `oke-gitops-ocir-reader`.
4. Add only the Git user to the Git group.
5. Add only the OCIR user to the OCIR group.

Do not add either user to an administrators group.

## 3. Grant the runtime users read-only access

Open **Identity & Security → Policies** in the parent compartment that is
allowed to govern the target resources. You may add these statements to an
existing policy; a new policy object is not required.

```text
Allow group <domain-name>/oke-gitops-git-readers to read devops-repositories in compartment id <devops-compartment-ocid>
Allow group <domain-name>/oke-gitops-ocir-readers to read repos in compartment id <ocir-compartment-ocid>
```

For users in the tenancy's default identity domain, follow the group-name
format accepted by your tenancy. Do not replace `read` with `manage`: these
identities must not seed Git repositories or push images.

## 4. Verify the DevOps resource-principal policy

The deployment pipeline—not either runtime user—reads the Vault secrets and
connects to OKE. When the stack input `create_iam` is `true`, the stack creates
the required dynamic group and policy. When IAM is managed externally, ensure
the DevOps dynamic group has the equivalent permissions:

```text
Allow dynamic-group <domain-name>/<devops-dynamic-group> to manage repos in compartment id <devops-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to manage devops-family in compartment id <devops-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to use ons-topics in compartment id <devops-compartment-ocid>

Allow dynamic-group <domain-name>/<devops-dynamic-group> to use subnets in compartment id <network-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to use vnics in compartment id <network-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to use dhcp-options in compartment id <network-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to use network-security-groups in compartment id <network-compartment-ocid>

Allow dynamic-group <domain-name>/<devops-dynamic-group> to read all-artifacts in compartment id <devops-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to manage compute-container-family in compartment id <devops-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to manage cluster in compartment id <oke-compartment-ocid>
Allow dynamic-group <domain-name>/<devops-dynamic-group> to read secret-bundles in compartment id <vault-secret-compartment-ocid>
```

If your tenancy has reached its policy-object limit, append the exact
statements to an existing policy in the appropriate parent compartment. Do not
broaden an unrelated group's permissions merely to avoid creating a policy.

## 5. Generate one auth token for each runtime user

For each new user:

1. Open the user in its identity domain.
2. Open **Resources → Auth tokens**.
3. Select **Generate token**, give it a purpose-specific description, and
   generate it.
4. Copy the token immediately. OCI displays it only once.

Use these username formats in the corresponding Vault JSON:

```text
Git:  <tenancy-name>/<domain-name>/<git-reader-username>
OCIR: <tenancy-namespace>/<domain-name>/<ocir-reader-username>
```

The tokens are passwords, not OCIDs. Do not place them in Terraform variables,
pipeline parameters, Git, shell history, tickets, or documentation.

## Checkpoint

Continue only when:

- each user belongs to exactly its intended group;
- the Git group has only repository-read access;
- the OCIR group has only registry-read access;
- the DevOps dynamic group can read secret bundles and reach the private OKE
  endpoint;
- both auth tokens have been copied into a secure temporary location.

[Next: create the two Vault secrets](runtime-secrets.md)
