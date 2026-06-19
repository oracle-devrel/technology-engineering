"""Command line interface for dbman-opsi."""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from dbman_opsi.agent_scripts import generate_agent_scripts
from dbman_opsi.bastion_exec import BastionSqlRunner
from dbman_opsi.config import ConfigError, EnablementConfig, load_config, save_config, validate_config
from dbman_opsi.credentials import CredentialService
from dbman_opsi.cross_region import cross_region_plan, format_cross_region_plan, parse_regions
from dbman_opsi.datasafe import DataSafeDecision, DataSafeService
from dbman_opsi.db_check import parse_validation_output
from dbman_opsi.db_exec import DbExecService
from dbman_opsi.db_scripts import generate_db_scripts
from dbman_opsi.discovery import DiscoveryService
from dbman_opsi.doctor import check_environment, check_session, summarize_checks
from dbman_opsi.enablement import EnablementService
from dbman_opsi.envfile import load_env_file
from dbman_opsi.journal import RunJournal, summarize
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.opsi_payloads import generate_opsi_payloads
from dbman_opsi.orchestrator import ConfigureReport, ConfigureService
from dbman_opsi.preflight import PreflightService
from dbman_opsi.prerequisites import PrerequisiteService
from dbman_opsi.regional_provisioning import (
    CHICAGO_REGION,
    RegionalProvisioningRequest,
    build_regional_provisioning_config,
    default_regional_output,
    prepare_regional_terraform_dir,
)
from dbman_opsi.redact import redact_data
from dbman_opsi.reporting import print_configure_report, print_inventory, print_preflight_report
from dbman_opsi.runner import CommandRunner
from dbman_opsi.terraform import run_terraform, write_tfvars
from dbman_opsi.tf_outputs import merge_outputs_into_config, read_terraform_outputs, validate_merged_config
from dbman_opsi.validation import ValidationService
from dbman_opsi.wizard import run_wizard

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CliContext:
    run_id: str
    verbose: bool


