"""
Convert Sigma YAML detection rules to OCI Log Analytics Query Language (OCL) JSON.

Supports:
  - Field modifiers: |contains, |startswith, |endswith, |re, |contains|all
  - Wildcard selection references: ``1 of selection*``, ``all of filter*``
  - Complex conditions: sel1 and sel2, sel1 or sel2, not, parenthesized groups
  - Graceful degradation for count()/timeframe conditions
  - Stable output filenames via existing ``sigma_id`` reuse
  - Routing browser APM rules into ``queries/apps/``
  - STIG metadata extraction from tags
  - MITRE ATT&CK technique mapping
  - Integration-ready JSON output for multicloudoperations

Usage:
  python3 scripts/convert_sigma.py                # Convert all rules
  python3 scripts/convert_sigma.py --validate     # Validate generated queries
  python3 scripts/convert_sigma.py --stats        # Print rule statistics
"""

import yaml
import os
import json
import re
import sys
import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from query_artifacts import GENERATED_QUERY_ARTIFACT_FILENAMES  # noqa: E402

CONFIG_PATH = 'config/sigma_oci_mapping.yaml'
RULES_DIR = 'rules'
OUTPUT_DIR = 'queries'
EXCLUDED_QUERY_FILENAMES = GENERATED_QUERY_ARTIFACT_FILENAMES
NON_PRESERVED_GENERATED_FIELDS = {'logsource_fallback', 'requires_aggregation'}

# ─── STIG severity mapping ──────────────────────────────────────

LEVEL_TO_STIG_CAT = {
    'critical': 'CAT I',
    'high': 'CAT I',
    'medium': 'CAT II',
    'low': 'CAT III',
    'informational': 'CAT III',
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, CONFIG_PATH)
        if not os.path.exists(config_path):
            return {}, {}
    else:
        config_path = CONFIG_PATH

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('field_mappings', {}), config.get('logsource_mappings', {})


def _strip_outer_single_quotes(value):
    """Normalize config values that may already include surrounding single quotes."""
    if isinstance(value, str) and len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1]
    return value


# OCI Log Analytics fields that store integer-looking values as STRINGS.
# Sigma rules express these as plain integers (``EventID: 4625``); the converter
# must quote them so the parser doesn't reject the comparison with
# ``Invalid string value for the field 'Event ID': 4625``.
#
# DO NOT include numeric LONG fields (``Source Port``, ``Destination Port``,
# ``Bytes Sent``, etc.) — those need an unquoted integer literal, and quoting
# them produces ``Invalid long value for the field 'Destination Port': '443'``.
_STRING_TYPED_OCI_FIELDS = frozenset({
    "'Event ID'",
    "'Logon Type'",
    "'Response Code'",
    "'Backend Status Code'",
    "'HTTP Status Code'",
    "'Status Code'",
    "'Risk Score'",
})


def _format_eq_value(oci_field, value):
    """Format the right-hand side of a SEARCH ``=`` comparison.

    Quotes integer values destined for known string-typed OCI fields so the
    parser accepts them — Sigma sources express Event IDs, Logon Types, etc.
    as bare integers, but OCI Log Analytics stores them as strings.
    """
    if isinstance(value, str):
        return f"'{_escape_like_value(value)}'"
    if isinstance(value, (int, float)):
        if oci_field in _STRING_TYPED_OCI_FIELDS:
            return f"'{value}'"
        return str(value)
    return f"'{value}'"


def _escape_like_value(value):
    """Escape special characters in string literal values for OCL.

    OCL interprets ``\\r``, ``\\n``, ``\\t`` etc. as escape sequences inside
    strings, and a literal single quote terminates the string. Both must be
    escaped so the generated ``like '...'`` clauses parse correctly:

      * Double backslashes so ``\\r`` stays a literal two-character sequence.
      * Backslash-escape single quotes so embedded ``'`` (e.g. SQL injection
        payloads like ``' OR 1=1``) doesn't close the literal early —
        unescaped quotes leave a bare ``OR 1=1*'`` orphan that the parser
        rejects with ``Unexpected input for SEARCH: =``.
    """
    if isinstance(value, str):
        return value.replace('\\', '\\\\').replace("'", "\\'")
    return value


