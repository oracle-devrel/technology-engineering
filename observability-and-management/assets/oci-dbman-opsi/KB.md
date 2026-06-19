# dbman-opsi Knowledge Base

This KB captures implementation and live-tenancy troubleshooting notes for OCI Database Management (DBM) and Operations Insights (OPSI). Keep tenant-specific values out of this file: no OCIDs, IP addresses, usernames beyond generic service users, secrets, Bastion session IDs, or private topology.

## 2026-06-04 CAP DBM/OPSI End-To-End Enablement

### OCI CLI database discovery parser failure

- Symptom: `oci db database list` failed with generated CLI parser warnings about duplicated parameters.
- Scope: Base Database Service discovery.
- Root cause: The installed OCI CLI generated command shape is unreliable for direct database listing in this environment.
- Fix: Use OCI Python SDK discovery with the sequence: compartment -> DB system -> DB homes -> databases -> pluggable databases.
- Validation: SDK discovery found the target DB system, CDB, and PDB while the CLI path failed.

### CDB/PDB orchestration used stale preflight state

- Symptom: A PDB could remain blocked by "parent CDB not enabled" even when the same `configure --apply` run enabled the parent CDB first.
- Root cause: Decisions were computed from one initial preflight snapshot.
- Fix: Process ordered targets sequentially and carry forward parent CDB IDs that were enabled or confirmed in the same run.
- Validation: Added regression coverage for "PDB listed first, CDB enabled first, PDB enabled second."

### DBM enabled does not mean OPSI enabled

- Symptom: `configure --apply` skipped targets when Database Management was already enabled, leaving OPSI Database Insights uncreated.
- Root cause: The orchestrator treated DBM enabled as complete target success.
- Fix: If DBM is already enabled but OPSI credential payloads are ready, continue with the OPSI create/enable step.
- Validation: Added regression coverage for DBM-enabled and OPSI-missing targets.

### OPSI PE co-managed create payload issues

- Symptom: OPSI `create-pe-comanged-database` rejected payloads with `Cannot provide both opsiPrivateEndpointId and dbmPrivateEndpointId`.
- Root cause: The create path accepts the OPSI private endpoint, not both OPSI and DBM private endpoint IDs.
- Fix: Send only `--opsi-private-endpoint-id` for `create-pe-comanged-database`.
- Validation: Unit coverage updated and live command progressed past this validation.

### OPSI database resource type mismatch

- Symptom: OPSI create rejected `ORACLE_DATABASE` as unsupported.
- Root cause: The OPSI API expects OCI resource type strings, not older guessed labels.
- Fix: Use `database` for Base Database Service CDB/non-CDB targets and `pluggabledatabase` for PDB targets.
- Validation: Live command progressed past resource-type validation after config update.

### OPSI `DbcsEntityChangeWorkflowFailed`

- Symptom: OPSI `CREATE_DATABASE_INSIGHT` work request failed after "Starting data collections" with `DbcsEntityChangeWorkflowFailed`; Database Insight list remained empty.
- Known-good state: DBM managed-database inventory listed both the CDB and PDB as VM/ADVANCED, and DBSNMP was OPEN with required grants in both containers.
- Likely cause: OPSI could not start collection with the initial credential/source configuration or secret-access scope.
- Fix path:
  - Prefer Vault-backed `CREDENTIALS_BY_VAULT` payloads for demos.
  - Store the DBSNMP password in OCI Vault.
  - Confirm IAM allows DBM/OPSI principals to read that secret.
  - Retry OPSI create and inspect work request logs/errors.
- Validation status: DBM and DB-side grants validated; OPSI retry remains the next live verification step after Vault payload/config update.

### DB-side access through Bastion

- Symptom: Managed SSH Bastion session required a target Compute instance OCID, but the DBCS flow exposed DB node/VNIC metadata.
- Fix: Use a Bastion port-forwarding session to the DB node private IP on port 22, then SSH to `127.0.0.1:<local-port>` with an authorized key.
- Operational note: If no local key matches the DB system key, add a temporary public key to the DB system authorized keys while preserving existing keys. Remove it after the demo.
- Validation: SSH through the Bastion port-forward reached the DB node and allowed SQL*Plus execution as the Oracle OS user.

