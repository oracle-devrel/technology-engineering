# GitHub Environment end-to-end verification

This mandatory acceptance test validates the `github-environments` profile
without applying infrastructure.

Set `security_profile` to `github-environments`. Create the `dev` base
Environment without required reviewers and the `dev-apply` Environment with
the required apply reviewers and prevention of self-review where supported.
In both Environments, set `READINESS_MARKER` to `true` and set
`GITOPS_SECRET_VALUES` to the same JSON object containing
`DEV_E2E_TEST_VALUE`. At repository scope, create the required non-sensitive
sentinels `READINESS_MARKER=false` and
`GITOPS_SECRET_VALUES={"INVALID":"true"}`. Never put real values in these
repository secrets.

Create a disposable dev manifest containing `__DEV_E2E_TEST_VALUE__`, then
open a pull request limited to one `oci/dev/<region>` tuple.

Confirm that the default-branch caller invokes pinned Platform CI, the reusable
job declares the `dev` GitHub Environment, the Environment values override the
repository sentinels, the placeholder resolves, the dev runner labels and state
key are selected, and Terraform reaches plan. Do not merge the test PR. Confirm
that plan is not reviewer-gated and creates no deployment record.

Before permitting a real merge, run a harmless reusable-workflow contract test
against `dev-apply`: confirm that the job waits for its configured reviewer,
uses the `dev-apply` copy of the secrets, and creates a deployment record after
approval. Do not run Terraform apply as part of this acceptance test.

Create `uat` and `uat-apply` in the same way, but omit `UAT_E2E_TEST_VALUE` from
both copies of `GITOPS_SECRET_VALUES`. Open a second PR with a disposable UAT
manifest containing `__UAT_E2E_TEST_VALUE__`. Variable preparation must fail
closed before Terraform. Confirm that the run declares the `uat` Environment,
selects UAT runner labels, and does not use the dev state key or secret bundle.

Also confirm that a dev manifest containing `__UAT_E2E_TEST_VALUE__` fails as a
cross-environment reference. Temporarily remove `READINESS_MARKER` from `dev`
and confirm that the repository sentinel does not permit the job to proceed.
Restore it, then repeat with `GITOPS_SECRET_VALUES` removed and confirm that the
invalid repository sentinel fails the environment-qualified secret-name check.

Live testing on GitHub Actions on 17 July 2026 confirmed this contract. The
reusable workflow intentionally declares both secret names under
`on.workflow_call.secrets`, and the protected caller intentionally passes the
same-named repository sentinels. A live GitHub acceptance test is required
because GitHub does not deliver the selected Environment secret to a called
workflow when either part of that channel is absent. When both are present, the
job's Environment value overrides the caller sentinel. Verify this behavior in
the disposable repository after any workflow-contract change.

Close both PRs and remove the disposable members. Keep the sentinels, but do not
configure `GITOPS_SECRET_VALUES_DEV`, `GITOPS_SECRET_VALUES_TEST`,
`GITOPS_SECRET_VALUES_UAT`, or `CONTROL_PLANE_READY_*` in this profile.