def _is_pipe_name_field(key_base, oci_field):
    """Return True when the Sigma field maps to a named-pipe field."""
    normalized_key = str(key_base).replace('_', '').replace(' ', '').lower()
    normalized_oci = str(oci_field).strip("'").replace('_', '').replace(' ', '').lower()
    return normalized_key == 'pipename' or normalized_oci == 'pipename'


def _keyword_text_search(value):
    """Map Sigma keyword selections to common OCI raw-message fields."""
    escaped = _escape_like_value(value)
    return f"('Original Log Content' like '*{escaped}*' or msg like '*{escaped}*')"


def _join_clauses(clauses, require_all=False):
    connector = ' and ' if require_all else ' or '
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    return f"({connector.join(clauses)})"


def _modifier_tokens(modifier):
    if not modifier:
        return []
    return [token.strip().lower() for token in str(modifier).split('|') if token.strip()]


def _bool_modifier_value(value):
    if isinstance(value, str):
        return value.strip().lower() not in {'false', '0', 'no'}
    return bool(value)


def slugify_title(title):
    """Create a filesystem-safe JSON filename stem from a rule title."""
    safe_title = title.replace(' ', '_').replace(':', '').lower()
    return re.sub(r'[^a-z0-9_\-]', '', safe_title)


def iter_query_files(output_root):
    """Yield all query JSON files beneath the output root, excluding catalogs."""
    for path in sorted(Path(output_root).rglob('*.json')):
        if path.name in EXCLUDED_QUERY_FILENAMES:
            continue
        yield path


def _load_dashboard_referenced_paths():
    """Return relative ``queries/...`` paths referenced by deploy_dashboard.py.

    These paths are the canonical ones for any sigma_id that has multiple
    generated query files on disk — overwriting them would break dashboard
    deployment, so the converter must keep regenerating into them.
    """
    deploy_path = Path(__file__).resolve().parent / 'deploy_dashboard.py'
    if not deploy_path.exists():
        return set()
    try:
        text = deploy_path.read_text()
    except OSError:
        return set()
    return set(re.findall(r'"query_file"\s*:\s*"([^"]+)"', text))


def load_existing_query_index(output_root):
    """Index existing generated queries by sigma_id for stable path reuse.

    When multiple query files share a ``sigma_id`` (rule renames left orphans),
    prefer the path that ``deploy_dashboard.py`` references. Without this
    preference the converter sometimes picks an alphabetically-earlier orphan
    and the canonical dashboard widget loses its query file on the next run.
    """
    referenced = _load_dashboard_referenced_paths()
    index = {}
    for path in iter_query_files(output_root):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        sigma_id = data.get('sigma_id')
        if not sigma_id:
            continue
        rel = path.relative_to(output_root).as_posix()
        if sigma_id not in index:
            index[sigma_id] = rel
            continue
        # If the existing pick is dashboard-referenced and the new one isn't,
        # keep the existing pick. Otherwise prefer the dashboard-referenced one.
        existing_referenced = index[sigma_id] in referenced
        new_referenced = rel in referenced
        if new_referenced and not existing_referenced:
            index[sigma_id] = rel
    return index


def resolve_output_relative_path(rule_path, result, output_root, rules_root=None, existing_index=None):
    """Resolve the generated output path for a rule relative to the output root.

    Rules under ``rules/web/browser_attacks`` are routed to ``queries/apps``.
    All other rules reuse an existing path when the same ``sigma_id`` is already
    present on disk; otherwise they fall back to a title-derived filename.
    """
    rule_path = Path(rule_path)
    if rules_root is None:
        base_dir = Path(__file__).resolve().parent.parent
        rules_root = base_dir / RULES_DIR
    else:
        rules_root = Path(rules_root)
    rel_rule = rule_path.relative_to(rules_root)

    if len(rel_rule.parts) >= 2 and rel_rule.parts[0] == 'web' and rel_rule.parts[1] == 'browser_attacks':
        return f"apps/{rel_rule.stem}.json"

    sigma_id = result.get('sigma_id')
    if sigma_id and existing_index and sigma_id in existing_index:
        return existing_index[sigma_id]

    return f"{slugify_title(result['title'])}.json"


