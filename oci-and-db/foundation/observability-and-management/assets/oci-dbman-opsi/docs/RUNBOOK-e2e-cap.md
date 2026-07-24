# Runbook: dbman-opsi End-to-End Enablement & Verification (cap)

Reproducible record of running the full `dbman-opsi` flow against a live Base
Database Service deployment in the **cap** staging tenancy (`eu-frankfurt-1`),
and the defects found and fixed along the way.

All tenant-specific values (OCIDs, IPs, passwords, service GUIDs) are redacted —
resolve them from the gitignored local config and `~/.claude/private/`.

Targets: one CDB (`DBMOPSI`) + one PDB (`PDB1`), both `management_type: ADVANCED`,
DBSNMP monitoring user, OPSI PE-comanaged with `CREDENTIALS_BY_VAULT`.

---

## Phase 0 — Confirm live infra (read-only)

```bash
oci iam tenancy get --tenancy-id <cap-tenancy> --query 'data.name'      # -> <cap-tenancy-name>
oci db database get --database-id <cdb> --query 'data."lifecycle-state"' # -> AVAILABLE
oci db database get --database-id <cdb> --query 'data."database-management-config"'  # ENABLED / ADVANCED
oci db pluggable-database get --pluggable-database-id <pdb> --query 'data."pluggable-database-management-config"'
oci database-management private-endpoint get --private-endpoint-id <dbm-pe> --query 'data."lifecycle-state"'   # ACTIVE
oci opsi opsi-private-endpoint get --opsi-private-endpoint-id <opsi-pe> --query 'data."lifecycle-state"'        # ACTIVE
oci vault secret get --secret-id <secret> --query 'data."lifecycle-state"'  # ACTIVE
```

Expected: tenancy confirmed; CDB & PDB `AVAILABLE`; both PEs `ACTIVE`;
Vault secret `ACTIVE`.

## Phase 1 — doctor + preflight (read-only)

```bash
dbman-opsi doctor                                          # python/oci/terraform OK
dbman-opsi preflight --config dbman-opsi.cap.local.yaml    # verdict: READY
```

Known non-blocking WARNs in cap: `service-gateway list` and `route-table get`
return `NotAuthorizedOrNotFound` (the cap user lacks those VCN reads); the
security-list 1521 heuristic warns when an NSG (not the security list) covers
the port. `target.monitoring_user` is `[MANUAL]` — proven DB-side in Phase 2.

## Phase 2 — DBSNMP connectivity proof (bastion)

```bash
# fresh port-forward session to the DB node :22, then tunnel local 8022 -> :22
oci bastion session create-port-forwarding --bastion-id <bastion> \
  --ssh-public-key-file <pub> --target-private-ip <db-ip> --target-port 22 \
  --session-ttl 10800 --wait-for-state SUCCEEDED
ssh -i <key> -N -L 8022:<db-ip>:22 -p 22 <session-ocid>@host.bastion.<region>.oci.oraclecloud.com ...
ssh -i <key> -p 8022 opc@localhost   # then: sudo su - oracle
```

On the DB host as `oracle`:

```bash
lsnrctl status     # <-- lists the REAL listener services (critical, see Defect 1)
sqlplus / as sysdba <<'SQL'
  select username, account_status from dba_users where username='DBSNMP';     -- expect OPEN
  alter session set container=PDB1;
  select username, account_status from dba_users where username='DBSNMP';
SQL
# prove OPSI-style TCP login per real service:
sqlplus -L DBSNMP/<pw>@<db-ip>:1521/<real-service>
```

## Phase 3 — generators (idempotent)

```bash
dbman-opsi generate-db-scripts     --config dbman-opsi.cap.local.yaml --output generated/db-scripts
dbman-opsi generate-opsi-payloads  --config dbman-opsi.cap.local.yaml --output generated/cap-opsi-payloads
dbman-opsi generate-agent-scripts  --config dbman-opsi.cap.local.yaml
```

## Phase 4 — enable + validate (the no-errors gate)

