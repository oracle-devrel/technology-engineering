# Production repository model

Production uses a dedicated `prod-<project>` repository created from
`components/prod-project-template`. Its `production-v1` contract permits
only the `prod` deployment environment and manifest paths of the form
`<cloud>/prod/<region>/...`. Terraform state, runner labels, CODEOWNERS and
handoffs are therefore separate from `nonprod-<project>`.

Publish the prepared `prod-project-template` repository from the deployment
runbook and create `prod-<project>` from that exact pinned template. Replace
`__PROJECT__`, install the verified production handoff at
`environments/prod/environment_information.md`, and configure:

```bash
gh secret set GITOPS_SECRET_VALUES_PROD --repo OWNER/prod-PROJECT
gh variable set CONTROL_PLANE_READY_PROD --body true --repo OWNER/prod-PROJECT
```

The secret command prompts for the JSON bundle value; never put its literal
members on a command line or in Git.

Create a dedicated production approver team before creating the repository,
replace `__PROJECT__` in the template, configure the repository secret
`GITOPS_SECRET_VALUES_PROD`, and set `CONTROL_PLANE_READY_PROD` to `true`.
Every bundle key and runtime placeholder must begin with `PROD_`. Require
independent approval, code-owner review, passing plans, and isolated production
runners. Run the
[repository-secret end-to-end verification](repository-secret-e2e.md) against
production with a disposable manifest before accepting a real production request.
