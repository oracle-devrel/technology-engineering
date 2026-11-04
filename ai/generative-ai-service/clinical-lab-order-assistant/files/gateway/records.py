"""Patient record store for the LabSense demo.

A single SQLite table holds one JSON record per patient. This is what lets the
agent remember a returning patient: every placed order and visit summary is
written here and read back at the start of the next consultation.
All data is fictional.
"""
import json
import sqlite3
import threading
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "labsense.db"
SEED_PATH = DATA / "patients.json"
_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.execute("CREATE TABLE IF NOT EXISTS patients (mrn TEXT PRIMARY KEY, record TEXT NOT NULL)")
    return connection


def reset() -> int:
    """Reload the fictional seed data, discarding anything added during a demo."""
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))["patients"]
    with _lock, _connect() as connection:
        connection.execute("DELETE FROM patients")
        connection.executemany("INSERT INTO patients VALUES (?, ?)", [(p["mrn"], json.dumps(p, ensure_ascii=False)) for p in seed])
    return len(seed)


def ensure_seeded() -> None:
    with _lock, _connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    if not count:
        reset()


def _summary(record: dict) -> dict:
    visits = record.get("visits", [])
    return {
        "mrn": record["mrn"], "name": record["name"], "name_ar": record.get("name_ar", record["name"]),
        "sex": record["sex"], "age": record["age"], "conditions": record.get("conditions", []),
        "last_visit": visits[-1]["date"] if visits else None, "visit_count": len(visits),
        "result_count": len(record.get("results", [])), "saved_total": sum(v.get("saved", 0) for v in visits),
    }


def list_patients() -> list[dict]:
    with _lock, _connect() as connection:
        rows = connection.execute("SELECT record FROM patients ORDER BY mrn").fetchall()
    return [_summary(json.loads(row[0])) for row in rows]


def get_patient(mrn: str) -> dict | None:
    with _lock, _connect() as connection:
        row = connection.execute("SELECT record FROM patients WHERE mrn = ?", (mrn,)).fetchone()
    if not row:
        return None
    record = json.loads(row[0])
    record["results"] = sorted(record.get("results", []), key=lambda r: r["date"], reverse=True)
    record["visits"] = sorted(record.get("visits", []), key=lambda v: v["date"])
    record["saved_total"] = sum(v.get("saved", 0) for v in record["visits"])
    record["spent_total"] = sum(v.get("cost", 0) for v in record["visits"])
    return record


def _save(record: dict) -> None:
    with _lock, _connect() as connection:
        connection.execute("UPDATE patients SET record = ? WHERE mrn = ?", (json.dumps(record, ensure_ascii=False), record["mrn"]))


def add_results(mrn: str, results: list[dict]) -> dict:
    record = get_patient(mrn)
    if not record:
        raise KeyError(mrn)
    existing = {(r["code"], r["date"]) for r in record["results"]}
    added = []
    for result in results:
        key = (result["code"], result["date"])
        if key in existing:
            continue
        entry = {"code": result["code"], "value": result.get("value", ""), "date": result["date"], "source": result.get("source", "External laboratory")}
        record["results"].append(entry)
        added.append(entry)
        existing.add(key)
    _save(record)
    return {"mrn": mrn, "added": added, "skipped_duplicates": len(results) - len(added)}


def add_visit(mrn: str, visit: dict) -> dict:
    record = get_patient(mrn)
    if not record:
        raise KeyError(mrn)
    visit = {**visit, "date": visit.get("date") or date.today().isoformat()}
    record["visits"].append(visit)
    # Ordered tests become results on file with a placeholder value until the lab reports.
    for code in visit.get("ordered", []):
        record["results"].append({"code": code, "value": "Pending (ordered today)", "date": visit["date"], "source": "Hospital Laboratory"})
    _save(record)
    return visit
