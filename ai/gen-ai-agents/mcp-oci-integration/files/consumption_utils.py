"""
Consumption utils
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List
import oci
from oci.usage_api import UsageapiClient
from oci.identity import IdentityClient
from oci.usage_api.models import RequestSummarizedUsagesDetails, Filter, Dimension

from utils import get_console_logger

logger = get_console_logger()

MAX_COMPARTMENT_DEPTH = 7


def _make_client(
    config_profile: Optional[str],
) -> Tuple[UsageapiClient, Dict[str, Any]]:
    """
    create a config from file and a client, or use resource principals
    """
    cfg: Optional[Dict[str, Any]] = None
    try:
        if config_profile is not None:
            cfg = oci.config.from_file(profile_name=config_profile)
    except Exception:
        cfg = None
    if cfg is not None:
        return UsageapiClient(cfg, timeout=60.0), cfg

    # this is to support resource principals
    logger.info("Using RESOURCE_PRINCIPAL...")

    signer = oci.auth.signers.get_resource_principals_signer()
    cfg = {"region": signer.region, "tenancy": signer.tenancy_id}

    return UsageapiClient(cfg, signer=signer, timeout=60.0), cfg


def _to_utc_midnight(d: date | datetime | str) -> str:
    """
    Convert date to the expected format 'YYYY-MM-DDT00:00:00Z'.
    """
    if isinstance(d, str):
        d = date.fromisoformat(d)
    if isinstance(d, datetime):
        d = d.date()
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return (
        dt.replace(hour=0, minute=0, second=0, microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _round_or_none(v: Any, ndigits: int = 2) -> Optional[float]:
    return round(float(v), ndigits) if v is not None else None


def _effective_depth(include_sub: bool, max_depth: int) -> int:
    """
    Used by fetch_consumption_by_compartment().
    """
    if not include_sub:
        return 1
    return max(1, min(int(max_depth), MAX_COMPARTMENT_DEPTH))


def _extract_group_value(it, key: str) -> Any:
    """
    Map common group_by keys to item attributes.
    Handles both snakeCase and camelCase variants returned by the SDK.
    Extend this map as needed.
    """
    mapping = {
        "service": ["service", "service_name"],
        "serviceName": ["service", "service_name"],
        "region": ["region"],
        "compartmentName": ["compartment_name"],
        "resourceId": ["resource_id"],
        "skuPartNumber": ["sku_part_number"],
        "skuName": ["sku_name"],
    }
    for attr in mapping.get(key, [key]):
        if hasattr(it, attr):
            return getattr(it, attr)
    # Fallback: try direct access if present
    return getattr(it, key, None)


def usage_summary_by_service_structured(
    start_day: str,
    end_day_inclusive: str,
    query_type: str = "COST",  # "USAGE" | "COST"
) -> Dict[str, Any]:
    """
    Generates a time-aggregated summary: for the whole [start,end] window,
    return exactly one item per unique group_by combination.

    Amount in $ when query_type == "COST".
    """

    # Period: start inclusive, end exclusive (clean UTC midnight)
    start = _to_utc_midnight(start_day)
    end = _to_utc_midnight(date.fromisoformat(end_day_inclusive) + timedelta(days=1))
    group_by = ["service"]

    usage_client, config = _make_client("DEFAULT")

    details = RequestSummarizedUsagesDetails(
        tenant_id=config["tenancy"],
        time_usage_started=start,
        time_usage_ended=end,
        # granularity can be anything when is_aggregate_by_time=False; keep DAILY
        granularity="DAILY",
        query_type=query_type,
        group_by=group_by,
        # crucial: aggregate over the whole window
        is_aggregate_by_time=False,
    )

    resp = usage_client.request_summarized_usages(details)

    # Fold results per group key(s)
    buckets: Dict[tuple, Dict[str, Any]] = {}
    total_amount = 0.0
    total_qty = 0.0

    for it in resp.data.items:
        # Build a composite key from the requested group_by dimensions
        key_values = tuple(_extract_group_value(it, k) for k in group_by)

        amount = getattr(it, "computed_amount", None)
        qty = getattr(it, "computed_quantity", None)

        amount_f = float(amount) if amount is not None else 0.0
        qty_f = float(qty) if qty is not None else 0.0

        if key_values not in buckets:
            buckets[key_values] = {
                "group": {k: v for k, v in zip(group_by, key_values)},
                "amount": 0.0,
                "quantity": 0.0,
            }

        buckets[key_values]["amount"] += amount_f
        buckets[key_values]["quantity"] += qty_f

        total_amount += amount_f
        total_qty += qty_f

    # Normalize items for output
    items = []
    for _, agg in buckets.items():
        item = {}
        # Flatten group fields. If single key, expose a friendly alias too (e.g., "service")
        for k, v in agg["group"].items():
            item[k] = v
        if len(group_by) == 1:
            # keep the old "service" convenience if grouping by service/serviceName
            k0 = group_by[0]
            if k0 in ("service", "serviceName") and "service" not in item:
                item["service"] = item.get(k0)

        item["amount"] = _round_or_none(agg["amount"])
        item["quantity"] = _round_or_none(agg["quantity"])
        items.append(item)

    # Final structured output
    out = {
        "period": {
            "start_inclusive": start,
            "end_exclusive": end,
            "query_type": query_type,
            "aggregated_over_time": True,
        },
        "group_by": group_by,
        "items": items,
        "totals": {
            "amount": _round_or_none(total_amount),
            "quantity": _round_or_none(total_qty),
        },
        "metadata": {
            "region": config.get("region"),
            "opc_request_id": (
                resp.headers.get("opc-request-id") if hasattr(resp, "headers") else None
            ),
        },
    }
    return out


def usage_summary_by_compartment_structured(
    start_day: str,
    end_day_inclusive: str,
    query_type: str = "COST",  # "USAGE" | "COST"
) -> Dict[str, Any]:
    """
    Generates a time-aggregated summary: for the whole [start,end] window,
    return exactly one item per unique group_by combination.

    Amount in $ when query_type == "COST".
    """

    # Period: start inclusive, end exclusive (clean UTC midnight)
    start = _to_utc_midnight(start_day)
    end = _to_utc_midnight(date.fromisoformat(end_day_inclusive) + timedelta(days=1))
    group_by = ["compartmentName"]

    usage_client, config = _make_client("DEFAULT")

    details = RequestSummarizedUsagesDetails(
        tenant_id=config["tenancy"],
        time_usage_started=start,
        time_usage_ended=end,
        # granularity can be anything when is_aggregate_by_time=False; keep DAILY
        granularity="DAILY",
        query_type=query_type,
        group_by=group_by,
        is_aggregate_by_time=False,  # <-- crucial: aggregate over the whole window,
        compartment_depth=1,  # <-- crucial: aggregate over the whole window,
    )

    resp = usage_client.request_summarized_usages(details)

    # Fold results per group key(s)
    buckets: Dict[tuple, Dict[str, Any]] = {}
    total_amount = 0.0
    total_qty = 0.0

    for it in resp.data.items:
        # Build a composite key from the requested group_by dimensions
        key_values = tuple(_extract_group_value(it, k) for k in group_by)

        amount = getattr(it, "computed_amount", None)
        qty = getattr(it, "computed_quantity", None)

        amount_f = float(amount) if amount is not None else 0.0
        qty_f = float(qty) if qty is not None else 0.0

        if key_values not in buckets:
            buckets[key_values] = {
                "group": {k: v for k, v in zip(group_by, key_values)},
                "amount": 0.0,
                "quantity": 0.0,
            }

        buckets[key_values]["amount"] += amount_f
        buckets[key_values]["quantity"] += qty_f

        total_amount += amount_f
        total_qty += qty_f

    # Normalize items for output
    items = []
    for _, agg in buckets.items():
        item = {}
        # Flatten group fields. If single key, expose a friendly alias too (e.g., "service")
        for k, v in agg["group"].items():
            item[k] = v
        if len(group_by) == 1:
            # keep the old "service" convenience if grouping by service/serviceName
            k0 = group_by[0]
            if k0 in ("service", "serviceName") and "service" not in item:
                item["service"] = item.get(k0)

        item["amount"] = _round_or_none(agg["amount"])
        item["quantity"] = _round_or_none(agg["quantity"])
        items.append(item)

    # Final structured output
    out = {
        "period": {
            "start_inclusive": start,
            "end_exclusive": end,
            "query_type": query_type,
            "aggregated_over_time": True,
        },
        "group_by": group_by,
        "items": items,
        "totals": {
            "amount": _round_or_none(total_amount),
            "quantity": _round_or_none(total_qty),
        },
        "metadata": {
            "region": config.get("region"),
            "opc_request_id": (
                resp.headers.get("opc-request-id") if hasattr(resp, "headers") else None
            ),
        },
    }
    return out


#
#
#
def _grouped_query(
    client: UsageapiClient,
    tenant_id: str,
    t_start: str,
    t_end_excl: str,
    depth: int,
    query_type: str,
    flt: Optional[Filter],
) -> List[Any]:
    """
    Used by fetch_consumption_by_compartment().
    """
    details = RequestSummarizedUsagesDetails(
        tenant_id=tenant_id,
        granularity=RequestSummarizedUsagesDetails.GRANULARITY_DAILY,
        query_type=query_type,
        is_aggregate_by_time=True,
        time_usage_started=t_start,
        time_usage_ended=t_end_excl,
        filter=flt,
        group_by=["compartmentPath", "compartmentName", "compartmentId", "service"],
        compartment_depth=depth,
    )
    resp = client.request_summarized_usages(details)
    return getattr(resp.data, "items", []) or []


def _resolve_service(requested: str, available: List[str]) -> Optional[str]:
    """
    Used by fetch_consumption_by_compartment().
    """
    # exact (case-insensitive)
    for s in available:
        if s.casefold() == requested.casefold():
            return s
    # substring (case-insensitive)
    cand = [s for s in available if requested.casefold() in s.casefold()]
    if len(cand) == 1:
        return cand[0]
    # unresolved or ambiguous; we'll handle by client-side filter
    return None


def _discover_services_union(
    client: UsageapiClient, tenant_id: str, t_start: str, t_end_excl: str, depth: int
) -> List[str]:
    """
    Used by fetch_consumption_by_compartment().
    """
    # Union of service labels from COST and USAGE (unfiltered)
    services = set()
    for qt in ("COST", "USAGE"):
        items = _grouped_query(client, tenant_id, t_start, t_end_excl, depth, qt, None)
        for it in items:
            s = getattr(it, "service", None)
            if s:
                services.add(s)
    return sorted(services)


def fetch_consumption_by_compartment(
    day_start: date | datetime | str,
    day_end: date | datetime | str,
    service: str,
    *,
    query_type: str = "COST",
    include_subcompartments: bool = True,
    max_compartment_depth: int = 7,
    config_profile: Optional[str] = "DEFAULT",
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Returns a single dictionary.

    If debug=False (default):
      {
        "rows": [ ... ]  # list of row dicts (COST or USAGE)
      }

    If debug=True:
      {
        "rows": [ ... ],
        "resolved_service": <str or None>,
        "service_candidates": [<up to 50 service labels>],
        "query_used": "COST" | "USAGE",
        "filtered_server_side": True | False,
        "depth": <int>,
        "time_window": {"start": <RFC3339>, "end_exclusive": <RFC3339>},
        "input": {
          "service": <requested service>,
          "query_type_requested": "COST" | "USAGE",
          "include_subcompartments": <bool>,
          "max_compartment_depth": <int>,
          "config_profile": <str or None>,
        }
      }
    """
    if query_type.upper() not in ("COST", "USAGE"):
        raise ValueError("query_type must be 'COST' or 'USAGE'")
    if not 1 <= int(max_compartment_depth) <= 7:
        raise ValueError("max_compartment_depth must be between 1 and 7")

    client, cfg = _make_client(config_profile)
    tenant_id = cfg.get("tenancy")
    if not tenant_id:
        raise RuntimeError("Cannot determine tenancy OCID (check auth).")

    t_start = _to_utc_midnight(day_start)
    t_end_incl = _to_utc_midnight(date.fromisoformat(day_end) + timedelta(days=1))

    # _to_utc_day_end_exclusive(day_end)
    depth = _effective_depth(include_subcompartments, int(max_compartment_depth))

    # 1) Discover union of service labels
    candidates = _discover_services_union(client, tenant_id, t_start, t_end_incl, depth)

    # 2) Try to resolve the requested service against the union
    svc_resolved = _resolve_service(service, candidates)

    def _transform(items, qt):
        rows: List[Dict[str, Any]] = []
        for it in items:
            row = {
                # "compartment_id": getattr(it, "compartment_id", None),
                "compartment_path": getattr(it, "compartment_path", None),
                "compartment_name": getattr(it, "compartment_name", None),
                "service": getattr(it, "service", None),
            }
            if qt == "COST":
                row.update(
                    {
                        "computed_amount": round(
                            float(getattr(it, "computed_amount", 0.0) or 0.0), 2
                        ),
                        "currency": getattr(it, "currency", None),
                    }
                )
            else:
                row.update(
                    {
                        "computed_quantity": float(
                            getattr(it, "computed_quantity", 0.0) or 0.0
                        ),
                        "unit": getattr(it, "unit", None),
                    }
                )
            rows.append(row)
        key = "computed_amount" if qt == "COST" else "computed_quantity"
        rows.sort(key=lambda r: r.get(key, 0.0) or 0.0, reverse=True)
        return rows

    qt = query_type.upper()

    # 3) Try server-side filter if we have a unique resolution
    if svc_resolved:
        flt = Filter(
            operator="AND", dimensions=[Dimension(key="service", value=svc_resolved)]
        )
        items = _grouped_query(client, tenant_id, t_start, t_end_incl, depth, qt, flt)
        rows = _transform(items, qt)
        if not rows:
            # Try the other query type (COST↔USAGE) with the same filter
            alt = "USAGE" if qt == "COST" else "COST"
            items_alt = _grouped_query(
                client, tenant_id, t_start, t_end_incl, depth, alt, flt
            )
            rows_alt = _transform(items_alt, alt)
            if rows_alt:
                result = {"rows": rows_alt}
                if debug:
                    result.update(
                        {
                            "resolved_service": svc_resolved,
                            "service_candidates": candidates[:50],
                            "query_used": alt,
                            "filtered_server_side": True,
                            "depth": depth,
                            "time_window": {
                                "start": t_start,
                                "end_exclusive": t_end_incl,
                            },
                            "input": {
                                "service": service,
                                "query_type_requested": qt,
                                "include_subcompartments": include_subcompartments,
                                "max_compartment_depth": max_compartment_depth,
                                "config_profile": config_profile,
                            },
                        }
                    )
                return result
        else:
            result = {"rows": rows}
            if debug:
                result.update(
                    {
                        "resolved_service": svc_resolved,
                        "service_candidates": candidates[:50],
                        "query_used": qt,
                        "filtered_server_side": True,
                        "depth": depth,
                        "time_window": {"start": t_start, "end_exclusive": t_end_incl},
                        "input": {
                            "service": service,
                            "query_type_requested": qt,
                            "include_subcompartments": include_subcompartments,
                            "max_compartment_depth": max_compartment_depth,
                            "config_profile": config_profile,
                        },
                    }
                )
            return result

    # 4) Fallback: fetch unfiltered and filter client-side (exact or substring)
    items_all = _grouped_query(client, tenant_id, t_start, t_end_incl, depth, qt, None)
    rows_all = _transform(items_all, qt)

    exact = [
        r
        for r in rows_all
        if r.get("service", "").casefold() == (svc_resolved or service).casefold()
    ]
    subset = exact or [
        r
        for r in rows_all
        if (svc_resolved or service).casefold() in r.get("service", "").casefold()
    ]

    if subset:
        result = {"rows": subset}
        if debug:
            result.update(
                {
                    "resolved_service": svc_resolved,
                    "service_candidates": candidates[:50],
                    "query_used": qt,
                    "filtered_server_side": False,
                    "depth": depth,
                    "time_window": {"start": t_start, "end_exclusive": t_end_incl},
                    "input": {
                        "service": service,
                        "query_type_requested": qt,
                        "include_subcompartments": include_subcompartments,
                        "max_compartment_depth": max_compartment_depth,
                        "config_profile": config_profile,
                    },
                }
            )
        return result

    # Try the other query type entirely
    alt = "USAGE" if qt == "COST" else "COST"
    items_all_alt = _grouped_query(
        client, tenant_id, t_start, t_end_incl, depth, alt, None
    )
    rows_all_alt = _transform(items_all_alt, alt)

    exact_alt = [
        r
        for r in rows_all_alt
        if r.get("service", "").casefold() == (svc_resolved or service).casefold()
    ]
    subset_alt = exact_alt or [
        r
        for r in rows_all_alt
        if (svc_resolved or service).casefold() in r.get("service", "").casefold()
    ]

    result = {"rows": subset_alt}
    if debug:
        result.update(
            {
                "resolved_service": svc_resolved,
                "service_candidates": candidates[:50],
                "query_used": alt,
                "filtered_server_side": False,
                "depth": depth,
                "time_window": {"start": t_start, "end_exclusive": t_end_incl},
                "input": {
                    "service": service,
                    "query_type_requested": qt,
                    "include_subcompartments": include_subcompartments,
                    "max_compartment_depth": max_compartment_depth,
                    "config_profile": config_profile,
                },
            }
        )
    return result


