# Verify first-project delivery

Cloud Operations and the Project Team use the first intended request to check the handed-off project. Use an enabled cloud, environment and region and the approved inputs for that request.

## Acceptance

| Check | Evidence |
| --- | --- |
| The project is ready | The approved handoff supplies OCI or Google Cloud inputs. For Azure, check the existing foundation inputs in the request or JSON and the configured runner. |
| The request reaches the intended scope | Open its pull request and confirm the expected runner and state scope. The plan or lifecycle check succeeds for the current revision. |
| The planned change matches the request | Review the safe resource-action report or validated targets. Check declared settings in the manifest diff and confirm the evidence contains only safe details. |
| The first use of a secret follows the approved path | Check the native reference and runner access when a request first uses a secret. |
| The Terraform job cleans up private files | Confirm that the run removed any private variable files it created, including for requests without secrets. |

Treat plan files and state as sensitive. Use the first intended request and its prerequisites for this check. Merge only after independent approval for the actual workload change. Close a disposable validation pull request without merging it.

## What this proves

This check verifies the routing and delivery path exercised by the request. IAM isolation depends on runner identities. A database connection or wallet test verifies a separate outcome. [Security and secret delivery](security.md#secret-delivery)

## Platform regression qualification

When Platform CI secret handling changes, run the existing resolver and workflow regressions for malformed references, denied reads, unavailable versions, removed password fields, unresolved placeholders and cleanup after failure. Do this as part of platform qualification.
