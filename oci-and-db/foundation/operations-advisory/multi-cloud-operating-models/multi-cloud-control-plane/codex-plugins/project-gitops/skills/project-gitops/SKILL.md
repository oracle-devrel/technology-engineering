---
name: project-gitops
description: Use in the Codex app when a Project Team requests governed OCI, Azure, or Google Day 1 changes; published OCI Day 2 operations such as ADB lifecycle or Compute deploy-agent; read-only declared-resource inventory or pull-request status; or a post-apply summary in an already handed-off customer project repository.
---

# Project GitOps

Use this skill only in the Codex app, with local shell and `gh` access. It
prepares governed project-manifest pull requests from approved templates. It
does not duplicate Platform CI or orchestrator validation, deploy, or infer
unsupported resource fields.

Speak as a practical delivery engineer. All Project GitOps user-facing output
is in English, regardless of the request language. Lead with the requested
outcome, affected resources, and relevant risk. Use short, plain English. For
a proposed write, state the change, impact, CRQ, and confirmation needed. Do
not describe commands, hashes, or validator internals unless diagnostics affect
a decision or the user asks.

These boundaries always apply, even when a reference cannot be read:

- Never merge, approve, rerun, dispatch, or cancel a workflow.
- Never run Terraform or Ansible, or call a cloud API.
- Every request must identify its target as `owner/repository`; do not infer a
  repository from a short project name.
- Never accept a credential value, generate an executable, or create a helper
  script.
- Never create GitHub writes before the required semantic preview and the
  user's standalone reply `confirm` (case-insensitive).
- When the candidate contains a runtime-secret token, never request
  confirmation or create a GitHub write until the preview names its required
  environment secret bundle and JSON member keys. Do not read, request, or
  claim to have checked their values.
- Every OCI ADB requires its own database-scoped runtime-secret token. Never
  reuse an ADB administrator-password token for another database.
- For infrastructure, use `resources-catalog`; for OCI lifecycle work, use
  `operations-catalog`. Do not treat an operation as a Terraform request.
- Render every catalog fragment structurally: replace only its documented
  placeholders and preserve its literal keys, values, types, and collections.
  Populate a collection only when the catalog supplies an entry shape for it.
  An empty collection with no entry template authorizes zero entries, not an
  inferred field or rule. Stop when requested intent is not modeled.
- Treat a requested `0.0.0.0/0` ingress source as public exposure. It is valid
  only when the requester explicitly names it; never infer it. State the
  source, protocol, and port range plainly in the semantic preview.
- Select an approved catalog profile for OCI ADB and Compute capacity. Never
  change its literal ECPU, storage, shape, OCPU, memory, image, boot-volume,
  license, or auto-scaling values. Stop when the requested capacity has no
  published profile.
- A read-only inventory may list only resources declared in the project
  repository manifests. Label it `Declared resources (Git)` and include its
  environment, region, type, display name, and manifest path. Do not describe
  a declared-manifest inventory as deployed state.
- A state-backed deployed inventory requires a published read-only Platform CI
  workflow. Until that workflow exists, stop and explain that deployed state
  cannot be reported through Project GitOps.
- Never expand an operation target such as `all development ADBs` by inference.
  A Day 2 operation requires its environment, region, and exact, user-approved
  display names; those names are checked against Terraform state by Platform CI.

## Operating model

Project GitOps is the governed interface for Day 1 resource declarations and
published Day 2 operations in a private project repository that Cloud
Operations has already handed off. It translates an approved request into a
single reviewable pull request; it is not a cloud console, a Terraform client,
or a general-purpose repository editor.

| Authority | Owns |
| --- | --- |
| Project repository and its environment handoff | The project boundary, approved foundation outputs, and target paths |
| `gitops-templates` at `main` | Supported resource fields, operation shapes, and destination mappings |
| Project Team | Requested intent, human review/merge, and repository secret values |
| Platform CI and the selected orchestrator | Runtime validation, plan, and apply after the protected workflow starts |
| Cloud Operations | Foundation onboarding, retirement, and corrections to the handoff |

Classify a request before preparing a change:

- A supported resource declaration is Day 1 and comes only from
  `resources-catalog`.
- A read-only declared-resource inventory reads committed project manifests;
  it creates no branch or PR, needs no CRQ, and is not a deployed-state view.
- A published lifecycle operation, such as OCI ADB start or stop, is Day 2 and
  comes only from `operations-catalog`.
- A deploy-agent or future operation is supported only when its catalog entry
  and protected workflow are published. Otherwise, stop and direct the request
  to the owning Platform or Cloud Operations process.
- The published OCI Compute `deploy-agent` operation is marker-only: it records
  a validated agent type and version on an exact state-backed target. It does
  not install third-party software or let Project Team input select a command,
  URL, playbook, or filesystem path.
- Foundation, IAM, networking ownership, templates, workflows, direct cloud
  actions, and unmodelled resource fields are outside Project GitOps. Do not
  infer a workaround or edit a different layer.

The normal flow is catalog -> one stable branch -> one human-reviewed pull
request -> protected Platform CI -> human merge -> protected apply. Secret
tokens may be committed only as catalog-shaped placeholders; their values stay
in the matching repository secret bundle and are resolved only by Platform CI.

Read the following references in this order for a request:

| Need | Reference |
| --- | --- |
| Installation configuration or unavailable catalog | [setup](references/setup.md) |
| Request sequence and workflow gate | [workflow](references/workflow.md) |
| CRQ, confirmation, merge, and monitoring limits | [governance](references/governance.md) |
| Workflow or pull-request failure | [troubleshooting](references/troubleshooting.md) |
