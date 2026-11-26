# Project Team guide

Use MCCP to request approved cloud resources and operations from your project repository. You can see what the change will do, get it reviewed and find the result in GitHub.

## What you need

- Your project repository and access from Cloud Operations. Use `nonprod-<project>` for `dev`, `test` or `uat`, and `prod-<project>` for `prod`.
- One [supported resource or operation](../reference/support.md) in one cloud, environment and region. Your project handoff describes the approved OCI or Google Cloud foundation. For Azure, use the existing foundation details supplied for the request.
- A change reference such as `CRQ1234` for the optional UI or Codex, or the reference required by your organization when using GitHub. For a first request, coordinate the [first-project check](../reference/verify-secret-isolation.md) with Cloud Operations.

## Choose how to request a change

| If you prefer | Use |
| --- | --- |
| Editing the request file directly | [GitHub website or CLI](github-interface.md) |
| Filling in a form | [Optional UI](optional-ui.md) |
| Describing what you need in a conversation | [Optional Codex plugin](codex-plugin.md) |

## From request to result

1. Pick an approved template and supply the project details it needs. For a database that requires a password, put the approved secret reference in the request.
2. Open a pull request in GitHub. Check that the plan or operation check shows the intended change.
3. Get approval from an independent reviewer, then merge through the approved process.
4. Open the post-merge workflow from GitHub and verify the outcome.

Follow the [request lifecycle](request-lifecycle.md) for review, verification, removal and troubleshooting, or walk through a [private OCI database request](oci-adb-walkthrough.md) with sample values.
