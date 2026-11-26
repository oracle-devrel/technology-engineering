# Optional Codex plugin

Describe an approved resource or lifecycle change to Project GitOps in Codex. The plugin prepares a pull request, follows its validation and shows you the evidence.

## Prepare and publish

1. Open the handed-off project repository in Codex. Give the cloud, environment, region, requested change and a change reference such as `CRQ1234`.
2. Supply any missing catalog inputs. For OCI and Google Cloud, use the approved handoff. For Azure, use the existing foundation details in the request or resource JSON.
3. For an OCI or Azure Autonomous Database, give its dedicated Vault secret OCID. If you need a new secret, review and separately confirm its preparation. Use your approved OCI profile and authentication method. OCI generates the password in Vault and the skill inserts the returned identifier.
4. Review the proposed resource actions and GitHub changes. Reply with `confirm` on its own line when ready to publish. This is a separate confirmation from secret preparation.

Read-only inventory and status requests need no change reference. Each database secret remains in Vault if you abandon its request. The skill checks metadata before retrying a secret creation whose result is uncertain.

## Merge and verify

The skill shows the GitHub workflow, its visible status and the evidence for the current validation. During a run, expect an update when the visible state changes and about once a minute while it stays the same. Its decision summary distinguishes declared settings from planned resource actions, unknown values and deviations. A lifecycle check reports the intended targets and actions. Treat evidence as unverified when the matching report is missing, even if the checks are green.

After an independent human approves the current version in GitHub, you can explicitly ask Codex to merge the exact PR, such as `Merge PR #123`. The skill rechecks the revision, base, approval, checks, evidence and repository restrictions. A changed revision, base or validation attempt requires a fresh decision summary and a new merge instruction. On merge, the skill follows the workflow for the actual merge commit. Approval stays with the reviewer and a merge request authorizes only that PR.

The optional UI uses GitHub for merge and requires an existing secret OCID. See the [common request lifecycle](request-lifecycle.md) or the [plugin installation guide](../installation/optional-interfaces.md#optional-codex-plugin).
