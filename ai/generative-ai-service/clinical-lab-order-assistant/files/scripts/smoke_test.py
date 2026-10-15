"""End-to-end checks against the running web app and the dedicated model.

Usage: uv run python scripts/smoke_test.py   (requires scripts/serve.py or the dev servers to be up)
"""
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:3000"
ROOT = Path(__file__).resolve().parents[1]
client = httpx.Client(timeout=600)


def ask(label, prompt, expected_tools, mrn, document_ids=None, history=None):
    start = time.monotonic(); events = []; tools = []; text = ""; errors = []
    messages = list(history or []) + [{"id": uuid.uuid4().hex, "role": "user", "parts": [{"type": "text", "text": prompt}]}]
    body = {"messages": messages, "mrn": mrn, "documentIds": document_ids or []}
    with client.stream("POST", BASE + "/api/chat", json=body) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:]); events.append(event)
            if event.get("type") == "text-delta": text += event.get("delta", "")
            if event.get("type") == "tool-input-available": tools.append(event.get("toolName"))
            if event.get("type") in ("error", "tool-output-error"): errors.append(event)
    outputs = [e for e in events if e.get("type") == "tool-output-available"]
    result = {"label": label, "seconds": round(time.monotonic() - start, 1), "tools": tools, "text": text, "errors": errors}
    print(json.dumps(result, ensure_ascii=False)[:900], flush=True)
    assert not errors, errors
    for tool in expected_tools:
        assert tool in tools, (label, tools)
    assert text.strip(), "Missing final assistant response"
    (ROOT / f"data/smoke-{label}.json").write_text(json.dumps({**result, "outputs": outputs}, ensure_ascii=False, indent=2))
    # Reconstruct a minimal assistant turn so the next call has history.
    assistant = {"id": uuid.uuid4().hex, "role": "assistant", "parts": [{"type": "text", "text": text}]}
    return messages + [assistant], outputs


client.post(BASE + "/api/reset").raise_for_status()
health = client.get(BASE + "/api/health").json(); print("health", health); assert health["gateway"] == "ready"

history, outputs = ask("evaluate", "Fatimah is back with dizziness on standing and tiredness. Order CBC, metabolic panel, lipid panel, HbA1c, TSH, vitamin D and urinalysis.", ["getPatientRecord", "evaluateOrder"], "PT-100234")
evaluation = next(o["output"] for o in outputs if o["output"].get("kind") == "evaluation")
statuses = {d["code"]: d["status"] for d in evaluation["decisions"]}
print("statuses", statuses)
assert statuses["CBC"] == "redundant" and statuses["TSH"] == "needed" and statuses["VITD"] == "needed", statuses

history, outputs = ask("place", "Confirm the order as recommended and summarise the visit.", ["placeOrder"], "PT-100234", history=history)
receipt = next(o["output"] for o in outputs if o["output"].get("kind") == "visit")
print("saved", receipt["visit"]["saved"], "lifetime", receipt["saved_total_sar"])
assert receipt["visit"]["saved"] > 0

if "--full" in sys.argv:
    report = ROOT / "web/public/samples/al-noor-lab-report.png"
    upload = client.post(BASE + "/api/documents", files={"file": (report.name, report.read_bytes(), "image/png")}); upload.raise_for_status()
    doc = upload.json(); print("vision", doc["method"], doc["characters"], "chars")
    assert "15.3" in doc["pages"][0]["text"], "Haemoglobin value not transcribed"
    history, outputs = ask("import", "Mohammed wants a full check-up. Order CBC, metabolic panel, lipid panel, HbA1c, TSH and vitamin D. He brought the attached report from another clinic: read it, add the results to his record, then evaluate.", ["readReport", "importResults", "evaluateOrder"], "PT-100871", [doc["id"]])
    final = [o["output"] for o in outputs if o["output"].get("kind") == "evaluation"][-1]
    print("after import", {d["code"]: d["status"] for d in final["decisions"]})
    assert final["totals"]["redundant_count"] >= 4, final["totals"]
    ask("arabic", "فاطمة هنا للمتابعة. اطلب تعداد الدم والسكر التراكمي.", ["evaluateOrder"], "PT-100234")
print("ALL CHECKS PASSED", flush=True)