```bash
dbman-opsi enable   --config dbman-opsi.cap.local.yaml --apply
dbman-opsi validate --config dbman-opsi.cap.local.yaml
# final state checks:
oci opsi work-requests list -c <cmpt> --sort-order DESC      # CREATE_DATABASE_INSIGHT SUCCEEDED 100%
oci database-management managed-database list -c <cmpt>      # DBMOPSI, PDB1 -> ADVANCED
```

End state: DBM `ADVANCED` on both; OPSI insights `ACTIVE / ENABLED`,
`database-connection-status-details: SUCCESS`; 0 FAILED.

---

## Defects found & fixed

### Defect 1 — OPSI insight create fails at 80% (`DbcsEntityChangeWorkflowFailed`)

Two independent root causes, both DB-connection failures the OPSI create test
surfaces (DBM hid them because it connects by OCID, not service+credential):

1. **Wrong `service_name`** — config used the bare names `DBMOPSI` / `PDB1`, but
   the listener only registers domain-qualified services
   (`<db_unique_name>.<domain>` for the CDB, `<pdb_name>.<domain>` for the PDB) →
   **ORA-12514**. Fixed by setting the real services in
   `dbman-opsi.cap.local.yaml` and regenerating OPSI payloads.
2. **DBSNMP credential drift** — the Vault secret password didn't match the DB
   (**ORA-01017**) and itself violated the DB verify function (**ORA-20000:
   >=2 special characters**), so it had never been applied. Fixed by setting a
   compliant DBSNMP password (`ALTER USER DBSNMP IDENTIFIED BY "<pw>"
   CONTAINER=ALL`) and syncing it into the Vault secret
   (`oci vault secret update-base64`).

To re-create after a failed attempt, the insight must be **disabled before
delete** (`oci opsi database-insights disable` then `... delete --force`).

See `KB.md` for the full diagnosis path (work-request errors via `oci
raw-request`, `lsnrctl status`, per-service `sqlplus` probes).

### Defect 2 — `enable` not idempotent (code fix)

`enable --apply` aborted on the already-enabled DBM **409 IncorrectState** before
reaching OPSI. Added `OciCli.run_tolerating()` so an already-enabled DBM is a
no-op and the flow continues. (`src/dbman_opsi/oci_cli.py`,
`src/dbman_opsi/enablement.py`; tests in `tests/test_enablement.py`.)

### Defect 3 — `validate` blind to OPSI state (code fix)

`validate` printed a generic "requires Database Insight validation" for every
target, so FAILED insights looked identical to healthy ones. It now queries the
insight lifecycle (`OciCli.list_opsi_database_insights`, all lifecycle states)
and reports `ACTIVE (ENABLED)` / `FAILED (ENABLED)` / `NOT_FOUND` / `UNKNOWN`,
with a retry on transient 404. (`src/dbman_opsi/validation.py`; tests in
`tests/test_validation.py`.)

## Known cap quirk (root-caused in Defect 6)

The OPSI `database-insights list` control-plane endpoint is **non-deterministic**:
it flaps between the full set, a partial set, and an exit-0 empty list (and
sometimes `NotAuthorizedOrNotFound`) for the same compartment, call to call — the
multi-`--lifecycle-state` + `--all` query shape makes it worse. Authoritative reads
that don't depend on it: a single-resource `database-insights get` **by insight
OCID** (reliable 10/10), the SUCCEEDED `CREATE_DATABASE_INSIGHT` work request, and
`database-connection-status-details: SUCCESS` on the insight. See Defect 6.

## Defect 4 — DBM monitoring stays Stopped after re-enable (stale service name)

DBM was first enabled with the wrong service name, and the idempotent re-run only
tolerated the already-enabled 409 and **skipped** DBM, so the corrected service
name never took effect — monitoring stayed Stopped (ORA-12514). Reconciled in place
with `modify-(pluggable-)database-management` (service name + current secret);
`database-status` then flipped to **UP**. `enable` now reconciles automatically on
an already-enabled DBM (`cloud_modify_command` in `enablement.py`), so repeat
runs / ORM are self-healing for connection drift.

## Defect 5 — DBSNMP lock loop after password rotation

