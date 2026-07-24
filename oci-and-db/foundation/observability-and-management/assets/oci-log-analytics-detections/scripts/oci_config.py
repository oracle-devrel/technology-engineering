"""
Centralized OCI configuration, client factories, and validation for SOC detection scripts.

Config resolution order (highest priority first):
  1. Environment variables (OCI_TENANCY_ID, OCI_COMPARTMENT_ID, etc.)
  2. Profile-scoped environment variables (DEFAULT_LA_NAMESPACE, CAP_LA_NAMESPACE, etc.)
  3. Profile-scoped .env.local values
  4. .env.local values for the selected profile
  5. Empty string (no hardcoded defaults — use require_oci_config() to guard API calls)

Client factories defer `import oci` so offline scripts (convert_sigma.py,
generate_test_logs.py) can import constants without requiring the OCI SDK.
"""

import os
import re
import sys

from query_artifacts import GENERATED_QUERY_ARTIFACT_FILENAMES

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMING_CONFIG_PATH = os.path.join(PROJECT_DIR, 'config', 'streaming_config.json')

# ─── .env.local loader (no python-dotenv dependency) ──────────

def _load_env_file(path):
    """Parse a KEY=VALUE file, ignoring comments and blank lines."""
    values = {}
    if not os.path.exists(path):
        return values
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            values[key] = value
    return values


_env_base = _load_env_file(os.path.join(PROJECT_DIR, '.env.local'))


def _resolve_active_profile_for_overlay():
    """Pick the active profile early to choose the overlay file."""
    return (
        os.environ.get('OCI_PROFILE')
        or os.environ.get('OCI_CONFIG_PROFILE')
        or _env_base.get('OCI_PROFILE')
        or _env_base.get('OCI_CONFIG_PROFILE')
        or 'DEFAULT'
    )


_env_overlay = _load_env_file(
    os.path.join(PROJECT_DIR, f'.env.local.{_resolve_active_profile_for_overlay()}')
)

# Effective env-file dict: per-profile overlay wins over the base file.
_env_local = {**_env_base, **_env_overlay}


def _profile_env_prefix(profile):
    """Return a safe prefix for profile-scoped config keys."""
    return re.sub(r'[^A-Za-z0-9]+', '_', profile).strip('_').upper()


def _profile_env_key(profile, env_key):
    """Return the profile-scoped key name for a config key."""
    prefix = _profile_env_prefix(profile)
    return f"{prefix}_{env_key}" if prefix else env_key


def _first_config_value(values, keys):
    """Return the first non-empty config value from a dict-like object."""
    for key in keys:
        value = values.get(key)
        if value:
            return value
    return ""


def _env_file_profile(env_file=None):
    """Return the profile declared by .env.local, if any."""
    env_file = _env_local if env_file is None else env_file
    return env_file.get("OCI_PROFILE") or env_file.get("OCI_CONFIG_PROFILE") or ""


def _resolve_profile(env=None, env_file=None):
    """Resolve the selected OCI CLI profile without using profile-scoped keys."""
    env = os.environ if env is None else env
    env_file = _env_local if env_file is None else env_file
    return (
        env.get("OCI_PROFILE")
        or env.get("OCI_CONFIG_PROFILE")
        or env_file.get("OCI_PROFILE")
        or env_file.get("OCI_CONFIG_PROFILE")
        or "DEFAULT"
    )


def _cfg(env_key, default, aliases=(), profile_bound=False, profile=None,
         env=None, env_file=None):
    """Resolve config: env var > profile-scoped env/.env.local > .env.local > default.

    Profile-bound values such as compartment, namespace, and log group are not
    inherited from a .env.local file that declares a different OCI profile. This
    prevents commands like ``OCI_PROFILE=DEFAULT ...`` from accidentally reusing
    another tenancy or Log Analytics identifiers from the local defaults.
    """
    env = os.environ if env is None else env
    env_file = _env_local if env_file is None else env_file
    keys = (env_key,) + tuple(aliases)

    value = _first_config_value(env, keys)
    if value:
        return value

    if profile_bound:
        selected_profile = profile or _resolve_profile(env=env, env_file=env_file)
        profile_keys = tuple(_profile_env_key(selected_profile, key) for key in keys)

        value = _first_config_value(env, profile_keys)
        if value:
            return value

        value = _first_config_value(env_file, profile_keys)
        if value:
            return value

        file_profile = _env_file_profile(env_file)
        if file_profile and selected_profile and file_profile != selected_profile:
            return default

    return _first_config_value(env_file, keys) or default


# ─── Configuration constants ──────────────────────────────────

OCI_PROFILE = _cfg("OCI_PROFILE", "") or _cfg("OCI_CONFIG_PROFILE", "DEFAULT")
_TENANCY_ID_EAGER = _cfg(
    "OCI_TENANCY_ID",
    "",
    aliases=("OCI_TENANCY_OCID",),
    profile_bound=True,
    profile=OCI_PROFILE,
)
_COMPARTMENT_ID_EAGER = _cfg(
    "OCI_COMPARTMENT_ID",
    "",
    aliases=("COMP_OBSERVABILITY",),
    profile_bound=True,
    profile=OCI_PROFILE,
)  # MAIN demo-observability (set in .env.local)
OCI_REGION = _cfg("OCI_REGION", "")

