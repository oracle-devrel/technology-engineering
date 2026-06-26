"""DB-side handoff packets for operators who run database steps separately."""

from __future__ import annotations

from pathlib import Path

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.db_scripts import DB_SCRIPT_TARGETS, generate_db_scripts
from dbman_opsi.enablement import cloud_enable_command, missing_cloud_fields

HANDOFF_KINDS = DB_SCRIPT_TARGETS


def _slug(name: str) -> str:
    return name.replace(" ", "-").lower()


def _enable_command_text(target: Target, config: EnablementConfig) -> str:
    missing = missing_cloud_fields(target)
    prefix = f"oci --profile {config.profile} --region {config.region}"
    command = " ".join([prefix, *cloud_enable_command(target)])
    if missing:
        note = (
            f"# NOTE: still missing {', '.join(missing)}. Fill these in (run prepare-prereqs)\n"
            f"# before the command below will succeed.\n"
        )
        return note + command
    return command


def _db_side_steps(target: Target) -> str:
    steps = [
        "@01-create-monitoring-user.sql",
        "@02-grant-basic-monitoring.sql",
        "-- optional, review licensing/security first:",
        "@03-grant-advanced-diagnostics.sql",
        "-- optional, enables PDB-level ADDM Spotlight / AWR Explorer data:",
        "@05-enable-performance-hub.sql",
        "@04-validate-monitoring-user.sql",
    ]
    if target.wants("datasafe"):
        steps.append("-- Data Safe service account + baseline assessment/audit privileges:")
        steps.append("@06-enable-data-safe.sql")
    return "\n".join(steps)


def _data_safe_context(target: Target) -> str:
    if not target.wants("datasafe"):
        return ""
    return f"""
## 4. Data Safe (security pillar)

| Field | Value |
| --- | --- |
| Data Safe service account | {target.monitoring_user or 'DBSNMP'} |
| Data Safe target OCID | {target.data_safe_target_id or '<run data-safe enable>'} |
| Data Safe private endpoint OCID | {target.data_safe_private_endpoint_id or '<run prepare-prereqs>'} |

After `06-enable-data-safe.sql` runs, register the database as a Data Safe target:

```bash
dbman-opsi data-safe --config <config> --apply
```

For Data Masking / Data Discovery, also download and run the per-target privilege
script from the OCI Console (Data Safe > Target databases > Register).
"""


def handoff_text(target: Target, config: EnablementConfig) -> str:
    is_external = target.kind in {"external-db", "external-exadata"}
    oci_step = (
        "Run the generated Management Agent script on the database host, then rerun "
        "`dbman-opsi preflight` to confirm the agent and plugins are registered."
        if is_external
        else "After the DB-side steps succeed, an operator with OCI rights runs:\n\n"
        f"```bash\n{_enable_command_text(target, config)}\n```"
    )
    return f"""# DB-side handoff for {target.name}

Target kind: {target.kind}
Region: {config.region}
Service name: {target.service_name or '<set service_name>'}
Monitoring user: {target.monitoring_user or 'DBSNMP'}
Pillars: {', '.join(target.services)}

## 1. Database-side steps (run as the DBA / SYSDBA)

Execute these scripts in order with SQLcl or SQL*Plus. They prompt for the
monitoring password interactively and never store it in a file:

```sql
{_db_side_steps(target)}
```

`04-validate-monitoring-user.sql` must show the monitoring user with
`CREATE SESSION`, `SELECT ANY DICTIONARY`, and `SELECT_CATALOG_ROLE`.

## 2. OCI-side context

| Field | Value |
| --- | --- |
| Private endpoint OCID | {target.private_endpoint_id or '<run prepare-prereqs>'} |
| Password secret OCID | {target.password_secret_id or '<store in Vault>'} |
| Ops Insights PE OCID | {target.opsi_private_endpoint_id or '<run prepare-prereqs>'} |

## 3. Enable in OCI

{oci_step}

Then confirm with `dbman-opsi validate --config <config>`.
{_data_safe_context(target)}"""


def generate_handoff(config: EnablementConfig, output_dir: str | Path) -> list[Path]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    paths = list(generate_db_scripts(config, base_dir))
    for target in config.targets:
        if target.kind not in HANDOFF_KINDS:
            continue
        target_dir = base_dir / _slug(target.name)
        target_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = target_dir / "HANDOFF.md"
        handoff_path.write_text(handoff_text(target, config), encoding="utf-8")
        paths.append(handoff_path)
    return paths