See `KB.md`. Rotating DBSNMP broke the DBCS local agent (old password) which
re-locked the account (ORA-28000), taking DBM + OPSI down. Fixed by moving DBSNMP
to a non-locking common profile `C##DBSNMP_MON`
(FAILED_LOGIN_ATTEMPTS/PASSWORD_LIFE_TIME UNLIMITED).

## Defect 6 — `validate` false `NOT_FOUND` from the flaky OPSI list (code fix)

Re-running the full e2e (2026-06-05) surfaced that `validate` (Defect 3's
list-based path) reported `Ops Insights NOT_FOUND` for the CDB and PDB while both
insights were `ACTIVE / SUCCESS`. Root cause: the aggregated `database-insights
list` flaps (0/2/7 items call-to-call), worsened by the 5-`--lifecycle-state` +
`--all` shape; `validate` matched the target against one flaky response. Fix:

- `OciCli.list_opsi_database_insights` now queries **one lifecycle state per call
  and unions** by insight OCID (each call fault-tolerant) instead of the broken
  single multi-state call.
- New `OciCli.get_opsi_database_insight(insight_id)`; `validate` prefers this
  **reliable GET by insight OCID** (`target.opsi_database_insight_id`, now persisted
  in config), falling back to the list only to discover an unknown OCID.
- List-fallback verdict model never emits a false `NOT_FOUND`: it uses
  `OciCli.list_opsi_database_insights_complete()` (per-state union + a
  `complete` flag) and a **clean-window** rule — `NOT_FOUND` only when every
  attempt answered, the read was complete and non-empty, and the id-set was
  stable and reproducibly missing the target; a positive hit is authoritative
  (then GET); empty/varying/incomplete → `UNKNOWN`.
- (`src/dbman_opsi/oci_cli.py`, `src/dbman_opsi/validation.py`; tests in
  `tests/test_oci_cli.py`, `tests/test_validation.py`.) After the fix `validate`
  reports `ACTIVE (ENABLED)` for both targets deterministically. Full KB entry:
  `KB.md` → "2026-06-05 OPSI list flap".

## Defect 7 — Performance Hub privileges (DB-side grant)

The OCI Console Performance Hub showed "Performance Hub requires granting of
appropriate user privileges." The DBM monitoring user `DBSNMP` had the basic +
advanced monitoring grants but not the Performance Hub / AWR set. Applied as SYSDBA
(via bastion port-forward → `ssh opc` with the DB-system key → `sudo su - oracle` →
`sqlplus / as sysdba`), using `CONTAINER=ALL` so the CDB common user covers CDB+PDB:

```sql
grant create procedure to DBSNMP container=all;
grant select any dictionary to DBSNMP container=all;
grant select_catalog_role to DBSNMP container=all;
grant alter system to DBSNMP container=all;
grant advisor to DBSNMP container=all;
grant execute on sys.dbms_workload_repository to DBSNMP container=all;
```

The toolkit now generates these in `03-grant-advanced-diagnostics.sql` and checks
them in `04-validate-monitoring-user.sql` (`src/dbman_opsi/db_scripts.py`). Verified
present in `CDB$ROOT` and `PDB1`; `dbms_workload_repository.create_snapshot`
succeeded (AWR — the Performance Hub data source — confirmed live, 46 snapshots).

## Defect 8 — ADDM Spotlight / AWR Explorer empty for the PDB (+ ORA-13750)