# Log Analytics identifiers — honour values set by upstream provisioning (OCI-DEMO)
LOG_GROUP_ID = _cfg(
    "LOG_ANALYTICS_LOG_GROUP_ID",
    "",
    aliases=("LA_LOG_GROUP_ID",),
    profile_bound=True,
    profile=OCI_PROFILE,
)
LA_NAMESPACE = _cfg("LA_NAMESPACE", "", profile_bound=True, profile=OCI_PROFILE)

# Cache for lazy SDK-fallback resolution (PEP 562 __getattr__ below)
_lazy_cache = {}

QUERIES_DIR = os.path.join(PROJECT_DIR, 'queries')
HUNTING_DIR = os.path.join(QUERIES_DIR, 'hunting')
APPS_DIR = os.path.join(QUERIES_DIR, 'apps')
TEST_DATA_DIR = os.path.join(PROJECT_DIR, 'test_data')

LOG_GROUP_NAME = "soc-detection-test-logs"
LOG_GROUP_DESC = "Log group for SOC detection rule test data"

CUSTOM_LOG_SOURCES = [
    "SOC Linux Syslog Logs",
    "SOC Windows Sysmon Logs",
    "SOC Sysmon Network Logs",
    "SOC Cloud Guard Logs",
    "SOC Cloud Guard Instance Security Logs",
    "SOC OSQuery Result Logs",
    "Windows PowerShell Operational Logs",
    "Windows Defender Operational Logs",
    "Azure Log Analytics Custom Logs",
    "SOC Application Logs",
    "SOC VCN Flow Logs",
    "SOC Network Firewall Logs",
]

# Preferred-to-fallback source candidates by detection family.
# Order matters: first match wins for runtime source selection.
SOURCE_CANDIDATE_GROUPS = {
    "oci_audit": [
        "OCI Audit Logs",
    ],
    # SOC source first: native OCI Cloud Guard Problems parser does not extract
    # the ``problemName`` JSON field that detections queries on, so test data
    # must land in SOC Cloud Guard Logs whose parser maps it to ``Problem Name``.
    "cloud_guard": [
        "SOC Cloud Guard Logs",
        "OCI Cloud Guard Problems",
        "OCI Cloud Guard Logs",
    ],
    "cloud_guard_instance_security": [
        "SOC Cloud Guard Instance Security Logs",
        "OCI Cloud Guard Instance Security Logs",
        "SOC OSQuery Result Logs",
    ],
    "osquery_results": [
        "SOC OSQuery Result Logs",
        "SOC Cloud Guard Instance Security Logs",
    ],
    # No exact native equivalent covers all SOC Linux Syslog detection patterns.
    "linux_syslog": [
        "SOC Linux Syslog Logs",
        "Linux Secure Logs",
        "Linux Syslog Logs",
        "Linux Audit Logs",
    ],
    # SOC source first: native sources use XML parsers that can't parse JSON uploads
    "windows_sysmon": [
        "SOC Windows Sysmon Logs",
        "Windows Sysmon Events",
        "Windows Sysmon Operational Logs",
    ],
    "windows_event_security": [
        "Windows Event Security Logs",
        "Windows Security Events",
    ],
    "windows_event_system": [
        "Windows Event System Logs",
    ],
    "windows_powershell_operational": [
        "Windows PowerShell Operational Logs",
    ],
    "windows_defender_operational": [
        "Windows Defender Operational Logs",
    ],
    # SOC source first: native ``Linux Secure Logs`` parser does not extract
    # ``Command Line`` from our JSON, so detection queries that LIKE on
    # argv (crontab -e, sudo -i, etc.) never match. SOC Linux Syslog parser
    # accepts the same JSON shape and exposes the Command Line column.
    "linux_secure": [
        "SOC Linux Syslog Logs",
        "Linux Secure Logs",
    ],
    # SOC source first: native sources use XML parsers that can't parse JSON uploads
    "sysmon_operational": [
        "Windows Sysmon Operational Logs",
        "SOC Windows Sysmon Logs",
        "Windows Sysmon Events",
    ],
    # Network connection events require a parser that maps Event ID 3 fields.
    "sysmon_network": [
        "SOC Sysmon Network Logs",
        "Windows Sysmon Operational Logs",
        "Windows Sysmon Events",
    ],
    "waf_security": [
        "SOC WAF Security Logs",
        "OCI WAF Logs",
    ],
    "lb_access": [
        "SOC Load Balancer Access Logs",
        "OCI Load Balancer Access Logs",
    ],
    "webapp_security": [
        "SOC Web Application Logs",
    ],
    "application_logs": [
        "SOC Application Logs",
    ],
    "genai_gateway": [
        "SOC GenAI Gateway Logs",
    ],
    "azure_log_analytics_custom": [
        "Azure Log Analytics Custom Logs",
        "SOC Application Logs",
    ],
    "vcn_flow": [
        "SOC VCN Flow Logs",
        "OCI VCN Flow Logs",
        "VCN Flow Logs",
    ],
    "network_firewall": [
        "SOC Network Firewall Logs",
        "OCI Network Firewall Logs",
        "Network Firewall Logs",
    ],
    "multicloud_health": [
        "SOC Multicloud Health Logs",
    ],
}

