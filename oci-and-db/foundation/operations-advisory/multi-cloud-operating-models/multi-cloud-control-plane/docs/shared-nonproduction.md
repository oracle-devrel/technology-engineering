# Shared non-production repository model

New projects use exactly one repository, `nonprod-<project>`, governed by the
`shared-nonprod-v2` contract. Allowed lowercase environments are `dev`, `test`,
and `uat`; `prod`, `production`, `prd`, and `live` are rejected.

The protected `control-plane.json` maps each environment to its repository
secret bundle, readiness variable, CODEOWNERS, cloud-specific runner labels,
supported clouds, and handoff. The trusted default-branch caller resolves one
cloud/environment/region tuple and passes it to Platform CI. State keys are
`<bucket>/<owner>/<repository>/<cloud>/<environment>/<region>/terraform.tfstate`.

For each enabled environment, create one Actions repository secret in that
project repository: `GITOPS_SECRET_VALUES_DEV`,
`GITOPS_SECRET_VALUES_TEST`, or `GITOPS_SECRET_VALUES_UAT`. Its value is a JSON
object whose keys and manifest placeholders start with the selected uppercase
environment. For example, `DEV_ADB_ADMIN_PASSWORD` resolves
`__DEV_ADB_ADMIN_PASSWORD__`. Do not combine environments in one secret.

Also create the matching repository variable `CONTROL_PLANE_READY_DEV`,
`CONTROL_PLANE_READY_TEST`, or `CONTROL_PLANE_READY_UAT` with the exact value
`true`. A missing secret or readiness variable fails closed. Caller workflows
select exactly one bundle and never use `secrets: inherit`.

For a trial organization, publish private `platform-ci`, `gitops-templates`,
and `nonprod-project-template` repositories from the deployment runbook. Then
configure each project repository directly:

```bash
gh secret set GITOPS_SECRET_VALUES_DEV --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_TEST --repo OWNER/nonprod-PROJECT
gh secret set GITOPS_SECRET_VALUES_UAT --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_DEV --body true --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_TEST --body true --repo OWNER/nonprod-PROJECT
gh variable set CONTROL_PLANE_READY_UAT --body true --repo OWNER/nonprod-PROJECT
```

Each `gh secret set` command prompts for the JSON value. Do not pass a literal
secret value on the command line, store it in a file, or commit it. Do not use
an organization secret or a single cross-environment bundle.

Audit the configured names and repository access without reading secret values:

```bash
gh secret list --repo OWNER/nonprod-PROJECT
gh variable list --repo OWNER/nonprod-PROJECT
gh api repos/OWNER/nonprod-PROJECT/actions/permissions
gh api repos/OWNER/nonprod-PROJECT/actions/runners
gh api repos/OWNER/platform-ci/actions/permissions/access
```

Confirm that only the enabled environment bundles and readiness variables are
present, Actions is enabled, runner registration matches the intended boundary,
and Platform CI is accessible to the project repository.

## GitHub Free security profile

GitHub Free private repositories are supported by this repository-secret
profile. PR evaluation uses the workflow from the default branch, rejects
forks and non-manifest changes, and sends only validated JSON to pinned Platform
CI. Apply creates and applies one exact saved binary plan after merge.

GitHub Free private repositories do not provide the same enforceable private
branch protection, CODEOWNERS review, or Environment approval controls as paid
plans. Keep repository administration restricted, prohibit direct pushes by
policy, require human PR review, and isolate runner groups. This is a weaker
governance guarantee than the paid profile; it cannot prevent a repository
administrator from bypassing process.

## Paid-plan and Vault evolution

On GitHub Pro/Team or Enterprise, add private-repository branch protection,
required status checks, CODEOWNERS approval, and—where the plan supports
them—GitHub Environment reviewers, prevention of self-review, and
environment-scoped secrets. Moving secret resolution from the repository
bundles to GitHub Environment secrets is a separately reviewed workflow change;
do not create both sources and assume automatic precedence.

Audit paid-plan protection with:

```bash
gh api repos/OWNER/nonprod-PROJECT/branches/main/protection
```

OCI Vault can become the system of record later, but it is not a drop-in source
in this release. A Vault evolution requires a pinned Platform CI resolver,
Instance Principal `read secret-bundles` policy, approved Vault OCID mappings,
masking, and fail-closed tests before Terraform. No GitHub App is required for
the current repository-secret profile.

Complete the mandatory [repository-secret end-to-end verification](repository-secret-e2e.md)
before allowing real workload requests.