def usage_summary_by_service_for_compartment(
    start_day: str | date,
    end_day_inclusive: str | date,
    compartment: str,  # OCID like 'ocid1.compartment...' OR exact name
    *,
    query_type: str = "COST",  # "COST" or "USAGE"
    include_subcompartments: bool = True,
    max_compartment_depth: int = 7,
    config_profile: Optional[str] = "DEFAULT",
) -> Dict[str, Any]:
    """
    Return a time-aggregated breakdown by service for the given compartment.
    - If `compartment` is an OCID, it is used directly.
    - If `compartment` is a name, it is resolved to OCID via IdentityClient
      (exact name match; includes root tenancy name).
    """
    qt = query_type.upper()
    if qt not in ("COST", "USAGE"):
        raise ValueError("query_type must be 'COST' or 'USAGE'")
    if not 1 <= int(max_compartment_depth) <= 7:
        raise ValueError("max_compartment_depth must be between 1 and 7")

    # Time window (end exclusive as required by the Usage API)
    start = _to_utc_midnight(start_day)
    end_excl = _to_utc_midnight(
        date.fromisoformat(str(end_day_inclusive)) + timedelta(days=1)
    )
    depth = _effective_depth(include_subcompartments, int(max_compartment_depth))

    # Usage API client and cfg (your existing helper)
    usage_client, cfg = _make_client(config_profile)
    tenancy_id = cfg.get("tenancy")
    if not tenancy_id:
        raise RuntimeError("Cannot determine tenancy OCID (check auth).")

    # Resolve compartment -> OCID (inline; no extra helpers)
    if compartment.startswith("ocid1.compartment."):
        compartment_id = compartment
    else:
        # Build IdentityClient consistent with auth used by _make_client
        if "user" in cfg:  # config-file auth
            id_client = IdentityClient(cfg)
        else:  # Resource Principals
            rp_signer = oci.auth.signers.get_resource_principals_signer()
            id_client = IdentityClient(
                {"region": cfg["region"], "tenancy": tenancy_id}, signer=rp_signer
            )

        # Match root tenancy name
        tenancy = id_client.get_tenancy(tenancy_id).data
        if tenancy.name == compartment:
            compartment_id = tenancy_id
        else:
            # Traverse subtree and find exact name match
            comps = oci.pagination.list_call_get_all_results(
                id_client.list_compartments,
                tenancy_id,  # required positional parent compartment_id
                access_level="ACCESSIBLE",
                compartment_id_in_subtree=True,
            ).data
            exact = [c for c in comps if c.name == compartment]
            if len(exact) == 1:
                compartment_id = exact[0].id
            elif len(exact) > 1:
                raise ValueError(
                    f"Multiple compartments named '{compartment}'. Use OCID."
                )
            else:
                raise ValueError(
                    f"Compartment '{compartment}' not found among accessible compartments."
                )

    # Server-side filter by compartment and group by service
    flt = Filter(
        operator="AND",
        dimensions=[Dimension(key="compartmentId", value=compartment_id)],
    )
    details = RequestSummarizedUsagesDetails(
        tenant_id=tenancy_id,
        time_usage_started=start,
        time_usage_ended=end_excl,
        granularity=RequestSummarizedUsagesDetails.GRANULARITY_DAILY,
        query_type=qt,
        group_by=["service"],
        is_aggregate_by_time=False,  # aggregate across the whole period
        filter=flt,
        compartment_depth=depth,
    )

    resp = usage_client.request_summarized_usages(details)
    items = getattr(resp.data, "items", []) or []

    # Fold per service
    buckets: Dict[str, Dict[str, Any]] = {}
    total_amount = 0.0
    total_qty = 0.0
    currency_seen = None
    unit_seen = None

    for it in items:
        svc = _extract_group_value(it, "service") or "UNKNOWN"
        if svc not in buckets:
            buckets[svc] = {"service": svc, "amount": 0.0, "quantity": 0.0}

        if qt == "COST":
            val = float(getattr(it, "computed_amount", 0.0) or 0.0)
            buckets[svc]["amount"] += val
            total_amount += val
            currency_seen = currency_seen or getattr(it, "currency", None)
        else:
            val = float(getattr(it, "computed_quantity", 0.0) or 0.0)
            buckets[svc]["quantity"] += val
            total_qty += val
            unit_seen = unit_seen or getattr(it, "unit", None)

    # Normalize + share %
    rows: List[Dict[str, Any]] = []
    denom = total_amount if qt == "COST" else total_qty
    for svc, agg in buckets.items():
        base = agg["amount"] if qt == "COST" else agg["quantity"]
        rows.append(
            {
                "service": svc,
                "amount": _round_or_none(agg["amount"]) if qt == "COST" else None,
                "quantity": _round_or_none(agg["quantity"]) if qt == "USAGE" else None,
                "currency": currency_seen if qt == "COST" else None,
                "unit": unit_seen if qt == "USAGE" else None,
                "share_pct": _round_or_none((base / denom * 100.0) if denom else 0.0),
            }
        )

    # Sort by primary metric
    key = "amount" if qt == "COST" else "quantity"
    rows.sort(key=lambda r: (r.get(key) or 0.0), reverse=True)

    return {
        "period": {
            "start_inclusive": start,
            "end_exclusive": end_excl,
            "query_type": qt,
            "aggregated_over_time": True,
        },
        "scope": {
            "compartment_input": compartment,
            "resolved_compartment_id": compartment_id,
            "include_subcompartments": include_subcompartments,
            "depth": depth,
        },
        "group_by": ["service"],
        "items": rows,
        "totals": {
            "amount": _round_or_none(total_amount) if qt == "COST" else None,
            "quantity": _round_or_none(total_qty) if qt == "USAGE" else None,
        },
        "metadata": {
            "region": cfg.get("region"),
            "opc_request_id": (
                resp.headers.get("opc-request-id") if hasattr(resp, "headers") else None
            ),
        },
    }
