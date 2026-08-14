# Project Team guide

Use this guide after Cloud Operations gives you a prepared project repository.
You can create, change, or remove approved resources and run supported lifecycle
operations without deployment credentials or a different process for each
cloud. Every request follows the same reviewed pull-request workflow.

## 1. Choose an interface

Each interface prepares the same Git change and pull request. It cannot approve,
merge, or deploy the request.

| Interface | Use it when | Guide |
| --- | --- | --- |
| GitHub interface | You want to edit JSON through the GitHub website or GitHub CLI. | [GitHub interface](github-interface.md) |
| Optional UI | You prefer a guided form. | [Optional UI](optional-ui.md) |
| Optional Codex plugin | You prefer a conversational request. | [Codex plugin](codex-plugin.md) |

## 2. Identify your repository

| Repository | Environments | Secret placeholder prefix |
| --- | --- | --- |
| `nonprod-<project>` | `dev`, `test`, `uat` | `DEV_`, `TEST_`, `UAT_` |
| `prod-<project>` | `prod` only | `PROD_` |

State is isolated by repository, cloud, environment, and region. Production
also has a separate handoff, secret bundle, and runner boundary. Cloud
Operations prepares those controls. Project Teams manage resource manifests and
their review ownership, using only the approved handoff and
environment-qualified placeholders.

## 3. Follow the request flow

1. Check that MCCP [supports the resource or operation](../reference/support.md).
2. Choose the approved catalog template and use only the foundation references
   from your environment handoff.
3. Open a pull request through your chosen interface.
4. Review the planned result and obtain human approval.
5. Merge through the governed process and verify the result.

The [request lifecycle](request-lifecycle.md) contains the detailed rules,
manifest paths, removal steps, and troubleshooting guidance.
