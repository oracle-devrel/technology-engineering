"""Deterministic redundancy check for a requested lab order.

The model never does the date arithmetic. It receives these decisions and
explains them to the doctor, handling clinical exceptions in conversation.
Validity windows come from data/catalog.json and are illustrative policy.
"""
import json
from datetime import date, timedelta
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "catalog.json"
EXPIRING_WITHIN_DAYS = 14


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["tests"]


def catalog_index() -> dict[str, dict]:
    return {t["code"]: t for t in load_catalog()}


def resolve_code(text: str) -> str | None:
    """Map a free-text test name or alias to a catalog code."""
    needle = text.strip().lower()
    for test in load_catalog():
        if needle in {test["code"].lower(), test["name"].lower(), test["name_ar"]} or needle in [a.lower() for a in test.get("aliases", [])]:
            return test["code"]
    return None


def evaluate(record: dict, codes: list[str], visit_date: date | None = None) -> dict:
    today = visit_date or date.today()
    index = catalog_index()
    decisions, unknown = [], []
    for raw in codes:
        code = raw.upper().strip()
        test = index.get(code) or (index.get(resolve_code(raw) or ""))
        if not test:
            unknown.append(raw)
            continue
        code = test["code"]
        prior = sorted((r for r in record.get("results", []) if r["code"] == code), key=lambda r: r["date"], reverse=True)
        last = prior[0] if prior else None
        decision = {
            "code": code, "name": test["name"], "name_ar": test["name_ar"], "category": test["category"],
            "price_sar": test["price_sar"], "validity_days": test["validity_days"],
            "last_date": last["date"] if last else None, "last_value": last["value"] if last else None,
            "last_source": last["source"] if last else None, "valid_until": None, "days_remaining": None,
        }
        if not last:
            decision.update(status="needed", reason="No prior result on file.")
        elif test["validity_days"] is None:
            decision.update(status="redundant", reason="Result never expires. Already on file.")
        else:
            last_date = date.fromisoformat(last["date"])
            valid_until = last_date + timedelta(days=test["validity_days"])
            remaining = (valid_until - today).days
            decision.update(valid_until=valid_until.isoformat(), days_remaining=remaining)
            if remaining <= 0:
                decision.update(status="needed", reason=f"Last result expired {-remaining} day(s) ago.")
            elif remaining <= EXPIRING_WITHIN_DAYS:
                decision.update(status="expiring", reason=f"Still valid for {remaining} day(s). Repeat only if the patient will not return in time.")
            else:
                decision.update(status="redundant", reason=f"Valid result from {last['date']}, good for {remaining} more day(s).")
        decisions.append(decision)
    full = sum(d["price_sar"] for d in decisions)
    needed = sum(d["price_sar"] for d in decisions if d["status"] == "needed")
    redundant = sum(d["price_sar"] for d in decisions if d["status"] == "redundant")
    expiring = sum(d["price_sar"] for d in decisions if d["status"] == "expiring")
    return {
        "kind": "evaluation", "mrn": record["mrn"], "patient": record["name"], "visit_date": today.isoformat(),
        "decisions": decisions, "unknown": unknown,
        "totals": {"requested_sar": full, "needed_sar": needed, "redundant_sar": redundant, "expiring_sar": expiring,
                   "recommended_sar": needed, "potential_saving_sar": redundant + expiring,
                   "requested_count": len(decisions), "needed_count": sum(d["status"] == "needed" for d in decisions),
                   "redundant_count": sum(d["status"] == "redundant" for d in decisions), "expiring_count": sum(d["status"] == "expiring" for d in decisions)},
        "policy_note": "Validity windows are illustrative hospital policy for this demo, not clinical guidance. The treating physician decides.",
    }