TEST_DATA_FILES = [
    "oci_audit.jsonl",
    "cloud_guard.jsonl",
    "cloud_guard_instance_security.jsonl",
    "linux_syslog.jsonl",
    "windows_sysmon.jsonl",
    "windows_event_security.jsonl",
    "windows_event_system.jsonl",
    "windows_powershell_operational.jsonl",
    "windows_defender_operational.jsonl",
    "linux_secure.jsonl",
    "sysmon_operational.jsonl",
    "sysmon_network.jsonl",
    "waf_security.jsonl",
    "lb_access.jsonl",
    "webapp_security.jsonl",
    "application_logs.jsonl",
    "genai_gateway.jsonl",
    "vcn_flow.jsonl",
    "network_firewall.jsonl",
    "multicloud_health.jsonl",
]

CORE_SOC_STREAMS = [
    "soc-detection-oci-audit",
    "soc-detection-cloud-guard",
    "soc-detection-linux-audit",
    "soc-detection-windows-sysmon",
]


def load_streaming_config(config_path=STREAMING_CONFIG_PATH):
    """Load ``streaming_config.json`` if present, else return an empty dict."""
    import json

    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def get_expected_stream_names(streaming_config=None, config_path=STREAMING_CONFIG_PATH):
    """Return the core SOC streams plus any configured SOC extras.

    The first four streams are the required detection pipeline. Additional
    ``soc-detection-*`` entries in ``streaming_config.json`` are treated as
    extra runtime expectations, for example ``soc-detection-multicloud-health``.
    """
    if streaming_config is None:
        streaming_config = load_streaming_config(config_path)

    configured = [
        name for name in streaming_config
        if name != "_metadata" and name.startswith("soc-detection-")
    ]
    extras = [name for name in configured if name not in CORE_SOC_STREAMS]
    return CORE_SOC_STREAMS + extras


def get_expected_connector_names(streaming_config=None, config_path=STREAMING_CONFIG_PATH):
    """Return the expected SCH connector names for the SOC pipeline."""
    return [f"sch-{stream_name}-to-la" for stream_name in get_expected_stream_names(
        streaming_config=streaming_config,
        config_path=config_path,
    )]


def require_oci_config():
    """Verify that essential OCI identifiers can be resolved before API access.

    Multi-tenancy: TENANCY_ID auto-derives from ``~/.oci/config`` when not
    explicitly set, and COMPARTMENT_ID falls back to the tenancy root.  This
    function only fails if NEITHER source is reachable — typically when the
    selected ``OCI_PROFILE`` does not exist in ``~/.oci/config``.
    """
    missing = []
    if not resolve_tenancy_id():
        missing.append(
            f"TENANCY_ID (set OCI_TENANCY_ID, drop a .env.local.{OCI_PROFILE} "
            f"overlay, or ensure ~/.oci/config has profile [{OCI_PROFILE}])"
        )
    if not resolve_compartment_id():
        missing.append("COMPARTMENT_ID (set OCI_COMPARTMENT_ID or COMP_OBSERVABILITY)")
    if missing:
        print("ERROR: Required OCI configuration is missing:")
        for m in missing:
            print(f"  - {m}")
        print(f"\nActive profile: {OCI_PROFILE}")
        print(f"Set values in .env.local.{OCI_PROFILE} or as environment variables.")
        sys.exit(1)


# ─── Production write guard (emdemo tenancy safety) ──────────
#
# Policy (see ~/.claude/CLAUDE.md "OCI Tenancy Boundaries"): the ``emdemo``
# profile is PRODUCTION and must stay read-only OUTSIDE the LogAnalytics
# compartment subtree. ``cap`` / ``DEFAULT`` (and any other/unknown profile)
# are staging/test with full rights, so the guard is a no-op for them.
#
# This guard is policy-as-code: it raises before any mutating OCI call when the
# active profile is ``emdemo`` and the target compartment is not within the
# configured LogAnalytics subtree, unless an explicit operator override is set.
#
# The allowed LogAnalytics compartment OCID is NEVER hardcoded — it is resolved
# from env / per-profile ``.env.local.emdemo`` overlay keys. Subtree membership
# is approximated by membership in the configured allow-set (the LogAnalytics
# root plus any explicit children) because traversing the real compartment
# hierarchy would require a live OCI call, which this guard deliberately avoids.

EMDEMO_PROFILE_NAME = "emdemo"
PROD_WRITE_OVERRIDE_ENV = "OCI_ALLOW_PROD_WRITE"