Console **ADDM Spotlight** and **AWR Explorer** for `PDB1` were empty ("no ADDM
analysis details" / "No AWR snapshots were found for this PDB"), and creating a
**SQL Tuning Set** failed with `ORA-13750` (DBSNMP lacks `ADMINISTER SQL TUNING
SET`). Root cause: in a CDB, automatic AWR snapshots run at the **root only** by
default (`AWR_PDB_AUTOFLUSH_ENABLED=FALSE`). Fixed as SYSDBA on cap CDB+PDB1:

```sql
grant administer sql tuning set     to DBSNMP container=all;   -- fixes ORA-13750
grant administer any sql tuning set to DBSNMP container=all;
alter system set awr_pdb_autoflush_enabled = true scope=both;  -- CDB$ROOT
alter session set container = PDB1;
alter system set awr_pdb_autoflush_enabled = true scope=both;  -- PDB
exec dbms_workload_repository.modify_snapshot_settings(interval=>60, retention=>11520);
exec dbms_workload_repository.create_snapshot;                  -- seed
```

`DBMS_ADDM.ANALYZE_DB` over the latest two **PDB-dbid** snapshots (filter by
`sys_context('USERENV','CON_DBID')`, else `ORA-13703`) completed with a report
("ADDM detected that the system is a PDB"). OOTB: the toolkit now emits
`05-enable-performance-hub.sql` (autoflush + PDB snapshot interval + seed) and adds
the STS grants to `03-grant-advanced-diagnostics.sql`. See `KB.md` 2026-06-07.

## Defect 9 — OCID redaction in the data path broke OCID-keyed joins (code fix)

Adding three-pillar discovery exposed that `CommandRunner.run()` redacted command
**stdout before `.json()` parsed it**, collapsing every OCID to `<OCI_OCID>`. Any
logic that joins resources by OCID (Data Safe / OPSI detection, named-credential
id lookup, `validate`'s insight id-set) matched everything-to-everything — live
`discover` falsely reported Data Safe `ENABLED` for *every* database. Fix: the
runner returns **raw** stdout for `.json()`; redaction moved to the display
boundary (`--json` wraps `redact_data`, errors/dry-run echo stay redacted). Human
`discover` output intentionally keeps real OCIDs (operator copies them to config).
Matcher also reads `associated-resource-ids` (the Data Safe LIST summary has
`database-details: null`) and never treats a target's own id as a DB reference.
(`runner.py`, `cli.py`, `status.py`; `KB.md` 2026-06-07.)

## Defect 10 — zero-start-poc Terraform could plan but not apply a DBCS (code fix)

Provisioning a new cap DBCS hit four apply-time failures, all now fixed in
`terraform/examples/zero-start-poc`: (1) provider used default auth → AD data
source null (`Attempt to index null value`) — added `config_file_profile`;
(2) `400-LimitExceeded vm-block-storage-gb` — a **per-AD Database** limit (AD-1
was 1024/1050; AD-2/AD-3 empty) — added `availability_domain_index`;
(3) `domain name cannot be null` (subnet has no DNS label) — added
`domain = var.dbcs_domain`; (4) Flex shape needs `cpu_core_count` +
`data_storage_size_in_gb`. Secrets go in a gitignored `secrets.auto.tfvars.json`.
See `KB.md` 2026-06-07.

## Defect 11 — Data Safe target NEEDS_ATTENTION (ORA-01017) + DBSNMP rotation

Registering DBMOPSI/PDB1 as a Data Safe target left it `NEEDS_ATTENTION` with
`ORA-01017` — the DS private endpoint reached the listener, but the DBSNMP
password was stale and could not be reset to it (CDB verify function needs **2+
special chars**, `ORA-20000`). DBSNMP is a **common user**, so the password is set
from the root with `CONTAINER=ALL` (`ORA-65066` if attempted inside a PDB). Fix
(single-account POC): rotate DBSNMP to a policy-compliant password and keep the
stack consistent — update the **one Vault secret** (DBM + OPSI both read it via
`passwordSecretId`) and the Data Safe target creds
(`data-safe target-database update --credentials file://... --force`). DBM stayed
`UP`, OPSI `ENABLED`, Data Safe target reached `ACTIVE`. Also: `data-safe
private-endpoint create` / `target-database update` return work requests
(`--wait-for-state SUCCEEDED`, not `ACTIVE`). See `KB.md` 2026-06-07.

## Defect 12 — OPSI create crashed on the post-enable propagation race (code fix)

Enabling a freshly-provisioned DBCS: right after DBM enable, the managed database
is not yet visible to Ops Insights, so `create-pe-comanaged` returns
`400-MissingParameter "Provided database resource details were missing"` and the
unhandled error crashed the whole orchestrated `configure` run before the PDB was
processed. `EnablementService` now **retries** the OPSI create on the propagation
markers (bounded `opsi_create_attempts`/`opsi_create_delay`, injectable sleeper)
and only re-raises after exhausting them. (`enablement.py`; tests in
`tests/test_enablement.py`.)

## Phase 6 — Data Safe + a second, freshly-provisioned DBCS (3-pillar end-to-end)

- **Existing DB:** created a Data Safe private endpoint in the DB subnet, applied
  the Data Safe service-account grants (`audit_viewer`/`audit_admin`) via Bastion,
  rotated DBSNMP, and registered PDB1 → Data Safe target **ACTIVE** alongside the
  existing DBM `UP` + OPSI `ENABLED`.
- **New DBCS (`dbman-opsi-dbcs2`, AD-2):** provisioned via the fixed Terraform,
  set DBSNMP + grants via Bastion, then enabled all three pillars with
  `configure --apply` (DBM+OPSI, CDB→PDB) and `data-safe --apply`. Final
  discovery: CDB `dbmanops` `dbm=ENABLED, opsi=ENABLED, ds=ENABLED`; both Data
  Safe targets **ACTIVE**.

## Phase 7 — Cross-region OPSI showcase (Chicago)

Goal: show the new Ops Insights multi-region experience from one Console flow:
Data Object Explorer queries selected regions and aggregates results; the
Configuration and Capacity dashboards use the same selected regions.

Provision one additional target in `us-chicago-1` for the POC. Generate a
separate gitignored config whose top-level `region` is `us-chicago-1` while
reusing the same tenancy/profile/compartment pattern:

```bash
dbman-opsi init-region --config dbman-opsi.cap.local.yaml \
  --region us-chicago-1 \
  --output dbman-opsi.cap-chicago.local.yaml \
  --target-kind dbcs
dbman-opsi provision --config dbman-opsi.cap-chicago.local.yaml --render-only
# review terraform/examples/zero-start-poc-us-chicago-1/terraform.tfvars.json, then:
dbman-opsi provision --config dbman-opsi.cap-chicago.local.yaml --apply
dbman-opsi import-tf-outputs --config dbman-opsi.cap-chicago.local.yaml
dbman-opsi db-exec --config dbman-opsi.cap-chicago.local.yaml --apply \
  --bastion-id <bastion> --target-ip <db-ip> --ssh-key <key>
dbman-opsi configure --config dbman-opsi.cap-chicago.local.yaml --apply
dbman-opsi validate --config dbman-opsi.cap-chicago.local.yaml
```

For Autonomous Database, use `--target-kind autonomous` and provide
`TF_VAR_adb_admin_password` through the environment. For DBCS, provide the SSH
public key and `TF_VAR_db_admin_password`; keep the generated Terraform secret
variables in ignored local files only. `init-region` creates a test VCN/subnet by
default; pass `--vcn-id <regional-vcn> --subnet-id <regional-private-subnet>` to
reuse an existing Chicago network.

Local paid provisioning uses `.env.local` as the operator-owned secret boundary:

```bash
cp .env.local.example .env.local
chmod 600 .env.local
# Fill in TF_VAR_db_admin_password and TF_VAR_ssh_public_keys locally.
# Set TF_VAR_create_identity_policy=false when IAM is managed outside this stack.
```

The CLI loads `.env.local` automatically. Do not paste real values into this
runbook, generated configs, screenshots, `terraform.tfvars.json`, or public app
code. Terraform state is also local-sensitive after apply; keep it in the
gitignored regional work directory and restrict access to the workstation.

After Chicago is enabled, add the Chicago target to the combined CAP showcase
config with `region: us-chicago-1` on that target, then declare the Console region
selector set:

```bash
dbman-opsi cross-region --config dbman-opsi.cap.local.yaml \
  --regions eu-frankfurt-1,us-chicago-1
dbman-opsi validate --config dbman-opsi.cap.local.yaml
```

Expected API state: Frankfurt and Chicago targets validate from their own regions;
DBCS/PDB targets show DBM `ENABLED`/`ADVANCED` and OPSI `ACTIVE`, while Autonomous
targets show Database Management and Ops Insights enabled on the Autonomous DB
resource.

Expected Console state: in Ops Insights Data Object Explorer, select
`eu-frankfurt-1` and `us-chicago-1` in the region selector, run the query, and
verify returned rows include region context. Repeat the same region selection on
the Configuration and Capacity dashboards.

CAP verification note: the Chicago DBCS path has been generated and checked with
`terraform init -backend=false` plus `terraform validate` in
`terraform/examples/zero-start-poc-us-chicago-1/`. On 2026-06-19 the paid
Chicago DBCS resource was created with local-only variables loaded from
`.env.local`; Terraform state now manages the VCN, private subnet, Service
Gateway, DB system, and DBM private endpoint in the ignored regional workdir.
The OPSI private endpoint was created through `prepare-prereqs --apply` and
persisted into the ignored local config.

Remaining enablement handoff for Chicago:

- Store the monitoring-user password in a regional Vault secret and set
  `password_secret_id` in `dbman-opsi.cap-chicago.local.yaml`.
- Run the generated DB-side scripts from `generated/db-scripts-chicago/` through
  a secure DB access path so `DBSNMP` has basic monitoring, advanced diagnostics,
  and Performance Hub grants.
- Re-run `configure --apply` and then `validate`; expected first post-provision
  state before those steps is DBM `NOT_ENABLED`.

## Final verified state (API)

- DBM: CDB `DBMOPSI` **UP**, PDB `PDB1` **UP** (ADVANCED).
- OPSI: DBMOPSI + PDB1 **ACTIVE**, `database-connection-status-details: SUCCESS`.
- `validate` reports `Ops Insights ACTIVE (ENABLED)` for both, deterministically
  (via GET-by-OCID), across repeated runs.
- Performance Hub: DBSNMP holds the AWR/advisor + SQL-Tuning-Set privileges in
  CDB+PDB; AWR snapshot creation succeeds.
- ADDM/AWR: `awr_pdb_autoflush_enabled=TRUE`, PDB AWR interval 1h / retention 8d,
  PDB snapshots collecting; `DBMS_ADDM.ANALYZE_DB` (PDB) COMPLETED with a report.
  ADDM Spotlight / AWR Explorer now populate; SQL Tuning Set creation succeeds.

## Phase 5 — OCI Console screenshots

Captured via **CDP attach** (extension-free; see `~/.claude/CLAUDE.md` "Browser
Automation"). User launches Chrome with `--remote-debugging-port=9222
--user-data-dir=~/.oci-cdp-profile`, logs in normally, then
`~/oci-cli/bin/python /tmp/oci_cdp_capture.py` connects over CDP and screenshots.

Working console route (eu-frankfurt-1): Managed Databases lives at
`/dbmgmt-ui/administration/managed_databases` (NOT `/dbmgmt/managed-databases`).
The console is an Oracle JET SPA that renders list rows and much content in
**shadow DOM**, so Playwright `get_by_role`/`get_by_text` clicks and `a[href]`
discovery do not reach them — drive by navigating the menu yourself (CDP attach to
your own logged-in Chrome) and screenshot the current tab, rather than automating
clicks. Automation-*launched* Chrome also hits the SSO/MFA wall; CDP-attach to a
real logged-in browser is the reliable path.

Committed (redacted) screenshots in `docs/screenshots/`:

- `console-01-managed-databases.png` — DBMOPSI (Container DB) + PDB1 (Pluggable DB)
  **Enabled / Full**, ADVANCED.
- `console-02-dbmopsi-summary.png` — DBMOPSI **Available**; Performance Hub / ADDM
  Spotlight / AWR Explorer accessible (no privilege prompt); monitoring timeline
  all-green.
- `console-03-dbmopsi-pdbs.png` — PDBs tab: PDB1 **Up** with live Performance Hub
  metrics; full Performance/Tuning nav.
- `console-04-data-safe-targets.png` — Data Safe **Target databases**: the three
  registered targets (`dbman-opsi-dbcs-PDB1`, `dbman-opsi-dbcs2-cdb`,
  `dbman-opsi-dbcs2-PDB1`) all **Active**.
- `console-05-performance-hub.png` — Performance Hub: Activity Summary / Average
  Active Sessions + ASH Analytics (SQL-detail tables blurred — live SQL/service/users).
- `console-06-data-safe-assessment.png` — Data Safe **Security Assessment**: Risk
  level + Risks by category + Top-5 security controls (aggregate charts only).
- `console-07-capacity-planning.png` — Ops Insights **Database Capacity Planning**:
  database inventory and CPU/storage/memory/I/O cards.
- `console-08-capacity-trend-forecast.png` — single-resource trend and forecast
  panel with forecast settings.
- `console-09-capacity-aggregate.png` — capacity aggregate treemap and all-database
  forecast trend.
- `console-10-sql-insights-fleet-analysis.png` — SQL Insights fleet analysis; live
  resource identifiers and SQL detail are redacted.
- `console-11-sql-insights-database-analysis.png` — SQL Insights database analysis;
  SQL IDs/modules/resource values are redacted.
- `console-12-sql-explorer-multiregion.png` — SQL Explorer with the multi-region
  selector showing Frankfurt + Chicago in one query flow.
- `console-13-db-performance.png` — DB Performance dashboard with activity cards
  and table-level identifiers redacted.
- `console-14-opsi-fleet-administration.png` — Ops Insights fleet administration;
  status/feature columns are visible while resource names and compartment values
  are redacted.

The Managed Databases (`console-01`) and fleet (`console-02`) views now show **both**
DB systems — the original `DBMOPSI`/`PDB1` and the freshly-provisioned
`dbmanops`/`dbmanops_pdb1` — all Enabled/Full.

### CAP fleet rows needing attention

The Console fleet-administration screenshot also showed three Autonomous Database
rows in **Needs Attention**. A redacted API triage with the `cap` profile on
2026-06-19 found:

- Autonomous Database resource state: `AVAILABLE`.
- Database Management resource state: `ENABLED`, with `ADVANCED` management.
- Operations Insights resource flag: `ENABLED`; an explicit enable dry-run is
  rejected by OCI as already enabled.
- Data Safe resource flag: `REGISTERED`.
- DBM preferred credential roles: `MONITORING`, `PC_READ`, and `PC_WRITE` exist
  for each affected Autonomous Database.
- OPSI `database-insights list` returns the VM CDB/PDB records as
  `ACTIVE`/`SUCCESS`; ATP-S records are not returned by the list endpoint even
  though the Autonomous DB resource-level OPSI flag is `ENABLED`.

Do not repair this by cycling the databases. Treat it as an Autonomous Database
OPSI collection-health/Console inventory issue: verify it from **Observability &
Management > Collection issues** and, if the Console still reports the rows after
the next collection interval, raise an OCI service request with the redacted API
evidence above. The CLI path has no safe force-refresh verb for this state.

Redaction: a DOM/text pass masks OCIDs, IPs, db_unique_name+domain, tenancy/account
name and emails; for operator-pasted images, sensitive bands (header
region/account/avatar, compartment chip), resource-name columns, SQL ID columns,
and live SQL/service/module tables are blurred or covered with PIL. Raw captures
go to `docs/screenshots/raw/` (gitignored) — only redacted images are committed.

### Capturing more Console views (CDP-attach recipe)

The Data Safe and Performance Hub views (`console-04`/`05`) were captured with the
CDP-attach flow above and are committed. The OCI Console is a JET SPA whose left-nav
and list rows live in **shadow DOM**, so Playwright/JS clicks do not reach them —
the reliable recipe is: **you** navigate the menu in the logged-in CDP Chrome, then a
small `connect_over_cdp` helper screenshots the current tab to
`docs/screenshots/raw/`, and a PIL pass blurs the region/account band, compartment
chip, and any SQL/service/user tables before committing. To add a **Security
Assessment** view, open Data Safe → a target → Security Assessment and capture it the
same way.