def _merge_unique(primary, secondary):
    """Return a de-duplicated list preserving the order of both inputs."""
    merged = []
    seen = set()
    for items in (primary or [], secondary or []):
        for item in items:
            if item in seen:
                continue
            merged.append(item)
            seen.add(item)
    return merged


def merge_preserved_fields(result, existing):
    """Preserve curated JSON metadata from an existing generated query file."""
    existing_query = existing.get('query', '')
    if '|' not in result.get('query', '') and '|' in existing_query:
        pipe_idx = existing_query.index('|')
        result['query'] = result['query'] + ' ' + existing_query[pipe_idx:].strip()

    if existing.get('atomic_red_team'):
        result['atomic_red_team'] = existing['atomic_red_team']

    if existing.get('tags'):
        result['tags'] = _merge_unique(result.get('tags', []), existing.get('tags', []))

    if existing.get('falsepositives') and not result.get('falsepositives'):
        result['falsepositives'] = existing['falsepositives']

    existing_mitre = existing.get('mitre_attack', {})
    if existing_mitre:
        result_mitre = result.setdefault('mitre_attack', {"tactics": [], "techniques": []})
        result_mitre['tactics'] = _merge_unique(
            result_mitre.get('tactics', []),
            existing_mitre.get('tactics', []),
        )
        result_mitre['techniques'] = _merge_unique(
            result_mitre.get('techniques', []),
            existing_mitre.get('techniques', []),
        )

    for key, value in existing.items():
        if key in result:
            continue
        if key in {
            'title',
            'description',
            'query',
            'sigma_id',
            'level',
            'logsource',
            'mitre_attack',
            *NON_PRESERVED_GENERATED_FIELDS,
        }:
            continue
        result[key] = value

    return result


def _existing_has_do_not_overwrite(output_path):
    """Read ``do_not_overwrite`` from an on-disk query file, if present.

    Lets curated query files protect themselves even when their Sigma source
    forgot the flag — once a JSON has ``do_not_overwrite: true`` set, the
    converter respects it on every subsequent run.
    """
    if not os.path.exists(output_path):
        return False
    try:
        with open(output_path) as fh:
            return bool(json.load(fh).get('do_not_overwrite'))
    except (OSError, json.JSONDecodeError):
        return False


def should_skip_existing_output(result, output_path):
    """Skip rewriting if either the Sigma rule OR the existing JSON marks the
    target as ``do_not_overwrite``. Reading the flag from disk preserves
    curated demo queries even when the Sigma source omits the opt-out.
    """
    if not os.path.exists(output_path):
        return False
    if bool(result.get('do_not_overwrite')):
        return True
    return _existing_has_do_not_overwrite(output_path)


def normalize_log_source_candidates(raw_value):
    """Convert a mapping value to an ordered list of log source display names."""
    if raw_value is None:
        return []

    if isinstance(raw_value, list):
        items = raw_value
    else:
        items = [raw_value]

    candidates = []
    for item in items:
        if not isinstance(item, str):
            continue
        normalized = _strip_outer_single_quotes(item.strip())
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def build_log_source_filter(candidates):
    """Build an OCL filter for one or more candidate log sources."""
    if not candidates:
        return "'Log Source' = 'OCI Audit Logs'"
    if len(candidates) == 1:
        return f"'Log Source' = '{candidates[0]}'"
    parts = [f"'Log Source' = '{src}'" for src in candidates]
    return f"({' or '.join(parts)})"


def map_field(field_name, field_map):
    return field_map.get(field_name, field_name)


