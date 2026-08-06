---
name: project-gitops
description: Use in the Codex app when a Project Team requests governed OCI, Azure, or Google Day 1 changes; OCI ADB start or stop; read-only pull-request status; or a post-apply summary in an already handed-off customer project repository.
---

# Project GitOps

Read `mccp-installation.json`, parse it with `jq -e`, reject unresolved
placeholders, and derive the canonical `<customer-org>/gitops-templates`
repository plus its immutable catalog ref. Then read
[safety boundaries](references/safety-boundaries.md) and
[operations](references/operations.md). Resolve that repository/ref through
GitHub before reading a schema or validating the repository, environment, and
workflow. Use English for user-facing output.

Run only in the Codex app when local shell and `gh` access are available.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the validator included in this package. Status and monitoring requests create no
local files. Writable flows keep non-executable temporary data inside one fresh system temporary
directory, register cleanup immediately, and remove it before finishing.

Accept only handed-off `nonprod-<project>` or `prod-<project>` repositories on exact `main`. Use disposable clones, but clone into a child directory whose name is the canonical repository name because the shared-layout validator verifies that name. Read schemas only from the configured catalog repository at the approved SHA and record the verified catalog repository, commit, and blob SHA in the semantic preview. Support OCI ADB, compute and NSG Day 1; Azure VM and ADB Day 1; Google VM and ADB-S Day 1; and OCI ADB start/stop in every supported environment. Preserve aggregate manifest roots and canonical `lifecycle_operations` paths. Refuse Azure and Google Day 2 because those provider-specific operations are not available.

Before every branch push or PR creation, show a semantic preview and hashes, state `GitHub writes: none`, ask `Do you confirm? Reply "Confirm".`, then revalidate. Never merge, approve, control workflows, or run Terraform/Ansible. For an explicit new OCI Compute request for Oracle Linux 9 on `VM.Standard.A1.Flex`, the sole cloud-read exception is the documented `oci compute image list` command: derive its region and App compartment from the validated handoff, verify the returned image metadata, show it in the preview, and write its exact OCID. Never call any other cloud API.

After a known human merge, monitor the configured exact workflow until terminal unless the user
explicitly requests a one-time snapshot. Keep the task active while it is queued or running; poll
structured GitHub reads every 15–30 seconds, use commentary for progress, and never require the
user to return and announce completion.

## Shared non-production repositories

For `nonprod-<project>`, require the user to select `dev`, `test`, or `uat`.
Derive the shared non-production layout from that canonical repository name and validate the
matching `environments/<environment>/environment_information.md`. Use the
environment-aware manifest path. Refuse production aliases, protected workflow
changes, placeholders that do not begin with the selected uppercase environment
(for example, `__DEV_...__`), and changes spanning more than one
cloud/environment/region tuple. Run `scripts/validate-shared-layout.py` before
proposing Git changes. The skill still creates Git changes only.

The OCI Landing Zone handoff uses TBAC schema 3: one project root with distinct
App, DB, and Infra child-compartment rows. Use App for Compute, DB for
Autonomous Database and its lifecycle operations, and Infra for project NSGs.
Reject schema-2 aliases and any OCI manifest that targets another role.