### DBSNMP password length

- Symptom: Rotating DBSNMP with a long generated quoted password failed with `ORA-00972: identifier is too long`.
- Root cause: The generated password exceeded what this 19c/profile combination accepted in the SQL statement.
- Fix: Use a shorter generated password that still satisfies complexity rules. Keep it in ignored local storage and OCI Vault only.
- Validation: DBSNMP remained OPEN and required grants were visible in CDB root and PDB.

### Network preflight warnings

- Symptom: Subnet was readable, but route table and service gateway reads returned `NotAuthorizedOrNotFound`; security list check did not prove listener ingress.
- Root cause: Network resources may be in a compartment or policy scope not fully readable by the current principal, or NSGs may be used instead of security lists.
- Fix: Treat these as warnings when target DBM/DB-side validation succeeds, but verify actual private endpoint/listener connectivity through DBM/OPSI work requests and collection startup.

## 2026-06-05 Performance Hub "requires granting of appropriate user privileges"

### Performance Hub greys out / prompts to grant DBSNMP privileges

- Symptom: OCI Console **Performance Hub** for a DBM-managed DBCS shows
  "Performance Hub requires granting of appropriate user privileges. After granting
  the required privileges, reopen Performance Hub." On-demand tasks (AWR, ADDM, ASH
  Analytics, SQL Tuning, Real-Time SQL Monitoring) are unavailable.
- Root cause: the DBM monitoring user (`DBSNMP`) had only the basic + advanced
  *monitoring* grants, not the Performance Hub set (which needs to run advisors and
  the workload repository).
- Fix: as SYSDBA, grant the exact set the Console asks for. `DBSNMP` is a CDB common
  user, so `CONTAINER=ALL` from the root covers the CDB **and** every PDB at once:
  ```sql
  grant create procedure to DBSNMP container=all;
  grant select any dictionary to DBSNMP container=all;
  grant select_catalog_role to DBSNMP container=all;
  grant alter system to DBSNMP container=all;
  grant advisor to DBSNMP container=all;
  grant execute on sys.dbms_workload_repository to DBSNMP container=all;
  ```
  (Diagnostics and/or Tuning Pack licensing applies — review before granting.)
- Toolkit: `03-grant-advanced-diagnostics.sql` now emits these (per container) and
  `04-validate-monitoring-user.sql` checks them. `src/dbman_opsi/db_scripts.py`,
  tests in `tests/test_db_scripts.py`.
- Live DB access for the grant: bastion **port-forward** session to the DB node
  `:22`, `ssh opc` with the DB-system key (kept under `generated/cap-ssh/`,
  gitignored — *not* the bastion-session key, which only authenticates the tunnel),
  `sudo su - oracle`, `sqlplus / as sysdba`, run the grants, then delete the bastion
  session.
- Validation: grants present in `dba_sys_privs` / `dba_role_privs` / `dba_tab_privs`
  in **both `CDB$ROOT` and `PDB1`**; `dbms_workload_repository.create_snapshot`
  succeeded (AWR — the Performance Hub data source — is live). Reopen Performance Hub.

## 2026-06-07 ADDM Spotlight / AWR Explorer empty for a PDB (+ ORA-13750)

### Performance Hub ADDM/AWR show no data for a PDB; SQL Tuning Set create fails

- Symptoms (DBM-managed Base DB, CDB+PDB):
  - **ADDM Spotlight** (PDB): "There are no ADDM analysis details available for the
    time period... Check the current AWR snapshot interval and retention period."
  - **AWR Explorer** (PDB): "No AWR snapshots were found for the selected database.
    Please enable automatic AWR snapshot collection or manually load AWR data for
    this PDB."
  - **Create SQL Tuning Set**: `ORA-13750 - User "DBSNMP" has not been granted the
    ADMINISTER SQL TUNING SET privilege.`