# Config keys that may carry the allowed emdemo LogAnalytics compartment OCID.
# With ``profile_bound=True`` for the emdemo profile, the base key also matches
# the ``EMDEMO_`` profile-scoped form (e.g. EMDEMO_LOGANALYTICS_COMPARTMENT_OCID).
_LOGANALYTICS_ROOT_KEY = "LOGANALYTICS_COMPARTMENT_OCID"
_LOGANALYTICS_ROOT_ALIASES = (
    "LOGANALYTICS_COMPARTMENT_ID",
    "LOG_ANALYTICS_COMPARTMENT_OCID",
    "LOG_ANALYTICS_COMPARTMENT_ID",
)
# Optional comma-separated list of additional allowed child compartment OCIDs.
_LOGANALYTICS_CHILDREN_KEY = "LOGANALYTICS_COMPARTMENT_IDS"


class ProdWriteGuardError(RuntimeError):
    """Raised when a mutating call targets emdemo outside the LogAnalytics subtree."""


def _mask_ocid(ocid):
    """Redact an OCID for log/error output (never echo the full value)."""
    if not ocid:
        return "<unset>"
    tail = ocid[-6:] if len(ocid) > 6 else ocid
    return f"...{tail}"


def _prod_write_override_from_env(env=None):
    """Return True when the operator set the explicit prod-write override env."""
    env = os.environ if env is None else env
    return str(env.get(PROD_WRITE_OVERRIDE_ENV, "")).strip() in ("1", "true", "True", "yes")


def resolve_loganalytics_compartment_ids(profile=None, env=None, env_file=None):
    """Resolve the allowed emdemo LogAnalytics compartment OCID(s).

    Returns a set of allowed compartment OCIDs. Never hardcodes a real OCID —
    values come from env vars or the per-profile ``.env.local.emdemo`` overlay.
    Empty set means "not configured" (the guard fails closed for emdemo).
    """
    env = os.environ if env is None else env
    env_file = _env_local if env_file is None else env_file
    selected = profile or _resolve_profile(env=env, env_file=env_file)

    root = _cfg(
        _LOGANALYTICS_ROOT_KEY,
        "",
        aliases=_LOGANALYTICS_ROOT_ALIASES,
        profile_bound=True,
        profile=selected,
        env=env,
        env_file=env_file,
    )
    children = _cfg(
        _LOGANALYTICS_CHILDREN_KEY,
        "",
        profile_bound=True,
        profile=selected,
        env=env,
        env_file=env_file,
    )

    allowed = set()
    if root and root.strip():
        allowed.add(root.strip())
    for item in (children or "").split(","):
        item = item.strip()
        if item:
            allowed.add(item)
    return allowed


def assert_write_allowed(compartment_id, profile=None, *, override=False,
                         env=None, env_file=None):
    """Raise ``ProdWriteGuardError`` for an unsafe write against the emdemo prod tenancy.

    Semantics:
      * For any profile other than ``emdemo`` (``cap``/``DEFAULT``/unknown), this
        is a NO-OP — those tenancies are staging/test with full rights.
      * For ``emdemo`` it ALLOWS the call only when ``compartment_id`` is within
        the configured LogAnalytics allow-set, OR when an explicit operator
        override is in effect (``override=True`` or ``OCI_ALLOW_PROD_WRITE=1``).
      * Fail-closed: when the LogAnalytics allow-set is unconfigured/empty, an
        emdemo write is REFUSED (we cannot prove the target is safe).

    The function performs no live OCI calls and is import-safe.
    """
    env = os.environ if env is None else env
    env_file = _env_local if env_file is None else env_file
    active = (profile or _resolve_profile(env=env, env_file=env_file) or "").strip()

    # Non-production profiles: full rights, nothing to guard.
    if active.lower() != EMDEMO_PROFILE_NAME:
        return

    # Explicit, deliberate operator override (CLI flag → override=True, or env).
    if override or _prod_write_override_from_env(env):
        return

    allowed = resolve_loganalytics_compartment_ids(
        profile=active, env=env, env_file=env_file
    )
    target = (compartment_id or "").strip()

    if allowed and target and target in allowed:
        return

    if not allowed:
        reason = (
            f"the LogAnalytics allow-set is not configured (set "
            f"{_LOGANALYTICS_ROOT_KEY} in .env.local.{EMDEMO_PROFILE_NAME} or "
            f"export {EMDEMO_PROFILE_NAME.upper()}_{_LOGANALYTICS_ROOT_KEY})"
        )
    else:
        reason = (
            f"target compartment {_mask_ocid(target)} is outside the allowed "
            f"LogAnalytics subtree"
        )

    raise ProdWriteGuardError(
        f"REFUSING mutating OCI call: active profile '{active}' is PRODUCTION and "
        f"{reason}. emdemo must stay read-only outside LogAnalytics. "
        f"If this is intentional, re-run with --i-understand-prod "
        f"(or {PROD_WRITE_OVERRIDE_ENV}=1)."
    )


# ─── OCI client factories (deferred import) ──────────────────

