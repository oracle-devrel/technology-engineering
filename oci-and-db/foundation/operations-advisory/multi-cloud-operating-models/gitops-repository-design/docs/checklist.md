# Anti-Patterns and Checklist

[Back to overview](../README.md)

Use this page to review a design. Each item links to the page that explains it.

## Anti-patterns

| Anti-pattern | Consequence | Instead |
|---|---|---|
| One state file for the whole Landing Zone | Global lock; any failure blocks production | One state per operation, environment and region ([state boundaries](dependencies-and-state.md#state-boundaries)) |
| Production and non-production in the same state file | Non-production failures block production | One state file per stack; separate buckets when access differs ([backends](dependencies-and-state.md#state-keys-and-backends)) |
| State of the DR region stored in the primary region | The DR region cannot be managed after a primary region outage | State, and ORM stacks, in the region they manage |
| Tenancy-wide families (IAM, tags, Cloud Guard) in a stack that is repeated per region | Duplicated resources; DR stacks depend on the home region | IAM only in non-regional stacks ([IAM placement](component-distribution.md#iam-placement)) |
| Project teams managing compartments or IAM policies | Privilege escalation | Project IAM created by Cloud Operations during OP.04 |
| Project teams holding cloud deployment credentials | Changes outside review | Trusted runners apply merged changes; teams only propose |
| Project and foundation state in the same bucket or reachable by the same runner | A project pipeline can read or damage foundation state | Separate buckets and runner identities |
| OCIDs copied by hand into configuration files | Hard to read, easy to break | Output files and keys ([output files](dependencies-and-state.md#output-files)) |
| Security zone recipes that deny NSG deletion on network or project compartments | Projects cannot delete NSGs or be retired | Test the full NSG lifecycle before adding stricter targets ([component distribution](component-distribution.md#tenancy-wide-vs-regional)) |
| Configuration or dependency files larger than 1 MB read by `rms-facade` from a bucket or GitHub | The stack fails to read its files | Split into stacks, keep dependency files small, or use Terraform CLI with local files ([runtime](runtime.md)) |
| One configuration family spread across several files of one stack | Silent override; resources missing from the plan | One complete configuration set per stack |
| Fully automated cascade of applies across stacks | The blast radius comes back | Reviewed multi-step changes ([changes that cross stacks](dependencies-and-state.md#changes-that-cross-stacks)) |
| Git platform only available in the primary region | Single point of failure in DR | Git platform reachable from every region |
| Each project creates its own notification topics | Service limits reached | Central topics per workload environment |

## Checklist

**Repositories**
- [ ] Terraform code and configuration are in separate repositories.
- [ ] Each operation (OP.00 to OP.04) has its own folder, and regional resources are in region folders.
- [ ] Project teams have their own repositories, with production separated from non-production.
- [ ] Branch protection, required reviewers and `CODEOWNERS` are enabled.
- [ ] Pull requests change one operation, one environment and one region.

**IAM and governance**
- [ ] IAM is only in non-regional stacks (`common/` when consolidated).
- [ ] Project teams cannot create compartments or IAM policies.
- [ ] Policies are attached as deep as possible in the compartment tree.
- [ ] Notification topics are central per workload environment, and service limits are reviewed at each onboarding.

**Dependencies**
- [ ] The IAM pattern (consolidated or per operation) is chosen and documented.
- [ ] Outputs reach downstream stacks automatically (from the upstream state, or saved to Git or a bucket).
- [ ] Resources are referenced by key, not by OCID.
- [ ] Each project has a reviewed `project-foundation-handoff.json` before its first request.
- [ ] Configuration and outputs are reachable from every region.

**State**
- [ ] One state file per operation, environment and region.
- [ ] Production and non-production never share a state file, and use separate buckets when different identities deploy them.
- [ ] The state of each region is stored in that region (with ORM, the stack is created there).
- [ ] Foundation and project state are in different buckets, with versioning and backups.

**Runtime**
- [ ] The trigger to move from ORM to runners is defined (number of stacks, Day-2 needs, change time).
- [ ] Runners use instance principals, with separate runners and identities for production and non-production.
- [ ] Runner patching and scaling are defined.