def _add_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="dbman-opsi.yaml", help="Path to YAML/JSON config")
    parser.add_argument("--dry-run", action="store_true", help="Print commands instead of executing")
    parser.add_argument("--apply", action="store_true", help="Execute changes even when config dry_run is true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbman-opsi")
    parser.add_argument("--verbose", action="store_true", help="Show per-command timing")
    verbose_parent = argparse.ArgumentParser(add_help=False)
    verbose_parent.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS)
    subcommands = parser.add_subparsers(dest="command", required=True)

    def add_parser(name: str, **kwargs) -> argparse.ArgumentParser:
        return subcommands.add_parser(name, parents=[verbose_parent], **kwargs)

    plan = add_parser("plan", help="Run interactive discovery/planning wizard")
    plan.add_argument("--profile", required=True)
    plan.add_argument("--region", required=True)
    plan.add_argument("--output", default="dbman-opsi.yaml")

    discover = add_parser(
        "discover",
        help="Read-only inventory of reusable resources (subnets, vaults, databases, endpoints, agents, bastions)",
    )
    discover.add_argument("--profile", required=True)
    discover.add_argument("--region", required=True)
    discover.add_argument("--compartment", help="Root compartment OCID (defaults to tenancy)")
    discover.add_argument("--tenancy", help="Tenancy OCID (defaults to compartment)")
    discover.add_argument("--subtree", action="store_true", help="Scan the compartment subtree")
    discover.add_argument("--json", action="store_true", help="Emit the inventory as JSON")

    provision = add_parser("provision", help="Render tfvars and run Terraform")
    _add_config_args(provision)
    provision.add_argument("--render-only", action="store_true", help="Only write terraform.tfvars.json")

    init_region = add_parser(
        "init-region",
        help="Create a region-specific provisioning config for a second-region PoC (defaults to Chicago)",
    )
    init_region.add_argument("--config", default="dbman-opsi.yaml")
    init_region.add_argument("--region", default=CHICAGO_REGION)
    init_region.add_argument("--output", help="Output config path (default: dbman-opsi.<region>.local.yaml)")
    init_region.add_argument("--terraform-dir", help="Terraform work directory for this region")
    init_region.add_argument("--target-name", help="Provisioned database target name")
    init_region.add_argument("--target-kind", choices=("dbcs", "autonomous"), default="dbcs")
    init_region.add_argument("--vcn-id", help="Existing VCN OCID in the selected region")
    init_region.add_argument("--subnet-id", help="Existing private subnet OCID in the selected region")

    import_outputs = add_parser(
        "import-tf-outputs",
        help="Read terraform outputs and merge created OCIDs (subnet, PE, provisioned DBs) back into the config",
    )
    import_outputs.add_argument("--config", default="dbman-opsi.yaml")
    import_outputs.add_argument("--terraform-dir", help="Override config.terraform_dir")
    import_outputs.add_argument("--dry-run", action="store_true", help="Print changes without writing the config")

    enable = add_parser("enable", help="Enable Database Management and Ops Insights")
    _add_config_args(enable)
    enable.add_argument(
        "--skip-credentials",
        action="store_true",
        help="Do not set DBM advanced-diagnostics preferred credentials after enabling",
    )
    enable.add_argument(
        "--force-reconcile",
        action="store_true",
        help="Always reconcile the DBM connection, even when monitoring is already healthy",
    )

    prereqs = add_parser("prepare-prereqs", help="Create OCI-side prerequisites such as private endpoints and optional Vault secrets")
    _add_config_args(prereqs)
    prereqs.add_argument("--password-env", help="Environment variable containing the monitoring password for Vault secret creation")

    validate = add_parser("validate", help="Validate registrations and collection readiness")
    _add_config_args(validate)

    cross_region = add_parser(
        "cross-region",
        help="Configure and summarize the OPSI multi-region Explorer/dashboard POC selection",
    )
    cross_region.add_argument("--config", default="dbman-opsi.yaml")
    cross_region.add_argument(
        "--regions",
        help="Comma-separated OCI regions to select in Ops Insights Explorer and supported dashboards",
    )

    preflight = add_parser("preflight", help="Read-only check of all enablement prerequisites")
    preflight.add_argument("--config", default="dbman-opsi.yaml")
    preflight.add_argument("--json", action="store_true", help="Emit the report as JSON")
    preflight.add_argument(
        "--db-check-file",
        help="Spooled output of 04-validate-monitoring-user.sql to verify the DB monitoring user",
    )

    configure = add_parser(
        "configure",
        help="Orchestrated flow: detect, branch by location, gate on prerequisites, then enable or hand off",
    )
    configure.add_argument("--config", default="dbman-opsi.yaml")
    configure.add_argument("--apply", action="store_true", help="Enable services when all prerequisites pass")
    configure.add_argument("--db-side-only", action="store_true", help="Generate DB-side handoff packets and stop")
    configure.add_argument("--force", action="store_true", help="Ignore blocking prerequisite failures")
    configure.add_argument(
        "--skip-credentials",
        action="store_true",
        help="Do not set DBM advanced-diagnostics preferred credentials after configuring",
    )
    configure.add_argument("--output", default="generated/handoff", help="Handoff packet output directory")
    configure.add_argument("--json", action="store_true", help="Emit the report as JSON")
    configure.add_argument(
        "--with-data-safe",
        action="store_true",
        help="Also register Data Safe targets (datasafe pillar) during --apply",
    )
    configure.add_argument("--data-safe-user", help="Data Safe service account (default: target monitoring_user or DBSNMP)")
    configure.add_argument("--data-safe-password-env", help="Env var holding the Data Safe account password (non-interactive)")

    agent = add_parser("generate-agent-scripts", help="Generate Management Agent install scripts")
    agent.add_argument("--config", default="dbman-opsi.yaml")
    agent.add_argument("--output", default="generated/agents")

    db_scripts = add_parser("generate-db-scripts", help="Generate database-side SQL scripts")
    db_scripts.add_argument("--config", default="dbman-opsi.yaml")
    db_scripts.add_argument("--output", default="generated/db-scripts")

    opsi_payloads = add_parser("generate-opsi-payloads", help="Generate Operations Insights JSON payload files")
    opsi_payloads.add_argument("--config", default="dbman-opsi.yaml")
    opsi_payloads.add_argument("--output", default="generated/opsi-payloads")

    set_creds = add_parser(
        "set-credentials",
        help="Set DBM advanced-diagnostics preferred credentials via a Vault named credential",
    )
    set_creds.add_argument("--config", default="dbman-opsi.yaml")

    doctor = add_parser("doctor", help="Check local or Cloud Shell prerequisites")
    doctor.add_argument("--profile", help="Also verify the OCI session is authenticated for this profile")
    doctor.add_argument("--region", help="Region to use for the session check")

    journal = add_parser("journal", help="Inspect a run journal")
    journal.add_argument("run_id", nargs="?", help="Run ID from runs/<RUN_ID>.jsonl")
    journal.add_argument("--last", action="store_true", help="Inspect the newest runs/*.jsonl file")
    journal.add_argument("--json", action="store_true", help="Emit the journal summary as JSON")

    db_exec = add_parser(
        "db-exec",
        help="Generate DB-side scripts and show the hybrid run plan (auto-run in non-prod, handoff in prod)",
    )
    db_exec.add_argument("--config", default="dbman-opsi.yaml")
    db_exec.add_argument("--scripts-dir", default="generated/db-scripts")
    db_exec.add_argument("--force", action="store_true", help="Treat as non-production (auto-exec even for prod)")
    db_exec.add_argument("--apply", action="store_true", help="Auto-run DB-side scripts via Bastion (non-prod). Requires --bastion-id/--target-ip/--ssh-key")
    db_exec.add_argument("--bastion-id", help="Bastion OCID for --apply auto-exec")
    db_exec.add_argument("--target-ip", help="DB node private IP for --apply auto-exec")
    db_exec.add_argument("--ssh-key", help="SSH private key path (with matching .pub) for the Bastion session + DB node")
    db_exec.add_argument("--answers-file", help="File whose contents are piped to each script's SQL*Plus accept prompts")

    data_safe = add_parser(
        "data-safe",
        help="Register databases as Data Safe targets (security pillar) for targets that opt into 'datasafe'",
    )
    data_safe.add_argument("--config", default="dbman-opsi.yaml")
    data_safe.add_argument("--apply", action="store_true", help="Perform live registration (otherwise dry-run)")
    data_safe.add_argument("--user", help="Data Safe service account (default: target monitoring_user or DBSNMP)")
    data_safe.add_argument("--password-env", help="Env var holding the Data Safe account password (non-interactive)")

    return parser


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)


