# Verify environment secret isolation

Run this acceptance test after Cloud Operations hands off the first project
repository and before the Project Team submits a workload request. The test
reaches Terraform plan but does not deploy infrastructure.

## Successful environment

1. Create a disposable `dev` manifest containing `__DEV_E2E_TEST_VALUE__`.
2. Add `DEV_E2E_TEST_VALUE` to the JSON repository secret
   `GITOPS_SECRET_VALUES_DEV`.
3. Open a pull request limited to one `oci/dev/<region>` path.
4. Confirm that the workflow selects the dev runner and state, resolves the
   value, and reaches Terraform plan.
5. Do not merge the pull request.

## Isolated environment

1. Create a disposable `uat` manifest containing `__UAT_E2E_TEST_VALUE__`
   without adding that key to `GITOPS_SECRET_VALUES_UAT`.
2. Open a pull request limited to one `oci/uat/<region>` path.
3. Confirm that variable preparation fails before Terraform, selects the UAT
   runner, and does not use dev state.
4. Confirm that a dev manifest containing `__UAT_E2E_TEST_VALUE__` also fails.

Caller workflows must not contain `secrets: inherit` or `toJSON(secrets)` and
must pass only the selected repository secret to Platform CI. Neither test run
may attach to or create a GitHub Environment.

Close both pull requests and remove the test keys from the repository secrets.
