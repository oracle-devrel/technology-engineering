---
name: oci-devops-starter-maintainer
description: Maintain, extend, validate, package, and functionally test the OKE DevOps Starter Resource Manager stack. Use when changing its Terraform, Resource Manager schema, OCI DevOps repositories, build or deployment pipelines, Helm charts, cluster-administration workflow, documentation, or release archive.
---

# OKE DevOps Starter Maintainer

Use this Skill only from the root of the OKE DevOps Starter repository.

## Start Every Task

1. Read `README.md` for the product contract and documentation map.
2. Read `AGENT.md` when it exists for local development history. Treat its environment identifiers as local context, never distributable content.
3. Inspect the working tree and preserve unrelated user changes.
4. Read only the references relevant to the task:
   - Architecture, ownership, and source locations: `references/architecture.md`
   - Invariants, security boundaries, and OCI constraints: `references/invariants.md`
   - Local and functional verification: `references/testing.md`

## Maintenance Workflow

1. Trace the requested behavior from Resource Manager input through normalized locals, OCI resources, templates, seeded repository content, and documentation.
2. Modify the true source of the generated behavior. Do not patch generated output when a Terraform template or local generates it.
3. Preserve template ownership: OCI DevOps resources are starters, and repository seed operations must not overwrite user-owned paths.
4. Keep changes entity-generic. Test at least two applications or components mentally whenever changing `for_each` maps, names, paths, parameters, tags, or pipeline wiring.
5. Add or update regression tests for structural contracts and past OCI provider failures.
6. Run `bash .agents/skills/oci-devops-starter-maintainer/scripts/validate.sh`.
7. When packaging is requested, run `./update.sh`, inspect the archive, and confirm `.agents`, `AGENT.md`, local state, credentials, logs, and ad hoc scripts are absent.
8. Apply or functionally test live OCI resources only when requested. Prefer focused tests after narrow changes and end-to-end tests after workflow changes.

## Editing Rules

- Keep Terraform authoritative for stable resource wiring and infrastructure, while preserving configured lifecycle ignores for user-customizable DevOps templates.
- Keep `schema.yaml`, `variables.tf`, validation checks, locals, outputs, and documentation synchronized when changing an input.
- Keep build specifications readable as macro steps; put complex shell behavior in named repository scripts.
- Use lowercase pipeline parameters and exported variables unless an OCI-defined variable requires another form.
- Never embed tenancy-specific OCIDs, usernames, auth tokens, secret values, or test-environment history in distributable files.
- Do not introduce OCI resources managed through `local-exec` or OCI CLI. Existing `null_resource` use is limited to add-only Git repository seeding.
- Do not assume pre-prod and prod are different physical clusters; the stack supports selecting the same cluster for both.
- Do not weaken production approvals or immutable image/chart/version behavior without explicit direction.

## Completion Report

State which product behavior changed, which checks ran, whether an archive or stack was updated, and any live functional test or cleanup that remains.
