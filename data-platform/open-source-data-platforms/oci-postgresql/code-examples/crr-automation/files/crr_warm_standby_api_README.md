# CRR Warm Standby API CLI

This script helps in orchestration of the PostgreSQL DB System CRR Warm Standby APIs

> ⚠️ **Important:** This script is an example/reference utility and is **not production-ready** as-is.
> Use it as a starting point and add production hardening (comprehensive validation, robust retry/backoff policies,
> observability, security review, and automated testing) before operational use.

## What this script does

The script calls these operations using an `--action` argument:

- `list-replicas` → Returns the OCID of the Replica DB attached to the database system.
- `change-role-to-standalone` → Changes the role of the warm standby(replica) database to standalone.
- `change-role-to-replica` → Synchronizes the database with a primary database and converts its role to warm standby(replica).
- `switchover` → Reverses the roles of the databases.

It signs HTTP requests with OCI auth:

- **Default:** Resource Principal (`--auth-mode resource_principal`)
- **Optional:** API key config file (`--auth-mode config`)

For async operations, the script also tracks the returned work request until terminal success/failure by default.

---

## Requirements

- Python 3.9+
- `oci` Python SDK
- `requests`

Install dependencies:

```bash
python -m pip install oci requests
```

---

## Basic usage

Show help:

```bash
python /home/opc/crr_warm_standby_api.py --help
```

General pattern:

```bash
python /home/opc/crr_warm_standby_api.py \
  --action <action-name> \
  --body-file <path-to-json> \
  [optional CLI overrides]
```

The `--body-file` can contain both:

- `settings` (region, db_system_id, auth, OCI config/profile, wait/polling defaults)
- `payload` (the API request body)

CLI args are optional and override values from `settings`.

---

## Authentication

### 1) Resource Principal (default)

No extra auth flags required:

```bash
python /home/opc/crr_warm_standby_api.py \
  --action list-replicas \
  --region us-phoenix-1 \
  --db-system-id <db_system_ocid>
```

### 2) API key config/profile auth

```bash
python /home/opc/crr_warm_standby_api.py \
  --action list-replicas \
  --region us-phoenix-1 \
  --db-system-id <db_system_ocid> \
  --auth-mode config \
  --config-file /home/opc/.oci/config \
  --profile DEFAULT
```

---

## Request body input

Actions that require a JSON payload must use `--body-file`:

- `change-role-to-standalone`
- `change-role-to-replica`
- `switchover`

`--body-file` can now contain both execution settings and payload in a single file:

```json
{
  "settings": {
    "region": "us-phoenix-1",
    "db_system_id": "ocid1.postgresqldbsystem.oc1..exampleprimary",
    "auth_mode": "config",
    "oci_config_file": "/home/opc/.oci/config",
    "oci_profile": "DEFAULT",
    "poll_interval_seconds": 10,
    "max_wait_seconds": 3600,
    "wait": true
  },
  "payload": {
    "replicaDbSystemId": "ocid1.postgresqldbsystem.oc1..examplereplica"
  }
}
```

Precedence order:

- CLI arguments override values in `settings`
- `settings` override script defaults

Backward compatibility note:

```json
{
  "replicaDbSystemId": "ocid1.postgresqldbsystem.oc1..example"
}
```

If `settings` and `payload` are omitted, the script treats the full JSON as direct request payload (legacy behavior).

Use with:

```bash
python /home/opc/crr_warm_standby_api.py \
  --action switchover \
  --region us-phoenix-1 \
  --db-system-id <primary_db_system_ocid> \
  --body-file /home/opc/switchover.json
```

If `db_system_id` and `region` are inside `settings`, you can run with fewer flags:

```bash
python /home/opc/crr_warm_standby_api.py \
  --action switchover \
  --body-file /home/opc/switchover.json
```

---

## Examples by action

These examples assume each JSON file includes `settings` (for `region`, `db_system_id`, auth defaults, etc.) and `payload` where needed.

### List Replicas

```bash
python /home/opc/crr_warm_standby_api.py \
  --action list-replicas \
  --body-file /home/opc/list_replicas.json
```

### Change Role to Standalone

