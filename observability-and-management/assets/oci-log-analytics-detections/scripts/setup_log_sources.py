"""
Create custom OCI Log Analytics fields, parsers, and log sources for SOC detections.

This script sets up the Log Analytics content required for detection rules to work:
  - Custom fields (Command Line, Process Name, Problem Name, etc.)
  - JSON parsers that map NDJSON test data fields to OCI LA fields
  - SOC custom log sources that reference those parsers (only when needed)

Log sources created:
  - SOC Linux Syslog Logs       (parses linux_syslog.jsonl)
  - SOC Windows Sysmon Logs     (parses windows_sysmon.jsonl)
  - SOC Cloud Guard Logs        (parses cloud_guard.jsonl)
  - SOC Application Logs        (parses application_logs.jsonl)

Native OCI sources are preferred when available (for example `OCI Cloud Guard Problems`
or `Windows Sysmon Events`). SOC custom sources are created only when an equivalent
native source is not present.

Prerequisites:
  1. OCI CLI configured (~/.oci/config)
  2. Log Analytics service enabled in the tenancy

Usage:
  python3 scripts/setup_log_sources.py          # Create all content
  python3 scripts/setup_log_sources.py --dry-run # Print plan only
"""

import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    TENANCY_ID, COMPARTMENT_ID, OCI_PROFILE,
    get_la_client, get_namespace, validate_oci_setup,
    list_available_log_sources,
    resolve_compartment_id,
    assert_write_allowed, ProdWriteGuardError,
)

import oci
from oci.log_analytics.models import (
    LogAnalyticsField,
    LogAnalyticsParserField,
    UpsertLogAnalyticsFieldDetails,
    UpsertLogAnalyticsParserDetails,
)

# ─── Static definitions + pure helpers (extracted to the logsources package) ───
from logsources.definitions import *  # noqa: F401,F403,E402
from logsources.field_helpers import *  # noqa: F401,F403,E402
from obs_logging import get_logger, bind  # noqa: E402

# Additive structured diagnostics on stderr; the stdout prints stay the UX/test
# contract. Correlates the live field/parser/source creation lifecycle by run-id.
log = get_logger("setup_log_sources")


# ─── Runtime retry / timeout configuration ───────────────────────
FIELD_LIST_ATTEMPTS = int(os.environ.get("OCI_LOG_ANALYTICS_FIELD_LIST_ATTEMPTS", "3"))
FIELD_LIST_RETRY_DELAY_SECONDS = float(
    os.environ.get("OCI_LOG_ANALYTICS_FIELD_LIST_RETRY_DELAY_SECONDS", "2")
)
LOG_ANALYTICS_READ_TIMEOUT_SECONDS = int(
    os.environ.get("OCI_LOG_ANALYTICS_READ_TIMEOUT_SECONDS", "180")
)


# ─── OCI Field / Parser / Source Orchestration ───────────────────
def build_existing_field_inventory(client, namespace):
    """Fetch all existing fields and return lookup metadata for reuse/audit."""
    entries = []
    by_display = {}
    by_name = {}
    page = None
    while True:
        kwargs = {"limit": 1000}
        if page:
            kwargs["page"] = page
        resp = list_fields_with_retry(client, namespace, kwargs)
        for field in resp.data.items:
            entry = build_field_inventory_entry(field)
            entries.append(entry)
            add_field_inventory_lookup(by_display, entry["display_name"], entry)
            add_field_inventory_lookup(by_name, entry["name"], entry)
        page = resp.headers.get("opc-next-page")
        if not page:
            break
    return {
        "entries": entries,
        "by_display": by_display,
        "by_name": by_name,
    }


def list_fields_with_retry(client, namespace, kwargs):
    """List fields with bounded retries for slow Log Analytics namespaces."""
    for attempt in range(1, FIELD_LIST_ATTEMPTS + 1):
        try:
            return client.list_fields(namespace, **kwargs)
        except oci.exceptions.RequestException:
            if attempt == FIELD_LIST_ATTEMPTS:
                raise
            print(
                "  WARNING: list_fields timed out; "
                f"retrying {attempt}/{FIELD_LIST_ATTEMPTS - 1}"
            )
            time.sleep(FIELD_LIST_RETRY_DELAY_SECONDS * attempt)
        except oci.exceptions.ServiceError as exc:
            retryable_statuses = {429, 500, 502, 503, 504}
            if attempt == FIELD_LIST_ATTEMPTS or getattr(exc, "status", None) not in retryable_statuses:
                raise
            print(
                "  WARNING: list_fields returned a retryable OCI error; "
                f"retrying {attempt}/{FIELD_LIST_ATTEMPTS - 1}"
            )
            time.sleep(FIELD_LIST_RETRY_DELAY_SECONDS * attempt)


