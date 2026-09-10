# Optional Codex plugin

Use the Project GitOps plugin to prepare a supported request conversationally
from your handed-off project repository. It reads the repository handoff and
approved catalog entry; Platform CI and the selected orchestrator validate the
resulting manifest after the pull request is opened.

1. Open the project repository in Codex.
2. Describe one supported resource change or OCI lifecycle operation, including
   its environment and region.
3. For a change, provide the change reference required for every mutable
   request, such as `CRQ1234`.
4. Review the proposed resource impact and GitHub writes.
5. Reply with standalone `confirm` when the preview is correct. Case does not
   matter.
6. Follow the standard [request lifecycle](request-lifecycle.md) after the
   plugin opens the pull request.

Read-only status and monitoring requests do not need a CRQ and do not create
Git changes.

The plugin supports the resource requests listed in
[Reference capabilities](../reference/support.md), published OCI lifecycle
operations, and clearing an existing operation request. OCI Compute
`deploy-agent` records a validated agent type and version on an exact
state-backed Compute target; it does not install third-party software.

The plugin prepares Git changes only; it never calls a cloud API or accepts a
raw password. If it is not available, ask Cloud Operations to complete the
[optional Codex setup](../installation/optional-interfaces.md#optional-codex-plugin).
