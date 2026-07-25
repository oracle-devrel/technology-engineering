"""Read-only prerequisite verification for Database Management / Ops Insights."""

from __future__ import annotations

from typing import Any, Callable

from dbman_opsi.checks import (
    CheckResult,
    PreflightReport,
    TargetReport,
    fail,
    manual,
    ok,
    skip,
    warn,
)
from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.db_check import DbUserCheck
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.status import dbm_status, is_enabled, opsi_status

OCI_NATIVE_KINDS = {"dbcs", "autonomous", "exadata"}
AGENT_KINDS = {"external-db", "external-exadata"}

# Service principals that must appear in policy for enablement to work. DB
# Management uses the `dpd` principal (there is no `database-management`
# principal); Ops Insights uses `operations-insights`. Both read the Vault secret.
_REQUIRED_PRINCIPALS: tuple[tuple[str, str], ...] = (
    ("service dpd", "Database Management reads the Vault secret + network access"),
    ("service operations-insights", "Operations Insights reads the Vault secret + network access"),
)

_MONITORING_PORTS = (1521, 1522)


def location_for(kind: str) -> str:
    return "management-agent" if kind in AGENT_KINDS else "oci-native"


def _active(state: str | None) -> bool:
    return str(state or "").upper() in {"ACTIVE", "AVAILABLE", "RUNNING"}


def _safe(call: Callable[[], Any], attempts: int = 2) -> tuple[Any, str | None]:
    """Run a read-only OCI lookup, retrying once to ride out transient 404/5xx blips."""

    error = ""
    for attempt in range(attempts):
        try:
            return call(), None
        except Exception as exc:  # noqa: BLE001 - surfaced as a check detail
            error = str(exc)
    return None, error


