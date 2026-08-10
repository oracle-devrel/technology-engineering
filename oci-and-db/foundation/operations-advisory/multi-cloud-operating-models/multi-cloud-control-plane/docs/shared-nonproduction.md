# Shared non-production repository model

New projects use exactly one repository, `nonprod-<project>`, governed by the
`shared-nonprod-v2` contract. It supports the independent lowercase
environments `dev`, `test`, and `uat`; it rejects production aliases.

This MVP has one fixed security profile: `repository-secrets`. The trusted
default-branch caller resolves exactly one cloud/environment/region tuple,
selects that environment's repository secret when its manifest needs one, and
calls Platform CI `main`. It retains the same-repository guard,
manifest-only diff, regular-file and JSON validation, pinned references,
runner routing, concurrency, and state isolation:
`<bucket>/<owner>/<repository>/<cloud>/<environment>/<region>/terraform.tfstate`.

## Configure a secret-backed environment

Create one JSON Actions repository secret only when an environment's workload
manifest contains a placeholder. The secret JSON may contain only keys whose
names begin with that environment in uppercase, for example
`DEV_ADB_ADMIN_PASSWORD` for `__DEV_ADB_ADMIN_PASSWORD__`.

```bash
gh secret set GITOPS_SECRET_VALUES_DEV --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_TEST --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_UAT --repo OWNER/nonprod-PROJECT
```

Configure only the secret-backed environments that the project will use. Do not
combine multiple environments in one bundle. Caller workflows never use `secrets: inherit` or
`toJSON(secrets)`; they pass one selected bundle to Platform CI.

GitHub Free private repositories provide procedural governance: restrict
administration and direct pushes, record an independent human PR review, and
verify the successful plan/check against the current commit before merge. This
MVP does not claim private-repository branch protection, enforced CODEOWNERS
review, or GitHub Environment approval. Use an organization runner group
restricted to the selected non-production project repositories. Keep the group
separate from production and add a repository only after its handoff is ready.
The private `platform-ci` repository is configured once to be accessible from
repositories in the organization through its Actions settings; new project
repositories inherit that access automatically. Its composite actions are
downloaded from `main` with GitHub's temporary scoped token, not a deploy key.

## Acceptance and audit

Complete the mandatory [repository-secret end-to-end verification](repository-secret-e2e.md)
before allowing workload requests. It verifies environment isolation and
fail-closed placeholder handling without applying infrastructure.

Audit configured names and access without reading secret values:

```bash
gh secret list --repo OWNER/nonprod-PROJECT
gh api repos/OWNER/nonprod-PROJECT/actions/permissions
gh api repos/OWNER/nonprod-PROJECT/actions/runners
gh api repos/OWNER/platform-ci/actions/permissions/access
```

For a future paid production-grade model, see
[final-environment-hardening.md](final-environment-hardening.md). It is a
separate hardened release path, not an unsupported switch in this MVP.
