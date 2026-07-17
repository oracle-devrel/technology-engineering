# Shared non-production repository model

New projects use exactly one repository, `nonprod-<project>`, governed by the
`shared-nonprod-v2` contract. Allowed lowercase environments are `dev`, `test`,
and `uat`; `prod`, `production`, `prd`, and `live` are rejected.

The protected `control-plane.json` declares one repository-wide
`security_profile`: `github-environments` or `repository-secrets`. It also maps
each environment to CODEOWNERS, cloud-specific runner labels, supported clouds,
the handoff path, and the Free-profile secret and readiness names. Never mix
profiles inside one repository.

The trusted default-branch caller resolves one cloud/environment/region tuple,
validates the profile, and passes both to pinned Platform CI. Both profiles use
the same `pull_request_target` same-repository guard, manifest-only diff,
regular-file and JSON validation, environment-qualified placeholders, pinned
refs, runner routing, concurrency, and state key:
`<bucket>/<owner>/<repository>/<cloud>/<environment>/<region>/terraform.tfstate`.

## Recommended paid-plan profile: GitHub Environments

Set `security_profile` to `github-environments`. For every enabled logical
environment, create a base GitHub Environment (`dev`, `test`, or `uat`) for
plan/check and a matching `<environment>-apply` Environment for apply/execute.
The base has no required reviewers. Configure required reviewers and prevention
of self-review on the apply Environment where supported. In both members of
each pair create identical copies of:

- `GITOPS_SECRET_VALUES`: a JSON object whose names begin with that Environment
  in uppercase, such as `DEV_ADB_ADMIN_PASSWORD` for
  `__DEV_ADB_ADMIN_PASSWORD__`.
- `READINESS_MARKER`: the exact value `true`.

The reusable job declares the base Environment with deployment recording
disabled for plan/check and declares `<environment>-apply` for apply/execute.
Protect `main`, require CODEOWNERS and successful checks, and isolate runner
groups. On Enterprise private repositories, the apply Environment's required
reviewers and prevention of self-review add the enforcement boundary; these
controls are not available for private repositories on Pro/Team. Apply and
execute jobs create the auditable deployment history. These controls make this
the recommended paid-plan profile.

Also create repository secrets named `GITOPS_SECRET_VALUES` with the exact
value `{"INVALID":"true"}` and `READINESS_MARKER` with the exact value `false`. These are
non-sensitive fail-closed sentinels for GitHub's reusable-workflow secret
channel, not credential storage. The selected Environment overrides them. Keep
the base/apply secret copies synchronized after every rotation.

Configure the secrets interactively; never put their values on the command
line or in Git:

```bash
gh secret set GITOPS_SECRET_VALUES --env dev --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env dev --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env dev-apply --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env dev-apply --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env test --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env test --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env test-apply --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env test-apply --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env uat --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env uat --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env uat-apply --repo OWNER/nonprod-PROJECT
gh secret set READINESS_MARKER --env uat-apply --repo OWNER/nonprod-PROJECT
printf '{"INVALID":"true"}\n' | gh secret set GITOPS_SECRET_VALUES --repo OWNER/nonprod-PROJECT
printf 'false\n' | gh secret set READINESS_MARKER --repo OWNER/nonprod-PROJECT
```

Complete the mandatory
[GitHub Environment end-to-end verification](environment-secret-e2e.md) before
allowing workload requests.

## GitHub Free fallback: repository secrets

Set `security_profile` to `repository-secrets`. For each enabled environment,
create one Actions repository secret: `GITOPS_SECRET_VALUES_DEV`,
`GITOPS_SECRET_VALUES_TEST`, or `GITOPS_SECRET_VALUES_UAT`. Create the matching
repository variable `CONTROL_PLANE_READY_DEV`, `CONTROL_PLANE_READY_TEST`, or
`CONTROL_PLANE_READY_UAT` with the exact value `true`.

Caller workflows pass exactly one named bundle and readiness value to Platform
CI. They never use `secrets: inherit` or `toJSON(secrets)`.

```bash
gh secret set GITOPS_SECRET_VALUES_DEV --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_TEST --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_UAT --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_DEV --body true --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_TEST --body true --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_UAT --body true --repo OWNER/nonprod-PROJECT
```

GitHub Free private repositories cannot enforce the same private branch
protection, CODEOWNERS review, or Environment approval controls as paid plans.
Restrict repository administration and direct pushes by policy, record a human
PR review, and isolate runner groups. This fallback has procedural approval,
not the paid profile's enforceable approval boundary.

Complete the mandatory
[repository-secret end-to-end verification](repository-secret-e2e.md) before
allowing workload requests.

## Audit

Audit configured names and access without reading secret values:

```bash
gh secret list --env dev --repo OWNER/nonprod-PROJECT
gh secret list --repo OWNER/nonprod-PROJECT
gh variable list --repo OWNER/nonprod-PROJECT
gh api repos/OWNER/nonprod-PROJECT/actions/permissions
gh api repos/OWNER/nonprod-PROJECT/actions/runners
gh api repos/OWNER/platform-ci/actions/permissions/access
```

On paid plans also audit branch protection:

```bash
gh api repos/OWNER/nonprod-PROJECT/branches/main/protection
```

OCI Vault can become the system of record later, but it is not a secret source
in this release. That evolution requires a pinned resolver, Instance Principal
policy, approved Vault OCID mappings, masking, and separate fail-closed tests.