class PreflightService:
    def __init__(self, oci: OciCli) -> None:
        self.oci = oci

    def run(self, config: EnablementConfig, db_check: DbUserCheck | None = None) -> PreflightReport:
        return PreflightReport(
            tenancy_checks=self._tenancy_checks(config),
            network_checks=self._network_checks(config),
            targets=tuple(self._target_report(target, config, db_check) for target in config.targets),
        )

    # --- tenancy / IAM -------------------------------------------------

    def _tenancy_checks(self, config: EnablementConfig) -> tuple[CheckResult, ...]:
        scope = config.tenancy_id or config.compartment_id
        if not scope:
            return (
                warn(
                    "iam.policies",
                    "No tenancy_id/compartment_id to inspect policies",
                    "Set tenancy_id in the config so IAM policies can be verified.",
                ),
            )
        policies, error = _safe(lambda: self.oci.list_policies(scope))
        if error is not None:
            return (warn("iam.policies", f"Could not list policies: {error}", "Confirm read access to iam policies."),)
        statements = " \n ".join(
            str(stmt).lower()
            for policy in policies
            for stmt in policy.get("statements", [])
        )
        missing = [label for needle, label in _REQUIRED_PRINCIPALS if needle not in statements]
        if not missing:
            return (ok("iam.policies", "Required service-principal policy statements present"),)
        remediation = "Run `dbman-opsi provision` (Terraform applies the IAM policy) or add the missing statements."
        if len(missing) == len(_REQUIRED_PRINCIPALS):
            return (fail("iam.policies", "No enablement service-principal policies found", remediation),)
        return (warn("iam.policies", f"Missing policy statements: {', '.join(missing)}", remediation),)

    # --- network -------------------------------------------------------

    def _network_checks(self, config: EnablementConfig) -> tuple[CheckResult, ...]:
        subnet_id = config.network.subnet_id
        if not subnet_id:
            return (
                skip(
                    "network.subnet",
                    "No subnet selected; run provision to create one or set network.subnet_id",
                ),
            )
        subnet, error = _safe(lambda: self.oci.get_subnet(subnet_id))
        if error is not None or not subnet:
            return (
                fail(
                    "network.subnet",
                    f"Subnet {subnet_id} not readable: {error or 'empty response'}",
                    "Verify the subnet OCID and that you have read access.",
                ),
            )
        checks = [self._subnet_check(subnet)]
        vcn_id = config.network.vcn_id or subnet.get("vcn-id")
        checks.append(self._service_gateway_check(config, subnet, vcn_id))
        checks.append(self._route_check(subnet))
        checks.append(self._security_list_check(subnet))
        return tuple(checks)

    def _subnet_check(self, subnet: dict[str, Any]) -> CheckResult:
        state = subnet.get("lifecycle-state")
        if _active(state):
            access = "private" if subnet.get("prohibit-public-ip-on-vnic") else "public"
            return ok("network.subnet", f"Subnet {state}; {access} subnet")
        return fail("network.subnet", f"Subnet lifecycle-state is {state}", "Wait for the subnet to become AVAILABLE.")

    def _service_gateway_check(
        self, config: EnablementConfig, subnet: dict[str, Any], vcn_id: str | None
    ) -> CheckResult:
        # The Service Gateway lives in the VCN's compartment, which may differ from
        # the database compartment. Resolve the VCN's compartment first.
        compartment = subnet.get("compartment-id") or config.compartment_id
        if vcn_id:
            vcn, _ = _safe(lambda: self.oci.get_vcn(vcn_id))
            if vcn:
                compartment = vcn.get("compartment-id") or compartment
        if not vcn_id or not compartment:
            return warn("network.service_gateway", "Cannot resolve VCN/compartment for Service Gateway lookup")
        gateways, error = _safe(lambda: self.oci.list_service_gateways(compartment, vcn_id))
        if error is not None:
            return warn("network.service_gateway", f"Could not list Service Gateways: {error}")
        active = [gw for gw in gateways or [] if _active(gw.get("lifecycle-state"))]
        if active:
            return ok("network.service_gateway", f"{len(active)} active Service Gateway(s) on the VCN")
        return fail(
            "network.service_gateway",
            "No active Service Gateway on the VCN",
            "Create a Service Gateway with the 'All <region> Services' label so the private "
            "subnet can reach Database Management and Ops Insights endpoints.",
        )

    def _route_check(self, subnet: dict[str, Any]) -> CheckResult:
        route_table_id = subnet.get("route-table-id")
        if not route_table_id:
            return warn("network.route", "Subnet has no route table id in its record")
        table, error = _safe(lambda: self.oci.get_route_table(route_table_id))
        if error is not None:
            return warn("network.route", f"Could not read route table: {error}")
        for rule in (table or {}).get("route-rules", []):
            destination_type = str(rule.get("destination-type", "")).upper()
            entity = str(rule.get("network-entity-id", "")).lower()
            if destination_type == "SERVICE_CIDR_BLOCK" and "servicegateway" in entity:
                return ok("network.route", "Route rule to OCI Services via Service Gateway present")
        return fail(
            "network.route",
            "No route rule to OCI Services via Service Gateway",
            "Add a route rule: destination = All <region> Services, target = the Service Gateway.",
        )

    def _security_list_check(self, subnet: dict[str, Any]) -> CheckResult:
        ids = subnet.get("security-list-ids") or []
        if not ids:
            return warn("network.security_list", "Subnet has no security lists (NSGs may be used instead)")
        for security_list_id in ids:
            data, error = _safe(lambda sid=security_list_id: self.oci.get_security_list(sid))
            if error is not None or not data:
                continue
            if _ingress_allows_db_ports(data.get("ingress-security-rules", [])):
                return ok("network.security_list", "Ingress allows Oracle listener ports (1521/1522)")
        return warn(
            "network.security_list",
            "No security-list ingress rule found for 1521/1522",
            "Allow TCP 1521-1522 ingress from the subnet/PE, or confirm an NSG covers it.",
        )

    # --- per target ----------------------------------------------------

    def _target_report(
        self, target: Target, config: EnablementConfig, db_check: DbUserCheck | None = None
    ) -> TargetReport:
        location = location_for(target.kind)
        if location == "management-agent":
            checks = self._agent_checks(target, config)
        else:
            checks = self._native_checks(target)
        checks = checks + (self._vault_check(target), self._monitoring_user_check(target, db_check))
        return TargetReport(name=target.name, kind=target.kind, location=location, checks=checks)

    def _native_checks(self, target: Target) -> tuple[CheckResult, ...]:
        if not target.resource_id:
            return (
                fail(
                    "target.resource",
                    "Missing resource OCID",
                    "Set resource_id, or run provision with provision=true to create it.",
                ),
            )
        if target.kind == "autonomous":
            details, error = _safe(lambda: self.oci.get_autonomous_database(target.resource_id or ""))
        elif target.database_role == "PDB":
            details, error = _safe(lambda: self.oci.get_pluggable_database(target.resource_id or ""))
        else:
            details, error = _safe(lambda: self.oci.get_database(target.resource_id or ""))
        if error is not None:
            return (fail("target.resource", f"Resource not readable: {error}", "Verify the resource OCID."),)
        details = details or {}
        state = details.get("lifecycle-state")
        label = "PDB" if target.database_role == "PDB" else "Database"
        resource_check = (
            ok("target.resource", f"{label} {state}")
            if _active(state)
            else fail("target.resource", f"{label} lifecycle-state is {state}", "Wait for AVAILABLE before enabling.")
        )
        dbm = dbm_status(details, target.kind, target.database_role) or "NOT_ENABLED"
        opsi = opsi_status(details, target.kind) or "n/a (Database Insight)"
        status_check = CheckResult(
            "target.dbm_status",
            "pass",
            f"Database Management: {dbm}; Ops Insights: {opsi}",
        )
        checks = [resource_check, status_check]
        if target.database_role == "PDB":
            checks.append(self._parent_cdb_check(target))
        if target.kind in {"dbcs", "exadata"}:
            checks.append(self._pe_check("target.dbm_private_endpoint", target.private_endpoint_id, self.oci.get_db_management_private_endpoint))
            checks.append(self._pe_check("target.opsi_private_endpoint", target.opsi_private_endpoint_id, self.oci.get_opsi_private_endpoint))
        return tuple(checks)

    def _parent_cdb_check(self, target: Target) -> CheckResult:
        name = "target.parent_cdb"
        if not target.parent_cdb_id:
            return warn(
                name,
                "Parent CDB not identified; PDB Database Management requires the CDB enabled first",
                "Set parent_cdb_id and enable the container database before the PDB.",
            )
        details, error = _safe(lambda: self.oci.get_database(target.parent_cdb_id or ""))
        if error is not None:
            return warn(name, f"Could not read parent CDB: {error}")
        if is_enabled(dbm_status(details or {}, "dbcs", "CDB")):
            return ok(name, "Parent CDB has Database Management enabled")
        return fail(
            name,
            "Parent CDB does not have Database Management enabled",
            "Enable the container database first; PDB enablement depends on it.",
        )

    def _pe_check(self, name: str, endpoint_id: str | None, getter: Callable[[str], dict[str, Any]]) -> CheckResult:
        if not endpoint_id:
            return warn(name, "Not set", "Run `dbman-opsi prepare-prereqs` to create the private endpoint.")
        data, error = _safe(lambda: getter(endpoint_id))
        if error is not None:
            return warn(name, f"Could not read endpoint: {error}")
        state = (data or {}).get("lifecycle-state")
        if _active(state):
            return ok(name, f"Private endpoint {state}")
        return fail(name, f"Private endpoint lifecycle-state is {state}", "Wait for the endpoint to become ACTIVE.")

    def _vault_check(self, target: Target) -> CheckResult:
        if target.kind == "autonomous":
            return skip("target.vault_secret", "Autonomous uses managed credentials")
        if not target.password_secret_id:
            return warn(
                "target.vault_secret",
                "No password_secret_id",
                "Store the monitoring password in Vault (prepare-prereqs --password-env) and set password_secret_id.",
            )
        data, error = _safe(lambda: self.oci.get_secret(target.password_secret_id or ""))
        if error is not None:
            return warn("target.vault_secret", f"Could not read secret: {error}")
        state = (data or {}).get("lifecycle-state")
        if _active(state):
            return ok("target.vault_secret", f"Vault secret {state}")
        return fail("target.vault_secret", f"Vault secret lifecycle-state is {state}", "Confirm the secret is ACTIVE.")

    def _monitoring_user_check(self, target: Target, db_check: DbUserCheck | None = None) -> CheckResult:
        if target.kind == "autonomous":
            return skip("target.monitoring_user", "Autonomous enablement does not need a manual monitoring user")
        user = target.monitoring_user or "DBSNMP"
        if db_check is None:
            return manual(
                "target.monitoring_user",
                f"Monitoring user '{user}' must exist with required grants (verified DB-side)",
                "Run the generated db-scripts (01/02/04) as SYSDBA, then confirm 04-validate output.",
            )
        if db_check.ok:
            return ok("target.monitoring_user", f"Monitoring user grants verified: {', '.join(db_check.found)}")
        if not db_check.account_open:
            return fail("target.monitoring_user", "Monitoring user account is not OPEN", "Unlock the user and re-run 01-create.")
        return fail(
            "target.monitoring_user",
            f"Missing required grants: {', '.join(db_check.missing)}",
            "Run 02-grant-basic-monitoring.sql (and 03 for advanced) then re-spool 04-validate.",
        )

    def _agent_checks(self, target: Target, config: EnablementConfig) -> tuple[CheckResult, ...]:
        if target.management_agent_id:
            data, error = _safe(lambda: self.oci.get_management_agent(target.management_agent_id or ""))
            if error is not None:
                return (warn("target.management_agent", f"Could not read agent: {error}"),)
            return (_agent_plugin_check(data or {}),)
        compartment = target.compartment_id or config.compartment_id or ""
        agents, error = _safe(lambda: self.oci.list_management_agents(compartment))
        if error is not None:
            return (warn("target.management_agent", f"Could not list agents: {error}"),)
        matched = [
            agent
            for agent in agents or []
            if target.name.lower() in str(agent.get("display-name", "")).lower()
        ]
        if not matched:
            return (
                fail(
                    "target.management_agent",
                    "No Management Agent matches this target name",
                    "Run the generated agent script on the host, then rerun preflight.",
                ),
            )
        return (_agent_plugin_check(matched[0]),)


