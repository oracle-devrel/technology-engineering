# GitHub Environment end-to-end verification

This mandatory acceptance test validates the `github-environments` profile
without applying infrastructure.

Set `security_profile` to `github-environments`. In the `dev` GitHub
Environment, set `READINESS_MARKER` to `true` and set `GITOPS_SECRET_VALUES` to
a JSON object containing `DEV_E2E_TEST_VALUE`. Create a disposable dev manifest
containing `__DEV_E2E_TEST_VALUE__`, then open a pull request limited to one
`oci/dev/<region>` tuple.

Confirm that the default-branch caller invokes pinned Platform CI, the reusable
job declares the `dev` GitHub Environment, the placeholder resolves, the dev
runner labels and state key are selected, and Terraform reaches plan. Do not
merge the test PR. Confirm that the Environment requires its reviewer where
configured and that the plan job does not create a deployment record; only
post-merge apply jobs record deployments.

In the `uat` GitHub Environment, set `READINESS_MARKER` to `true` but omit
`UAT_E2E_TEST_VALUE` from `GITOPS_SECRET_VALUES`. Open a second PR with a
disposable UAT manifest containing `__UAT_E2E_TEST_VALUE__`. Variable
preparation must fail closed before Terraform. Confirm that the run declares
the `uat` Environment, selects UAT runner labels, and does not use the dev state
key or secret bundle.

Also confirm that a dev manifest containing `__UAT_E2E_TEST_VALUE__` fails as a
cross-environment reference. Close both PRs and remove the disposable members.
Do not configure the repository-secret bundles or readiness variables in this
profile.
