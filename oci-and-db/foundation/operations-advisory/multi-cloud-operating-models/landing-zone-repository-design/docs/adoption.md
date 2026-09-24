# Adoption Path

[Back to overview](../README.md)

This page is for teams that already run a Landing Zone in one large stack and want to move to the multi-stack model without recreating resources. It ends with a detailed procedure for the most common case: splitting a network configuration into a hub stack and one stack per spoke.

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
3. In the old stack, remove the resources from state without destroying them, with `removed` blocks and `lifecycle { destroy = false }` (Terraform 1.7 or later) or `terraform state rm`. A `removed` block cannot target a single instance key, so for resources created from a map, as the orchestrator does, use `terraform state rm` with the full instance address.
4. Run `plan` on both stacks. Continue only when **both plans show no changes** for the moved resources.

> [!WARNING]
> Never apply a plan that shows destroy or replace actions on moved foundation resources such as compartments, VCNs or DRGs. Move one operation at a time, and start with a non-production environment.

## Splitting a network configuration managed by the orchestrator

A common first move is to split one large network configuration (hub, DRG and every spoke VCN in one state) into a hub stack and one stack per spoke. The rules below come from the [networking module](https://github.com/oci-landing-zones/terraform-oci-modules-networking) used by the orchestrator.

### Why resource addresses do not change

The networking module creates each resource type in one map, indexed by its configuration key: for example `oci_core_vcn.these["<VCN-KEY>"]` or `oci_core_drg_attachment.these["<DRG-ATTACHMENT-KEY>"]`. The category a VCN belongs to is not part of the address, and attachments injected into an existing DRG use the same map as attachments defined next to the DRG. Route tables are split into several maps by the type of target in their rules; a route to a DRG counts as a DRG target whether the DRG is in the same stack or comes from a dependency.

If the keys stay the same, each moved resource has the same address in the new stack. Only its state entry has to move. Any address change shows up in the local verification plan (step 5 below).

### What stays in the hub and what moves

| Stays in the hub stack | Moves to each spoke stack |
|---|---|
| Hub VCN, DRG, DRG route tables, DRG route distributions, the hub attachment and, where present, FastConnect, IPSec and remote peering | All the resources of the spoke VCN (for example its subnets, route tables and their subnet associations, security lists, NSGs and their rules, gateways, DHCP options and the VCN default resources) and **its own DRG attachment**, declared under `inject_into_existing_drgs` with the same key |

This matches the [reference implementation](https://github.com/multicloud-control-plane/oci-landing-zone), which keeps the DRG and the hub VCN in the same configuration. Keeping the original stack as the hub stack means only the spokes move. References that cross the new boundary change as follows:

| Reference | Before (same stack) | After (hub and spoke in different stacks) |
|---|---|---|
| Spoke attachment → DRG | DRG key | DRG key, resolved by the module from the hub network output |
| Spoke route rule → DRG | DRG key | DRG key, resolved by the module from the hub network output |
| Spoke attachment → hub DRG route table | `drg_route_table_key` | `drg_route_table_id` (OCID). A route table key only resolves inside the same stack. |
| Hub DRG route rule → spoke attachment | `next_hop_drg_attachment_key` | `next_hop_drg_attachment_id` (OCID), for the same reason |
| Hub route distribution → spoke attachment | Attachment key | Match by attachment type or by OCID. A key would have to be resolved from the spoke outputs, so the hub would depend on the spokes as well as the other way round. |

### Procedure

The same procedure works with ORM and with Terraform CLI pipelines. The state entries are moved offline, on local copies of the state files, and only the loading step depends on the runtime. `import` blocks can only be declared in the root module, so a stack that runs the orchestrator unchanged (for example through `rms-facade`) has nowhere to add them. `removed` blocks do not help either: they do not accept instance keys, so they cannot remove only the resources of one VCN.

1. **Prepare.** Freeze changes on the network stack and pause its pipeline. Run a plan and confirm it shows no changes. Get a copy of the state and keep a backup: *Download Terraform state* in ORM, or `terraform state pull > original.tfstate` with Terraform CLI. Locally, use the same Terraform version, the same orchestrator release, the same entry point (addresses start with `module.oci_lz_orchestrator.module.oci_lz_network[0]` with `rms-facade`, and with `module.oci_lz_network[0]` when the orchestrator root is called directly) and the same variables as the stack, so that the plan shows no differences unrelated to the move. The address rules above were checked against networking module v0.8.3; with an older orchestrator release, confirm them with `terraform state list` first.
2. **Publish the hub outputs.** With `rms-facade`, *Save Output* writes the output files when the configuration comes from an OCI bucket or GitHub, or in file mode; the plan of that apply should only add the output files. In any case, the dependency file can also be written by hand, with the keys and OCIDs of the hub resources that the spoke configuration references by key. If it only references the DRG: `{"network_resources": {"dynamic_routing_gateways": {"<DRG-KEY>": {"id": "<DRG-OCID>"}}}}`.
3. **Split the configuration.** Move one spoke to its own file with the same keys and values, and change the references in the table above. The new stack depends on the hub network output and, if the configuration references compartments by key, on the compartments output.
4. **Move the state entries.** List all the entries of the spoke with `terraform state list` on a copy of the state, and move each one with `terraform state mv -state=original.tfstate -state-out=spoke.tfstate '<address>' '<address>'` (quoted, because addresses contain brackets). Terraform documents `-state` and `-state-out` as legacy options, supported for local state files.
5. **Verify locally.** Plan the reduced original configuration with the reduced state, and the new spoke configuration with the new state and its dependencies. Both plans must show no changes, apart from output files if *Save Output* is enabled on the new stack. If a plan shows changes to attributes, fix the configuration. If it destroys and creates the same object under two different addresses, move the state entry to the new address.
6. **Load the states.** First update the configuration of the original stack, now without the spoke, and create the spoke stack with its configuration.
   - **With ORM:** import the reduced state into the original stack and `spoke.tfstate` into the spoke stack with the *Import state* job. Create the spoke stack in the region it manages.
   - **With Terraform CLI and an Object Storage backend:** in each stack directory, run `terraform init` with the stack's own state key and then `terraform state push` with the matching file. Terraform refuses a push if the lineage differs or the remote serial is higher; if that happens, stop and find out why, and do not force it.
7. **Verify.** Run a plan on both stacks through their normal pipeline or ORM job. Both must show no changes. Only then lift the freeze.

To roll back, restore the previous configuration of the original stack and load the original state into it again. With ORM, use *Import state*. With Terraform CLI, restore the previous version of the state object if the bucket is versioned, or use `terraform state push -force`; here `-force` is needed because the backup has a lower serial than the current state.

Teams that run Terraform CLI from their own root module can also use `import` blocks in the new stack instead of moving state entries, followed by `terraform state rm` in the original stack. Moving the entries offline is still simpler, because it works the same way with both runtimes and every step can be checked with a plan before anything is loaded.

Move one spoke per change window. Start with a non-production spoke of low criticality as a pilot, and leave the most critical platforms for the end. Moving state entries does not change the infrastructure or any OCID, so resources that use these subnets are not affected.