def _get_client(client_class, **extra_kwargs):
    """Create OCI SDK client with 4-tier auth fallback.

    1. Resource Principal (OCI_RESOURCE_PRINCIPAL_VERSION set)
    2. Instance Principal (OCI_AUTH_MODE=instance_principal)
    3. OCI config file (~/.oci/config)
    4. Environment variables (OCI_KEY_FILE/OCI_KEY_CONTENT)
    """
    import oci
    client_name = client_class.__name__
    auth_mode = os.environ.get("OCI_AUTH_MODE", "").lower().replace("-", "_")

    # 1. Resource Principal
    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        try:
            signer = oci.auth.signers.get_resource_principals_signer()
            return client_class({}, signer=signer, **extra_kwargs)
        except Exception:
            pass

    # 2. Instance Principal
    if auth_mode in ("instance_principal", "instanceprincipal", "auto"):
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            return client_class({}, signer=signer, **extra_kwargs)
        except Exception:
            pass

    # 3. OCI config file
    try:
        config = get_oci_config()
        return client_class(config, **extra_kwargs)
    except Exception:
        pass

    # 4. Environment variables
    key_file = os.environ.get("OCI_KEY_FILE")
    key_content = os.environ.get("OCI_KEY_CONTENT")
    if key_file or key_content:
        try:
            if key_file:
                with open(os.path.expanduser(key_file)) as f:
                    key_pem = f.read()
            else:
                key_pem = key_content.replace("\\n", "\n")
            config = {
                "user": os.environ["OCI_USER_OCID"],
                "key_content": key_pem,
                "fingerprint": os.environ["OCI_FINGERPRINT"],
                "tenancy": os.environ["OCI_TENANCY_OCID"],
                "region": os.environ.get("OCI_REGION", ""),
                "pass_phrase": os.environ.get("OCI_KEY_PASSPHRASE", ""),
            }
            return client_class(config, **extra_kwargs)
        except Exception:
            pass

    raise RuntimeError(f"No OCI auth method succeeded for {client_name}")


def get_oci_config():
    """Load and return the OCI SDK config dict."""
    import oci
    kwargs = {}
    if OCI_PROFILE:
        kwargs["profile_name"] = OCI_PROFILE
    config = oci.config.from_file(**kwargs)
    if OCI_REGION:
        config["region"] = OCI_REGION
    return config


def resolve_tenancy_id():
    """Return TENANCY_ID, falling back to the OCI SDK config file.

    Used when running with a profile that has no explicit ``OCI_TENANCY_ID``
    in the per-profile env overlay — the OCI CLI config already pins the
    tenancy for that profile, so we trust it.
    """
    if _TENANCY_ID_EAGER:
        return _TENANCY_ID_EAGER
    if "tenancy" in _lazy_cache:
        return _lazy_cache["tenancy"]
    try:
        cfg = get_oci_config()
        val = cfg.get("tenancy", "")
    except Exception:
        val = ""
    _lazy_cache["tenancy"] = val
    return val


def resolve_compartment_id():
    """Return COMPARTMENT_ID, defaulting to the tenancy root when unset."""
    if _COMPARTMENT_ID_EAGER:
        return _COMPARTMENT_ID_EAGER
    if "compartment" in _lazy_cache:
        return _lazy_cache["compartment"]
    val = resolve_tenancy_id()
    _lazy_cache["compartment"] = val
    return val


def __getattr__(name):
    """PEP 562 lazy attribute resolution for the legacy bare constants.

    Many scripts ``from oci_config import COMPARTMENT_ID`` or ``TENANCY_ID``.
    With multi-tenancy, those values may be empty for a profile that has no
    explicit overlay yet. Auto-fall back to the SDK-derived values so callers
    don't need to be rewritten.
    """
    if name == "COMPARTMENT_ID":
        return resolve_compartment_id()
    if name == "TENANCY_ID":
        return resolve_tenancy_id()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_la_client(timeout=None):
    """Return an OCI Log Analytics client."""
    import oci
    kwargs = {"timeout": timeout} if timeout is not None else {}
    return _get_client(oci.log_analytics.LogAnalyticsClient, **kwargs)


def get_dashboard_client(timeout=(10, 180)):
    """Return an OCI Management Dashboard client."""
    import oci
    return _get_client(oci.management_dashboard.DashxApisClient, timeout=timeout)


def get_streaming_admin_client():
    """Return an OCI Streaming Admin client."""
    import oci
    return _get_client(oci.streaming.StreamAdminClient)


def get_sch_client():
    """Return an OCI Service Connector Hub client."""
    import oci
    return _get_client(oci.sch.ServiceConnectorClient)


# ─── Shared utilities ─────────────────────────────────────────

def get_namespace(la_client, quiet=False):
    """Return the Log Analytics namespace.

    Resolution order:
      1. ``LA_NAMESPACE`` from env / per-profile overlay (if set for this profile)
      2. ``list_namespaces`` against the active tenancy (auto-discovery)

    Auto-discovery makes the script tenancy-agnostic: switching ``OCI_PROFILE``
    is enough to ingest into the right namespace, no code changes required.
    """
    if LA_NAMESPACE:
        if quiet:
            return LA_NAMESPACE
        print("  Namespace: resolved from env")
        return LA_NAMESPACE
    tenancy = resolve_tenancy_id()
    if not tenancy:
        print("ERROR: Cannot resolve tenancy. Set OCI_TENANCY_ID or ensure "
              f"~/.oci/config has profile [{OCI_PROFILE}] with a tenancy line.")
        sys.exit(1)
    namespaces = la_client.list_namespaces(compartment_id=tenancy).data
    if not namespaces.items:
        print("ERROR: No Log Analytics namespace found. Is Log Analytics enabled?")
        sys.exit(1)
    ns = namespaces.items[0].namespace_name
    if quiet:
        return ns
    print(f"  Namespace: auto-discovered for {OCI_PROFILE}")
    return ns