def parse_selection(selection, field_map):
    """Parse a single Sigma selection block into an OCL query fragment."""
    query_parts = []

    if isinstance(selection, (str, int, float)):
        return _keyword_text_search(selection)

    # Selection can be a list of maps (OR of ANDs)
    if isinstance(selection, list):
        list_parts = []
        for item in selection:
            parsed = parse_selection(item, field_map)
            if parsed:
                list_parts.append(f"({parsed})")
        return f"({' or '.join(list_parts)})" if list_parts else ""

    if not isinstance(selection, dict):
        return _keyword_text_search(str(selection))

    for key, value in selection.items():
        # Handle field modifiers (e.g., field|contains, field|endswith, field|contains|all)
        modifier = None
        key_base = key
        if '|' in key:
            parts = key.split('|')
            key_base = parts[0]
            modifier = '|'.join(parts[1:])

        oci_field = map_field(key_base, field_map)
        tokens = _modifier_tokens(modifier)
        require_all = 'all' in tokens
        operator = next((token for token in tokens if token != 'all'), None)

        if operator == 'exists':
            clause = f"{oci_field} like '*'"
            query_parts.append(clause if _bool_modifier_value(value) else f"not ({clause})")
        elif operator in {'gt', 'gte', 'lt', 'lte'}:
            op = {'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<='}[operator]
            values = value if isinstance(value, list) else [value]
            clauses = [f"{oci_field} {op} {_format_eq_value(oci_field, item)}" for item in values]
            query_parts.append(_join_clauses(clauses, require_all))
        elif operator == 'contains':
            values = value if isinstance(value, list) else [value]
            clauses = [f"{oci_field} like '*{_escape_like_value(v)}*'" for v in values]
            query_parts.append(_join_clauses(clauses, require_all))
        elif operator == 'startswith':
            values = value if isinstance(value, list) else [value]
            clauses = [f"{oci_field} like '{_escape_like_value(v)}*'" for v in values]
            query_parts.append(_join_clauses(clauses, require_all))
        elif operator == 'endswith':
            values = value if isinstance(value, list) else [value]
            clauses = [f"{oci_field} like '*{_escape_like_value(v)}'" for v in values]
            query_parts.append(_join_clauses(clauses, require_all))
        elif operator == 're':
            # OCI Log Analytics uses ``matches`` for regex search, not the
            # SQL-style ``REGEX MATCH`` operator emitted by other Sigma
            # backends. See OCL grammar: ``<field> matches '<pattern>'``.
            values = value if isinstance(value, list) else [value]
            clauses = [f"{oci_field} matches '{_escape_like_value(v)}'" for v in values]
            query_parts.append(_join_clauses(clauses, require_all))
        elif _is_pipe_name_field(key_base, oci_field):
            if isinstance(value, list):
                or_parts = [
                    f"{oci_field} like '*{_escape_like_value(v)}*'"
                    if isinstance(v, str)
                    else f"{oci_field} = {v}"
                    for v in value
                ]
                query_parts.append(f"({' or '.join(or_parts)})")
            elif isinstance(value, str):
                query_parts.append(f"{oci_field} like '*{_escape_like_value(value)}*'")
            elif isinstance(value, (int, float)):
                query_parts.append(f"{oci_field} = {value}")
            elif value is None:
                query_parts.append(f"not ({oci_field} like '*')")
        else:
            if isinstance(value, (str, int, float)):
                query_parts.append(f"{oci_field} = {_format_eq_value(oci_field, value)}")
            elif isinstance(value, list):
                clauses = [
                    f"{oci_field} = {_format_eq_value(oci_field, v)}"
                    for v in value
                ]
                query_parts.append(_join_clauses(clauses, require_all))
            elif value is None:
                query_parts.append(f"not ({oci_field} like '*')")

    return " and ".join(query_parts)


def _expand_wildcard_selections(condition_str, detection):
    """Expand ``1 of sel*`` / ``all of filter*`` wildcards in condition strings.

    Returns the condition string with wildcard patterns replaced by explicit
    boolean combinations of matching detection keys.
    """
    detection_keys = [k for k in detection if k != 'condition']
    wildcard_re = re.compile(r'\b(1|all|\d+)\s+of\s+(\w+\*)')

    def _replace(m):
        quantifier = m.group(1)
        pattern = m.group(2)
        matching = [k for k in detection_keys if fnmatch.fnmatch(k, pattern)]
        if not matching:
            return m.group(0)  # leave as-is if nothing matches
        if quantifier == 'all':
            return '(' + ' and '.join(matching) + ')'
        else:
            # "1 of" or any numeric quantifier → OR (true if any match)
            return '(' + ' or '.join(matching) + ')'

    return wildcard_re.sub(_replace, condition_str)