def _make_journal(run_id: str, profile: str, region: str) -> RunJournal:
    return RunJournal(run_id=run_id, profile=profile, region=region)


def _make_runner(
    *,
    dry_run: bool,
    run_id: str,
    profile: str,
    region: str,
    verbose: bool,
) -> CommandRunner:
    return CommandRunner(
        dry_run=dry_run,
        journal=_make_journal(run_id, profile, region),
        run_id=run_id,
        verbose=verbose,
    )


def _make_data_safe_provider(apply: bool, user_override: str | None, password_env: str | None):
    """Build a (user, password) provider for Data Safe registration.

    Only prompts when applying live; in dry-run the password is unused. A
    password env var supports non-interactive runs (CI/Cloud Shell).
    """

    def provider(target) -> tuple[str, str]:
        user = user_override or target.monitoring_user or "DBSNMP"
        if not apply:
            return (user, "")
        if password_env:
            return (user, os.environ.get(password_env, ""))
        return (user, getpass.getpass(f"Data Safe password for {user}@{target.name}: "))

    return provider


def _persist_data_safe_targets(
    config: EnablementConfig, decisions: list[DataSafeDecision]
) -> EnablementConfig:
    """Write any newly-registered Data Safe target OCIDs back into the config."""

    ids = {d.target: d.target_id for d in decisions if d.target_id}
    if not ids:
        return config
    new_targets = tuple(
        replace(t, data_safe_target_id=ids[t.name]) if t.name in ids and not t.data_safe_target_id else t
        for t in config.targets
    )
    return replace(config, targets=new_targets)