- Root cause: in a CDB, automatic AWR snapshots run at the **root only** by default
  (`AWR_PDB_AUTOFLUSH_ENABLED=FALSE`), so PDB-level ADDM/AWR have nothing to analyze.
  And the DBM monitoring user lacked the SQL-Tuning-Set admin privilege.
- Fix (as SYSDBA; verified live on cap CDB `DBMOPSI` + `PDB1`):
  ```sql
  -- SQL Tuning Set privilege (fixes ORA-13750); DBSNMP is a CDB common user
  grant administer sql tuning set     to DBSNMP container=all;
  grant administer any sql tuning set to DBSNMP container=all;

  -- Enable PDB-level AWR: master switch at root, then per-PDB interval
  alter system set awr_pdb_autoflush_enabled = true scope=both;          -- in CDB$ROOT
  alter session set container = PDB1;
  alter system set awr_pdb_autoflush_enabled = true scope=both;          -- in the PDB
  exec dbms_workload_repository.modify_snapshot_settings(interval=>60, retention=>11520);
  exec dbms_workload_repository.create_snapshot;                          -- seed
  ```
- Gotcha — **ADDM by PDB dbid**: inside a PDB, `dba_hist_snapshot` lists *both* the
  root snapshots and the PDB's own. `DBMS_ADDM.ANALYZE_DB` analyzes the PDB's
  `CON_DBID`, so the snapshot pair must be filtered to that dbid or you hit
  `ORA-13703 ... snapshots not found`:
  ```sql
  select min(snap_id), max(snap_id) into l_beg, l_end from (
    select snap_id from dba_hist_snapshot
    where dbid = sys_context('USERENV','CON_DBID')
    order by snap_id desc fetch first 2 rows only);
  dbms_addm.analyze_db(l_task, l_beg, l_end, sys_context('USERENV','CON_DBID'));
  ```
  Note: `ANALYZE_DB`'s first arg is **IN OUT task_name** — passing it positionally
  *and* as `task_name =>` raises `PLS-00703 multiple instances of named argument`.
- OOTB: the toolkit now generates `05-enable-performance-hub.sql` (AWR autoflush +
  PDB snapshot interval + seed) and adds the SQL-Tuning-Set grants to
  `03-grant-advanced-diagnostics.sql`. Run 05 for the CDB and each PDB.
  (`src/dbman_opsi/db_scripts.py`, tests in `tests/test_db_scripts.py`.)
- Validation: after the fix, `awr_pdb_autoflush_enabled=TRUE`, PDB AWR interval 1h /
  retention 8d, PDB AWR snapshots collecting, `DBMS_ADDM.ANALYZE_DB` task COMPLETED
  with a report ("ADDM detected that the system is a PDB"), and SQL Tuning Set
  creation succeeds.

## 2026-06-05 OPSI list flap → false `validate` NOT_FOUND (get-by-id fix)

### `validate` reports OPSI `NOT_FOUND` while insights are ACTIVE

- Symptom: `dbman-opsi validate` prints `Ops Insights NOT_FOUND (no Database Insight)`
  for the CDB and/or PDB even though `oci opsi database-insights list ...
  --lifecycle-state ACTIVE` shows them `ACTIVE` with
  `database-connection-status-details: SUCCESS`.
- Root cause (the real one): the OPSI `database-insights list` control plane in cap
  is **non-deterministic**. Passing the full `--lifecycle-state` set
  (`CREATING UPDATING ACTIVE FAILED NEEDS_ATTENTION`) together with `--all` in a
  **single** call makes it flap between the full set, a partial set, and an exit-0
  **empty** list for the same compartment, call to call (observed bouncing 0 / 2 / 7
  items within seconds). `validate` matched the target `database-id` against
  whatever that one flaky list happened to return → frequent false `NOT_FOUND`.
  This was previously mislabeled a "known cap quirk"; it is partly self-inflicted by
  the multi-state query shape.
