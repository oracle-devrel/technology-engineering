# Repository-secret end-to-end verification

This mandatory installation acceptance test checks environment isolation
without applying infrastructure.

Create a disposable `dev` JSON manifest containing
`__DEV_E2E_TEST_VALUE__`. Add `DEV_E2E_TEST_VALUE` to the JSON value of the
project repository secret `GITOPS_SECRET_VALUES_DEV`, and set
`CONTROL_PLANE_READY_DEV` to `true`. Open a pull request limited to one
`oci/dev/<region>` tuple. Confirm that the default-branch caller invokes the
pinned reusable workflow, selects the dev runner labels and state key, prepares
the variable, and reaches Terraform plan. Do not merge this test PR.

Create a second disposable `uat` manifest containing
`__UAT_E2E_TEST_VALUE__`, but do not add `UAT_E2E_TEST_VALUE` to
`GITOPS_SECRET_VALUES_UAT`. Set `CONTROL_PLANE_READY_UAT` to `true` and open a
PR limited to one `oci/uat/<region>` tuple. **Prepare variables** must fail
closed before Terraform with an unresolved-placeholder error. Confirm that the
run selected UAT runner labels and did not use the dev state key.

Also verify that a dev manifest containing `__UAT_E2E_TEST_VALUE__` fails as a
cross-environment placeholder. Caller workflows must contain neither
`secrets: inherit` nor `toJSON(secrets)`; they pass exactly one named repository
secret to Platform CI.

Close both test PRs and remove the test members from the repository secret JSON
objects. This procedure validates the GitHub Free repository-secret profile.
OCI Vault and paid-plan GitHub Environment secrets require their own acceptance
tests if a later release implements either source.