def _config_runner(config: EnablementConfig, ctx: _CliContext, dry_run: bool) -> CommandRunner:
    return _make_runner(
        dry_run=dry_run,
        run_id=ctx.run_id,
        profile=config.profile,
        region=config.region,
        verbose=ctx.verbose,
    )


def _args_runner(args: argparse.Namespace, ctx: _CliContext, dry_run: bool) -> CommandRunner:
    return _make_runner(
        dry_run=dry_run,
        run_id=ctx.run_id,
        profile=args.profile,
        region=args.region,
        verbose=ctx.verbose,
    )


def _config_oci(config: EnablementConfig, ctx: _CliContext, dry_run: bool) -> OciCli:
    return OciCli(config.profile, config.region, _config_runner(config, ctx, dry_run))


def _cmd_plan(args: argparse.Namespace, ctx: _CliContext) -> int:
    discovery = OciCli(args.profile, args.region, _args_runner(args, ctx, dry_run=False))
    config = run_wizard(args.profile, args.region, discovery)
    save_config(args.output, config)
    print(f"Wrote sanitized config to {args.output}")
    return 0


def _cmd_doctor(args: argparse.Namespace, ctx: _CliContext) -> int:
    checks = check_environment()
    if args.profile:
        checks = checks + (check_session(args.profile, args.region),)
    for check in checks:
        status = "ok" if check.ok else "missing"
        print(f"{check.name}: {status} ({check.detail})")
    print(summarize_checks(checks))
    return 0 if all(check.ok for check in checks) else 1


def _latest_journal_run_id(root: Path) -> str:
    matches = list(root.glob("*.jsonl"))
    if not matches:
        raise SystemExit("no run journals found in runs/")
    # Secondary key (name) makes the pick deterministic when two journals share an
    # mtime (coarse-resolution filesystems); otherwise max() returns an arbitrary
    # one in glob order.
    return max(matches, key=lambda path: (path.stat().st_mtime, path.name)).stem


def _print_journal_summary(summary: dict[str, object]) -> None:
    print(f"Commands: {summary['command_count']}")
    print(f"Total duration: {summary['total_duration_ms']} ms")
    failures = summary["failures"]
    if not failures:
        print("Failing commands: none")
        return
    print("Failing commands:")
    for entry in failures:
        if not isinstance(entry, dict):
            continue
        command = " ".join(str(part) for part in entry.get("argv_redacted") or [])
        returncode = entry.get("returncode")
        duration = entry.get("duration_ms")
        print(f"- rc={returncode} duration_ms={duration} {command}".rstrip())


def _cmd_journal(args: argparse.Namespace, ctx: _CliContext) -> int:
    root = Path("runs")
    run_id = _latest_journal_run_id(root) if args.last else args.run_id
    if not run_id:
        raise SystemExit("journal requires RUN_ID or --last")
    try:
        summary = redact_data(summarize(RunJournal.read(run_id, root=root)))
    except FileNotFoundError as exc:
        raise SystemExit(f"journal file not found: {root / f'{run_id}.jsonl'}") from exc
    except ValueError as exc:
        raise SystemExit(f"invalid run id: {exc}") from exc
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_journal_summary(summary)
    return 0