def _ingress_allows_db_ports(rules: list[dict[str, Any]]) -> bool:
    for rule in rules:
        protocol = str(rule.get("protocol", ""))
        if protocol not in {"6", "all"}:
            continue
        port_range = (rule.get("tcp-options") or {}).get("destination-port-range")
        if port_range is None:
            return True  # all TCP ports allowed
        low = port_range.get("min", 0)
        high = port_range.get("max", 65535)
        if any(low <= port <= high for port in _MONITORING_PORTS):
            return True
    return False


def _agent_plugin_check(agent: dict[str, Any]) -> CheckResult:
    name = "target.management_agent"
    if not _active(agent.get("availability-status") or agent.get("lifecycle-state")):
        return warn(name, "Agent found but not reporting as available")
    plugins = {
        str(plugin.get("plugin-name", "")).lower(): str(plugin.get("plugin-status", "")).upper()
        for plugin in agent.get("plugin-list", [])
    }
    needed = {"dbmgmt", "opsi"}
    running = {plugin for plugin in needed if plugins.get(plugin) == "RUNNING"}
    if running == needed:
        return ok(name, "Agent available with dbmgmt and opsi plugins running")
    missing = needed - running
    return warn(name, f"Agent available; plugins not running: {', '.join(sorted(missing))}",
                "Enable the dbmgmt and opsi plugins on the Management Agent.")
