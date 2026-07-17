# Environment-secret end-to-end verification

This mandatory installation acceptance test exercises the real GitHub
Environment boundary without applying infrastructure.

Create a temporary dev manifest with one synthetic placeholder and add its
mapping only to the `dev` Environment's `GITOPS_SECRET_VALUES`; set
`READINESS_MARKER` there too. Open a pull request limited to one
`oci/dev/<region>` tuple and confirm the reusable Terraform workflow reaches
the plan after variable preparation.

Submit the same placeholder under `uat` without a UAT mapping. **Prepare
variables** must fail closed before Terraform with an unresolved-placeholder
error. Confirm that the failed run used UAT runner labels and did not access the
dev state key or secret. Delete both test PRs and their test secrets afterwards.
Caller workflows must remain free of `secrets: inherit`; Platform CI receives
only the selected environment's secrets because its reusable job declares that
environment.
