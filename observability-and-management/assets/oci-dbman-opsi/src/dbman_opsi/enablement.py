"""Enable Database Management and Ops Insights for configured targets."""

from __future__ import annotations

import logging
import time

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.status import dbm_status

log = logging.getLogger(__name__)

CLOUD_REQUIRED_FIELDS = ("resource_id", "password_secret_id", "private_endpoint_id", "service_name", "monitoring_user")


def missing_cloud_fields(target: Target) -> list[str]:
    values = {
        "resource_id": target.resource_id,
        "password_secret_id": target.password_secret_id,
        "private_endpoint_id": target.private_endpoint_id,
        "service_name": target.service_name,
        "monitoring_user": target.monitoring_user,
    }
    return [name for name in CLOUD_REQUIRED_FIELDS if not values[name]]


def cloud_enable_command(target: Target) -> list[str]:
    """Build the enable-database-management argument list for the target's role.

    Containers / non-CDB databases use ``db database enable-database-management``
    (which takes ``--management-type``). Pluggable databases use
    ``db pluggable-database enable-pluggable-database-management`` with
    ``--pluggable-database-id`` and no management type.
    """

    if target.database_role == "PDB":
        return [
            "db",
            "pluggable-database",
            "enable-pluggable-database-management",
            "--pluggable-database-id",
            target.resource_id or "",
            "--password-secret-id",
            target.password_secret_id or "",
            "--private-end-point-id",
            target.private_endpoint_id or "",
            "--service-name",
            target.service_name or "",
            "--user-name",
            target.monitoring_user or "",
        ]
    return [
        "db",
        "database",
        "enable-database-management",
        "--database-id",
        target.resource_id or "",
        "--management-type",
        target.management_type,
        "--password-secret-id",
        target.password_secret_id or "",
        "--private-end-point-id",
        target.private_endpoint_id or "",
        "--service-name",
        target.service_name or "",
        "--user-name",
        target.monitoring_user or "",
    ]


def cloud_modify_command(target: Target) -> list[str]:
    """Build the modify-(pluggable-)database-management argument list.

    Used to *reconcile* an already-enabled Database Management connection — e.g.
    when the service name or monitoring credential changed after the initial
    enable. Without this, a re-run silently keeps stale connection details and
    monitoring stays broken (ORA-12514 wrong service / ORA-01017 wrong password).
    Waits for the database to return to AVAILABLE so sequential CDB-then-PDB
    updates on the same DB system do not collide.
    """

    wait = ["--wait-for-state", "AVAILABLE", "--max-wait-seconds", "900"]
    conn = [
        "--service-name", target.service_name or "",
        "--password-secret-id", target.password_secret_id or "",
        "--private-end-point-id", target.private_endpoint_id or "",
        "--user-name", target.monitoring_user or "",
        "--role", "NORMAL", "--protocol", "TCP", "--port", "1521",
    ]
    if target.database_role == "PDB":
        return [
            "db", "pluggable-database", "modify-pluggable-database-management",
            "--pluggable-database-id", target.resource_id or "",
            *conn, *wait,
        ]
    return [
        "db", "database", "modify-database-management",
        "--database-id", target.resource_id or "",
        "--management-type", target.management_type,
        *conn, *wait,
    ]


# Markers that mean Ops Insights does not yet see the database after Database
# Management was just enabled — a propagation race, not a permanent error. The
# managed database takes a short while to register before OPSI can attach.
OPSI_PROPAGATION_MARKERS = (
    "Provided database resource",
    "details were missing",
    "MissingParameter",
)