def ensure_log_group(la_client, namespace):
    """Find or create the SOC detection test log group.

    Resolution priority:
      1. LOG_GROUP_ID env var — verify it exists via API
      2. Search by LOG_GROUP_NAME in the compartment
      3. Create a new log group
    """
    import oci

    # Priority 1: use LOG_GROUP_ID from env if set
    if LOG_GROUP_ID:
        try:
            lg = la_client.get_log_analytics_log_group(
                namespace_name=namespace,
                log_analytics_log_group_id=LOG_GROUP_ID,
            ).data
            print(f"  Log Group (from env): {lg.display_name} ({lg.id})")
            return lg.id
        except oci.exceptions.ServiceError as e:
            print(f"  WARNING: LOG_GROUP_ID from env not accessible ({e.status}): {LOG_GROUP_ID}")
            print("  Falling back to name-based search...")

    # Priority 2: search by name (use resolved compartment so DEFAULT-tenancy
    # runs without an explicit COMPARTMENT_ID land at the tenancy root).
    compartment_id = resolve_compartment_id()
    if not compartment_id:
        print("ERROR: No COMPARTMENT_ID resolvable for log group search.")
        sys.exit(1)
    existing = la_client.list_log_analytics_log_groups(
        namespace_name=namespace,
        compartment_id=compartment_id,
    ).data.items

    for lg in existing:
        if lg.display_name == LOG_GROUP_NAME:
            print(f"  Log Group exists: {lg.display_name} ({lg.id})")
            if LOG_GROUP_ID and lg.id != LOG_GROUP_ID:
                print(f"  WARNING: Found log group differs from LOG_GROUP_ID env var!")
                print(f"    env:   {LOG_GROUP_ID}")
                print(f"    found: {lg.id}")
            return lg.id

    # Priority 3: create new
    print(f"  Creating Log Group: {LOG_GROUP_NAME}")
    details = oci.log_analytics.models.CreateLogAnalyticsLogGroupDetails(
        display_name=LOG_GROUP_NAME,
        description=LOG_GROUP_DESC,
        compartment_id=compartment_id,
    )
    new_lg = la_client.create_log_analytics_log_group(
        namespace_name=namespace,
        create_log_analytics_log_group_details=details,
    ).data
    print(f"  Created Log Group: {new_lg.id}")
    return new_lg.id


def list_available_log_sources(la_client, namespace, compartment_id=None):
    """Return a set of available Log Analytics source display names."""
    if compartment_id is None:
        compartment_id = resolve_compartment_id()
    sources = set()
    page = None
    while True:
        kwargs = {
            "limit": 1000,
            "is_system": "ALL",
        }
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        if page:
            kwargs["page"] = page

        resp = la_client.list_sources(namespace, **kwargs)
        for src in resp.data.items:
            if src.display_name:
                sources.add(src.display_name)
        page = resp.headers.get("opc-next-page")
        if not page:
            break
    return sources


def resolve_source_from_candidates(available_sources, candidates):
    """Pick the first source that exists from an ordered candidate list."""
    for candidate in candidates or []:
        if candidate in available_sources:
            return candidate
    return None


# ─── Validation functions ─────────────────────────────────────

_OCID_RE = re.compile(
    r'^ocid1\.[a-z]+\.oc[0-9]+\.[a-z0-9-]*\.[a-z0-9]{60}$'
)


def validate_ocid_format():
    """Check that TENANCY_ID, COMPARTMENT_ID, and LOG_GROUP_ID look like valid OCIDs."""
    results = []
    checks = [
        ("TENANCY_ID", resolve_tenancy_id()),
        ("COMPARTMENT_ID", resolve_compartment_id()),
    ]
    if LOG_GROUP_ID:
        checks.append(("LOG_GROUP_ID", LOG_GROUP_ID))
    for name, value in checks:
        if not value:
            results.append((name, False, "not set"))
        elif _OCID_RE.match(value):
            results.append((name, True, value[:40] + "..."))
        else:
            results.append((name, False, f"invalid format: {value[:50]}"))
    return results


