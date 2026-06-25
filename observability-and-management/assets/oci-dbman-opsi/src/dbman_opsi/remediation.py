"""Map known DBM/OPSI failure signatures to actionable remediation.

When a live OCI or DB-side operation fails, the raw error is rarely actionable.
This module turns recognised error signatures into a short solution plus the
concrete manual step (CLI command, SQL, Console action, or IAM policy) needed to
resolve it — so a failed run hands the operator a task list instead of a stack
trace.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Remediation:
    signature: str
    cause: str
    solution: str
    manual_step: str


# Order matters: the first signature found in the error text wins, so put the
# more specific signatures before generic ones (e.g. ORA-28000 before 12514).
REMEDIATIONS: tuple[Remediation, ...] = (
    Remediation(
        "ORA-28000",
        "The monitoring user account is locked (too many failed logins, usually a stale consumer using an old password).",
        "Unlock the account and move it to a non-locking profile so a stale agent cannot re-lock it.",
        "SQL (as SYSDBA): CREATE PROFILE C##DBSNMP_MON LIMIT FAILED_LOGIN_ATTEMPTS UNLIMITED PASSWORD_LIFE_TIME UNLIMITED; "
        "ALTER USER DBSNMP PROFILE C##DBSNMP_MON CONTAINER=ALL; ALTER USER DBSNMP ACCOUNT UNLOCK CONTAINER=ALL;",
    ),
    Remediation(
        "ORA-01017",
        "The DBSNMP password in the Vault secret does not match the database.",
        "Set DBSNMP to the Vault secret's password (or rotate both to a new compliant value) so credential and DB agree.",
        "SQL (as SYSDBA): ALTER USER DBSNMP IDENTIFIED BY \"<vault-password>\" CONTAINER=ALL;  "
        "then re-run enable. The password needs >=2 special characters (DB verify function).",
    ),
    Remediation(
        "ORA-20000",
        "The chosen password violates the database password-verify function (commonly needs >=2 special characters).",
        "Pick a password with upper/lower/digit and at least two special characters, set it on DBSNMP, and update the Vault secret.",
        "Generate a compliant password, ALTER USER DBSNMP IDENTIFIED BY \"<pw>\" CONTAINER=ALL, then "
        "oci vault secret update-base64 --secret-id <secret> --secret-content-content <base64-pw>.",
    ),
    Remediation(
        "ORA-12514",
        "The connection service name is not registered on the listener (the bare DB/PDB name is usually wrong).",
        "Use the real listener service (db_unique_name.domain for the CDB, pdb_name.domain for the PDB) and reconcile the connection.",
        "On the DB host run `lsnrctl status` to list real services; set service_name in the config, regenerate OPSI payloads, "
        "and re-run enable (which reconciles DBM via modify-database-management).",
    ),
    Remediation(
        "DbcsEntityChangeWorkflowFailed",
        "The OPSI Database Insight create failed its post-create connection test (wrong service name or credential).",
        "Fix the service name and credential, then disable+delete the FAILED insight and recreate.",
        "Check the work-request error (oci raw-request GET .../workRequests/<id>/errors). Disable the FAILED insight "
        "(oci opsi database-insights disable) before delete, then re-run enable.",
    ),
    Remediation(
        "IncorrectState",
        "The resource is already in the requested state (e.g. Database Management already enabled).",
        "Treat as idempotent and reconcile the connection instead of re-enabling.",
        "Re-run enable — it tolerates the already-enabled 409 and reconciles via modify-(pluggable-)database-management.",
    ),
    Remediation(
        "RelatedResourceNotAuthorizedOrNotFound",
        "A referenced resource (often a Named Credential) was passed via the wrong CLI body and not resolved.",
        "Use the dedicated named-credential preferred-credential verb instead of the generic update.",
        "oci database-management preferred-credential update-preferred-credential-update-named-preferred-credential-details "
        "--managed-database-id <id> --credential-name PC_READ --named-credential-id <nc-id>.",
    ),
    Remediation(
        "NotAuthorizedOrNotFound",
        "Either a transient control-plane 404 (cap dbmgmt/opsi endpoints flap) or a missing IAM policy.",
        "Retry once; if it persists, add the Database Management IAM policy for the secret/named credential.",
        "Policy: Allow any-user to read secret-family in compartment <C> where ALL "
        "{target.secret.id='<secret>', request.principal.type='dbmgmtmanageddatabase'}. "
        "Also grant the operator group manage dbmgmt-named-credentials + use dbmgmt-managed-databases.",
    ),
    Remediation(
        "InternalError",
        "An OCI service-side 500, often transient or caused by an unsupported request shape (e.g. inline BASIC preferred credential).",
        "Retry; prefer the Named Credential path over inline BASIC preferred credentials.",
        "Create a RESOURCE_PRINCIPAL named credential, then set the preferred credential to reference it "
        "(see `dbman-opsi set-credentials`).",
    ),
)


def remediation_for(error_text: str) -> Remediation | None:
    """Return the first remediation whose signature appears in ``error_text``."""

    for remediation in REMEDIATIONS:
        if remediation.signature in error_text:
            return remediation
    return None


def format_remediation(remediation: Remediation) -> str:
    return (
        f"  ! {remediation.signature}: {remediation.cause}\n"
        f"    Solution: {remediation.solution}\n"
        f"    Manual step: {remediation.manual_step}"
    )
