# Optional Codex app assistant

The Cloud Operator plugin guides OP04 onboarding in the Codex app. It validates
the Git change, shows a preview, and requires confirmation before pushing a
branch or opening a pull request.

Copy `plugins/cloud-operator-gitops`, replace `__CUSTOMER_ORG__`, install it
through your approved Codex plugin process, and set `codex_app_plugin` to `true`
in the deployment contract. The operator needs the Codex app with local shell
access, authenticated GitHub CLI access, repository permission, and the
deployment contract generated during setup.

The assistant cannot merge or approve pull requests, control workflows, run
Terraform, call OCI, or create a project repository. Read-only work creates no
persistent local files. Normal GitHub pull requests remain fully supported
without the assistant.