- Reliable signal (measured): a **single-resource**
  `oci opsi database-insights get --database-insight-id <ocid>` is rock-solid
  (10/10 `ACTIVE` for both CDB and PDB across back-to-back calls), where the
  aggregated list flaps. A single `--lifecycle-state ACTIVE` list is stable in good
  windows but still drops to empty in bad windows — not trustworthy alone.
- Fix (code):
  1. `OciCli.list_opsi_database_insights` now queries **one lifecycle state per call
     and unions** results by insight OCID (each per-state call is individually
     fault-tolerant), instead of the broken multi-state + `--all` single call.
  2. New `OciCli.get_opsi_database_insight(insight_id)` (single-resource GET).
  3. `validate` prefers the reliable GET: it reads `target.opsi_database_insight_id`
     (now persisted in config) and calls `database-insights get`; only when the OCID
     is unknown does it fall back to the list, and a positive list hit is then GET
     for the authoritative state.
  4. List-fallback verdict model never emits a *false* `NOT_FOUND`: a positive
     `database-id` hit is authoritative; a negative is `NOT_FOUND` only from a
     **clean window** — every attempt answered, every answer was a **complete**
     per-state union (no lifecycle state skipped by a failed call), non-empty, and
     the **same id-set on ≥2 attempts** without the target. Any empty / erroring /
     incomplete / varying read makes the window inconclusive →
     `UNKNOWN (insight query failed; verify in OCI Console)`. (`list_opsi_database_insights_complete`
     carries the completeness flag; hardening per Codex review — an insight hiding
     in a skipped `FAILED` state can no longer be mistaken for absent.)
  5. Persisted both insight OCIDs in `dbman-opsi.cap.local.yaml`
     (`opsi_database_insight_id:` per target) so `validate` is deterministic.
- Files: `src/dbman_opsi/oci_cli.py`, `src/dbman_opsi/validation.py`. Tests:
  `tests/test_oci_cli.py` (per-state union + fault tolerance),
  `tests/test_validation.py` (get-by-id, positive-authoritative, stability-gated
  NOT_FOUND, varying-list → UNKNOWN).
- Validation: after the fix, `validate` reports `Ops Insights ACTIVE (ENABLED)` for
  both CDB and PDB on repeated runs.
- Discipline note (debugging pitfall that cost time here): `CommandRunner(dry_run=...)`
  **defaults to `True`**. In dry-run mode `run()` returns a stub `{}` for *every*
  call, so `OciCli(profile, region, CommandRunner())` (default) makes every read
  return empty — indistinguishable from the flaky-endpoint symptom. When
  reproducing read-only behavior in a REPL, pass `CommandRunner(dry_run=False)`.
  The CLI's read paths (`validate`, `preflight`, `configure` reads) correctly use
  `dry_run=False`.

## 2026-06-07 Redaction in the data path broke OCID-keyed joins (Data Safe detection)

- Symptom: live `discover` reported **Data Safe ENABLED for every database** in the
  compartment, including databases with no registered Data Safe target. The same
  matcher returned the correct NOT_ENABLED when called directly in a REPL with a
  pasted real OCID.
- Scope: any feature that joins two OCI resources by OCID parsed out of CLI output
  — the new discovery pillar matching (OPSI insight / Data Safe target per DB),
  `create_named_credential`/`set_preferred_named_credential` id linkage,
  `find_managed_database_id`, and `validate`'s insight id-set comparison.
- Root cause: `CommandRunner.run()` ran `redact_text()` over `process.stdout`
  **before** `CommandResult.json()` parsed it, so every OCID became the literal
  string `<OCI_OCID>`. With both sides of a join collapsed to the same token,
  `wanted & candidate_ids` matched everything-to-everything. Redaction (a display
  concern) was wrongly applied in the data path.
