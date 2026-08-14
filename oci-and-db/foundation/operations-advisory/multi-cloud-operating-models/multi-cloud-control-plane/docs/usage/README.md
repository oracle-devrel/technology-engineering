# Project Team guide

Use this guide after Cloud Operations gives you a prepared project repository.
You manage approved resources through pull requests; Cloud Operations retains
the cloud credentials, runners, repository controls, and foundation setup.

## 1. Identify your repository

| Repository | Environments | Secret placeholder prefix |
| --- | --- | --- |
| `nonprod-<project>` | `dev`, `test`, `uat` | `DEV_`, `TEST_`, `UAT_` |
| `prod-<project>` | `prod` only | `PROD_` |

State is isolated by repository, cloud, environment, and region. Production
also has a separate handoff, review ownership, secret bundle, and runner
boundary. Cloud Operations prepares those controls; Project Teams use only the
handoff and environment-qualified placeholders.

## 2. Choose an interface

Each interface prepares the same Git change and pull request. It cannot approve,
merge, or deploy the request.

| Interface | Use it when | Guide |
| --- | --- | --- |
| GitHub interface | You want to edit JSON through GitHub or GitHub CLI. | [GitHub interface](github-interface.md) |
| Optional UI | You prefer a guided form. | [Multi-Cloud Plane UI](optional-ui.md) |
| Optional Codex plugin | You prefer a conversational request. | [Codex plugin](codex-plugin.md) |

## 3. Follow the request lifecycle

The [request lifecycle](request-lifecycle.md) is the single source for request
rules, manifest paths, review, merge, deletion, and troubleshooting. Check
[what MCCP supports](../reference/support.md) before preparing a request.
