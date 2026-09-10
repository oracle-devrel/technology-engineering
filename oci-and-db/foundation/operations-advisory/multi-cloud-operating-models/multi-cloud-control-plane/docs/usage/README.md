# Project Team guide

Use this guide after Cloud Operations gives you a prepared project repository.
You can declare or remove approved resources, add published NSG rules, and run
supported lifecycle operations without deployment credentials or a different
process for each cloud. Every request follows the same reviewed pull-request
workflow.

## 1. Check that you are ready

Before choosing an interface, confirm that you:

- have write access to a handed-off project repository;
- are requesting something in [Reference capabilities](../reference/support.md);
- have selected one cloud, environment, and region from your environment
  handoff; and
- have completed the [environment secret-isolation check](../reference/verify-secret-isolation.md)
  with Cloud Operations; and
- have any change reference your organization requires, such as `CRQ1234`, to
  record in the pull request.

## 2. Choose an interface

Each interface follows the same governed pull-request lifecycle, and none of
them can approve, merge, or deploy it. The optional UI and Codex plugin render
only published catalog capabilities — see the
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

## 5. Follow a first worked example

To see one complete request without using customer values, follow the
[private OCI Autonomous Database walkthrough](oci-adb-walkthrough.md). It
shows the manifest, pull-request, review, and verification flow using only
placeholders and sample names.