def validate_oci_cli_config():
    """Check that OCI auth is available (signer-based or config file)."""
    # Signer-based auth doesn't need ~/.oci/config
    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        return [("OCI Auth", True, "Resource Principal")]

    auth_mode = os.environ.get("OCI_AUTH_MODE", "").lower().replace("-", "_")
    if auth_mode in ("instance_principal", "instanceprincipal"):
        return [("OCI Auth", True, "Instance Principal")]

    # Check for env var auth
    if os.environ.get("OCI_KEY_FILE") or os.environ.get("OCI_KEY_CONTENT"):
        return [("OCI Auth", True, "Environment variables (OCI_KEY_FILE/OCI_KEY_CONTENT)")]

    # Fall back to config file check
    config_path = os.path.expanduser("~/.oci/config")
    if not os.path.exists(config_path):
        return [("~/.oci/config", False, "file not found (set OCI_AUTH_MODE=instance_principal for VM/Docker)")]

    profile_header = f"[{OCI_PROFILE}]"
    with open(config_path, 'r') as f:
        content = f.read()

    if profile_header in content:
        return [("~/.oci/config", True, f"profile [{OCI_PROFILE}] found")]
    return [("~/.oci/config", False, f"profile [{OCI_PROFILE}] not found")]


def validate_namespace():
    """Check that the Log Analytics namespace is discoverable (online)."""
    try:
        la_client = get_la_client()
        tenancy = resolve_tenancy_id()
        if not tenancy:
            return [("LA Namespace", False, "tenancy unresolved")]
        ns = la_client.list_namespaces(compartment_id=tenancy).data
        if ns.items:
            return [("LA Namespace", True, ns.items[0].namespace_name)]
        return [("LA Namespace", False, "no namespace found")]
    except Exception as e:
        return [("LA Namespace", False, str(e)[:100])]


def validate_compartment():
    """Check that the compartment is accessible via the Identity API (online)."""
    try:
        import oci
        identity = _get_client(oci.identity.IdentityClient)
        comp = identity.get_compartment(resolve_compartment_id()).data
        return [("Compartment", True, comp.name)]
    except Exception as e:
        return [("Compartment", False, str(e)[:100])]


def validate_query_files():
    """Check that all query JSON files exist and contain a 'query' field."""
    import json
    results = []
    if not os.path.isdir(QUERIES_DIR):
        return [("queries/", False, "directory not found")]

    json_files = []
    for root, _, files in os.walk(QUERIES_DIR):
        for f in files:
            if f.endswith('.json') and f not in GENERATED_QUERY_ARTIFACT_FILENAMES:
                json_files.append(os.path.join(root, f))

    if not json_files:
        return [("Query files", False, "no .json files found")]

    errors = 0
    for path in json_files:
        try:
            with open(path, 'r') as fh:
                data = json.load(fh)
            if 'query' not in data:
                errors += 1
                results.append((os.path.basename(path), False, "missing 'query' field"))
        except (json.JSONDecodeError, OSError) as e:
            errors += 1
            results.append((os.path.basename(path), False, str(e)[:80]))

    if errors == 0:
        results.insert(0, ("Query files", True, f"{len(json_files)} files OK"))
    else:
        results.insert(0, ("Query files", False, f"{errors}/{len(json_files)} files have errors"))
    return results


def validate_log_sources():
    """Check that at least one candidate source exists per detection family."""
    try:
        la_client = get_la_client()
        tenancy = resolve_tenancy_id()
        ns = la_client.list_namespaces(compartment_id=tenancy).data.items[0].namespace_name
        available = list_available_log_sources(la_client, ns, resolve_compartment_id())
        results = []

        for group_name, candidates in SOURCE_CANDIDATE_GROUPS.items():
            resolved = resolve_source_from_candidates(available, candidates)
            if resolved:
                results.append((group_name, True, f"using '{resolved}'"))
            else:
                results.append((group_name, False, f"none found from {candidates}"))
        return results
    except Exception as e:
        return [("Log Sources", False, str(e)[:100])]


def validate_test_data():
    """Check that the configured NDJSON test data files are present."""
    results = []
    for filename in TEST_DATA_FILES:
        path = os.path.join(TEST_DATA_DIR, filename)
        if os.path.exists(path):
            size = os.path.getsize(path)
            results.append((filename, True, f"{size} bytes"))
        else:
            results.append((filename, False, "not found"))
    return results


def validate_log_group():
    """Check that the target log group is accessible (online)."""
    if not LOG_GROUP_ID:
        return [("Log Group", False, "LOG_ANALYTICS_LOG_GROUP_ID / LA_LOG_GROUP_ID not set")]
    try:
        la_client = get_la_client()
        ns = get_namespace.__wrapped__(la_client) if hasattr(get_namespace, '__wrapped__') else (
            LA_NAMESPACE or la_client.list_namespaces(compartment_id=resolve_tenancy_id()).data.items[0].namespace_name
        )
        lg = la_client.get_log_analytics_log_group(
            namespace_name=ns,
            log_analytics_log_group_id=LOG_GROUP_ID,
        ).data
        return [("Log Group", True, f"{lg.display_name} ({LOG_GROUP_ID[:40]}...)")]
    except Exception as e:
        return [("Log Group", False, f"{LOG_GROUP_ID[:40]}... — {str(e)[:60]}")]


