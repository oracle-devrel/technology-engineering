# Architecture And Source Ownership

## Product Paths

The stack creates two related workflows:

- Developer delivery: application baselines plus independently built and released components.
- Cluster administration: cluster tools, supplemental namespace resources, and cluster-wide baseline resources.

Read `docs/architecture.md`, then use the task-specific guides linked from `README.md`.

## Input To Resource Flow

```text
schema.yaml
  -> variables.tf and checks.tf
  -> root locals.tf
  -> main.tf module inputs
  -> modules/devops/locals.tf normalized entity maps
  -> Terraform repositories, artifacts, pipelines, stages, triggers, and environments
  -> templates/*.tpl and repos/* starter content
```

When changing an input, inspect every layer in that path. `schema.yaml` controls the Resource Manager form but does not replace Terraform validation.

## Source Map

| Concern | Primary source locations |
| --- | --- |
| Resource Manager form | `schema.yaml` |
| Inputs and validation | `variables.tf`, `checks.tf`, `locals.tf` |
| Root composition and outputs | `main.tf`, `outputs.tf` |
| Entity normalization | `modules/devops/locals.tf` |
| Repositories and seeding | `modules/devops/repositories.tf`, `modules/devops/cluster_admin_repositories.tf`, `script/seed_repo.sh` |
| Build pipelines and triggers | `modules/devops/build_pipelines.tf`, `modules/devops/cluster_admin_build_pipelines.tf`, `modules/devops/triggers.tf` |
| Deployment pipelines | `modules/devops/deploy_pipelines.tf`, `modules/devops/cluster_admin_deploy_pipelines.tf` |
| Artifacts | `modules/devops/artifacts.tf`, `modules/devops/cluster_admin_artifacts.tf` |
| Build and command specifications | `templates/*.yaml.tpl` |
| Shared runtime scripts | `repos/pipelines/script`, `repos/cluster-admin/script` |
| Generated starter content | `repos/generated` plus `local_file` resources |
| Packaging | `update.sh` |
| Stack upload helper | `script/update_orm_stack.sh` |
| Regression tests | `tests/` |

## Ownership Boundaries

- Terraform creates stable OCI wiring and initial templates.
- Release archives retain lifecycle ignores on user-customizable OCI DevOps resources.
- Development archives remove only the exact release ownership blocks staged by `update.sh`.
- Git seed operations are add-only. They may create missing files and directories but must preserve an existing path.
- A custom component build-spec path receives the starter build spec only when missing and is never refreshed afterward.
- `catalog/tools.yaml` is generated from Resource Manager cluster-tool input; cluster-specific values and manifests remain administrator-owned.

Read `docs/template-ownership.md` before changing lifecycle blocks, repository seed triggers, or generated files.

## Entity Model

- One shared `pipelines` repository.
- One chart repository and application baseline lifecycle per application.
- One source, PR, build, dev deployment, and release lifecycle per globally unique component.
- Optional shared `cluster-admin` repository and cluster-specific administration pipelines.
- Pre-prod and prod networking, environments, and approvals remain independently configured even when both target the same cluster.
