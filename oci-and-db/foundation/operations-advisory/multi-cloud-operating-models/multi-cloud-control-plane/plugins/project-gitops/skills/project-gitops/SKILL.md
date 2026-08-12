---
name: project-gitops
description: Use in the Codex app when a Project Team requests governed OCI, Azure, or Google Day 1 changes; OCI ADB start, stop, or lifecycle clear; read-only pull-request status; or a post-apply summary in an already handed-off customer project repository.
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

## User-facing communication

Speak as a practical delivery engineer. Lead with the requested outcome, what
will change, and any relevant risk or trade-off; use plain technical language.
Give short updates only for material state changes and conclude with a concise
handoff. Do not narrate commands, validator output, hashes, or internal
mechanics unless they affect a decision or the user asks for diagnostics. For a
proposed write, state the change, impact, CRQ, and needed confirmation plainly.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the validator included in this package. Status and monitoring requests create no
local files. Writable flows keep non-executable temporary data inside one fresh system temporary
directory, register cleanup immediately, and remove it before finishing.

Accept only handed-off `nonprod-<project>` or `prod-<project>` repositories on exact `main`. Use disposable clones, but clone into a child directory whose name is the canonical repository name because the shared-layout validator verifies that name. Read schemas only from the configured catalog repository at the approved SHA and verify its repository, commit, and blob identity internally. Support OCI ADB, compute and NSG Day 1; Azure VM and ADB Day 1; Google VM and ADB-S Day 1; and OCI ADB start/stop in every supported environment. Use `{}` only to clear a completed OCI ADB lifecycle request; otherwise preserve aggregate manifest roots and canonical `lifecycle_operations` paths. Refuse Azure and Google Day 2 because those provider-specific operations are not available.

Treat a valid environment handoff as the repository-initialization boundary. Do
not require an active `.github/CODEOWNERS`: accept a template-only
`.github/CODEOWNERS.template` and leave review-ownership configuration to the
Project Team. Never describe the absence of active CODEOWNERS as a handoff or
manifest-change blocker.

A repository secret bundle is optional. Require it only when the selected
manifest contains environment-qualified secret placeholders; an absent bundle
is valid for manifests with no placeholders.

For any mutable manifest, lifecycle, branch-push, or pull-request flow, require
a user-provided CRQ matching `CRQ[0-9]{1,20}` before creating a change
candidate. Do not infer a CRQ. Show it as the change reference in the concise
preview; it does not replace explicit confirmation. Do not request a CRQ for
status, validation, or monitoring.

Before every branch push or PR creation, show one concise semantic preview with
user-relevant changes and the required CRQ, state `GitHub writes: none`, and ask
`Do you confirm? Reply "Confirm".` Bind that one confirmation internally to
the validated base and content hashes, then revalidate them after the reply. Do not
display validator metadata or hash values (including template tree, handoff
Markdown, layout, base/template revision, or content hashes) unless the user
explicitly requests diagnostic detail. If the candidate drifts, discard the
confirmation, regenerate the semantic preview, and request one new confirmation;
never ask for a separate hash-confirmation. Never merge, approve, control workflows,
or run Terraform/Ansible. For a new OCI Compute request, offer the Frankfurt
`VM.Standard.A1.Flex` image pinned in the approved catalog template as the
default and ask whether to use it or provide another regional image OCID.
Validate the selected OCID through the manifest contract. The user confirms
the image choice manually before approval; never use OCI CLI or call a cloud
API to resolve an image.

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
