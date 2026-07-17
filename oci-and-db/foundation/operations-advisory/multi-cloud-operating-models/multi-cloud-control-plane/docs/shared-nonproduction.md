# Shared non-production repository model

New projects use exactly one repository, `oe-nonprod-<project>`, governed by
the `shared-nonprod-v2` contract. Production is not part of this installation.
Allowed lowercase environments are `dev`, `test`, and `uat`; `prod`,
`production`, `prd`, and `live` are rejected.

The protected `control-plane.json` maps each environment to its GitHub
Environment, CODEOWNERS, cloud-specific runner labels, supported clouds, and
handoff. Workflows do not infer the layout from a path: the protected caller
resolves one cloud/environment/region tuple and passes it to Platform CI.
State keys are `<bucket>/<owner>/<repository>/<cloud>/<environment>/<region>/terraform.tfstate`.

For every enabled GitHub Environment, create environment-scoped placeholder
secrets and a non-empty `CONTROL_PLANE_READY` marker with that same name in
each distinct GitHub Environment. A missing
marker must fail closed. Placeholder names must be environment-qualified and
may not reference a different environment. Plan/check selects the environment
without deployment recording; apply/execute records the deployment.

Use `gh api` to audit the controls after configuration:

```bash
gh api repos/OWNER/oe-nonprod-PROJECT/environments
gh api repos/OWNER/oe-nonprod-PROJECT/branches/main/protection
gh api repos/OWNER/oe-nonprod-PROJECT/actions/permissions
```

Enterprise installations should require environment reviewers, prevent
self-review, require CODEOWNERS and passing checks, and isolate runners. On
Pro/Team, private-repository required environment reviewers are unavailable:
use environment secrets, CODEOWNERS, branch protection, pinned trusted
workflows, and runner isolation, while recognizing the weaker pre-plan approval
guarantee. GitHub Free private repositories are unsupported because environment
secrets are unavailable.
