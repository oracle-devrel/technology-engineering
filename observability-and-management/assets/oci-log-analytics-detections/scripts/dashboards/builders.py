"""Widget / layout / saved-search builders (behavior-preserving extract).

Leaf helpers used by deploy_dashboard's inventory + dashboard-JSON orchestration.
``resolve_widget_layout`` itself stays in deploy_dashboard.py per the 12-column
layout contract; everything it depends on lives here.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oci_config import COMPARTMENT_ID, QUERIES_DIR
from query_artifacts import is_saved_search_query_file


SUPPORTED_VISUALIZATION_TYPES = {
    "bar",
    "cluster",
    "distinct",
    "hbar",
    "issues",
    "line",
    "link",
    "map",
    "pie",
    "records",
    "records_histogram",
    "summary_table",
    "sunburst",
    "table",
    "table_histogram",
    "tile",
    "treemap",
}


ADVANCED_VISUALIZATION_TYPES = {
    "bar",
    "hbar",
    "line",
    "link",
    "map",
    "pie",
    "summary_table",
    "sunburst",
    "tile",
    "treemap",
}


FIELD_REFERENCE_RE = re.compile(r"'([^']+)'")


FIELD_OPERATOR_RE = re.compile(r"\s*(?:=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b|\bin\b|\bnot\s+in\b|\bis\b)", re.IGNORECASE)


DEFAULT_DASHBOARD_TIME_PERIOD = "l21d"


DASHBOARD_GRID_COLUMNS = 12


VISUALIZATION_LAYOUT_DEFAULTS = {
    "bar": {"width": 6, "height": 5},
    "cluster": {"width": 12, "height": 6},
    "distinct": {"width": 3, "height": 3},
    "hbar": {"width": 6, "height": 5},
    "issues": {"width": 12, "height": 6},
    "line": {"width": 6, "height": 5},
    "link": {"width": 12, "height": 6},
    "map": {"width": 12, "height": 6},
    "pie": {"width": 6, "height": 5},
    "records": {"width": 12, "height": 6},
    "records_histogram": {"width": 12, "height": 6},
    "summary_table": {"width": 12, "height": 5},
    "sunburst": {"width": 6, "height": 6},
    "table": {"width": 12, "height": 5},
    "table_histogram": {"width": 12, "height": 6},
    "tile": {"width": 3, "height": 3},
    "treemap": {"width": 6, "height": 6},
}


def _iter_quoted_values(text):
    in_quote = False
    escaped = False
    start = 0
    value = []
    for index, char in enumerate(text):
        if escaped:
            value.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            escaped = True
            value.append(char)
            continue
        if char == "'":
            if in_quote:
                yield "".join(value), start, index + 1
                in_quote = False
                value = []
            else:
                in_quote = True
                start = index
                value = []
            continue
        if in_quote:
            value.append(char)


def load_query_info(query_file, queries_dir=QUERIES_DIR):
    """Load and validate one query JSON payload referenced by a dashboard widget."""
    query_path = os.path.join(queries_dir, query_file)
    if not os.path.exists(query_path):
        raise FileNotFoundError(f"missing query file: {query_file}")
    if not is_saved_search_query_file(query_path):
        raise ValueError(f"{query_file}: generated support artifact is not a saved-search query file")

    with open(query_path, "r") as f:
        query_info = json.load(f)

    if not isinstance(query_info, dict):
        raise ValueError(f"{query_file}: query payload must be an object")
    if not query_info.get("title"):
        raise ValueError(f"{query_file}: missing title")
    if not query_info.get("query"):
        raise ValueError(f"{query_file}: missing query")

    return query_info


def _resolve_ask_ai_prompts(widget, query_info):
    dashboard_meta = query_info.get("dashboard", {}) if isinstance(query_info, dict) else {}
    return widget.get("ask_ai_prompts", dashboard_meta.get("ask_ai_prompts", []))


def _quote_context_indicates_field(query, start, end):
    after = query[end:]
    before = query[:start]
    if FIELD_OPERATOR_RE.match(after):
        return True
    return bool(re.search(r"\b(?:distinctcount|unique|count|sum|max|min|avg|average)\s*\($", before[-32:].lower()))


def extract_dashboard_query_fields(query):
    fields = []
    for value, start, end in _iter_quoted_values(query):
        if value not in fields and _quote_context_indicates_field(query, start, end):
            fields.append(value)
    for by_match in re.finditer(
        r"\|\s*(?:stats|timestats|eventstats|link)[^|]*\bby\b(?P<clause>[^|]+)",
        query,
        flags=re.IGNORECASE,
    ):
        for value, _start, _end in _iter_quoted_values(by_match.group("clause")):
            if value not in fields:
                fields.append(value)
    for fields_match in re.finditer(r"\|\s*fields\s+(?P<clause>[^|]+)", query, flags=re.IGNORECASE):
        for value, _start, _end in _iter_quoted_values(fields_match.group("clause")):
            if value not in fields:
                fields.append(value)
    return fields


def build_widget_drilldowns(query_info):
    """Return lightweight field-pivot metadata for downstream UIs."""
    fields = [
        field for field in extract_dashboard_query_fields(query_info.get("query", ""))
        if field not in {"Log Source", "Count"}
    ]
    return [
        {
            "type": "log_explorer_field_pivot",
            "field": field,
            "label": f"Pivot by {field}",
        }
        for field in fields[:6]
    ]


def score_dashboard_widget_quality(ui_config, layout):
    """Additive dashboard-quality metadata; live row health is filled by CAP checks."""
    checks = {
        "no_overlap": True,
        "supported_visualization": ui_config["visualizationType"] in SUPPORTED_VISUALIZATION_TYPES,
        "widget_returns_rows_in_cap": "not_run",
        "field_contract_coverage": "not_evaluated",
        "visualization_task_fit": "not_scored",
    }
    score = 100
    if not checks["supported_visualization"]:
        score -= 40
    if layout["width"] > DASHBOARD_GRID_COLUMNS or layout["width"] < 1:
        score -= 20
    if layout["height"] < 1:
        score -= 20
    return {
        "score": max(score, 0),
        "checks": checks,
    }


def iter_inventory_widgets(inventory):
    """Yield all widget inventory records."""
    for dashboard in inventory.get("dashboards", []):
        for widget in dashboard.get("widgets", []):
            yield widget


def build_scope_filters(compartment_id):
    """Build OCI LA scope filters that scope queries to the correct compartment."""
    return {
        "LogGroup": {
            "flags": {"IncludeSubCompartments": True},
            "type": "LogGroup",
            "values": [{"label": "root", "value": compartment_id}],
        },
        "Entity": {
            "flags": {"IncludeDependents": True, "ScopeCompartmentId": compartment_id},
            "type": "Entity",
            "values": [],
        },
        "LogSet": {"flags": {}, "type": "LogSet", "values": []},
        "filters": [
            {"flags": {"IncludeSubCompartments": True}, "type": "LogGroup",
             "values": [{"label": "root", "value": compartment_id}]},
            {"flags": {"IncludeDependents": True, "ScopeCompartmentId": compartment_id},
             "type": "Entity", "values": []},
            {"flags": {}, "type": "LogSet", "values": []},
        ],
        "isGlobal": False,
    }


def resolve_widget_ui_config(widget, query_info):
    """Resolve visualization and investigation metadata for a widget.

    Query-local dashboard metadata is the default. Explicit widget-level
    overrides win if they are provided in ``DASHBOARDS``.
    """
    dashboard_meta = query_info.get("dashboard", {}) if isinstance(query_info, dict) else {}

    visualization_type = widget.get(
        "visualization_type",
        dashboard_meta.get("visualizationType", "table"),
    )
    if visualization_type not in SUPPORTED_VISUALIZATION_TYPES:
        raise ValueError(f"unsupported visualization type: {visualization_type}")

    visualization_options = dashboard_meta.get("visualizationOptions", {}).copy()
    visualization_options.update(widget.get("visualization_options", {}))

    ask_ai_prompts = widget.get("ask_ai_prompts", dashboard_meta.get("ask_ai_prompts", []))
    if ask_ai_prompts and not isinstance(ask_ai_prompts, list):
        raise ValueError("ask_ai_prompts must be a list of strings")

    return {
        "enableWidgetInApp": True,
        "queryString": query_info["query"],
        "scopeFilters": build_scope_filters(COMPARTMENT_ID),
        "showTitle": widget.get("show_title", dashboard_meta.get("showTitle", True)),
        "timeSelection": widget.get(
            "time_selection",
            dashboard_meta.get("timeSelection", {"timePeriod": DEFAULT_DASHBOARD_TIME_PERIOD}),
        ),
        "visualizationOptions": visualization_options,
        "visualizationType": visualization_type,
        "vizType": "lxSavedSearchWidgetType",
    }


def _coerce_layout_dimension(value, fallback, lower_bound, upper_bound=None):
    """Normalize widget layout dimensions from query/widget metadata."""
    try:
        dimension = int(value)
    except (TypeError, ValueError):
        dimension = fallback
    dimension = max(lower_bound, dimension)
    if upper_bound is not None:
        dimension = min(upper_bound, dimension)
    return dimension


def build_saved_search_json(search_id, title, query, description="", tags=None, ui_config=None):
    """Build a saved search JSON definition for embedding in a dashboard import.

    The import_dashboard API requires saved searches to be embedded in the
    dashboard JSON. Tiles reference them by their 'id' field (not OCID).
    """
    if ui_config is None:
        ui_config = {
            "enableWidgetInApp": True,
            "queryString": query,
            "scopeFilters": build_scope_filters(COMPARTMENT_ID),
            "showTitle": True,
            "timeSelection": {"timePeriod": DEFAULT_DASHBOARD_TIME_PERIOD},
            "visualizationOptions": {},
            "visualizationType": "table",
            "vizType": "lxSavedSearchWidgetType",
        }

    return {
        "id": search_id,
        "displayName": title,
        "providerId": "log-analytics",
        "providerName": "Log Analytics",
        "providerVersion": "3.0.0",
        "compartmentId": COMPARTMENT_ID,
        "isOobSavedSearch": False,
        "description": description,
        "nls": {},
        "type": "SEARCH_SHOW_IN_DASHBOARD",
        "uiConfig": ui_config,
        "dataConfig": [],
        "screenImage": " ",
        "metadataVersion": "2.0",
        "widgetTemplate": "visualizations/chartWidgetTemplate.html",
        "widgetVM": "jet-modules/dashboards/widgets/lxSavedSearchWidget",
        "freeformTags": tags or {},
        "parametersConfig": [],
    }