def _cmd_provision(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    tfvars = write_tfvars(config)
    print(f"Wrote {tfvars}")
    if not args.render_only:
        dry_run = not args.apply and (args.dry_run or config.dry_run)
        run_terraform(config, _config_runner(config, ctx, dry_run))
    return 0


def _cmd_init_region(args: argparse.Namespace, ctx: _CliContext) -> int:
    base = load_config(args.config)
    try:
        config = build_regional_provisioning_config(
            base,
            RegionalProvisioningRequest(
                region=args.region,
                target_kind=args.target_kind,
                target_name=args.target_name,
                terraform_dir=args.terraform_dir,
                vcn_id=args.vcn_id,
                subnet_id=args.subnet_id,
            ),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    problems = validate_config(config)
    if problems:
        raise ConfigError(problems)
    output = args.output or default_regional_output(args.region)
    save_config(output, config)
    copied = prepare_regional_terraform_dir(base.terraform_dir, config.terraform_dir)
    print(f"Wrote regional provisioning config to {output}")
    if copied:
        print(f"Prepared Terraform workdir {config.terraform_dir}")
    print(f"Next: dbman-opsi provision --config {output} --render-only")
    return 0


def _cmd_enable(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    dry_run = not args.apply and (args.dry_run or config.dry_run)
    EnablementService(_config_oci(config, ctx, dry_run)).enable_all(
        config, force_reconcile=args.force_reconcile
    )
    if args.apply and not args.skip_credentials:
        # Complete the workflow: set the DBM advanced-diagnostics preferred
        # credentials. Best-effort: blocked targets print remediation.
        for decision in CredentialService(_config_oci(config, ctx, dry_run=False)).set_all(config):
            print(f"- credentials {decision.target}: {decision.status} ({decision.detail})")
    return 0


def _cmd_prepare_prereqs(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    dry_run = not args.apply and (args.dry_run or config.dry_run)
    PrerequisiteService(_config_oci(config, ctx, dry_run)).prepare(config, args.password_env)
    return 0


def _cmd_validate(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)

    def oci_for_region(region: str) -> OciCli:
        return OciCli(
            config.profile,
            region,
            _make_runner(
                dry_run=False,
                run_id=ctx.run_id,
                profile=config.profile,
                region=region,
                verbose=ctx.verbose,
            ),
        )

    # Regression R2, formerly under `if args.command == "validate":`:
    # validate is read-only and must remain equivalent to CommandRunner(dry_run=False).
    findings = ValidationService(
        _config_oci(config, ctx, dry_run=False),
        oci_for_region=oci_for_region,
    ).validate(config)
    for finding in findings:
        print(f"- {finding}")
    return 0


def _cmd_cross_region(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    if args.regions:
        config = replace(config, monitoring_regions=parse_regions(args.regions))
        problems = validate_config(config)
        if problems:
            raise ConfigError(problems)
        save_config(args.config, config)
        print(f"Updated monitoring_regions in {args.config}")
    print(format_cross_region_plan(cross_region_plan(config)))
    return 0


def _cmd_set_credentials(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    # Live reads + idempotent writes (named credential reuse, preferred SET).
    decisions = CredentialService(_config_oci(config, ctx, dry_run=False)).set_all(config)
    for decision in decisions:
        print(f"- {decision.target}: {decision.status} ({decision.detail})")
    blocked = [decision for decision in decisions if decision.status == "blocked"]
    return 1 if blocked else 0


def _cmd_discover(args: argparse.Namespace, ctx: _CliContext) -> int:
    oci = OciCli(args.profile, args.region, _args_runner(args, ctx, dry_run=False))
    root = args.compartment or args.tenancy
    if not root:
        raise SystemExit("discover requires --compartment or --tenancy")
    compartments = [{"id": root, "name": "root"}]
    if args.subtree:
        tenancy = args.tenancy or root
        compartments += oci.list_compartments(tenancy)
    inventory = DiscoveryService(oci).discover(compartments)
    if args.json:
        print(json.dumps(redact_data(inventory.to_dict()), indent=2, sort_keys=True))
    else:
        print_inventory(inventory)
    return 0


def _cmd_import_tf_outputs(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    outputs = read_terraform_outputs(
        args.terraform_dir or config.terraform_dir,
        _config_runner(config, ctx, dry_run=False),
    )
    merged, changes = merge_outputs_into_config(config, outputs)
    merged, resolved_changes = _resolve_provisioned_dbcs_databases(merged, ctx)
    changes.extend(resolved_changes)
    if not changes:
        print("No new values to import from terraform outputs.")
        return 0
    for change in changes:
        print(f"Updated {change}")
    if args.dry_run:
        print("Dry run: config not written.")
        return 0
    validate_merged_config(merged)
    save_config(args.config, merged)
    print(f"Wrote merged config to {args.config}")
    return 0


def _resolve_provisioned_dbcs_databases(
    config: EnablementConfig,
    ctx: _CliContext,
) -> tuple[EnablementConfig, list[str]]:
    """Resolve Terraform-created DB system IDs to database IDs for enablement."""

    changes: list[str] = []
    targets = []
    oci = _config_oci(config, ctx, dry_run=False)
    for target in config.targets:
        if not (target.provision and target.kind == "dbcs" and target.db_system_id):
            targets.append(target)
            continue
        needs_database_id = not target.resource_id or target.resource_id == target.db_system_id
        if not needs_database_id:
            targets.append(target)
            continue
        databases = oci.list_databases(target.compartment_id or config.compartment_id or "", target.db_system_id)
        if not databases:
            targets.append(target)
            continue
        database = databases[0]
        database_id = database.get("id")
        if not database_id:
            targets.append(target)
            continue
        updates = {"resource_id": database_id}
        if not target.service_name and database.get("db-name"):
            updates["service_name"] = database["db-name"]
        target = replace(target, **updates)
        changes.append(f"target[{target.name}]: resource_id")
        targets.append(target)
    return replace(config, targets=tuple(targets)), changes


def _cmd_preflight(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    db_check = None
    if args.db_check_file:
        db_check = parse_validation_output(Path(args.db_check_file).read_text(encoding="utf-8"))
    report = PreflightService(_config_oci(config, ctx, dry_run=False)).run(config, db_check=db_check)
    if args.json:
        print(json.dumps(redact_data(report.to_dict()), indent=2, sort_keys=True))
    else:
        print_preflight_report(report)
    return 0 if report.ok else 1


def _configure_datasafe(
    args: argparse.Namespace,
    config: EnablementConfig,
    mode: str,
    write_oci: OciCli,
) -> DataSafeService | None:
    if not args.with_data_safe or not any(target.wants("datasafe") for target in config.targets):
        return None
    return DataSafeService(
        write_oci,
        credential_provider=_make_data_safe_provider(
            mode == "apply", args.data_safe_user, args.data_safe_password_env
        ),
    )


def _cmd_configure(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    mode = "db-side-only" if args.db_side_only else ("apply" if args.apply else "plan")
    # Reads are always live (read-only); only the enable write respects the mode.
    read_oci = _config_oci(config, ctx, dry_run=False)
    write_oci = _config_oci(config, ctx, dry_run=mode != "apply")
    datasafe = _configure_datasafe(args, config, mode, write_oci)
    service = ConfigureService(read_oci, EnablementService(write_oci), datasafe=datasafe)
    report: ConfigureReport = service.configure(
        config, mode=mode, handoff_dir=args.output, force=args.force
    )
    credential_decisions = []
    if mode == "apply" and report.ok and not args.skip_credentials:
        credential_decisions = CredentialService(
            _config_oci(config, ctx, dry_run=False)
        ).set_all(config)
    if args.json:
        payload = report.to_dict()
        if credential_decisions:
            payload["credentials"] = [decision.__dict__ for decision in credential_decisions]
        print(json.dumps(redact_data(payload), indent=2, sort_keys=True))
    else:
        print_configure_report(report)
        for decision in credential_decisions:
            print(f"- credentials {decision.target}: {decision.status} ({decision.detail})")
    return 0 if report.ok else 1


def _cmd_generate_agent_scripts(args: argparse.Namespace, ctx: _CliContext) -> int:
    paths = generate_agent_scripts(load_config(args.config), Path(args.output))
    for path in paths:
        print(path)
    return 0


def _cmd_generate_db_scripts(args: argparse.Namespace, ctx: _CliContext) -> int:
    paths = generate_db_scripts(load_config(args.config), Path(args.output))
    for path in paths:
        print(path)
    return 0


def _cmd_generate_opsi_payloads(args: argparse.Namespace, ctx: _CliContext) -> int:
    paths = generate_opsi_payloads(load_config(args.config), Path(args.output))
    for path in paths:
        print(path)
    return 0


def _db_exec_apply_decisions(args: argparse.Namespace, config: EnablementConfig):
    if not (args.bastion_id and args.target_ip and args.ssh_key):
        raise SystemExit("db-exec --apply requires --bastion-id, --target-ip, and --ssh-key")
    answers = Path(args.answers_file).read_text(encoding="utf-8") if args.answers_file else None
    runner = BastionSqlRunner(
        bastion_id=args.bastion_id,
        target_private_ip=args.target_ip,
        ssh_key=args.ssh_key,
        profile=config.profile,
        region=config.region,
        answers=answers,
    )
    return DbExecService(runner).execute(config, args.scripts_dir, force=args.force)


def _cmd_db_exec(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    # Regenerate scripts so the plan reflects the current config.
    generate_db_scripts(config, Path(args.scripts_dir))
    if args.apply:
        decisions = _db_exec_apply_decisions(args, config)
    else:
        decisions = DbExecService().plan(config, force=args.force)
    for decision in decisions:
        print(f"- db-exec {decision.target}: {decision.action} ({decision.detail})")
    return 1 if any(d.action == "failed" for d in decisions) else 0


def _cmd_data_safe(args: argparse.Namespace, ctx: _CliContext) -> int:
    config = load_config(args.config)
    # Reads (list targets/PEs for idempotency) must be live; writes respect --apply.
    oci = _config_oci(config, ctx, dry_run=not args.apply)
    service = DataSafeService(
        oci, credential_provider=_make_data_safe_provider(args.apply, args.user, args.password_env)
    )
    decisions = service.enable_all(config)
    for decision in decisions:
        print(f"- data-safe {decision.target}: {decision.status} ({decision.detail})")
    if args.apply:
        updated = _persist_data_safe_targets(config, decisions)
        if updated is not config:
            save_config(args.config, updated)
            print(f"Updated Data Safe target OCIDs in {args.config}")
    blocked = [decision for decision in decisions if decision.status == "blocked"]
    return 1 if blocked else 0


def _command_handlers():
    return {
        "plan": _cmd_plan,
        "journal": _cmd_journal,
        "doctor": _cmd_doctor,
        "provision": _cmd_provision,
        "init-region": _cmd_init_region,
        "enable": _cmd_enable,
        "prepare-prereqs": _cmd_prepare_prereqs,
        "validate": _cmd_validate,
        "cross-region": _cmd_cross_region,
        "set-credentials": _cmd_set_credentials,
        "discover": _cmd_discover,
        "import-tf-outputs": _cmd_import_tf_outputs,
        "preflight": _cmd_preflight,
        "configure": _cmd_configure,
        "generate-agent-scripts": _cmd_generate_agent_scripts,
        "generate-db-scripts": _cmd_generate_db_scripts,
        "generate-opsi-payloads": _cmd_generate_opsi_payloads,
        "db-exec": _cmd_db_exec,
        "data-safe": _cmd_data_safe,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging()
    load_env_file()
    ctx = _CliContext(run_id=str(uuid.uuid4()), verbose=args.verbose)
    log.debug("run_id=%s", ctx.run_id)
    handler = _command_handlers().get(args.command)
    if handler is None:
        raise ValueError(f"Unhandled command {args.command}")
    return handler(args, ctx)


if __name__ == "__main__":
    raise SystemExit(main())