```bash
python /home/opc/crr_warm_standby_api.py \
  --action change-role-to-standalone \
  --body-file /home/opc/change_to_standalone.json
```

`change_to_standalone.json` must include `payload.changeMode`, for example:

```json
{
  "settings": {
    "region": "us-phoenix-1",
    "db_system_id": "ocid1.postgresqldbsystem.oc1..replica"
  },
  "payload": {
    "changeMode": "REPLAY_PENDING_UPDATES"
  }
}
```

Allowed `changeMode` values:

- `REPLAY_PENDING_UPDATES`
- `IMMEDIATELY`

### Change Role to Replica

```bash
python /home/opc/crr_warm_standby_api.py \
  --action change-role-to-replica \
  --body-file /home/opc/change_to_replica.json
```

`change_to_replica.json` must include `payload.primaryDbSystemId`, for example:

```json
{
  "settings": {
    "region": "us-phoenix-1",
    "db_system_id": "ocid1.postgresqldbsystem.oc1..standalone"
  },
  "payload": {
    "primaryDbSystemId": "ocid1.postgresqldbsystem.oc1..primary"
  }
}
```

### Switchover

```bash
python /home/opc/crr_warm_standby_api.py \
  --action switchover \
  --body-file /home/opc/switchover_primary.json
```

Optional override example (CLI overrides file settings):

```bash
python /home/opc/crr_warm_standby_api.py \
  --action switchover \
  --body-file /home/opc/switchover_primary.json \
  --region us-ashburn-1
```

---

## Optional headers and flags

- `--if-match <etag>`
- `--opc-request-id <id>` (auto-generated if omitted)
- `--opc-retry-token <token>`
- `--page <token>` (for `list-replicas`)
- `--insecure` (disables TLS verification; not recommended)
- `--wait` / `--no-wait` (default is wait)
- `--poll-interval-seconds <n>` (default `10`)
- `--max-wait-seconds <n>` (default `3600`)
- `--work-request-path-template <path>` (default `/workRequests/{workRequestId}`)

---

## Async operation tracking

These actions are treated as async and are tracked automatically when `--wait` is enabled:

- `change-role-to-standalone`
- `change-role-to-replica`
- `switchover`

Flow:

1. Initial API call is executed.
2. `opc-work-request-id` is extracted from response headers.
3. Script polls the work request endpoint until terminal state.
   - During polling, a live progress line is printed each interval (default 10s), for example:
     - elapsed seconds
     - work request id
     - HTTP status
     - current state
4. Script exits with:
   - `0` on success state
   - `1` on failed/canceled/timeout/non-2xx poll response

If your service uses a different work request route, override with `--work-request-path-template`.

Example:

```bash
python /home/opc/crr_warm_standby_api.py \
  --action switchover \
  --region us-phoenix-1 \
  --db-system-id <current_primary_db_system_ocid> \
  --body-file /home/opc/switchover.json \
  --poll-interval-seconds 15 \
  --max-wait-seconds 7200
```

Sample progress output during wait:

```text
[poll] elapsed=0s work_request_id=ocid1.postgresworkrequest... http_status=200 state=ACCEPTED
[poll] elapsed=10s work_request_id=ocid1.postgresworkrequest... http_status=200 state=IN_PROGRESS
[poll] completed work_request_id=ocid1.postgresworkrequest... state=SUCCEEDED result=SUCCESS
```

At completion, the script also prints a one-line timing summary to stderr, for example:

```text
[summary] action=switchover total=184.231s initial_call=1.127s polling=183.104s poll_count=19
```

---

## Output format

The script prints JSON including:

- request details (`action`, `method`, `url`, query, `opc-request-id`)
- response status code
- key OCI headers (`opc-request-id`, `opc-work-request-id`, `etag`, `opc-next-page`)
- response body (JSON if parsable, otherwise raw text)

For async operations, final JSON also includes a `timing` section with:

- `operation`
- `initial_call_duration_seconds`
- `polling_duration_seconds`
- `total_operation_duration_seconds`
- `poll_count`
- `average_poll_interval_seconds`

Exit codes:

- `0` for success (HTTP 2xx)
- `1` for non-2xx HTTP response or unsuccessful async work-request completion
- `2` for argument/auth/runtime errors
