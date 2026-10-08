# Designing OCI Full Stack Disaster Recovery

## Purpose and design boundary

OCI Full Stack Disaster Recovery (FSDR) coordinates recovery of an application stack. It groups OCI resources into paired DR protection groups, generates DR plans, runs prechecks, and executes planned switchovers, unplanned failovers, and drills. The replication and recovery behavior of each underlying service must be designed and configured separately. FSDR does not substitute for database, storage, or application replication.

Start with the application, not the list of FSDR member types. For each application, record its business owner, dependencies, recovery time objective (RTO), recovery point objective (RPO), normal traffic path, and criteria for declaring recovery complete. These answers determine the protection-group boundary and the order of recovery steps.

## 1. Establish the standby foundation

Disaster Recovery infrastructure must be designed and built first. Once the foundation is established, Full Stack DR automates and orchestrates the recovery process.

1. **Network and traffic:** prepare VCNs, subnets, security rules, routing, private connectivity where needed, regional load balancers, DNS or other traffic redirection, and certificate dependencies.
2. **Capacity and configuration:** confirm compute capacity, service limits, images, operating-system packages, identities, secrets, application settings, and startup procedures in the recovery location.
3. **Data protection:** configure and monitor the replication or backup mechanism for every stateful component. Examples include Data Guard for an Oracle database, volume-group replication for VM volumes, File Storage replication, Object Storage replication, and the appropriate MySQL replication pattern.
4. **Access:** configure IAM policies required by FSDR and by any custom scripts, Functions, or Run Command steps. Keep application access and DR operator access explicit.
5. **Observability:** identify replication-lag signals, plan-execution alerts, application health checks, and the person responsible for acting on failures.

An RPO is principally constrained by each data replication mechanism and its observed lag. An RTO depends on the whole recovery path: detection and decision time, data-role transition, storage activation, compute startup, application recovery, traffic change, and validation. Measure both in exercises; a successful FSDR precheck alone does not prove either target.

## 2. Choose the compute and data pattern

| Pattern | What is prepared before recovery | Data placement | Typical trade-off |
| --- | --- | --- | --- |
| **Moving compute** | The active VM runs at the primary site; the recovery site has the network and capacity to create it. | Replicate a volume group containing the boot volume and required attached data volumes. | Less standby compute, but VM creation and startup add recovery time. |
| **Non-moving compute** | Application VMs exist in both sites; standby VMs are configured to run the application. | Replicate the application data volumes; attach their recovered copies to the standby VMs. Keep required application software and configuration ready on those VMs. | More standby preparation and cost, but less VM provisioning during recovery. |

The choice must follow the application’s startup behavior, state placement, target RTO, and standby cost. For non-moving VMs, explicitly inventory anything left on the boot volume: it will not be recovered merely because the application data volume is replicated. Oracle's [Block Storage preparation guide](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/block-storage-disaster-recovery.html) describes volume-group requirements for these patterns.

For databases and managed services, distinguish **native FSDR members** from resources needing **user-defined steps**. For example, the source design uses Data Guard for Oracle Database and native FSDR integration for OCI MySQL HeatWave. Its user-managed MySQL-on-VM example requires custom promotion and reconfiguration steps. Verify current member support and the exact service prerequisites in the [FSDR documentation](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/how-disaster-recovery-works.html).


## 3. Define the recovery unit

A DR protection group (DRPG) is a consistency grouping for resources that must recover together. A pair contains a primary and a standby DRPG. A DRPG has one exclusive peer; separate applications can have separate pairs. The peer regions can be different regions, or the topology can be across availability domains within one region where the services involved support it.

**Default design:** create one DRPG pair per application stack that has its own owner, release cycle, recovery objectives, or operating runbook. Combine applications in one pair only if they are operationally dependent and must always transition together. A shared platform component does not automatically mean that every application using it belongs in one pair; document how it will be recovered and coordinated across application plans.

| Design question | Decision to record |
| --- | --- |
| What is the application boundary? | Entry points, application tiers, stateful services, and external dependencies. |
| What must recover together? | Resources with a strict start-order or consistency dependency. |
| What can recover independently? | Workloads with different owners, schedules, RTO/RPO targets, or change cycles. |
| What is shared? | Network, identity, DNS, observability, or data services used by several applications; name the owner and recovery dependency. |
| What is the recovery acceptance test? | A user-visible transaction and the data checks that prove the application works. |

## 4. Map the protection-group pair

Use this worksheet for each application. Record actual resource names and OCIDs in the implementation runbook, not in a generic public example.

| Component | Primary site | Standby site | Replication or readiness check | FSDR handling |
| --- | --- | --- | --- | --- |
| Application compute |  |  |  | Moving or non-moving member; startup validation |
| Block/boot volumes |  |  |  | Volume-group activation/attachment |
| Database |  |  |  | Native role transition or custom step |
| File/Object Storage |  |  |  | Native member where supported or custom step |
| Load balancer and traffic |  |  |  | Backend handling and external traffic update |
| Application configuration |  |  |  | Custom step and verification |
| External or shared dependency |  |  |  | Named owner and prerequisite; may be outside the DRPG |

Create and associate the DRPGs, add the appropriate members to each side, then create the DR plans at the **standby** DRPG. Member placement varies by service and recovery pattern; use the current member-specific instructions rather than copying one example to every topology. [Protection group concepts](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/overview-protection-groups.html); [DR plan concepts](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/overview-dr-plans.html).

## 5. Design the recovery sequence

A DR plan consists of plan groups that execute sequentially. Steps within a group execute in parallel. Inspect the generated built-in groups, then add user-defined groups or steps where the application needs more work. Place dependent actions in separate sequential groups; parallelize only actions that are genuinely independent.

For each switchover and failover plan, draw a dependency graph covering:

1. Preconditions: replication state, standby capacity, required network and permissions.
2. Data transitions: database promotion, storage activation, and any consistency or fencing action.
3. Compute and middleware: VM recovery, volume attachment, mounts, application services, and connection configuration.
4. Traffic: load-balancer backends, DNS or other routing changes, and prevention of traffic reaching the old active stack.
5. Verification: database role and data checks, a representative user transaction, logs, and monitoring.

The exact order depends on the application. Review the generated plan rather than assuming that every built-in step has the right order for custom dependencies. Test custom scripts independently before adding them to a plan. Make each script's preconditions, success signal, retry behavior, and effect after partial execution clear to the operator.

Create separate plans for planned **switchover** and unplanned **failover**. Switchover normally uses both sites for an orderly transition; failover may have to proceed without the primary site. A **start drill** brings up a recovery copy for testing without changing production roles, and a **stop drill** ends that drill. [DR plan types](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/dr-plans-type.html).

## 6. Operate and test the design

- Run FSDR prechecks regularly and after material infrastructure or plan changes. Resolve failures before treating the plan as ready.  [Automate Disaster Recovery Plan Validation in OCI Using a Custom Precheck Tool](https://dev.to/amoubarak/automate-disaster-recovery-plan-validation-in-oci-using-a-custom-precheck-tool-1omo)
- Monitor replication health and lag independently of FSDR prechecks.
- Exercise a drill with production isolation, then stop the drill and verify cleanup. Record the observed recovery time and application checks.
- Run a planned switchover exercise when appropriate; review the resulting primary/standby roles and create or refresh plans needed on the new standby side.
- Revisit dependency maps, scripts, IAM, members, and plans after application releases or infrastructure changes.
- Keep an operator runbook with decision authority, communications, manual gates, failure handling, and evidence from the latest successful exercise.