class EnablementService:
    def __init__(
        self,
        oci: OciCli,
        *,
        opsi_create_attempts: int = 5,
        opsi_create_delay: float = 30.0,
        sleeper=time.sleep,
    ) -> None:
        self.oci = oci
        self.opsi_create_attempts = opsi_create_attempts
        self.opsi_create_delay = opsi_create_delay
        self._sleep = sleeper
        # Bounded wait for DBM to finish ENABLING before attempting OPSI, so the
        # managed database is registered and Ops Insights can attach on the first
        # try (the OPSI create retry above remains as a backstop).
        self.dbm_wait_attempts = 20
        self.dbm_wait_delay = 15.0

    def enable_all(self, config: EnablementConfig, force_reconcile: bool = False) -> None:
        for target in config.targets:
            self.enable_target(target, force_reconcile=force_reconcile)

    def enable_target(self, target: Target, force_reconcile: bool = False) -> None:
        if target.kind == "autonomous":
            self._enable_autonomous(target)
            return
        if target.kind in {"dbcs", "exadata"}:
            self._enable_cloud_database(target, force_reconcile=force_reconcile)
            return
        if target.kind in {"external-db", "external-exadata"}:
            self._print_external_next_step(target)
            return
        raise ValueError(f"Unsupported target kind: {target.kind}")

    def enable_opsi(self, target: Target) -> None:
        if target.kind not in {"dbcs", "exadata"}:
            return
        self._enable_opsi_pe_comanaged_if_ready(target)

    def _enable_autonomous(self, target: Target) -> None:
        if not target.resource_id:
            raise ValueError(f"Target {target.name} is missing resource_id")
        self.oci.run([
            "db",
            "autonomous-database",
            "enable-autonomous-database-management",
            "--autonomous-database-id",
            target.resource_id,
        ])
        if target.opsi_database_insight_id:
            self.oci.run([
                "opsi",
                "database-insights",
                "enable-autonomous-database",
                "--database-insight-id",
                target.opsi_database_insight_id,
                "--is-advanced-features-enabled",
                "false",
            ])

    # Markers returned by the Database service when Database Management is
    # already on (or its enable request is already in flight). Treated as an
    # idempotent no-op so re-runs proceed to the Ops Insights step.
    DBM_ALREADY_ENABLED_MARKERS = ("already enabled", "already created")

    def _enable_cloud_database(self, target: Target, force_reconcile: bool = False) -> None:
        missing = missing_cloud_fields(target)
        if missing:
            raise ValueError(f"Target {target.name} is missing required fields: {', '.join(missing)}")
        applied = self.oci.run_tolerating(
            cloud_enable_command(target), tolerated=self.DBM_ALREADY_ENABLED_MARKERS
        )
        if not applied:
            # Already enabled. Reconciling (modify-database-management) takes ~2 min
            # per target, so skip it when monitoring is already healthy — only
            # reconcile to repair a broken connection (or when forced).
            if not force_reconcile and self._dbm_monitoring_healthy(target):
                log.info(
                    "Database Management already enabled and monitoring healthy for %s; skipping reconcile",
                    target.name,
                )
            else:
                log.info("Database Management already enabled for %s; reconciling connection", target.name)
                self.oci.run(cloud_modify_command(target))
        elif applied:
            # Freshly enabled: wait until DBM reports ENABLED (managed database
            # registered) before attaching Ops Insights, to avoid the propagation
            # race ("Provided database resource details were missing").
            self._wait_dbm_enabled(target)
        self._enable_opsi_pe_comanaged_if_ready(target)

    def _wait_dbm_enabled(self, target: Target) -> None:
        """Poll until the target's Database Management status is ENABLED.

        Best-effort: an unreadable status (no getter / transient error) returns
        immediately and lets the OPSI create retry handle any remaining race.
        """

        if not target.resource_id:
            return
        for attempt in range(self.dbm_wait_attempts):
            try:
                if target.database_role == "PDB":
                    details = self.oci.get_pluggable_database(target.resource_id)
                else:
                    details = self.oci.get_database(target.resource_id)
            except (RuntimeError, AttributeError):
                return
            status = str(dbm_status(details, target.kind, target.database_role) or "").upper()
            # Done once strictly ENABLED (the managed database is registered).
            # Only keep waiting while it is actively ENABLING; any other/unknown
            # status returns immediately (best-effort — the OPSI create retry is
            # the backstop, and this avoids busy-waiting on a non-progressing read).
            if status != "ENABLING":
                return
            if attempt < self.dbm_wait_attempts - 1:
                self._sleep(self.dbm_wait_delay)

    def _dbm_monitoring_healthy(self, target: Target) -> bool:
        """True when the managed database reports an UP monitoring status.

        For OCI-native databases the Managed Database OCID is the database OCID
        itself. A flaky/failed read returns False so we fall back to reconciling.
        """

        if not target.resource_id:
            return False
        try:
            return self.oci.get_managed_database_status(target.resource_id) == "UP"
        except (RuntimeError, AttributeError):
            return False

    def _enable_opsi_pe_comanaged_if_ready(self, target: Target) -> None:
        shared_missing = [
            name
            for name, value in {
                "compartment_id": target.compartment_id,
                "opsi_private_endpoint_id": target.opsi_private_endpoint_id,
                "opsi_credential_details_file": target.opsi_credential_details_file,
                "service_name": target.service_name,
            }.items()
            if not value
        ]
        if shared_missing:
            log.info("Skipping Ops Insights for %s; missing: %s", target.name, ", ".join(shared_missing))
            return
        if self._opsi_insight_active(target):
            # Idempotent: an ACTIVE insight already collects, so do not re-create
            # (create-pe-comanaged on an existing insight conflicts / hangs).
            log.info("Ops Insights insight already ACTIVE for %s; skipping create", target.name)
            return
        if not target.opsi_database_insight_id:
            self._create_opsi_pe_comanaged(target)
            return
        args = [
            "opsi",
            "database-insights",
            "enable-pe-comanaged-database",
            "--compartment-id",
            target.compartment_id or "",
            "--opsi-private-endpoint-id",
            target.opsi_private_endpoint_id or "",
            "--service-name",
            target.service_name or "",
            "--credential-details",
            f"file://{target.opsi_credential_details_file}",
            "--database-insight-id",
            target.opsi_database_insight_id or "",
        ]
        if target.opsi_connection_details_file:
            args.extend(["--connection-details", f"file://{target.opsi_connection_details_file}"])
        self.oci.run(args)

    def _opsi_insight_active(self, target: Target) -> bool:
        """True when an ACTIVE OPSI insight already exists for this database."""

        compartment = target.compartment_id or ""
        if not compartment or not target.resource_id:
            return False
        # Fast path: when the insight OCID is known, read it with the reliable
        # single-resource GET instead of the flaky list — no false "inactive"
        # from a partial list that dropped the insight.
        if target.opsi_database_insight_id:
            getter = getattr(self.oci, "get_opsi_database_insight", None)
            if getter is not None:
                try:
                    detail = getter(target.opsi_database_insight_id)
                except RuntimeError:
                    detail = {}
                if detail:
                    return detail.get("lifecycle-state") == "ACTIVE"
        # The opsi list endpoint flaps: it returns NotAuthorizedOrNotFound *or*
        # an exit-0 empty list even when insights exist. Both are inconclusive,
        # so retry on either. An empty result that falls through to create is
        # only tolerated by the 409 "already exists" guard; retrying lets us
        # detect the existing ACTIVE insight and skip the create round-trip.
        for _ in range(3):
            try:
                insights = self.oci.list_opsi_database_insights(compartment)
            except AttributeError:
                return False
            except RuntimeError:
                continue
            if not insights:
                continue
            return any(
                insight.get("database-id") == target.resource_id
                and insight.get("lifecycle-state") == "ACTIVE"
                for insight in insights
            )
        return False

    def _create_opsi_pe_comanaged(self, target: Target) -> None:
        missing = [
            name
            for name, value in {
                "resource_id": target.resource_id,
                "private_endpoint_id": target.private_endpoint_id,
                "database_resource_type": target.database_resource_type,
                "deployment_type": target.deployment_type,
            }.items()
            if not value
        ]
        if missing:
            log.info("Skipping Ops Insights for %s; missing: %s", target.name, ", ".join(missing))
            return
        args = [
            "opsi",
            "database-insights",
            "create-pe-comanged-database",
            "--compartment-id",
            target.compartment_id or "",
            "--database-id",
            target.resource_id or "",
            "--database-resource-type",
            target.database_resource_type,
            "--service-name",
            target.service_name or "",
            "--credential-details",
            f"file://{target.opsi_credential_details_file}",
            "--deployment-type",
            target.deployment_type,
            "--opsi-private-endpoint-id",
            target.opsi_private_endpoint_id or "",
            "--wait-for-state",
            "SUCCEEDED",
            "--max-wait-seconds",
            "1200",
            "--wait-interval-seconds",
            "30",
        ]
        if target.opsi_connection_details_file:
            args.extend(["--connection-details", f"file://{target.opsi_connection_details_file}"])
        # Tolerate a 409 "already exists" so a flaky active-check that fell through
        # does not fail the run when the insight is in fact present. Retry on the
        # post-enable propagation race ("database resource details were missing"):
        # right after DBM is enabled, the managed database is not yet visible to
        # Ops Insights, so the create is rejected until registration completes.
        for attempt in range(self.opsi_create_attempts):
            try:
                created = self.oci.run_tolerating(args, tolerated=("already exists",))
                if not created:
                    log.info("Ops Insights insight already exists for %s; left as-is", target.name)
                return
            except RuntimeError as exc:
                is_propagation = any(marker in str(exc) for marker in OPSI_PROPAGATION_MARKERS)
                if is_propagation and attempt < self.opsi_create_attempts - 1:
                    log.info(
                        "Ops Insights not ready for %s (database registering); retry %s/%s",
                        target.name,
                        attempt + 1,
                        self.opsi_create_attempts - 1,
                    )
                    self._sleep(self.opsi_create_delay)
                    continue
                raise

    def _print_external_next_step(self, target: Target) -> None:
        log.info("External target %s: run generated Management Agent script, then rerun validate.", target.name)
