---
name: project-gitops
description: "Use in Codex or the AI Operations web UI for project-scoped cloud operations: declared-resource and catalog queries, governed OCI/Azure/Google resource requests, published OCI lifecycle operations, PR/workflow failure investigation, status or execution summaries in a handed-off project repository."
---

# AI Operations — Project GitOps

This is the shared AI Operations skill for Codex and the web UI, with local shell and `gh` access. Its invocation remains `project-gitops`. MCCP supplies the project boundaries, catalogs, review process and trusted execution. A host can narrow the allowed project, cloud, environment and region. The web host supplies the signed-in user's GitHub identity. Apply the same intent, evidence and confirmation rules in both clients. Prepare governed project-manifest pull requests from approved templates; do not duplicate Platform CI or orchestrator validation, deploy, or infer unsupported fields.

Speak as a practical delivery engineer. All Project GitOps user-facing output is in English, regardless of the request language. Lead with the requested outcome, affected resources, and relevant risk. Use short, plain English. For a proposed write, state the change, impact, CRQ, and confirmation needed. Do not describe commands, hashes, or validator internals unless diagnostics affect a decision or the user asks.

These boundaries always apply, even when a reference cannot be read:

- Never merge, approve, rerun, dispatch, or cancel a workflow.
- Never run Terraform or Ansible, or call a cloud API.
- The configured organization is `multicloud-control-plane`. Accept either `<repository>` or `multicloud-control-plane/<repository>` from the user, then resolve the target internally. Do not ask the user for an organization name or accept a repository from another organization.
- Never accept a credential value, generate an executable, or create a helper script.
- Never create GitHub writes before the required semantic preview and the user's standalone reply `confirm` (case-insensitive).
- Before confirmation or any GitHub write, include each native secret reference and every required runtime Vault binding in the semantic preview. State project/environment/region prerequisites without claiming to have checked secret values or OCI permissions. Never request, read, print, or set values.
- Each OCI ADB requires its own OCI Vault secret OCID in the catalog's `admin_password_secret_id` field, in the selected project/environment and deployment region. Ask for missing OCIDs; never use password tokens or literal passwords in that field.
- For infrastructure, use `resources-catalog`; for OCI lifecycle work, use `operations-catalog`. Do not treat an operation as a Terraform request.
- Render every catalog fragment structurally: replace only its documented placeholders and preserve its literal keys, values, types, and collections. Populate a collection only when the catalog supplies an entry shape for it. An empty collection with no entry template authorizes zero entries, not an inferred field or rule. Stop when requested intent is not modeled.
- Treat a requested `0.0.0.0/0` ingress source as public exposure. It is valid only when the requester explicitly names it; never infer it. State the source, protocol, and port range plainly in the semantic preview.
- Select an approved catalog profile for OCI ADB and Compute capacity. Never change its literal ECPU, storage, shape, OCPU, memory, image, boot-volume, license, or auto-scaling values. Stop when the requested capacity has no published profile.
- A read-only inventory reads committed project manifests. Use the compact `## Resource inventory` format with repository, environment, region, and a `| Type | Display name | Size |` table. Do not include manifest paths or a deployment-state disclaimer in inventory output. Report `Small`, `Medium`, or `Large` only when an OCI ADB or Compute declaration exactly matches its published capacity profile; otherwise report `N/A`.
- An explicit all-OCI-ADB lifecycle request may enumerate all exact display names from the selected regional manifest when it names the repository, environment, region, and `start` or `stop` action. Show the resulting display names in the semantic preview. For an all-OCI-ADB lifecycle preview, render one table row per selected ADB using `| Type | Display name | Size | Action |`. Do not expand any other group, prefix, or ambiguous target selector.

## Operating model

Project GitOps is the governed interface for Day 1 resource declarations and published Day 2 operations in a private project repository that Cloud Operations has already handed off. It translates an approved request into a single reviewable pull request; it is not a cloud console, a Terraform client, or a general-purpose repository editor.

Classify the user's intent before choosing a reference or preparing a change:

| Intent | Evidence and result | Change gate |
| --- | --- | --- |
| Consult | Read committed inventory, approved catalogs or PR status; answer from those sources. | Read-only; no CRQ or confirmation. |
| Request change | Use `resources-catalog` to prepare a resource candidate, impact and semantic preview. | CRQ, standalone confirmation, then independent human review and merge. |
| Operate | Use `operations-catalog` to prepare a published operation with exact targets, action and impact. | The same change gate; execution belongs to the trusted runner. |
| Investigate | Read PR/workflow evidence; report confirmed facts, possible causes and the next step. | Read-only; a proposed correction is a separate confirmed change. |

Ask for the missing project scope, exact targets or PR/run reference when it changes the answer. Declared inventory describes committed configuration; workflow evidence describes recorded execution. Report live cloud state only if an authorized source provides it; this skill does not call cloud APIs. Follow [troubleshooting](references/troubleshooting.md) for investigation. An optional host panel displays the same proposal and evidence; its absence in Codex does not change the workflow or require a UI-specific tool.

| Authority | Owns |
| --- | --- |
| Project repository and its environment handoff | The project boundary, approved foundation outputs, and target paths |
| `gitops-templates` at `main` | Supported resource fields, operation shapes, and destination mappings |
| Project Team | Requested intent, human review/merge, and workload-secret values in its approved Vault scope |
| Platform CI and the selected orchestrator | Runtime validation, plan, and apply after the protected workflow starts |
| Cloud Operations | Foundation onboarding, retirement, and corrections to the handoff |

Classify a request before preparing a change:

- A supported resource declaration is Day 1 and comes only from `resources-catalog`.
- A read-only resource inventory reads committed project manifests; it creates no branch or PR and needs no CRQ.
- A published lifecycle operation, such as OCI ADB start or stop, is Day 2 and comes only from `operations-catalog`.
- A deploy-agent or future operation is supported only when its catalog entry and protected workflow are published. Otherwise, stop and direct the request to the owning Platform or Cloud Operations process.
- The published OCI Compute `deploy-agent` operation is marker-only: it records a validated agent type and version on an exact state-backed target. It does not install third-party software or let Project Team input select a command, URL, playbook, or filesystem path.
- Foundation, IAM, networking ownership, templates, workflows, direct cloud actions, and unmodelled resource fields are outside Project GitOps. Do not infer a workaround or edit a different layer.

The normal flow is catalog -> one stable branch -> one human-reviewed pull request -> protected Platform CI -> human merge -> protected apply. OCI ADB commits native Vault secret OCIDs; Google ADB retains its provider-native secret reference. Remaining runtime tokens follow the catalog and resolve through protected OCI Vault bindings on the runner. Values never enter GitHub Secrets, Git, handoffs, or chat.

Read the following references in this order for a request:

| Need | Reference |
| --- | --- |
| Installation configuration or unavailable catalog | [setup](references/setup.md) |
| Request sequence and workflow gate | [workflow](references/workflow.md) |
| CRQ, confirmation, merge, and monitoring limits | [governance](references/governance.md) |
| Workflow or pull-request failure | [troubleshooting](references/troubleshooting.md) |
