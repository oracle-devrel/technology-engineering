# Project Team guide

Use this guide after Cloud Operations gives you a prepared project repository.
You can create, change, or remove approved resources and run supported lifecycle
operations without deployment credentials or a different process for each
cloud. Every request follows the same reviewed pull-request workflow.

## 1. Check that you are ready

Before choosing an interface, confirm that you:

- have write access to a handed-off project repository;
- are requesting something in the [current MVP scope](../reference/support.md);
- have selected one cloud, environment, and region from your environment
  handoff; and
- have any change reference your organisation requires, such as `CRQ1234`, to
  record in the pull request.

## 2. Choose an interface

Each interface prepares the same Git change and pull request, and none of them
can approve, merge, or deploy it — see the
[trust boundary](../reference/architecture.md#execution-and-trust-boundary).

| Interface | Use it when | Guide |
| --- | --- | --- |
| GitHub interface | You want to edit JSON through the GitHub website or GitHub CLI. | [GitHub interface](github-interface.md) |
| Optional UI | You prefer a guided form. | [Optional UI](optional-ui.md) |
| Optional Codex plugin | You prefer a conversational request. | [Codex plugin](codex-plugin.md) |

## 3. Identify your repository

| Repository | Environments | Placeholder prefix |
| --- | --- | --- |
| `nonprod-<project>` | `dev`, `test`, `uat` | `__DEV_`, `__TEST_`, `__UAT_` |
| `prod-<project>` | `prod` only | `__PROD_` |

Production has its own repository, handoff, and approval path. Cloud Operations
owns the state, secret, and runner boundaries behind both; you work with
manifests, the approved handoff values, and your review ownership. The
[architecture](../reference/architecture.md#repository-model) describes those
boundaries if you need them.

## 4. Follow the request flow

1. Choose the approved catalog template and use only the foundation references
   from your environment handoff.
2. Open a pull request through your chosen interface and record the change
   reference before review.
3. Review the planned result and obtain human approval.
4. Merge through the governed process and verify the result.

The [request lifecycle](request-lifecycle.md) contains the detailed rules,
manifest paths, removal steps, and troubleshooting guidance.
