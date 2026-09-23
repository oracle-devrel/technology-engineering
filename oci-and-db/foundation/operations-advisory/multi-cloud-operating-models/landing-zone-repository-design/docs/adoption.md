# Adoption Path

[Back to overview](../README.md)

This page is for teams that already run a Landing Zone in one large stack and want to move to the multi-stack model without recreating resources.

## The technical debt trap

> [!WARNING]
> Splitting a monolithic configuration after it is in production is much harder than structuring it well from the start. Resources must be moved between state files without being recreated, dependencies must be rebuilt, and everything happens on a live environment. Teams that start with a single file of thousands of lines usually reach the point where it is no longer manageable, and then must split it under pressure.

During the initial build, many changes affect everything (for example adding tags to all compartments). In this phase the benefit of the split is small, because a cross-cutting change fails at the top level anyway. The benefit appears during Day-2 operations, which last for years.

## Order of changes

Start with the [minimum split](../README.md#minimum-split-for-a-small-team) and then continue in this order:

| Phase | Action | Main benefit |
|---|---|---|
| 1 | Move all tenancy-wide IAM and governance to non-regional stacks (`common/`, OP.00), each with its own state | One owner for IAM; ready for multi-region |
| 2 | Split regional Landing Zone resources (OP.01) into region folders, with state stored in each region | The DR region can be managed on its own |
| 3 | Split workload environments (OP.02), starting with production vs. non-production | No locking between environments |
| 4 | Onboard projects (OP.04) with a handoff and hand off `nonprod-<project>` and `prod-<project>` repositories, for example with the [MCCP](../../multi-cloud-control-plane/README.md) | Delegation without IAM access or credentials |
| 5 | Introduce runners with Terraform CLI when Day-2 automation or scale requires it (see [Runtime](runtime.md)) | Same workflow for provisioning and operations |

## Moving resources between stacks

Moving existing resources to a new stack must never recreate them:

1. Copy the configuration of the resources to the new stack, with the same keys.
2. In the new stack, bring the resources under management with `import` blocks (Terraform 1.5 or later) or by importing a prepared state file (ORM supports importing a state file into a stack).
3. In the old stack, remove the resources from state without destroying them, with `removed` blocks and `lifecycle { destroy = false }` (Terraform 1.7 or later) or `terraform state rm`.
4. Run `plan` on both stacks. Continue only when **both plans show no changes** for the moved resources.

> [!WARNING]
> Never apply a plan that shows destroy or replace actions on moved foundation resources such as compartments, VCNs or DRGs. Move one operation at a time, and start with a non-production environment.