def validate_streams():
    """Check that the expected SOC detection streams are ACTIVE (online)."""
    expected_names = get_expected_stream_names()
    try:
        stream_admin = get_streaming_admin_client()
        compartment_id = resolve_compartment_id()
        results = []
        for name in expected_names:
            streams = stream_admin.list_streams(
                compartment_id=compartment_id, name=name, lifecycle_state="ACTIVE"
            ).data
            if streams:
                results.append((name, True, f"ACTIVE ({streams[0].id[:40]}...)"))
            else:
                results.append((name, False, "not found or not ACTIVE"))
        return results
    except Exception as e:
        return [("Streams", False, str(e)[:100])]


def validate_service_connectors():
    """Check that the expected SCH connectors are ACTIVE (online)."""
    expected_prefixes = get_expected_connector_names()
    try:
        sch = get_sch_client()
        compartment_id = resolve_compartment_id()
        results = []
        for name in expected_prefixes:
            connectors = sch.list_service_connectors(
                compartment_id=compartment_id, display_name=name
            ).data.items
            active = [c for c in connectors if getattr(c, "lifecycle_state", "") == "ACTIVE"]
            if active:
                results.append((name, True, f"ACTIVE ({active[0].id[:40]}...)"))
            else:
                results.append((name, False, "not found or not ACTIVE"))
        return results
    except Exception as e:
        return [("Service Connectors", False, str(e)[:100])]


def validate_streaming_config():
    """Check consistency between streaming_config.json and env vars (offline)."""
    import json
    config_path = os.path.join(PROJECT_DIR, 'config', 'streaming_config.json')
    if not os.path.exists(config_path):
        return [("streaming_config.json", False, "file not found")]

    try:
        with open(config_path) as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return [("streaming_config.json", False, str(e)[:80])]

    results = []
    meta = cfg.get("_metadata", {})

    # Check log group ID consistency
    cfg_lg = meta.get("log_group_id", "")
    if LOG_GROUP_ID and cfg_lg and cfg_lg != LOG_GROUP_ID:
        results.append(("log_group_id", False,
                         f"MISMATCH: config={cfg_lg[-12:]} vs env={LOG_GROUP_ID[-12:]}"))
    elif cfg_lg:
        results.append(("log_group_id", True, f"...{cfg_lg[-12:]}"))
    else:
        results.append(("log_group_id", False, "not set in config"))

    # Check compartment consistency
    cfg_comp = meta.get("compartment_id", "")
    active_comp = resolve_compartment_id()
    if active_comp and cfg_comp and cfg_comp != active_comp:
        results.append(("compartment_id", False,
                         f"MISMATCH: config={cfg_comp[-12:]} vs env={active_comp[-12:]}"))
    elif cfg_comp:
        results.append(("compartment_id", True, f"...{cfg_comp[-12:]}"))

    # Check namespace consistency
    cfg_ns = meta.get("la_namespace", "")
    if LA_NAMESPACE and cfg_ns and cfg_ns != LA_NAMESPACE:
        results.append(("la_namespace", False,
                         f"MISMATCH: config={cfg_ns} vs env={LA_NAMESPACE}"))
    elif cfg_ns:
        results.append(("la_namespace", True, cfg_ns))

    # Check stream entries
    stream_count = sum(1 for k in cfg if k != "_metadata")
    expected_stream_count = len(get_expected_stream_names(cfg))
    results.append(("streams", True if stream_count >= expected_stream_count else False,
                     f"{stream_count} stream(s) configured, expecting {expected_stream_count}"))

    return results


# ─── Validation orchestrator ──────────────────────────────────

_VALIDATORS = {
    'ocid': ('OCID Format', validate_ocid_format),
    'cli': ('OCI CLI Config', validate_oci_cli_config),
    'namespace': ('LA Namespace', validate_namespace),
    'compartment': ('Compartment Access', validate_compartment),
    'query_files': ('Query Files', validate_query_files),
    'log_sources': ('Log Sources', validate_log_sources),
    'test_data': ('Test Data', validate_test_data),
    'log_group': ('Log Group', validate_log_group),
    'streams': ('Streams', validate_streams),
    'service_connectors': ('Service Connectors', validate_service_connectors),
    'streaming_config': ('Streaming Config', validate_streaming_config),
}


def validate_oci_setup(checks=None):
    """Run selected validation checks and print results.

    Args:
        checks: list of check names (keys from _VALIDATORS), or None for all offline checks.

    Returns:
        True if all checks passed, False otherwise.
    """
    if checks is None:
        checks = ['ocid', 'cli']

    all_ok = True
    print("\n" + "=" * 60)
    print("  Pre-flight Validation")
    print("=" * 60)

    for check_name in checks:
        if check_name not in _VALIDATORS:
            print(f"\n  ? Unknown check: {check_name}")
            continue

        label, validator = _VALIDATORS[check_name]
        print(f"\n  [{label}]")
        results = validator()
        for name, ok, detail in results:
            icon = "OK" if ok else "FAIL"
            print(f"    [{icon:4s}] {name}: {detail}")
            if not ok:
                all_ok = False

    print(f"\n{'=' * 60}")
    if all_ok:
        print("  All checks passed.")
    else:
        print("  Some checks FAILED. Fix issues above before proceeding.")
    print(f"{'=' * 60}\n")
    return all_ok
