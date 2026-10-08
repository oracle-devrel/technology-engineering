"""Streamlit front end for doc-compare: upload two PDFs, run the pipeline, review the changes.

    streamlit run app.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

OUT_ROOT = Path("out/ui")

st.set_page_config(page_title="Document compare", layout="wide")
st.title("Document compare")
st.caption("Upload two versions of a document. Changes are detected deterministically and verified by Qwen 3.8 on OCI.")

col_old, col_new = st.columns(2)
old_file = col_old.file_uploader("OLD version", type="pdf")
new_file = col_new.file_uploader("NEW version", type="pdf")

with st.sidebar:
    st.header("Options")
    verify = st.toggle("Verify with the model", value=True, help="Off = deterministic candidates only, seconds")
    workers = st.slider("Parallel model calls", 1, 8, 6)
    dpi = st.select_slider("Render dpi", [150, 200, 300], value=200)
    show_rejected = st.toggle("Show rejected candidates", value=False)


def run_compare(old_path: Path, new_path: Path, out_dir: Path) -> int:
    cmd = [sys.executable, "-m", "doccompare.compare", str(old_path), str(new_path), "--out", str(out_dir),
           "--dpi", str(dpi), "--workers", str(workers)] + ([] if verify else ["--no-verify"])
    log = st.empty()
    lines: list[str] = []
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        for line in proc.stdout:
            if "warning" in line.lower():
                continue
            lines.append(line.rstrip())
            log.code("\n".join(lines[-12:]))
    return proc.returncode


if st.button("Compare", type="primary", disabled=not (old_file and new_file)):
    out_dir = OUT_ROOT / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True)
    old_path, new_path = out_dir / "old.pdf", out_dir / "new.pdf"
    old_path.write_bytes(old_file.getvalue())
    new_path.write_bytes(new_file.getvalue())
    with st.status("Running comparison…", expanded=True) as status:
        rc = run_compare(old_path, new_path, out_dir)
        status.update(label="Done" if rc == 0 else f"Failed (exit {rc})", state="complete" if rc == 0 else "error")
    if rc == 0:
        st.session_state["run_dir"] = str(out_dir)

# DOCCOMPARE_RUN_DIR=out/<run> streamlit run app.py   → opens an earlier run without re-running
run_dir = st.session_state.get("run_dir") or os.environ.get("DOCCOMPARE_RUN_DIR")
if not run_dir:
    st.stop()

record = json.loads(Path(run_dir, "changes.json").read_text())
changes = record["changes"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Verified changes", len(changes))
m2.metric("Rejected candidates", len(record["rejected"]))
m3.metric("Unverified", len(record["unverified"]))
m4.metric("Run time", f"{record['timings'].get('total', 0):.0f} s")

unpaired = [pp for pp in record["page_pairs"] if pp["old_page"] is None or pp["new_page"] is None]
if unpaired:
    st.warning("Pages inserted or removed: " + ", ".join(
        f"old p{pp['old_page']}" if pp["new_page"] is None else f"new p{pp['new_page']}" for pp in unpaired))


def page_with_boxes(png_path: str, boxes: list) -> Image.Image:
    im = Image.open(png_path).convert("RGB")
    d = ImageDraw.Draw(im)
    for b in boxes:
        d.rectangle([b[0] - 6, b[1] - 6, b[2] + 6, b[3] + 6], outline=(220, 50, 50), width=6)
    return im


st.subheader("Pages")
paired = [pp for pp in record["page_pairs"] if pp["old_page"] and pp["new_page"]]
for pp in paired:
    on = [c for c in changes if (c["old_page"], c["new_page"]) == (pp["old_page"], pp["new_page"])]
    with st.expander(f"Old p{pp['old_page']} ↔ New p{pp['new_page']} · {len(on)} change(s)", expanded=len(paired) <= 2):
        a, b = st.columns(2)
        a.image(page_with_boxes(pp["old_png"], [c["old_bbox"] for c in on if c.get("old_bbox")]), caption="OLD")
        b.image(page_with_boxes(pp["new_png"], [c["new_bbox"] for c in on if c.get("new_bbox")]), caption="NEW")


def change_row(c: dict) -> dict:
    v = c.get("verdict") or {}
    return {"#": c["id"], "page": f"{c['old_page']}→{c['new_page']}", "type": v.get("change_type", c["op"]),
            "where": v.get("row_label") or "", "old": v.get("old_text") or c["hint"]["old_text"],
            "new": v.get("new_text") or c["hint"]["new_text"], "confidence": v.get("confidence", ""),
            "p": v.get("token_prob")}


st.subheader("Changes")
if not changes and not record["unverified"]:
    st.success("No changes found.")
rows = [change_row(c) for c in changes + record["unverified"]]
if rows and all(r["p"] is None for r in rows):      # no log-probs from this model: hide the column
    for r in rows:
        r.pop("p")
st.dataframe(rows, hide_index=True)

for c in changes + record["unverified"] + (record["rejected"] if show_rejected else []):
    v = c.get("verdict") or {}
    status = "rejected" if c in record["rejected"] else ("unverified" if c in record["unverified"] else v.get("change_type", c["op"]))
    where = f" · {v['row_label']}" if v.get("row_label") else ""
    with st.expander(f"#{c['id']}  p{c['old_page']}→p{c['new_page']}  {status}{where}:  "
                     f"'{(v.get('old_text') or c['hint']['old_text'])[:40]}' → '{(v.get('new_text') or c['hint']['new_text'])[:40]}'"):
        a, b = st.columns(2)
        a.image(c["crops"]["old"], caption="OLD")
        b.image(c["crops"]["new"], caption="NEW")
        if v.get("description"):
            st.write(v["description"])
        if v.get("error"):
            st.error(v["error"])

with st.expander("Raw changes.json"):
    st.download_button("Download changes.json", json.dumps(record, ensure_ascii=False, indent=1),
                       file_name="changes.json", mime="application/json")
    st.json({"changes": changes}, expanded=False)
st.caption(f"Run folder: {run_dir} · full report: {Path(run_dir, 'report.html')}")
