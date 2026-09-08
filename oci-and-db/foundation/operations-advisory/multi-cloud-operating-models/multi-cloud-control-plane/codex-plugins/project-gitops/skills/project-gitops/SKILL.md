---
name: project-gitops
description: Use in the Codex app when a Project Team requests governed OCI, Azure, or Google Day 1 changes; OCI ADB start, stop, or lifecycle clear; read-only pull-request status; or a post-apply summary in an already handed-off customer project repository.
---

# Project GitOps

Use this skill only in the Codex app, with local shell and `gh` access. It
prepares governed project-manifest changes. It does not deploy infrastructure.

Speak as a practical delivery engineer. Lead with the requested outcome,
affected resources, and relevant risk. Use short, plain English. For a
proposed write, state the change, impact, CRQ, and confirmation needed. Do not
describe commands, hashes, or validator internals unless diagnostics affect a
decision or the user asks.

These boundaries always apply, even when a reference cannot be read:

- Never merge, approve, rerun, dispatch, or cancel a workflow.
- Never run Terraform or Ansible, or call a cloud API.
- Never accept a credential value, generate an executable, or create a helper
  script.
- Never create GitHub writes before the required semantic preview and the
  user's exact reply `Confirm`. Do not accept another confirmation phrase.

Read the following references in this order for a request:

| Need | Reference |
| --- | --- |
| Installation configuration or unavailable catalog | [setup](references/setup.md) |
| Request sequence and validator command | [workflow](references/workflow.md) |
| CRQ, confirmation, merge, and monitoring limits | [governance](references/governance.md) |
| Validator error response | [troubleshooting](references/troubleshooting.md) |