- Fix:
  - Runner returns RAW stdout/stderr for `.json()`. Only the dry-run command echo
    and the `RuntimeError` message stay redacted (those are user-facing text).
  - Redact at the display boundary instead: CLI `--json` output wraps `to_dict()`
    in `redact_data()`. Human `discover` output already prints real OCIDs on
    purpose (operators copy them into config; it is their own tenancy).
  - Second bug in the same area: the Data Safe `target-database list` summary has
    `database-details = null` and carries the registered DB OCID in
    `associated-resource-ids`; the matcher now reads that and no longer treats a
    target's own `id` as a DB reference.
- Validation: live on cap — DBMOPSI/PDB1 correctly NOT_ENABLED for Data Safe; the
  three registered ATP targets ENABLED; an unregistered ATP NOT_ENABLED.
- Prevention: never redact in a value that downstream logic parses. Redact only at
  print/serialize boundaries (`--json`, `sanitized()`, log lines, error strings).

## 2026-06-07 Provisioning a new Base DB via zero-start-poc terraform (apply-time failures)

The example planned cleanly but failed at apply with a sequence of issues; all are
now fixed in `terraform/examples/zero-start-poc`:

1. **`Attempt to index null value` on the AD data source.** The `provider "oci"`
   block only set `region`, so it used default auth (wrong/empty tenancy) and
   `oci_identity_availability_domains` returned null. Fix: add
   `config_file_profile = var.config_file_profile` and pass the profile (e.g.
   `cap`). Symptom is generic — any data source silently returns empty.
2. **`vm-block-storage-gb` LimitExceeded.** This is a **Database** service limit
   (not Block Volume), enforced **per availability domain** (1050 GB/AD here). The
   existing DB system filled AD-1 (1024/1050); AD-2/AD-3 were empty. The terraform
   hardcoded `ads[0]`. Fix: `availability_domain_index` var to pin a DB system to
   an AD with headroom. Check with:
   `oci limits resource-availability get --service-name database --limit-name vm-block-storage-gb --availability-domain <AD> --compartment-id <tenancy>`.
3. **`domain name cannot be null` on LaunchDbSystem.** The subnet has no DNS label,
   so the DB system can't derive its network domain and one must be passed
   explicitly. Fix: `domain = var.dbcs_domain`; reuse the existing DB system's
   domain (`oci db system get ... --query 'data.domain'`).
4. **Flex shape needs explicit sizing.** `VM.Standard.E4.Flex` requires
   `cpu_core_count`, and a VM DB system requires `data_storage_size_in_gb`
   (min 256). Added both as vars.

Secrets (`ssh_public_keys`, `db_admin_password`) go in a gitignored
`secrets.auto.tfvars.json` (now `*.auto.tfvars*` and `*.tfvars` are gitignored),
never in `render_tfvars` or committed files.

## 2026-06-07 Data Safe target stuck NEEDS_ATTENTION (ORA-01017) + DBSNMP rotation

- Symptom: `data-safe target-database` registers but stays NEEDS_ATTENTION with
  `lifecycle-details = "Failed to connect to database. ORA-01017: invalid
  username/password"`. The network path is fine (DS PE reached the listener) —
  only the credential failed.
- Root cause: the stored DBSNMP password was stale, and DBSNMP could not be reset
  to it because the **CDB** password verify function requires **2+ special
  characters** (`ORA-20000`). DBSNMP is a **common user**, so its password must be
  changed from the root with `alter user DBSNMP identified by "..." container=ALL`
  — an in-PDB `alter user` fails with `ORA-65066` ("must apply to all containers").
- Fix (single-account POC): rotate DBSNMP to a policy-compliant password
  CONTAINER=ALL via Bastion, then keep the stack consistent by updating BOTH the
  Vault secret (DBM + OPSI both read it via `passwordSecretId`) and the Data Safe
  target credentials (`data-safe target-database update --credentials file://... --force`).
  DBM monitoring stayed `UP`, OPSI `ENABLED`, Data Safe target reached `ACTIVE`.
- `data-safe private-endpoint create` and `target-database update` return WORK
  REQUESTS: `--wait-for-state` takes `SUCCEEDED`, not `ACTIVE`. `update` also needs
  `--force` to skip the confirmation prompt non-interactively.
