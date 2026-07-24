"""Human-readable rendering for preflight and configure reports."""

from __future__ import annotations

from dbman_opsi.checks import CheckResult, PreflightReport
from dbman_opsi.discovery import Inventory
from dbman_opsi.orchestrator import ConfigureReport

_STATUS_MARK = {
    "pass": "PASS",
    "fail": "FAIL",
    "warn": "WARN",
    "manual": "MANUAL",
    "skip": "SKIP",
}

_ACTION_MARK = {
    "enabled": "ENABLED",
    "ready": "READY",
    "handoff": "HANDOFF",
    "skip-enabled": "SKIP",
    "blocked": "BLOCKED",
    "stopped-not-found": "STOPPED",
}


def _print_check(check: CheckResult, indent: str = "  ") -> None:
    mark = _STATUS_MARK.get(check.status, check.status.upper())
    print(f"{indent}[{mark}] {check.name}: {check.detail}")
    if check.remediation and check.status in {"fail", "warn"}:
        print(f"{indent}       -> {check.remediation}")


def print_preflight_report(report: PreflightReport) -> None:
    print("Tenancy / IAM:")
    for check in report.tenancy_checks:
        _print_check(check)
    print("Network:")
    for check in report.network_checks:
        _print_check(check)
    for target in report.targets:
        print(f"Target {target.name} ({target.kind}, {target.location}):")
        for check in target.checks:
            _print_check(check)
    print(f"\nPreflight: {'READY' if report.ok else 'NOT READY'}")


def print_inventory(inventory: Inventory) -> None:
    shown = [compartment for compartment in inventory.compartments if not compartment.is_empty]
    if not shown:
        print("No reusable resources discovered in the scanned compartments.")
        return
    for compartment in shown:
        print(f"\n# Compartment: {compartment.name}")
        for subnet in compartment.subnets:
            access = "private" if subnet.private else "public"
            sgw = "SGW ok" if subnet.has_service_gateway else "NO Service Gateway"
            print(f"  subnet: {subnet.name} ({access}, {sgw}) {subnet.id}")
        for vault in compartment.vaults:
            print(f"  vault:  {vault.name} ({len(vault.keys)} key(s)) {vault.id}")
            for key_id, key_name in vault.keys:
                print(f"            key: {key_name} {key_id}")
        for database in compartment.databases + compartment.autonomous:
            print(f"  db:     {database.name} [{database.role}] {database.state}; DBM {database.dbm_status} {database.id}")
        for pe in compartment.dbm_private_endpoints:
            print(f"  dbm-pe: {pe.get('name') or pe.get('display-name')}")
        for pe in compartment.opsi_private_endpoints:
            print(f"  opsi-pe: {pe.get('display-name')}")
        for agent in compartment.management_agents:
            print(f"  agent:  {agent}")
        for bastion in compartment.bastions:
            print(f"  bastion: {bastion}")
    print("\nReuse any of the above by putting its OCID into the config (or pass to the wizard).")


def print_configure_report(report: ConfigureReport) -> None:
    print_preflight_report(report.preflight)
    print(f"\nConfigure ({report.mode}):")
    for decision in report.decisions:
        mark = _ACTION_MARK.get(decision.action, decision.action.upper())
        print(f"  [{mark}] {decision.name}: {decision.reason}")
    if report.handoff_paths:
        print("\nHandoff packets:")
        for path in report.handoff_paths:
            print(f"  {path}")
    if report.data_safe:
        print("\nData Safe (security pillar):")
        for decision in report.data_safe:
            print(f"  [{decision.status.upper()}] {decision.target}: {decision.detail}")
