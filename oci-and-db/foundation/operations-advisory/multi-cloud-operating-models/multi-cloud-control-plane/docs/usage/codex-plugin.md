# Optional Codex plugin

Use the Project GitOps plugin to prepare a supported request conversationally from your handed-off project repository. It reads the approved catalog entry and OCI/Google handoff references. Azure inputs come from the explicit request or relevant existing resource JSON, with optional Markdown suggestions; Platform CI and the selected orchestrator validate the resulting manifest after the pull request is opened.

1. Open the project repository in Codex.
2. Describe one supported resource change or OCI lifecycle operation, including its environment and region.
3. For a change, provide the change reference required for every mutable request, such as `CRQ1234`.
4. For an OCI or Azure ADB, provide its existing secret OCID or let the skill propose preparing a dedicated secret in the handed-off Vault. Review and confirm that preparation separately. Use your authorized Project Team OCI profile; the skill asks only for its name and authentication method, never credentials. OCI generates the password inside Vault, and the skill inserts the returned OCID into the ADB manifest.
5. Review the proposed resource impact and GitHub writes.
6. Reply with standalone `confirm` when the GitHub preview is correct. Case does not matter. Confirmation of secret preparation does not authorize publication.
7. Follow the standard [request lifecycle](request-lifecycle.md) after the plugin opens the pull request.

Read-only status and monitoring requests do not need a CRQ and do not create Git changes.

During workflow monitoring, the skill reports the validation or post-merge execution phase, observed status, current job/step when GitHub exposes it, elapsed time when available, workflow link and next milestone. It updates on meaningful changes and about once per minute while unchanged. Composite steps may hide internal progress; the skill reports only the visible step and does not estimate completion percentages or remaining time. Successful checks still need the matching plan or execution evidence before the skill reports the result.

At the end of PR validation, the skill returns the declared configuration, planned resource actions and totals, differences from your request, current checks, evidence links, independent review and merge readiness. Declared settings are distinguished from plan-proven actions and unknown resolved values. Lifecycle requests show validated targets and actions instead of a Terraform plan. Missing matching evidence stays unverified even when checks are green.

After an independent human has approved the current PR version in GitHub, you may explicitly request `Merge PR #123` in the selected project repository. In Codex only, the skill rechecks the exact reviewed head and base, approval, checks, matching plan/check and repository restrictions, then uses a guarded merge commit and monitors its post-merge workflow. No extra `confirm` is needed for the same unchanged merge request. If the version, base or validation attempt changed, the skill refreshes its summary and waits for a new merge instruction. It never approves its own PR, bypasses restrictions, activates auto-merge or deletes the branch. A publication or secret-preparation confirmation does not authorize merge. The optional UI still requires merge through GitHub.

The plugin supports the resource requests listed in [Reference capabilities](../reference/support.md), published OCI lifecycle operations, and clearing an existing operation request. OCI Compute `deploy-agent` records a validated agent type and version on an exact state-backed Compute target; it does not install third-party software.

The plugin prepares Git changes and, in Codex only, can prepare a dedicated ADB secret after a separate confirmation. Its cloud exception is limited to OCI secret metadata lookup and native secret creation. It never accepts or reads a raw password, deploys resources, or changes the Vault, key or IAM. A secret remains if the ADB request is abandoned; retries recover its metadata before any further creation. The optional web UI still requires an existing secret OCID and cannot use host cloud credentials. Cloud Operations supplies the foundation and access; Project Team owns the secret preparation and ADB request. If the plugin is not available, ask Cloud Operations to complete the [optional Codex setup](../installation/optional-interfaces.md#optional-codex-plugin).