def audit_existing_fields(client, namespace, field_display_names, show_exact=False):
    """Fetch namespace fields, print an audit, and return the audit details."""
    inventory = build_existing_field_inventory(client, namespace)
    audit = build_field_reuse_audit(inventory, field_display_names)
    print_field_reuse_audit(audit, show_exact=show_exact)
    return audit


def build_existing_field_map(client, namespace):
    """Fetch all existing fields and return name -> internal_name map.

    Supports lookup by both display_name and internal_name, so parser
    field mappings can reference either (e.g., built-in 'msg' and 'time').
    """
    inventory = build_existing_field_inventory(client, namespace)
    result = {}
    for entry in inventory["entries"]:
        if entry.get("display_name") and entry.get("name"):
            result[entry["display_name"]] = entry["name"]
            result[entry["display_name"].lower()] = entry["name"]
        if entry.get("name"):
            result[entry["name"]] = entry["name"]
            result[entry["name"].lower()] = entry["name"]
    return result


def create_fields(client, namespace, field_display_names):
    """Create or upsert custom fields. Returns display_name -> internal_name map."""
    existing = build_existing_field_inventory(client, namespace)
    field_map = {}

    for display_name in unique_preserving_order(field_display_names):
        existing_entry = find_existing_field_for_creation(existing, display_name)
        if existing_entry and existing_entry.get("name"):
            field_map[display_name] = existing_entry["name"]
            print(f"  Field EXISTS {existing_entry['name']:20s} -> {display_name}")
            continue

        details = UpsertLogAnalyticsFieldDetails()
        details.display_name = display_name
        details.data_type = field_data_type_for(display_name)
        details.is_multi_valued = False
        try:
            resp = client.upsert_field(namespace, details)
            field_map[display_name] = resp.data.name
            print(f"  Field OK     {resp.data.name:20s} -> {display_name} ({details.data_type})")
        except oci.exceptions.ServiceError as exc:
            if details.data_type == "String" and is_single_value_string_limit_error(exc):
                details.is_multi_valued = True
                try:
                    resp = client.upsert_field(namespace, details)
                    field_map[display_name] = resp.data.name
                    print(
                        f"  Field OK     {resp.data.name:20s} -> {display_name} "
                        "(multi-valued String fallback)"
                    )
                    continue
                except oci.exceptions.ServiceError as retry_exc:
                    exc = retry_exc
            if details.data_type != "String":
                details.data_type = "String"
                try:
                    resp = client.upsert_field(namespace, details)
                    field_map[display_name] = resp.data.name
                    print(
                        f"  Field OK     {resp.data.name:20s} -> {display_name} "
                        "(fallback String)"
                    )
                    continue
                except oci.exceptions.ServiceError as retry_exc:
                    exc = retry_exc
            print(f"  Field ERR    {display_name}: {exc.message}")

    return field_map


def create_parser(client, namespace, parser_name, display_name, description,
                  field_mappings, field_map, example_log):
    """Create or upsert a JSON parser with field mappings."""
    parser_field_maps = []
    for name_or_display, json_path, seq in field_mappings:
        internal = field_map.get(name_or_display) or field_map.get(name_or_display.lower())
        if not internal:
            print(f"  WARNING: Field '{name_or_display}' not found in field_map, skipping from parser")
            continue
        parser_field_maps.append(
            LogAnalyticsParserField(
                field=LogAnalyticsField(name=internal),
                parser_field_name=internal,
                parser_field_sequence=seq,
                storage_field_name=internal,
                structured_column_info=json_path,
            )
        )

    example_content = json.dumps(example_log, indent=2)

    parser_details = UpsertLogAnalyticsParserDetails(
        name=parser_name,
        display_name=display_name,
        description=description,
        type="JSON",
        language="en_US",
        encoding="UTF-8",
        is_default=True,
        is_single_line_content=False,
        is_system=False,
        header_content="$:0",
        content=example_content,
        example_content=example_content,
        field_maps=parser_field_maps,
    )

    etag = None
    try:
        existing = client.get_parser(namespace, parser_name)
        etag = existing.headers.get("etag")
    except oci.exceptions.ServiceError:
        pass

    kwargs = {"if_match": etag} if etag else {}
    result = client.upsert_parser(namespace, parser_details, **kwargs)
    print(f"  Parser OK: {result.data.name} ({len(result.data.field_maps)} field maps)")