def parse_condition(condition_str, detection, field_map):
    """Parse a Sigma condition string, replacing selection references with OCL.

    Handles patterns like:
      - selection
      - sel1 or sel2
      - sel1 and sel2
      - sel_target and sel_path
      - (sel1 or sel2) and sel3
      - not sel1
      - 1 of selection*
      - all of filter*
    """
    if not isinstance(condition_str, str):
        return ""

    # Expand wildcard selection references before tokenizing
    condition_str = _expand_wildcard_selections(condition_str, detection)

    # Tokenize: split on whitespace but preserve parentheses
    tokens = re.findall(r'\(|\)|[^\s()]+', condition_str)

    result_parts = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        lower = token.lower()
        if lower in ('and', 'or', 'not'):
            result_parts.append(lower)
        elif token in ('(', ')'):
            result_parts.append(token)
        elif token in detection and token != 'condition':
            result_parts.append(f"({parse_selection(detection[token], field_map)})")
        else:
            # Skip leftover quantifier keywords from unexpanded patterns
            if lower in ('1', 'all', 'of') or (lower.isdigit()):
                i += 1
                continue
            result_parts.append(token)
        i += 1

    return " ".join(result_parts)


def extract_stig_tags(tags):
    """Extract STIG IDs, MITRE techniques, and compliance frameworks from tags."""
    stig_ids = []
    mitre_techniques = []
    mitre_tactics = []
    compliance = []

    for tag in (tags or []):
        if tag.startswith('stig.'):
            stig_ids.append(tag[5:])
        elif tag.startswith('compliance.'):
            compliance.append(tag[11:])
        elif tag.startswith('attack.t') and tag[8:9].isdigit():
            mitre_techniques.append(tag[7:].upper())
        elif tag.startswith('attack.'):
            mitre_tactics.append(tag[7:])

    return {
        'stig_ids': stig_ids,
        'mitre_techniques': mitre_techniques,
        'mitre_tactics': mitre_tactics,
        'compliance_frameworks': compliance,
    }


def convert_rule(rule_path, field_map, logsource_map):
    try:
        with open(rule_path, 'r') as f:
            rule = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {rule_path}: {e}")
        return None

    if not rule or 'detection' not in rule:
        return None

    title = rule.get('title', 'Untitled')
    logsource = rule.get('logsource', {})
    product = logsource.get('product', '')
    service = logsource.get('service', '')
    category = logsource.get('category', '')

    raw_source_mapping = (
        logsource_map.get(f"{product}_{category}")
        or logsource_map.get(f"{product}_{service}")
        or logsource_map.get(category)
        or logsource_map.get(product)
    )
    source_candidates = normalize_log_source_candidates(raw_source_mapping)
    logsource_fallback = False
    if not source_candidates:
        source_candidates = ["OCI Audit Logs"]
        logsource_key = f"{product}_{service}" if service else (f"{product}_{category}" if category else product)
        if logsource_key and logsource_key != '_':
            print(f"WARN: No logsource mapping for '{logsource_key}' in {rule_path}, "
                  f"falling back to OCI Audit Logs", file=sys.stderr)
        logsource_fallback = True
    source_filter = build_log_source_filter(source_candidates)

    detection = rule.get('detection', {})
    condition = detection.get('condition', '')

    # Detect aggregation conditions (count(), timeframe)
    requires_aggregation = False
    if 'count(' in str(condition) or rule.get('detection', {}).get('timeframe'):
        requires_aggregation = True
        # Strip aggregation parts — emit only the base filter query
        condition = re.sub(r'\|\s*count\([^)]*\)\s*(by\s+\w+)?\s*(>|<|>=|<=|==|!=)\s*\d+', '', str(condition)).strip()
        if not condition:
            condition = 'selection'

    # Parse condition using the improved tokenizer
    query_body = parse_condition(condition, detection, field_map)

    full_query = source_filter
    if query_body:
        # If query_body is just a selection name that didn't get replaced
        if query_body in detection:
            query_body = parse_selection(detection[query_body], field_map)
        full_query += f" and ({query_body})"

    # Extract STIG and MITRE metadata
    tags = rule.get('tags', [])
    level = rule.get('level', 'medium')
    metadata = extract_stig_tags(tags)

    result = {
        "title": title,
        "description": rule.get('description', ''),
        "query": full_query,
        "sigma_id": rule.get('id', ''),
        "level": level,
        "stig_category": LEVEL_TO_STIG_CAT.get(level, 'CAT II'),
        "tags": tags,
        "mitre_attack": {
            "tactics": metadata['mitre_tactics'],
            "techniques": metadata['mitre_techniques'],
        },
        "logsource": {
            "product": product,
            "service": service,
            "candidates": source_candidates,
        },
    }

    # Add STIG/compliance fields only if present
    if metadata['stig_ids']:
        result['stig_ids'] = metadata['stig_ids']
    if metadata['compliance_frameworks']:
        result['compliance_frameworks'] = metadata['compliance_frameworks']
    if rule.get('falsepositives'):
        result['falsepositives'] = rule['falsepositives']
    if rule.get('do_not_overwrite'):
        result['do_not_overwrite'] = True
    if logsource_fallback:
        result['logsource_fallback'] = True
    if requires_aggregation:
        result['requires_aggregation'] = True

    return result


