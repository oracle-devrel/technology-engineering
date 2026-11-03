# ADB-D `COLOCATION_TAG` comparative workload

## What `COLOCATION_TAG` is intended to do

`COLOCATION_TAG` is an alphanumeric Oracle Net connect-descriptor parameter placed inside `CONNECT_DATA`. When clients connect to the same service with the same tag, listener-side normal load balancing is ignored and the listener makes an effort to route those connections to one database instance. The routing choice is based on the tag and the service's currently available instances. The intended benefit is to keep sessions that repeatedly work on related data together, reducing inter-instance communication and therefore contention on the RAC interconnect.

This is deliberately a best-effort affinity mechanism, not an absolute placement guarantee. Oracle notes that sessions with the same tag can be distributed when an instance reaches its maximum load or when instances are added to or removed from the service. Autonomous Database on Dedicated Exadata Infrastructure documents colocation tagging as a supported high-performance feature for transaction-processing applications that repeatedly connect to the same service.

Sources: [Oracle Database Net Services — COLOCATION_TAG of Client Connections](https://docs.oracle.com/en/database/oracle/oracle-database/26/netag/colocation_tag-client-connections.html); [Autonomous Database on Dedicated Exadata Infrastructure — High Performance Features](https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/hpfad/index.html).

This suite measures the mechanism behind colocation rather than only checking routing. For each run, it executes the **same concurrent sequential-primary-key insert workload** twice:

1. `CONTROL`: `SESSION_COUNT` workers use normal connection descriptors with no `COLOCATION_TAG`; the listener can balance them across RAC instances.
2. `TAGGED`: the same number of workers use the one configured tag, `C_TAGGED` by default; the listener tries to route the entire cohort to one instance.

Both cohorts repeatedly insert into the same table using an increasing primary-key value. The table is hash-partitioned into 16 partitions by that key and its primary-key index is local, so inserts are distributed across table/index partitions rather than concentrating on one right-edge index block. This reduces buffer-busy contention without taking row locks through `SELECT ... FOR UPDATE`. In the control phase, sessions on different instances can still move ownership of active index blocks between buffer caches and generate RAC global-cache (`gc`) traffic. In the tagged phase, colocation should remove or greatly reduce that cross-instance block movement. The sequence is `NOORDER CACHE` so its allocation is not the RAC bottleneck being measured. The suite snapshots `GV$SYSTEM_EVENT` cluster wait time and `GV$SYSSTAT` GC block counters around each phase, then normalizes event wait time by completed application operations. The practical success signal is lower `gc` wait microseconds per operation in `TAGGED` than `CONTROL`, while throughput remains comparable.

After both phases of a run finish, the runner truncates `CT_COLOCATION_INSERT_LOG` with `DROP STORAGE` before starting the next run. This gives every run a fresh table and primary-key index while preserving the sequence's increasing, unique values. It never truncates between the paired `CONTROL` and `TAGGED` phases.

Colocation is explicitly best effort: Oracle documents exceptions under capacity pressure and topology changes. It bypasses ordinary load balancing for matching tags; it does not promise one instance forever. [Oracle Net reference](https://docs.oracle.com/en/database/oracle/oracle-database/26/netag/colocation_tag-client-connections.html).

## Prerequisites

- SQLcl (`sql`) and Bash 4.3+.
- A full ADB-D `DESCRIPTION` descriptor; not a TNS alias. Wallet/TLS setup must already work.
- A quiet, multi-instance ADB-D service and enough headroom for the configured workers.
- An ADB-D administrative account to provision the dedicated `TEST_CTAG` schema. The included provisioning script gives it only the object-creation and RAC-metric privileges needed by this suite. The run stops if metric snapshots fail, because without them it cannot substantiate the interconnect comparison.

### Optional AWR reports

Set `AWR=y` in `config.env` to create a manual AWR snapshot immediately before and after every `CONTROL` or `TAGGED` phase. The runner records the exact snapshot ID returned by `CREATE_SNAPSHOT`, rather than looking up the latest snapshot. After all runs complete, it creates one RAC-global HTML AWR report from the matching `BEFORE` and `AFTER` IDs for every phase—for example, run 1 `CONTROL` uses only its own two snapshots—in `results/<run-id>/awr/`. This option is off by default. AWR use requires the Oracle Diagnostics Pack (or applicable cloud entitlement); enable it only when that use is licensed. The provisioning script grants the `DBMS_WORKLOAD_REPOSITORY` access needed for this option. Oracle documents both the snapshot-return function and the global report function in the [DBMS_WORKLOAD_REPOSITORY reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_REPOSITORY.html).

The example stores a password in `config.env` for unattended workers. Protect that file (`chmod 600`) or, preferably, adapt `sqlcl()` to use a Secure External Password Store (`/@alias`). Do not commit it.

## Run

```bash
cd /Users/stef/Documents/Codex/2026-07-21/i/outputs/adb_colocation_tag_test
cp config.env.example config.env
# edit config.env; use your actual dedicated-service descriptor
# In a separate SQLcl administrative session (destructive if TEST_CTAG exists):
sql admin@<admin-service> @recreate_test_ctag.sql
bash ./validate_config.sh
bash ./setup_workload.sh                 # once
# Optional: set AWR=y in config.env before this command
bash ./run_colocation_test.sh
```

`setup_workload.sql` creates a 16-way hash-partitioned shared insert table, a matching local primary-key index, and a cached sequence. It starts empty; no seed data is required. Use [cleanup_workload.sql](/Users/stef/Documents/Codex/2026-07-21/i/outputs/adb_colocation_tag_test/cleanup_workload.sql) only after workers finish; it drops the three `CT_COLOCATION_*` objects.

[recreate_test_ctag.sql](/Users/stef/Documents/Codex/2026-07-21/i/outputs/adb_colocation_tag_test/recreate_test_ctag.sql) is the complete schema-reset/provisioning script. It grants `CREATE SESSION`, `CREATE TABLE`, `CREATE PROCEDURE`, `CREATE SEQUENCE`, `UNLIMITED TABLESPACE`, and read access to `GV_$SYSTEM_EVENT` and `GV_$SYSSTAT`. It drops the schema with `CASCADE` first; use [drop_test_ctag.sql](/Users/stef/Documents/Codex/2026-07-21/i/outputs/adb_colocation_tag_test/drop_test_ctag.sql) for final teardown.

## Results and interpretation

Each execution creates `results/<UTC-run-id>/`:

- `workers.psv` and `workload_summary.psv`: operations and instance placement by phase.
- `metrics_snapshots.psv` and `metric_deltas.psv`: RAC-wide before/after counters.
- `gc_event_per_operation.psv`: `GV$SYSTEM_EVENT` delta divided by phase operations—the principal comparison file.
- `gc_wait_summary.psv`: aggregate `gc%` event waits, elapsed wait time, average wait in microseconds/milliseconds, and wait microseconds per operation for every phase.
- `awr/snapshots.psv`, `awr/report_pairs.psv`, and `awr/*.html`: exact snapshot IDs, their per-phase report pairs, and one RAC-global AWR report per phase, when `AWR=y`.
- `failures.log`: connection, worker, or metric-snapshot errors.

The run prints the untagged and `C_TAGGED` connect descriptors used (never credentials), the workload summary, and aggregate average `gc%` wait time. Compare like-for-like event rows for `CONTROL` and `TAGGED` across the alternating runs; use medians, not one noisy phase. A credible result has: all workers successful, the `TAGGED` cohort observed on one instance, similar operations/worker, and lower tagged `gc` wait time/op and/or GC block-receive counts/op. If untagged workers also happen to land together, or background workload dominates the global views, the result is inconclusive—raise `SESSION_COUNT` gradually, keep the database quiet, and repeat.

This deliberately uses short-lived, direct SQLcl sessions. A reused client pool would mostly test pool reuse rather than listener routing.