- Detection nuance: a DATABASE_CLOUD_SERVICE target registered with a PDB service
  name associates (in `associated-resource-ids`) with the **DB system**, so
  discovery attributes Data Safe to the CDB/DB-system level, not the individual PDB.

## Current Demo Validation Checklist

- DB system lifecycle: AVAILABLE.
- CDB lifecycle: AVAILABLE.
- PDB lifecycle: AVAILABLE.
- DBM private endpoint: ACTIVE.
- OPSI private endpoint: ACTIVE.
- CDB DBM status: ENABLED.
- PDB DBM status: ENABLED.
- DBM managed database inventory: CDB and PDB listed as VM/ADVANCED.
- DBSNMP: OPEN in CDB root and PDB.
- Grants: `CREATE SESSION`, `SELECT ANY DICTIONARY`, `SELECT_CATALOG_ROLE`; advanced grants present in the live test.
- OPSI Database Insight: pending successful create after Vault-backed credential payload is wired into config.

## Repeatable Diagnostic Commands

Use these patterns with local variables. Do not paste raw command output containing OCIDs or IPs into committed files.

```bash
oci database-management managed-database list \
  -c "$COMPARTMENT_OCID" \
  --deployment-type VM \
  --management-option ADVANCED

oci database-management work-request list \
  -c "$COMPARTMENT_OCID" \
  --sort-order DESC

oci opsi database-insights list \
  -c "$COMPARTMENT_OCID"

oci opsi work-requests list \
  -c "$COMPARTMENT_OCID" \
  --sort-order DESC
```

SQL validation:

```sql
select username, account_status
from dba_users
where username = 'DBSNMP';

select privilege
from dba_sys_privs
where grantee = 'DBSNMP'
  and privilege in ('CREATE SESSION', 'SELECT ANY DICTIONARY', 'ANALYZE ANY', 'ANALYZE ANY DICTIONARY')
order by privilege;

select granted_role
from dba_role_privs
where grantee = 'DBSNMP'
  and granted_role = 'SELECT_CATALOG_ROLE';
```

### OPSI CREATE_DATABASE_INSIGHT fails at 80% — DbcsEntityChangeWorkflowFailed

- Symptom: `oci opsi database-insights create-pe-comanged-database` (PE-comanaged DBCS)
  reaches 80% then FAILED. Work-request error (via REST
  `GET /20200630/workRequests/{id}/errors`): `Failed to create Database Insight.,
  Error: DbcsEntityChangeWorkflowFailed`. Work-request logs stop at
  `Starting data collections` / `Fetch system infrastructure details`.
  Database Management ADVANCED on the same DB/user/port looks fine, masking the issue.
- Scope: Base Database Service CDB and PDB, OPSI Database Insight with
  `CREDENTIALS_BY_VAULT` over an OPSI private endpoint.
- Why DBM hid it: DBM connects by managed-database OCID and reports lifecycle
  `ENABLED` even when its data-path auth is broken; only OPSI's create runs an
  explicit connect-and-collect test, so OPSI is the first place the failure surfaces.
- Root cause (two independent defects, both fatal to OPSI):
  1. **Wrong service name.** OPSI `connection-details.serviceName` was set to the
     bare DB/PDB name (e.g. `DBMOPSI`, `PDB1`). The listener registers no such
     service — real services are domain-qualified
     (`<db_unique_name>.<db_domain>` for the CDB root, `<pdb_name>.<db_domain>`
     for the PDB). Connecting with the bare name returns **ORA-12514**.
  2. **Credential drift.** The monitoring-user (DBSNMP) password stored in the
     Vault secret did not match the database. Connecting with the correct service
     returned **ORA-01017**. The Vault password also violated the DB password
     verify function (**ORA-20000: password must contain 2 or more special
     characters**), so it could never have been applied — the secret was written
     but the `ALTER USER` had silently been rejected at provisioning time.
