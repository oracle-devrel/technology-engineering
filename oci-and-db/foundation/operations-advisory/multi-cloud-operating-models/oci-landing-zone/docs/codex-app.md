# Optional Codex app assistant

The Cloud Operator plugin guides OP04 onboarding and the validated project
handoff in the Codex app. It validates Git changes and both handoff artifacts,
shows a preview, and requires a separate confirmation before each repository
creation, branch push, or pull request.

Copy `plugins/cloud-operator-gitops`, replace `__CUSTOMER_ORG__`, install it
through your approved Codex plugin process, and set `codex_app_plugin` to `true`
in the deployment contract. The operator needs the Codex app with local shell
access, authenticated GitHub CLI access, repository permission, and the
deployment contract generated during setup.

After a successful human-merged OP04 run, the assistant may create only the
exact private target repository from the contract-pinned template when it is
absent. It reuses an existing validated shared non-production repository for
additional environment handoffs and writes only
`environments/<environment>/environment_information.md` through a pull
request. It cannot merge or approve pull requests, control workflows, run
Terraform, or call OCI. Read-only work creates no persistent local files.
Normal GitHub pull requests remain fully supported without the assistant.
