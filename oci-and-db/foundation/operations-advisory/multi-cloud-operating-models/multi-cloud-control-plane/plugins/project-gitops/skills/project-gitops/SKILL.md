---
name: project-gitops
description: Use in the Codex app when a Project Team requests governed OCI, Azure, or Google Day 1 changes; OCI ADB start or stop; OCI SSH deploy-agent; read-only pull-request status; or a post-apply summary in an already handed-off customer project repository.
---

# Project GitOps

Read `deployment-contract.json`, [safety boundaries](references/safety-boundaries.md), and [operations](references/operations.md). Fail closed unless the contract validates the exact organization, repository, environment, immutable catalog ref, and workflow. Use English for user-facing output.

Run only in the Codex app when local shell and `gh` access are available.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the validator included in this package. Status and monitoring requests create no
local files. Writable flows keep non-executable temporary data inside one fresh system temporary
directory, register cleanup immediately, and remove it before finishing.

Accept only handed-off `nonprod-<project>` or `prod-<project>` repositories on exact `main`. Use disposable clones. Read schemas only from the configured catalog repository at the approved SHA. Support OCI ADB, compute and NSG Day 1; Azure Day 1; Google ADB-S Day 1; and, only in `nonprod-<project>`, OCI ADB start/stop and OCI SSH `deploy-agent`. Preserve aggregate manifest roots and canonical `lifecycle_operations` paths. Refuse every Day 2 request in `prod-<project>` because the production template has no Ansible workflow in this release. Refuse Azure and Google Day 2 because those provider-specific operations are not available.

Before every branch push or PR creation, show a semantic preview and hashes, state `GitHub writes: none`, ask `Do you confirm? Reply "Confirm".`, then revalidate. Never merge, approve, control workflows, call cloud APIs, or run Terraform/Ansible.

After a known human merge, monitor the configured exact workflow until terminal unless the user
explicitly requests a one-time snapshot. Keep the task active while it is queued or running; poll
structured GitHub reads every 15–30 seconds, use commentary for progress, and never require the
user to return and announce completion.
# Shared non-production repositories

For `nonprod-<project>`, require the user to select `dev`, `test`, or `uat`.
Read `control-plane.json`; never infer a layout from path segments. Validate the
matching `environments/<environment>/environment_information.md` and use the
environment-aware manifest path. Refuse production aliases, protected contract
or workflow changes, placeholders that do not begin with the selected uppercase
environment (for example, `__DEV_...__`), and changes spanning more
than one cloud/environment/region tuple. Run `scripts/validate-shared-layout.py`
before proposing Git changes. The skill still creates Git changes only.
