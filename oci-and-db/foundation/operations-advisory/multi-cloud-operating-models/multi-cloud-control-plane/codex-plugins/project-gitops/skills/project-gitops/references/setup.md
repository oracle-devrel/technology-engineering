# Setup

1. Read the project repository `origin` before every operation. Accept only a
   GitHub origin for a handed-off private `nonprod-<project>` or
   `prod-<project>` repository at exact `main`. The origin supplies the
   customer organization, and the completed environment handoff establishes
   readiness.
2. Use `<customer-org>/gitops-templates` at `main`. Its `resources-catalog`
   provides the current approved templates. If the catalog cannot be retrieved,
   stop and provide the validator error code to Cloud Operations.
3. A template-only `.github/CODEOWNERS.template` is valid; Project Team owns
   its active CODEOWNERS configuration.
4. Before proposing a manifest with a secret placeholder, require the repository
   secret `GITOPS_SECRET_VALUES_<ENVIRONMENT>`. Use `GITOPS_SECRET_VALUES_DEV`
   for `dev`, `GITOPS_SECRET_VALUES_TEST` for `test`,
   `GITOPS_SECRET_VALUES_UAT` for `uat`, and `GITOPS_SECRET_VALUES_PROD` for
   `prod`. Its value is a JSON object. For an OCI ADB placeholder
   `__DEV_ADB_ADMIN_PASSWORD__`, the required shape is:

   ```json
   {"DEV_ADB_ADMIN_PASSWORD":"<ADB_ADMIN_PASSWORD>"}
   ```

   The key omits the surrounding double underscores and starts with the
   environment in uppercase. Tell the repository administrator which secret to
   create, but never request, print, or set its value.