- Diagnosis path (no Console needed):
  - `oci opsi work-requests list` → find FAILED `CREATE_DATABASE_INSIGHT`.
  - `oci raw-request --http-method GET --target-uri .../workRequests/{id}/errors`
    and `.../logs` (the `oci opsi work-requests` CLI group has no errors/logs
    subcommand in 3.81.x).
  - On the DB host (bastion port-forward to :22 → `sqlplus / as sysdba`):
    `lsnrctl status` to list real services; test
    `DBSNMP/<pw>@<db_ip>:1521/<service>` for each candidate to separate
    ORA-12514 (wrong service) from ORA-01017 (wrong password).
  - Repeated bad-password probes will lock DBSNMP (**ORA-28000**); unlock with
    `ALTER USER DBSNMP ACCOUNT UNLOCK CONTAINER=ALL`.
- Fix:
  1. Set a policy-compliant DBSNMP password (>=2 special chars, mixed case,
     digit) and sync it to the Vault secret:
     `ALTER USER DBSNMP IDENTIFIED BY "<pw>" CONTAINER=ALL;` then
     `oci vault secret update-base64 --secret-id <id> --secret-content-content <b64>`.
  2. Correct `service_name` in the config to the real listener service, regenerate
     the OPSI payloads, then disable+delete the FAILED insights
     (`disable` first — a FAILED insight cannot be deleted directly:
     "Database Insight should be disabled before it can be deleted") and re-run
     `enable --apply`.
- Validation: new `CREATE_DATABASE_INSIGHT` SUCCEEDED 100%; insight
  `lifecycle-state ACTIVE`, `database-connection-status-details SUCCESS` for both
  CDB and PDB.

### enable is not idempotent — DBM 409 aborts before OPSI

- Symptom: `dbman-opsi enable --apply` crashes with
  `IncorrectState: Either DatabaseManagement is already enabled or request to
  enable it is already created.` (HTTP 409) and never reaches the Ops Insights
  step. Hits every re-run once DBM is enabled.
- Root cause: `EnablementService._enable_cloud_database` called the DBM enable
  unconditionally and let the runner raise, so a benign already-enabled state
  killed the whole flow.
- Fix: `OciCli.run_tolerating(args, tolerated)` swallows errors whose message
  contains an idempotent marker ("already enabled" / "already created") and
  re-raises anything else; `_enable_cloud_database` uses it and continues to OPSI.

### validate could not see OPSI collection state (silent OPSI failure)

- Symptom: `dbman-opsi validate` printed
  "Ops Insights requires Database Insight validation" for every DBCS/Exadata
  target regardless of the real state, so a fleet of FAILED insights looked the
  same as healthy ones.
- Fix: `validate` now calls `OciCli.list_opsi_database_insights` (querying all
  lifecycle states explicitly, since the list excludes FAILED by default), matches
  by `database-id == target.resource_id`, and reports the real
  `lifecycle-state (status)` — e.g. `ACTIVE (ENABLED)`, `FAILED (ENABLED)`,
  `NOT_FOUND (no Database Insight)`. Retries once on transient
  NotAuthorizedOrNotFound and degrades to `UNKNOWN (...)` rather than lying.
- Note: in CAP the OPSI `database-insights list` endpoint intermittently returns
  NotAuthorizedOrNotFound / empty even when insights exist and are ACTIVE; the
  authoritative cross-checks are the SUCCEEDED `CREATE_DATABASE_INSIGHT` work
  request and `database-connection-status-details: SUCCESS` on the insight.

### DBSNMP re-locks after password rotation (ORA-28000 lock loop)

- Symptom: after rotating the DBSNMP password (to fix OPSI/DBM credential drift),
  DBM monitoring goes green briefly then flips to **Stopped** / red timeline, and
  OPSI collection stalls ("Needs attention"). Console error:
  `ORA-28000 - The account is locked` (`DB_Account_Lock`). Account status cycles
  OPEN -> LOCKED within minutes of being unlocked.
