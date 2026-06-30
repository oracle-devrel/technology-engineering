#!/usr/bin/env python3
# -----------------------------------------------------------------
# teardown_oci_log_analytics.py
#
# Delete OCI Log Analytics custom content created by
# setup_log_analytics.py / setup_oci_log_analytics.sh:
#   1. Source  (azureLogsSource)
#   2. Parsers (azureEntraIDAuditJsonParser, azureDiagnosticLogJsonParser)
#   3. Fields  (37 Azure-prefixed fields; "Cloud Provider" excluded)
#
# Auth (tried in order, same as setup_log_analytics.py):
#   1. OCI Resource Principal
#   2. OCI config file (~/.oci/config)
#   3. Environment variables
#
# Flags:
#   --dry-run       Show what would be deleted without deleting
#   --keep-fields   Skip field deletion (keep fields for shared use)
#
# Required env:
#   LA_NAMESPACE          Log Analytics namespace
#   OCI_COMPARTMENT_ID    Compartment OCID
# -----------------------------------------------------------------
import argparse
import json
import os
import subprocess
import sys

try:
    import oci
except ImportError:
    print("ERROR: OCI Python SDK not found. Install with: pip install oci")
    sys.exit(1)


# -- Authentication (mirrors setup_log_analytics.py) ---------------

def get_client():
    """Build LogAnalyticsClient with auto-detected auth."""

    # 1. Resource Principal
    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        signer = oci.auth.signers.get_resource_principals_signer()
        return oci.log_analytics.LogAnalyticsClient({}, signer=signer)

    # 2. OCI config file
    try:
        config = oci.config.from_file()
        oci.config.validate_config(config)
        return oci.log_analytics.LogAnalyticsClient(config)
    except Exception:
        pass

    # 3. Environment variables
    key_file = os.environ.get("OCI_KEY_FILE")
    key_content = os.environ.get("OCI_KEY_CONTENT")
    if key_file:
        with open(os.path.expanduser(key_file)) as f:
            key_pem = f.read()
    elif key_content:
        # Normalize PEM: handle escaped newlines from .env files
        key_pem = key_content.replace("\\n", "\n").strip()
    else:
        print("ERROR: No OCI credentials found.")
        print("  Set OCI config file (~/.oci/config), OCI_KEY_FILE, or")
        print("  run inside OCI Resource Manager.")
        sys.exit(1)

    config = {
        "user": os.environ["OCI_USER_OCID"],
        "key_content": key_pem,
        "pass_phrase": os.environ.get("OCI_KEY_PASSPHRASE", ""),
        "fingerprint": os.environ["OCI_FINGERPRINT"],
        "tenancy": os.environ["OCI_TENANCY_OCID"],
        "region": os.environ.get("OCI_REGION", ""),
    }
    return oci.log_analytics.LogAnalyticsClient(config)


# -- Constants -----------------------------------------------------

SOURCE_NAME = "Azure Logs"
SOURCE_INTERNAL_NAME = "azureLogsSource"
PARSER_NAMES = [
    "azureEntraIDAuditJsonParser",
    "azureDiagnosticLogJsonParser",
]

# Fields to delete (Azure-prefixed only; "Cloud Provider" is shared with gcplogs2oci)
AZURE_FIELD_DISPLAY_NAMES = [
    # EntraID / Unified Audit Log fields
    "Azure Time Generated",
    "Azure Event ID",
    "Azure Operation",
    "Azure Record Type",
    "Azure Result Status",
    "Azure User Type",
    "Azure User ID",
    "Azure User Key",
    "Azure Workload",
    "Azure Object ID",
    "Azure Client IP",
    "Azure Organization ID",
    "Azure Schema Version",
    "Azure Creation Time",
    "Azure AD Event Type",
    "Azure Actor Context ID",
    "Azure Actor IP Address",
    "Azure Inter Systems ID",
    "Azure Intra System ID",
    "Azure Target Context ID",
    "Azure Application ID",
    # Azure Monitor Diagnostic / Activity Log fields
    "Azure Resource ID",
    "Azure Resource Group",
    "Azure Resource Type",
    "Azure Resource Provider",
    "Azure Subscription ID",
    "Azure Correlation ID",
    "Azure Caller",
    "Azure Level",
    "Azure Tenant ID",
    "Azure Location",
    "Azure Category",
    "Azure Duration Ms",
    "Azure Result Type",
    "Azure Result Signature",
    "Azure Result Description",
    "Azure Caller IP",
]


