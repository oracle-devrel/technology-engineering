"""
Consumption utils
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, Any
import oci
from oci.usage_api import UsageapiClient
from oci.usage_api.models import RequestSummarizedUsagesDetails


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


def get_usage_client() -> UsageapiClient:
    """
    Get an OCI Usage API client.
    """
    config = oci.config.from_file()  # ~/.oci/config
    return UsageapiClient(config)


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

    config = oci.config.from_file()  # ~/.oci/config
    usage_client = UsageapiClient(config)

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

    config = oci.config.from_file()
    usage_client = UsageapiClient(config)

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
