# Project Team guide

Use this guide after Cloud Operations gives you a prepared project repository. You can declare or remove approved resources, add published NSG rules, and run supported lifecycle operations without deployment credentials or a different process for each cloud. Every request follows the same reviewed pull-request workflow.

## 1. Check that you are ready

Before choosing an interface, confirm that you:

- have write access to a handed-off project repository;
- are requesting something in [Reference capabilities](../reference/support.md);
- have selected one cloud, environment and region, using the OCI/Google handoff or the Azure request inputs and prepared runner;
- have agreed the [first-project check](../reference/verify-secret-isolation.md) with Cloud Operations; and
- have a change reference such as `CRQ1234` when using the optional UI or Codex plugin, or follow your organization's requirements when working directly in GitHub.

## 2. Choose an interface

Each interface follows the same governed pull-request lifecycle. A human reviewer approves the request in GitHub, and the trusted runner executes it after merge. The optional UI directs users to GitHub to merge. The Codex plugin can merge an exact pull request on explicit instruction after verifying its current independent approval and checks. The optional UI and Codex plugin render only published catalog capabilities. See the [trust boundary](../reference/architecture.md#execution-and-trust-boundary).

| Interface | Use it when | Guide |
| --- | --- | --- |
| GitHub interface | You want to edit JSON through the GitHub website or GitHub CLI. | [GitHub interface](github-interface.md) |
| Optional UI | You prefer a guided form. | [Optional UI](optional-ui.md) |
| Optional Codex plugin | You prefer a conversational request. | [Codex plugin](codex-plugin.md) |

## 3. Identify your repository

| Repository | Environments |
| --- | --- |
| `nonprod-<project>` | `dev`, `test`, `uat` |
| `prod-<project>` | `prod` only |

Production has its own repository, handoff, and approval path. Cloud Operations owns the state, secret, and runner boundaries behind both; you work with manifests, approved foundation inputs and your review ownership. The [architecture](../reference/architecture.md#repository-model) describes those boundaries if you need them.

## 4. Follow the request flow

1. Choose the approved catalog template. Use the OCI/Google handoff for foundation references; Azure inputs come from the request or relevant existing JSON, with optional Markdown suggestions. Never invent references or reuse another database's secret.
2. Open a pull request through your chosen interface and record the change reference before review.
3. Review the planned result and obtain human approval.
4. Merge through the governed process and verify the result.

The [request lifecycle](request-lifecycle.md) contains the detailed rules, manifest paths, removal steps, and troubleshooting guidance.

## 5. Follow a first worked example

To see one complete request without using customer values, follow the [private OCI Autonomous Database walkthrough](oci-adb-walkthrough.md). It shows the manifest, pull-request, review, and verification flow using only placeholders and sample names.