- Root cause: on Base Database Service the **local Oracle Cloud Agent** monitors
  the DB as DBSNMP using the password set at provisioning time. Rotating DBSNMP's
  password without updating that agent leaves a consumer repeatedly authenticating
  with the old password; it trips the profile's `FAILED_LOGIN_ATTEMPTS` and locks
  the account, which then knocks out DBM and OPSI (collateral damage) since they
  share the same DB user.
- Fix (break the lock loop): put DBSNMP on a dedicated non-locking common profile.
  ```sql
  CREATE PROFILE C##DBSNMP_MON LIMIT FAILED_LOGIN_ATTEMPTS UNLIMITED PASSWORD_LIFE_TIME UNLIMITED;
  ALTER USER DBSNMP PROFILE C##DBSNMP_MON CONTAINER=ALL;   -- common profile needs C## prefix (ORA-65140 otherwise)
  ALTER USER DBSNMP ACCOUNT UNLOCK CONTAINER=ALL;
  ```
  A bare `ACCOUNT UNLOCK` is not enough — the stale agent re-locks it within
  minutes. With the non-locking profile, the stale consumer's failures no longer
  lock the account, so DBM (via DBM PE) and OPSI (via OPSI PE) — which use the
  correct password from the Vault secret — connect and stay connected.
- Prevention: avoid rotating DBSNMP unless every consumer is updated. If a rotation
  is unavoidable, assign the non-locking monitoring profile first. DBM monitoring
  status takes a few minutes to re-poll from UNKNOWN/Stopped back to healthy after
  the account is fixed.
- Related: DBM "Credential required ... Advanced diagnostics preferred credential
  is not set" is a separate item — the managed database's `PC_READ`/`PC_WRITE`
  preferred credentials are `NOT_SET` (only `MONITORING` is `SET`). Set them with
  `oci database-management preferred-credential update --type BASIC` (userName
  DBSNMP, role NORMAL, passwordSecretId <vault-secret>) or via the Console banner;
  it gates on-demand advanced tasks, not basic collection.

### DBM monitoring stays Stopped after re-enable — stale connection (wrong service name)

- Symptom: Database Management monitoring shows **Stopped** (red timeline, Console
  `database-status: UNKNOWN/Stopped`) even after the DBSNMP account is unlocked and
  the Vault password is correct. The DBM "Managed database details" still loads but
  never collects.
- Root cause: DBM was first enabled with the wrong `--service-name` (bare
  `DBMOPSI`/`PDB1`). A later `enable --apply` only **tolerated** the
  already-enabled 409 and skipped DBM, so the corrected service name (and rotated
  credential) never reached the DBM connection — it kept resolving a non-existent
  service (ORA-12514) and could not connect.
- Fix: reconcile the existing DBM connection in place with the corrected values —
  no disable/re-enable needed:
  ```bash
  oci db database modify-database-management --database-id <cdb> \
    --management-type ADVANCED --service-name <db_unique_name>.<domain> \
    --password-secret-id <secret> --private-end-point-id <dbm-pe> \
    --user-name DBSNMP --role NORMAL --protocol TCP --port 1521 \
    --wait-for-state AVAILABLE          # NOTE: DB lifecycle state, not work-request SUCCEEDED
  oci db pluggable-database modify-pluggable-database-management --pluggable-database-id <pdb> \
    --service-name <pdb>.<domain> --password-secret-id <secret> --private-end-point-id <dbm-pe> \
    --user-name DBSNMP --role NORMAL --protocol TCP --port 1521 --wait-for-state AVAILABLE
  ```
  After the modify, `database-status` flips to `UP` within a minute or two.
- Code: `enable` now reconciles automatically — on an already-enabled DBM it calls
  `cloud_modify_command` (modify-(pluggable-)database-management) so a corrected
  service name / rotated credential actually takes effect on re-run (needed for
  repeatable ORM/script enablement). `src/dbman_opsi/enablement.py`.
- Console URL bases (eu-frankfurt-1): DB systems `cloud.oracle.com/dbaas/dbsystems`.
  (The Database Management / Ops Insights SPA routes are not the obvious
  `/dbmgmt` or `/opsi`; navigate via the console menu rather than guessing.)