# -- Deletion Functions --------------------------------------------

def delete_source(client, namespace, compartment_id, dry_run=False):
    """Delete the LA source via oci CLI subprocess."""
    print(f"  Source: {SOURCE_NAME}")

    # Check if source exists
    try:
        existing = client.list_sources(
            namespace, compartment_id,
            name=SOURCE_NAME, is_system="ALL",
        )
        if not existing.data.items:
            print("    -> already deleted (not found)")
            return
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            print("    -> already deleted (404)")
            return
        raise

    if dry_run:
        print("    -> would delete (dry-run)")
        return

    # Use oci CLI for source deletion (SDK source delete is complex)
    cmd = [
        "oci", "log-analytics", "source", "delete-source",
        "--namespace-name", namespace,
        "--source-name", SOURCE_INTERNAL_NAME,
        "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("    -> deleted")
    elif "404" in result.stderr or "NotFound" in result.stderr:
        print("    -> already deleted (404)")
    else:
        print(f"    -> warning: {result.stderr[:200]}")


def delete_parsers(client, namespace, dry_run=False):
    """Delete all JSON parsers."""
    for parser_name in PARSER_NAMES:
        print(f"  Parser: {parser_name}")

        try:
            client.get_parser(namespace, parser_name)
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                print("    -> already deleted (404)")
                continue
            raise

        if dry_run:
            print("    -> would delete (dry-run)")
            continue

        try:
            client.delete_parser(namespace, parser_name)
            print("    -> deleted")
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                print("    -> already deleted (404)")
            else:
                print(f"    -> warning: {e.message}")


def delete_fields(client, namespace, dry_run=False):
    """Delete Azure-prefixed custom fields (excludes Cloud Provider)."""
    print(f"  Fields: {len(AZURE_FIELD_DISPLAY_NAMES)} Azure-prefixed fields")
    print("    (Cloud Provider excluded — shared with gcplogs2oci)")

    deleted = 0
    skipped = 0
    for display_name in AZURE_FIELD_DISPLAY_NAMES:
        # Find the internal field name using the filter parameter
        internal_name = None
        try:
            # Use filter param to search by display name
            fields = client.list_fields(
                namespace, filter=display_name
            ).data.items
            for f in fields:
                if f.display_name == display_name:
                    internal_name = f.name
                    break
        except oci.exceptions.ServiceError:
            pass

        if not internal_name:
            skipped += 1
            continue

        if dry_run:
            print(f"    {internal_name:30s} ({display_name}) -> would delete")
            deleted += 1
            continue

        try:
            client.delete_field(namespace, internal_name)
            print(f"    {internal_name:30s} ({display_name}) -> deleted")
            deleted += 1
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                skipped += 1
            elif e.status == 409:
                print(f"    {internal_name:30s} ({display_name}) -> in use, skipped")
                skipped += 1
            else:
                print(f"    {internal_name:30s} ({display_name}) -> error: {e.message}")
                skipped += 1

    action = "would delete" if dry_run else "deleted"
    print(f"  Total: {action} {deleted}, skipped {skipped}")


# -- Main ----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Delete OCI Log Analytics custom content for azurelogs2oci"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be deleted without deleting")
    parser.add_argument("--keep-fields", action="store_true",
                        help="Skip field deletion entirely")
    args = parser.parse_args()

    namespace = os.environ.get("LA_NAMESPACE")
    compartment_id = os.environ.get("OCI_COMPARTMENT_ID")

    if not namespace:
        print("ERROR: LA_NAMESPACE environment variable is required")
        sys.exit(1)
    if not compartment_id:
        print("ERROR: OCI_COMPARTMENT_ID environment variable is required")
        sys.exit(1)

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Teardown OCI Log Analytics custom content")
    print(f"  Namespace:   {namespace}")
    print(f"  Compartment: {compartment_id[:40]}...")
    print()

    client = get_client()

    # Delete in reverse dependency order: source -> parser -> fields
    print("--- Deleting source ---")
    delete_source(client, namespace, compartment_id, args.dry_run)
    print()

    print("--- Deleting parsers ---")
    delete_parsers(client, namespace, args.dry_run)
    print()

    if args.keep_fields:
        print("--- Skipping field deletion (--keep-fields) ---")
    else:
        print("--- Deleting fields ---")
        delete_fields(client, namespace, args.dry_run)
    print()

    print(f"{mode}Log Analytics teardown complete.")


if __name__ == "__main__":
    main()