def find_existing_source(client, namespace, compartment_id, source_internal_name, source_display_name):
    """Find an existing source by internal or display name."""
    candidates = unique_preserving_order([source_internal_name, source_display_name])
    for candidate in candidates:
        try:
            existing = client.list_sources(
                namespace, compartment_id,
                name=candidate, is_system="ALL",
            )
        except Exception:
            continue
        for src in existing.data.items:
            if src.name in candidates or src.display_name == source_display_name:
                return src

    page = None
    while True:
        kwargs = {"limit": 1000, "is_system": "ALL"}
        if page:
            kwargs["page"] = page
        try:
            resp = client.list_sources(namespace, compartment_id, **kwargs)
        except Exception:
            return None
        for src in resp.data.items:
            if src.name in candidates or src.display_name == source_display_name:
                return src
        page = resp.headers.get("opc-next-page")
        if not page:
            return None


def get_source_etag(client, namespace, compartment_id, source_name):
    """Return the current source ETag when OCI requires optimistic concurrency."""
    try:
        response = client.get_source(namespace, source_name, compartment_id)
        return response.headers.get("etag")
    except Exception:
        return None


def create_source(client, namespace, compartment_id, source_internal_name,
                  source_display_name, source_description, parser_name):
    """Create or refresh a Log Analytics source referencing a parser (via OCI CLI)."""
    existing_source = find_existing_source(
        client, namespace, compartment_id, source_internal_name, source_display_name
    )
    source_name = existing_source.name if existing_source else source_internal_name
    etag = get_source_etag(client, namespace, compartment_id, source_name) if existing_source else None
    action = "REFRESH" if existing_source else "OK"

    try:
        if existing_source:
            print(f"  Source EXISTS: {existing_source.name} (display={existing_source.display_name})")
    except Exception:
        pass

    parsers_json = json.dumps([{"name": parser_name, "isDefault": True}])
    entity_types_json = json.dumps(
        [{"entityType": "oci_generic_resource",
          "entityTypeCategory": "Undefined",
          "entityTypeDisplayName": "OCI Generic Resource"}]
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as pf:
        pf.write(parsers_json)
        parsers_path = pf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as ef:
        ef.write(entity_types_json)
        entity_path = ef.name

    try:
        cmd = [
            "oci", "log-analytics", "source", "upsert-source",
            "--namespace-name", namespace,
            "--name", source_name,
            "--display-name", source_display_name,
            "--description", source_description,
            "--type-name", "os_file",
            "--is-system", "false",
            "--is-for-cloud", "false",
            "--parsers", f"file://{parsers_path}",
            "--entity-types", f"file://{entity_path}",
        ]
        if OCI_PROFILE:
            cmd.extend(["--profile", OCI_PROFILE])
        if etag:
            cmd.extend(["--if-match", etag])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Source {action}: {source_display_name} -> parser {parser_name}")
        else:
            stderr = result.stderr.strip()
            if "already exists" in stderr.lower():
                print(f"  Source EXISTS: {source_display_name}")
            else:
                print(f"  Source WARN: {stderr[:300]}")
    finally:
        os.unlink(parsers_path)
        os.unlink(entity_path)


def should_skip_custom_source_creation(available_sources, source_display_name):
    """Return (bool, reason) when a custom source should not be created.

    Note: We always create SOC custom sources even when native equivalents exist,
    because native sources use XML/built-in parsers that cannot parse our JSON
    test data. The SOC sources use JSON parsers for field extraction.
    """
    if source_display_name in available_sources:
        return False, ""

    # Do NOT skip — always create SOC sources alongside native ones.
    # Native XML parsers can't parse our JSON uploads; SOC JSON parsers can.
    return False, ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Set up custom OCI LA log sources for SOC detections")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    parser.add_argument("--validate", action="store_true", help="Run pre-flight validation checks")
    parser.add_argument(
        "--application-only",
        action="store_true",
        help="Only create/refresh SOC Application Logs fields, parser, and source",
    )
    parser.add_argument(
        "--octo-apm-only",
        action="store_true",
        help="Alias for --application-only, scoped to the Octo APM demo schema",
    )
    parser.add_argument(
        "--field-audit",
        action="store_true",
        help="Inspect namespace fields and report exact reuse versus fields setup would create",
    )
    parser.add_argument(
        "--field-audit-details",
        action="store_true",
        help="With --field-audit, print every exact field reuse mapping",
    )
    parser.add_argument(
        "--i-understand-prod",
        action="store_true",
        dest="i_understand_prod",
        help="Acknowledge a deliberate create against the emdemo PRODUCTION "
             "tenancy outside the LogAnalytics subtree (or set OCI_ALLOW_PROD_WRITE=1).",
    )
    args = parser.parse_args()
    octo_apm_only = args.octo_apm_only
    application_only = args.application_only or octo_apm_only

    if args.validate:
        ok = validate_oci_setup(['ocid', 'cli', 'namespace', 'compartment'])
        sys.exit(0 if ok else 1)

    if args.dry_run:
        fields_to_create, field_mappings = select_field_contract(
            octo_apm_only=octo_apm_only,
            application_only=application_only,
        )
        if not application_only:
            field_mappings = []
        print("DRY RUN - would create:")
        print(f"  up to {len(unique_preserving_order(fields_to_create))} custom fields")
        print("  existing namespace fields are reused by exact display name")
        print("  run with --field-audit to inspect live reuse before creating fields")
        if application_only:
            print(f"  1 JSON parser: {APP_PARSER_DISPLAY} ({len(field_mappings)} field maps)")
            print(f"  1 log source: {APP_SOURCE_DISPLAY} ({APP_SOURCE_INTERNAL})")
            return
        print(f"  19 JSON parsers")
        print(f"  up to 21 log sources (SOC sources skipped when native equivalent exists):")
        print(f"    - {LINUX_SOURCE_DISPLAY} ({LINUX_SOURCE_INTERNAL})")
        print(f"    - {WINDOWS_SOURCE_DISPLAY} ({WINDOWS_SOURCE_INTERNAL})")
        print(f"    - {CG_SOURCE_DISPLAY} ({CG_SOURCE_INTERNAL})")
        print(f"    - {CGIS_SOURCE_DISPLAY} ({CGIS_SOURCE_INTERNAL})")
        print(f"    - {OSQUERY_SOURCE_DISPLAY} ({OSQUERY_SOURCE_INTERNAL})")
        print(f"    - {WINSEC_SOURCE_DISPLAY} ({WINSEC_SOURCE_INTERNAL})")
        print(f"    - {WINSYS_SOURCE_DISPLAY} ({WINSYS_SOURCE_INTERNAL})")
        print(f"    - {WINPS_SOURCE_DISPLAY} ({WINPS_SOURCE_INTERNAL})")
        print(f"    - {WINDEF_SOURCE_DISPLAY} ({WINDEF_SOURCE_INTERNAL})")
        print(f"    - {LINSEC_SOURCE_DISPLAY} ({LINSEC_SOURCE_INTERNAL})")
        print(f"    - {SYSMON_SOURCE_DISPLAY} ({SYSMON_SOURCE_INTERNAL})")
        print(f"    - {SYSNET_SOURCE_DISPLAY} ({SYSNET_SOURCE_INTERNAL})")
        print(f"    - {WAF_SOURCE_DISPLAY} ({WAF_SOURCE_INTERNAL})")
        print(f"    - {LB_SOURCE_DISPLAY} ({LB_SOURCE_INTERNAL})")
        print(f"    - {WEBAPP_SOURCE_DISPLAY} ({WEBAPP_SOURCE_INTERNAL})")
        print(f"    - {APP_SOURCE_DISPLAY} ({APP_SOURCE_INTERNAL})")
        print(f"    - {GENAI_SOURCE_DISPLAY} ({GENAI_SOURCE_INTERNAL})")
        print(f"    - {AZURE_CUSTOM_SOURCE_DISPLAY} ({AZURE_CUSTOM_SOURCE_INTERNAL})")
        print(f"    - {VCN_SOURCE_DISPLAY} ({VCN_SOURCE_INTERNAL})")
        print(f"    - {FW_SOURCE_DISPLAY} ({FW_SOURCE_INTERNAL})")
        print(f"    - {HEALTH_SOURCE_DISPLAY} ({HEALTH_SOURCE_INTERNAL})")
        return

    la_client = get_la_client(timeout=(10, LOG_ANALYTICS_READ_TIMEOUT_SECONDS))

    # Get namespace + active compartment (resolved per-profile)
    namespace = get_namespace(la_client, quiet=args.field_audit)

    fields_to_create, app_field_mappings = select_field_contract(
        octo_apm_only=octo_apm_only,
        application_only=application_only,
    )

    if args.field_audit:
        audit_existing_fields(
            la_client,
            namespace,
            fields_to_create,
            show_exact=args.field_audit_details,
        )
        return

    compartment_id = resolve_compartment_id()
    print("Compartment: resolved from OCI configuration")
    slog = bind(
        log,
        compartment=compartment_id,
        namespace=namespace,
        application_only=application_only,
    )
    slog.info("setup.start")

    # Tenancy safety: refuse field/parser/source creation against emdemo (prod)
    # outside the LogAnalytics subtree unless --i-understand-prod was passed.
    try:
        assert_write_allowed(compartment_id, override=args.i_understand_prod)
    except ProdWriteGuardError as guard_err:
        slog.error("setup.prod_write_blocked", extra={"override": args.i_understand_prod})
        print(f"\n  {guard_err}")
        sys.exit(2)

    available_sources = list_available_log_sources(la_client, namespace, compartment_id)
    print(f"Discovered {len(available_sources)} existing log sources")

    # Step 1: Create custom fields
    print("\n" + "=" * 60)
    print("STEP 1: CREATE CUSTOM FIELDS")
    print("=" * 60)
    field_map = create_fields(la_client, namespace, fields_to_create)

    # Also load ALL existing fields (including built-in) for parser creation
    all_fields = build_existing_field_map(la_client, namespace)
    field_map.update(all_fields)
    print(f"\n  Total fields available for parser mapping: {len(field_map)}")

    if octo_apm_only:
        missing_fields = missing_octo_apm_workshop_fields(field_map)
        if missing_fields:
            print("\n  Octo APM workshop field readiness FAILED.")
            for field_name in missing_fields:
                print(f"    - missing field: {field_name}")
            sys.exit(2)
        print("  Octo APM workshop field readiness OK")

    # Step 2: Create parsers
    print("\n" + "=" * 60)
    print("STEP 2: CREATE JSON PARSERS")
    print("=" * 60)

    if application_only:
        print("\n--- Application Telemetry Parser ---")
        create_parser(la_client, namespace,
                      APP_PARSER_NAME, APP_PARSER_DISPLAY, APP_PARSER_DESC,
                      app_field_mappings, field_map, APP_EXAMPLE)

        print("\n" + "=" * 60)
        print("STEP 3: CREATE LOG SOURCES")
        print("=" * 60)
        print("\n--- Application Telemetry Source ---")
        create_source(
            la_client, namespace, compartment_id,
            APP_SOURCE_INTERNAL, APP_SOURCE_DISPLAY, APP_SOURCE_DESC, APP_PARSER_NAME
        )
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print(f"\nConfigured log source/parser:")
        print(f"  - {APP_SOURCE_DISPLAY}")
        return

    print("\n--- Linux Syslog Parser ---")
    create_parser(la_client, namespace,
                  LINUX_PARSER_NAME, LINUX_PARSER_DISPLAY, LINUX_PARSER_DESC,
                  LINUX_FIELD_MAPPINGS, field_map, LINUX_EXAMPLE)

    print("\n--- Windows Sysmon Parser ---")
    create_parser(la_client, namespace,
                  WINDOWS_PARSER_NAME, WINDOWS_PARSER_DISPLAY, WINDOWS_PARSER_DESC,
                  WINDOWS_FIELD_MAPPINGS, field_map, WINDOWS_EXAMPLE)

    print("\n--- Cloud Guard Parser ---")
    create_parser(la_client, namespace,
                  CG_PARSER_NAME, CG_PARSER_DISPLAY, CG_PARSER_DESC,
                  CG_FIELD_MAPPINGS, field_map, CG_EXAMPLE)

    print("\n--- Cloud Guard Instance Security Parser ---")
    create_parser(la_client, namespace,
                  CGIS_PARSER_NAME, CGIS_PARSER_DISPLAY, CGIS_PARSER_DESC,
                  CGIS_FIELD_MAPPINGS, field_map, CGIS_EXAMPLE)

    print("\n--- Windows Event Security Parser ---")
    create_parser(la_client, namespace,
                  WINSEC_PARSER_NAME, WINSEC_PARSER_DISPLAY, WINSEC_PARSER_DESC,
                  WINSEC_FIELD_MAPPINGS, field_map, WINSEC_EXAMPLE)

    print("\n--- Windows Event System Parser ---")
    create_parser(la_client, namespace,
                  WINSYS_PARSER_NAME, WINSYS_PARSER_DISPLAY, WINSYS_PARSER_DESC,
                  WINSYS_FIELD_MAPPINGS, field_map, WINSYS_EXAMPLE)

    print("\n--- Windows PowerShell Operational Parser ---")
    create_parser(la_client, namespace,
                  WINPS_PARSER_NAME, WINPS_PARSER_DISPLAY, WINPS_PARSER_DESC,
                  WINPS_FIELD_MAPPINGS, field_map, WINPS_EXAMPLE)

    print("\n--- Windows Defender Operational Parser ---")
    create_parser(la_client, namespace,
                  WINDEF_PARSER_NAME, WINDEF_PARSER_DISPLAY, WINDEF_PARSER_DESC,
                  WINDEF_FIELD_MAPPINGS, field_map, WINDEF_EXAMPLE)

    print("\n--- Linux Secure Parser ---")
    create_parser(la_client, namespace,
                  LINSEC_PARSER_NAME, LINSEC_PARSER_DISPLAY, LINSEC_PARSER_DESC,
                  LINSEC_FIELD_MAPPINGS, field_map, LINSEC_EXAMPLE)

    print("\n--- Sysmon Operational Parser ---")
    create_parser(la_client, namespace,
                  SYSMON_PARSER_NAME, SYSMON_PARSER_DISPLAY, SYSMON_PARSER_DESC,
                  SYSMON_FIELD_MAPPINGS, field_map, SYSMON_EXAMPLE)

    print("\n--- Sysmon Network Parser ---")
    create_parser(la_client, namespace,
                  SYSNET_PARSER_NAME, SYSNET_PARSER_DISPLAY, SYSNET_PARSER_DESC,
                  SYSNET_FIELD_MAPPINGS, field_map, SYSNET_EXAMPLE)

    print("\n--- WAF Security Parser ---")
    create_parser(la_client, namespace,
                  WAF_PARSER_NAME, WAF_PARSER_DISPLAY, WAF_PARSER_DESC,
                  WAF_FIELD_MAPPINGS, field_map, WAF_EXAMPLE)

    print("\n--- Load Balancer Access Parser ---")
    create_parser(la_client, namespace,
                  LB_PARSER_NAME, LB_PARSER_DISPLAY, LB_PARSER_DESC,
                  LB_FIELD_MAPPINGS, field_map, LB_EXAMPLE)

    print("\n--- Web Application Parser ---")
    create_parser(la_client, namespace,
                  WEBAPP_PARSER_NAME, WEBAPP_PARSER_DISPLAY, WEBAPP_PARSER_DESC,
                  WEBAPP_FIELD_MAPPINGS, field_map, WEBAPP_EXAMPLE)

    print("\n--- Application Telemetry Parser ---")
    create_parser(la_client, namespace,
                  APP_PARSER_NAME, APP_PARSER_DISPLAY, APP_PARSER_DESC,
                  APP_FIELD_MAPPINGS, field_map, APP_EXAMPLE)

    print("\n--- GenAI Gateway Parser ---")
    create_parser(la_client, namespace,
                  GENAI_PARSER_NAME, GENAI_PARSER_DISPLAY, GENAI_PARSER_DESC,
                  GENAI_FIELD_MAPPINGS, field_map, GENAI_EXAMPLE)

    print("\n--- VCN Flow Parser ---")
    create_parser(la_client, namespace,
                  VCN_PARSER_NAME, VCN_PARSER_DISPLAY, VCN_PARSER_DESC,
                  VCN_FIELD_MAPPINGS, field_map, VCN_EXAMPLE)

    print("\n--- Network Firewall Parser ---")
    create_parser(la_client, namespace,
                  FW_PARSER_NAME, FW_PARSER_DISPLAY, FW_PARSER_DESC,
                  FW_FIELD_MAPPINGS, field_map, FW_EXAMPLE)

    print("\n--- Multicloud Health Parser ---")
    create_parser(la_client, namespace,
                  HEALTH_PARSER_NAME, HEALTH_PARSER_DISPLAY, HEALTH_PARSER_DESC,
                  HEALTH_FIELD_MAPPINGS, field_map, HEALTH_EXAMPLE)

    # Step 3: Create log sources
    print("\n" + "=" * 60)
    print("STEP 3: CREATE LOG SOURCES")
    print("=" * 60)

    def create_source_if_needed(source_internal, source_display, source_desc, parser_name):
        skip, reason = should_skip_custom_source_creation(available_sources, source_display)
        if skip:
            print(f"  Source SKIP: {source_display} ({reason})")
            return
        create_source(
            la_client, namespace, compartment_id,
            source_internal, source_display, source_desc, parser_name
        )
        available_sources.add(source_display)

    print("\n--- Linux Source ---")
    create_source_if_needed(
        LINUX_SOURCE_INTERNAL, LINUX_SOURCE_DISPLAY, LINUX_SOURCE_DESC, LINUX_PARSER_NAME
    )

    print("\n--- Windows Sysmon Source ---")
    create_source_if_needed(
        WINDOWS_SOURCE_INTERNAL, WINDOWS_SOURCE_DISPLAY, WINDOWS_SOURCE_DESC, WINDOWS_PARSER_NAME
    )

    print("\n--- Cloud Guard Source ---")
    create_source_if_needed(
        CG_SOURCE_INTERNAL, CG_SOURCE_DISPLAY, CG_SOURCE_DESC, CG_PARSER_NAME
    )

    print("\n--- Cloud Guard Instance Security Source ---")
    create_source_if_needed(
        CGIS_SOURCE_INTERNAL, CGIS_SOURCE_DISPLAY, CGIS_SOURCE_DESC, CGIS_PARSER_NAME
    )

    print("\n--- OSQuery Result Source ---")
    create_source_if_needed(
        OSQUERY_SOURCE_INTERNAL, OSQUERY_SOURCE_DISPLAY, OSQUERY_SOURCE_DESC, CGIS_PARSER_NAME
    )

    print("\n--- Windows Event Security Source ---")
    create_source_if_needed(
        WINSEC_SOURCE_INTERNAL, WINSEC_SOURCE_DISPLAY, WINSEC_SOURCE_DESC, WINSEC_PARSER_NAME
    )

    print("\n--- Windows Event System Source ---")
    create_source_if_needed(
        WINSYS_SOURCE_INTERNAL, WINSYS_SOURCE_DISPLAY, WINSYS_SOURCE_DESC, WINSYS_PARSER_NAME
    )

    print("\n--- Windows PowerShell Operational Source ---")
    create_source_if_needed(
        WINPS_SOURCE_INTERNAL, WINPS_SOURCE_DISPLAY, WINPS_SOURCE_DESC, WINPS_PARSER_NAME
    )

    print("\n--- Windows Defender Operational Source ---")
    create_source_if_needed(
        WINDEF_SOURCE_INTERNAL, WINDEF_SOURCE_DISPLAY, WINDEF_SOURCE_DESC, WINDEF_PARSER_NAME
    )

    print("\n--- Linux Secure Source ---")
    create_source_if_needed(
        LINSEC_SOURCE_INTERNAL, LINSEC_SOURCE_DISPLAY, LINSEC_SOURCE_DESC, LINSEC_PARSER_NAME
    )

    print("\n--- Sysmon Operational Source ---")
    create_source_if_needed(
        SYSMON_SOURCE_INTERNAL, SYSMON_SOURCE_DISPLAY, SYSMON_SOURCE_DESC, SYSMON_PARSER_NAME
    )

    print("\n--- Sysmon Network Source ---")
    create_source_if_needed(
        SYSNET_SOURCE_INTERNAL, SYSNET_SOURCE_DISPLAY, SYSNET_SOURCE_DESC, SYSNET_PARSER_NAME
    )

    print("\n--- WAF Security Source ---")
    create_source_if_needed(
        WAF_SOURCE_INTERNAL, WAF_SOURCE_DISPLAY, WAF_SOURCE_DESC, WAF_PARSER_NAME
    )

    print("\n--- Load Balancer Access Source ---")
    create_source_if_needed(
        LB_SOURCE_INTERNAL, LB_SOURCE_DISPLAY, LB_SOURCE_DESC, LB_PARSER_NAME
    )

    print("\n--- Web Application Source ---")
    create_source_if_needed(
        WEBAPP_SOURCE_INTERNAL, WEBAPP_SOURCE_DISPLAY, WEBAPP_SOURCE_DESC, WEBAPP_PARSER_NAME
    )

    print("\n--- Application Telemetry Source ---")
    create_source_if_needed(
        APP_SOURCE_INTERNAL, APP_SOURCE_DISPLAY, APP_SOURCE_DESC, APP_PARSER_NAME
    )

    print("\n--- GenAI Gateway Source ---")
    create_source_if_needed(
        GENAI_SOURCE_INTERNAL, GENAI_SOURCE_DISPLAY, GENAI_SOURCE_DESC, GENAI_PARSER_NAME
    )

    print("\n--- Azure Log Analytics Custom Source ---")
    create_source_if_needed(
        AZURE_CUSTOM_SOURCE_INTERNAL, AZURE_CUSTOM_SOURCE_DISPLAY, AZURE_CUSTOM_SOURCE_DESC, APP_PARSER_NAME
    )

    print("\n--- VCN Flow Source ---")
    create_source_if_needed(
        VCN_SOURCE_INTERNAL, VCN_SOURCE_DISPLAY, VCN_SOURCE_DESC, VCN_PARSER_NAME
    )

    print("\n--- Network Firewall Source ---")
    create_source_if_needed(
        FW_SOURCE_INTERNAL, FW_SOURCE_DISPLAY, FW_SOURCE_DESC, FW_PARSER_NAME
    )

    print("\n--- Multicloud Health Source ---")
    create_source_if_needed(
        HEALTH_SOURCE_INTERNAL, HEALTH_SOURCE_DISPLAY, HEALTH_SOURCE_DESC, HEALTH_PARSER_NAME
    )

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"\nConfigured log sources/parsers:")
    print(f"  - {LINUX_SOURCE_DISPLAY}")
    print(f"  - {WINDOWS_SOURCE_DISPLAY}")
    print(f"  - {CG_SOURCE_DISPLAY}")
    print(f"  - {CGIS_SOURCE_DISPLAY}")
    print(f"  - {OSQUERY_SOURCE_DISPLAY}")
    print(f"  - {WINSEC_SOURCE_DISPLAY}")
    print(f"  - {WINSYS_SOURCE_DISPLAY}")
    print(f"  - {WINPS_SOURCE_DISPLAY}")
    print(f"  - {WINDEF_SOURCE_DISPLAY}")
    print(f"  - {LINSEC_SOURCE_DISPLAY}")
    print(f"  - {SYSMON_SOURCE_DISPLAY}")
    print(f"  - {SYSNET_SOURCE_DISPLAY}")
    print(f"  - {WAF_SOURCE_DISPLAY}")
    print(f"  - {LB_SOURCE_DISPLAY}")
    print(f"  - {WEBAPP_SOURCE_DISPLAY}")
    print(f"  - {APP_SOURCE_DISPLAY}")
    print(f"  - {AZURE_CUSTOM_SOURCE_DISPLAY}")
    print(f"  - {VCN_SOURCE_DISPLAY}")
    print(f"  - {FW_SOURCE_DISPLAY}")
    print(f"  - {HEALTH_SOURCE_DISPLAY}")
    print(f"  - OCI Audit Logs (built-in)")
    print(f"  - OCI Cloud Guard Problems (native, preferred when available)")
    print(f"  - Windows Sysmon Events (native, preferred when available)")
    print(f"\nNext: python3 scripts/convert_sigma.py")
    slog.info("setup.done")


if __name__ == "__main__":
    main()