def print_stats(output_path):
    """Print statistics about generated queries."""
    queries = []
    for path in iter_query_files(output_path):
        with open(path) as fh:
            data = json.load(fh)
        if not data.get('sigma_id'):
            continue
        queries.append(data)

    print(f"\n{'=' * 60}")
    print(f"Detection Rule Statistics")
    print(f"{'=' * 60}")
    print(f"  Total rules: {len(queries)}")

    # By logsource
    sources = {}
    for q in queries:
        src = q.get('logsource', {}).get('product', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    print(f"\n  By platform:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src:20s} {count}")

    # By severity
    levels = {}
    for q in queries:
        lvl = q.get('level', 'unknown')
        levels[lvl] = levels.get(lvl, 0) + 1
    print(f"\n  By severity:")
    for lvl in ['critical', 'high', 'medium', 'low', 'informational']:
        if lvl in levels:
            stig = LEVEL_TO_STIG_CAT.get(lvl, '')
            print(f"    {lvl:15s} ({stig:6s}) {levels[lvl]}")

    # STIG coverage
    stig_rules = [q for q in queries if q.get('stig_ids')]
    print(f"\n  STIG-tagged rules: {len(stig_rules)}")

    # MITRE coverage
    techniques = set()
    tactics = set()
    for q in queries:
        ma = q.get('mitre_attack', {})
        techniques.update(ma.get('techniques', []))
        tactics.update(ma.get('tactics', []))
    print(f"  MITRE ATT&CK techniques: {len(techniques)}")
    print(f"  MITRE ATT&CK tactics: {len(tactics)}")
    for t in sorted(tactics):
        print(f"    - {t}")


def query_syntax_issues(query):
    """Return a list of OCL syntax issues for a single generated query string.

    Extracted from ``validate_queries`` so the per-query checks are unit-testable
    in isolation (e.g. regression tests that regenerate the Windows named-pipe
    rules and assert the emitted LAQL stays parseable). An empty list means the
    query passed every structural check.
    """
    issues = []
    # A query must be anchored on a scoping filter. Log Source is the common
    # case, but cross-source correlation/hunting analytics legitimately anchor
    # on a strong identifier field (Trace ID, Client/Source/Destination IP).
    # Allow any number of leading group-open parens before the anchor so
    # multi-level grouping like ((('Log Source' = ...))) is not flagged.
    anchor = r"'(Log Source|Trace ID|Client IP|Source IP|Destination IP)'"
    if not re.match(rf"^\(*\s*{anchor}\s*(=|in)\s*", query):
        issues.append("missing Log Source prefix")
    # Count parentheses outside of quoted strings, and detect structural
    # double spaces the same way. Several subtleties matter:
    #   * a quote is a string delimiter only when it is NOT escaped. A quote is
    #     escaped iff preceded by an ODD number of backslashes, so "\'" is a
    #     literal quote inside a LIKE pattern but "\\'" (escaped backslash) is a
    #     real delimiter -- tracking only the single previous char gets this
    #     wrong. This keeps literal parens in patterns like '*SLEEP(*' from
    #     desyncing the counter while still closing strings correctly;
    #   * parenthesis depth must never go negative: a closing paren before its
    #     opener (e.g. "(...)) ... (") is malformed even if the final depth
    #     happens to net back to zero;
    #   * a quote left open at end-of-string means the rest of the query was
    #     wrongly treated as quoted, which would mask unbalanced parens or
    #     double spaces -- flag it explicitly;
    #   * spaces inside a LIKE literal (e.g. mimikatz '*SID      :*') are
    #     intentional and must not count as structural double spaces.
    in_quote = False
    paren_depth = 0
    depth_went_negative = False
    backslashes = 0
    prev = ""
    double_space = False
    for ch in query:
        if ch == "'":
            if backslashes % 2 == 0:
                in_quote = not in_quote
            backslashes = 0
        else:
            if not in_quote:
                if ch == '(':
                    paren_depth += 1
                elif ch == ')':
                    paren_depth -= 1
                    if paren_depth < 0:
                        depth_went_negative = True
                elif ch == ' ' and prev == ' ':
                    double_space = True
            backslashes = backslashes + 1 if ch == "\\" else 0
        prev = ch
    if paren_depth != 0 or depth_went_negative:
        issues.append("unbalanced parentheses")
    if in_quote:
        issues.append("unterminated quoted string")
    if double_space:
        issues.append("double spaces")
    return issues


def validate_queries(output_path):
    """Validate OCL syntax of generated queries."""
    errors = 0
    total = 0
    for path in iter_query_files(output_path):
        with open(path) as fh:
            q = json.load(fh)
        query = q.get('query', '')
        total += 1
        issues = query_syntax_issues(query)
        if issues:
            rel_path = path.relative_to(output_path).as_posix()
            print(f"  WARN {rel_path}: {', '.join(issues)}")
            errors += 1
    print(f"\n  Validated {total} queries, {errors} warnings")


def _refresh_catalogs(output_root):
    """Re-emit catalog/manifest/dashboard-inventory JSONs after a sweep.

    The orphan sweep deletes stale query files; the catalogs embed those
    filenames and otherwise drift out of sync. We invoke the existing
    generators in-process so a single ``python3 scripts/convert_sigma.py``
    leaves every downstream artifact internally consistent.

    Failures are NOT masked: if any refresh exits non-zero we print the
    captured stdout/stderr, collect the failure, and after running the
    full set raise ``RuntimeError`` so the caller sees the breakage.
    Silently swallowing returncodes was the previous bug — drift would
    re-appear at the next deploy with no audit trail.
    """
    import subprocess
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    failures = []
    for cmd_args, label in (
        (['scripts/generate_catalog.py'], 'catalog'),
        (['scripts/export_for_multicloud.py', '--manifest-only'], 'manifest'),
        (['scripts/deploy_dashboard.py', '--export-inventory'], 'dashboard inventory'),
    ):
        try:
            result = subprocess.run(
                ['python3', *cmd_args],
                cwd=base,
                check=False,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            failures.append((label, f"spawn error: {exc}"))
            print(f"ERROR: {label} refresh could not start: {exc}", file=sys.stderr)
            continue
        if result.returncode != 0:
            stderr_tail = (result.stderr or '').strip().splitlines()[-10:]
            stdout_tail = (result.stdout or '').strip().splitlines()[-10:]
            # Flush stdout first so the ERROR line can't get re-ordered
            # behind buffered "Refreshed …" output when piped (2>&1 | tail).
            sys.stdout.flush()
            print(
                f"ERROR: {label} refresh exited {result.returncode}",
                file=sys.stderr, flush=True,
            )
            for line in stdout_tail:
                print(f"  stdout: {line}", file=sys.stderr, flush=True)
            for line in stderr_tail:
                print(f"  stderr: {line}", file=sys.stderr, flush=True)
            failures.append((label, f"exit {result.returncode}"))
            continue
        print(f"Refreshed {label}", flush=True)
    if failures:
        raise RuntimeError(
            "Catalog refresh failed: "
            + ", ".join(f"{label}={detail}" for label, detail in failures)
        )


def _sweep_stale_duplicates(output_root, written_by_sigma):
    """Delete query files that share a sigma_id with a freshly generated file.

    When a Sigma rule is renamed or moved, ``resolve_output_relative_path``
    chooses the canonical filename for the new title. The previous filename
    survives on disk as an orphan whose Log Source filter, field map, or
    detection logic may already be stale. Smoke tests treat the orphan as a
    real detection and may even deploy it. This sweep keeps exactly one
    query file per ``sigma_id`` — the one the converter just wrote.

    Files marked ``do_not_overwrite: true`` in their JSON are preserved
    even when they share a ``sigma_id`` with a regenerated file. Several
    curated demo-tuned queries (``mimikatz_command_indicators.json``,
    ``cmd_suspicious_child_process.json``, etc.) are pinned by tests in
    ``scripts/test_query_audit.py`` and must not be swept just because the
    Sigma source got regenerated under a slightly different filename.
    """
    canonical = {sid: os.path.realpath(p) for sid, p in written_by_sigma.items()}
    removed = []
    for path in iter_query_files(output_root):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        sid = data.get('sigma_id')
        if not sid or sid not in canonical:
            continue
        if os.path.realpath(path) == canonical[sid]:
            continue
        if data.get('do_not_overwrite'):
            continue
        try:
            os.remove(path)
            removed.append(str(path))
        except OSError:
            pass
    return removed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert Sigma rules to OCI Log Analytics queries")
    parser.add_argument('--validate', action='store_true', help='Validate generated OCL syntax')
    parser.add_argument('--stats', action='store_true', help='Print rule statistics')
    args = parser.parse_args()

    field_map, logsource_map = load_config()

    # Determine base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, OUTPUT_DIR)
    rules_path = os.path.join(base_dir, RULES_DIR)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    existing_index = load_existing_query_index(output_path)
    # Track every sigma_id → canonical path written this run so we can sweep
    # stale duplicate query files at the end. Prior rule renames left orphan
    # files on disk with outdated Log Source filters or field mappings; without
    # the sweep, those orphans get smoke-tested and re-deployed alongside the
    # current canonical query, which is exactly the kind of drift Codex flagged.
    written_by_sigma = {}
    count = 0
    for root, dirs, files in os.walk(rules_path):
        for file in sorted(files):
            if file.endswith('.yaml') or file.endswith('.yml'):
                rule_path = os.path.join(root, file)
                print(f"Processing {rule_path}...")

                result = convert_rule(rule_path, field_map, logsource_map)

                if result:
                    out_rel_path = resolve_output_relative_path(
                        rule_path=rule_path,
                        result=result,
                        output_root=output_path,
                        rules_root=rules_path,
                        existing_index=existing_index,
                    )
                    out_full_path = os.path.join(output_path, out_rel_path)
                    os.makedirs(os.path.dirname(out_full_path), exist_ok=True)

                    if should_skip_existing_output(result, out_full_path):
                        print(f"Skipped {out_full_path} (do_not_overwrite)")
                        if result.get('sigma_id'):
                            existing_index[result['sigma_id']] = out_rel_path
                        continue

                    # Preserve hand-edited fields from existing file
                    if os.path.exists(out_full_path):
                        try:
                            with open(out_full_path) as ef:
                                existing = json.load(ef)
                            result = merge_preserved_fields(result, existing)
                        except (json.JSONDecodeError, KeyError):
                            pass

                    with open(out_full_path, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Generated {out_full_path}")
                    if result.get('sigma_id'):
                        existing_index[result['sigma_id']] = out_rel_path
                        written_by_sigma[result['sigma_id']] = out_full_path
                    count += 1

    removed = _sweep_stale_duplicates(output_path, written_by_sigma)
    catalog_refresh_error = None
    if removed:
        print(f"Removed {len(removed)} stale duplicate query files:")
        for r in removed:
            print(f"  - {r}")
        # Catalog files (queries/catalog.json, manifest.json,
        # dashboard_inventory.json) embed query filenames. After a sweep
        # they reference deleted files, so refresh them in lock-step.
        # We surface refresh failures non-fatally so the converter still
        # finishes its primary job (regenerating queries), but the caller
        # gets a non-zero exit so CI / the user knows catalogs are stale.
        try:
            _refresh_catalogs(output_path)
        except RuntimeError as exc:
            catalog_refresh_error = exc
            print(f"\nWARNING: {exc}", file=sys.stderr)

    print(f"\nConverted {count} rules")
    if catalog_refresh_error is not None:
        sys.exit(2)

    if args.validate:
        print("\nValidating queries...")
        validate_queries(output_path)

    if args.stats:
        print_stats(output_path)


if __name__ == "__main__":
    main()
