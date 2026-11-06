"""CLI: compare two PDF versions and emit an exact, grounded change list.

    python -m doccompare.compare OLD.pdf NEW.pdf --out out/run1
    python -m doccompare.compare OLD.pdf NEW.pdf --out out/run1 --no-verify   # deterministic only
    python -m doccompare.compare OLD.pdf NEW.pdf --out out/run1 --no-ocr      # never call the VLM for OCR

Stages: render+ground → align pages → register+pixel diff → text diff →
combine candidates → VLM verify → changes.json + report.html
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2

from doccompare.align import align_pages
from doccompare.candidates import combine, dedupe_verified
from doccompare.models.client import client_for
from doccompare.models.registry import load_registry
from doccompare.pages import load_document
from doccompare.register import load_gray, pixel_diff, register, warp_old_to_new
from doccompare.report import write_html, write_json
from doccompare.textdiff import diff_pages, equal_word_pairs
from doccompare.verify import crop_pair, verdict_dict, verify_candidates
from doccompare.vlm_ocr import make_ocr


def _parse_pages(spec: str | None) -> list[int] | None:
    if not spec:
        return None
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--model", default=None, help="registry slug (default: first in MODELS=)")
    ap.add_argument("--pages-old", default=None, help="1-based, e.g. 1-3,5")
    ap.add_argument("--pages-new", default=None)
    ap.add_argument("--no-verify", action="store_true", help="skip VLM adjudication")
    ap.add_argument("--no-confirm", action="store_true", help="skip the hint-free re-check on scanned pages")
    ap.add_argument("--no-ocr", action="store_true", help="scanned pages: pixel diff only, no VLM OCR")
    ap.add_argument("--max-candidates", type=int, default=40, help="per page pair")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--ocr-frame", default="norm1000", choices=["norm1000", "pixel", "auto"],
                    help="coordinate frame the VLM uses for OCR boxes on tiles")
    ap.add_argument("--ocr-tile", type=int, default=900, help="max tile side in px for VLM OCR")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    timings: dict[str, float] = {}

    client = None
    model_slug = None
    if not (args.no_verify and args.no_ocr):
        reg = load_registry()
        model_slug = args.model or next(iter(reg))
        spec = reg[model_slug]
        client = client_for(spec, timeout=(10, 600))
        print(f"model: {spec}")

    ocr = None if (args.no_ocr or client is None) else make_ocr(
        client, frame=args.ocr_frame, max_tile_px=args.ocr_tile, workers=args.workers, debug_dir=out / "ocr_debug")

    t0 = time.time()
    print(f"[1/6] rendering + grounding")
    old = load_document(args.old, out / "old", doc_id="old", dpi=args.dpi,
                        page_indices=_parse_pages(args.pages_old), ocr=ocr)
    new = load_document(args.new, out / "new", doc_id="new", dpi=args.dpi,
                        page_indices=_parse_pages(args.pages_new), ocr=ocr)
    timings["ground"] = round(time.time() - t0, 1)
    for d in (old, new):
        src = {p.source for p in d.pages}
        print(f"    {d.doc_id}: {len(d.pages)} pages, sources={sorted(src)}")

    t0 = time.time()
    print(f"[2/6] aligning pages")
    pairs = align_pages(old, new)
    timings["align"] = round(time.time() - t0, 1)
    for pp in pairs:
        print(f"    old p{(pp.old + 1) if pp.old is not None else '—'} ↔ new p{(pp.new + 1) if pp.new is not None else '—'}  sim={pp.similarity:.2f}")

    print(f"[3/6] registration + pixel diff, [4/6] text diff, [5/6] combine")
    t0 = time.time()
    page_pairs_rec = []
    all_items = []   # (pair_index, candidate, old_crop_box, new_crop_box, png_old, png_new)
    imgs_cache: dict[str, object] = {}
    for pi, pp in enumerate(pairs):
        rec = {"old_page": pp.old + 1 if pp.old is not None else None,
               "new_page": pp.new + 1 if pp.new is not None else None,
               "similarity": round(pp.similarity, 3)}
        if pp.old is None or pp.new is None:
            page_pairs_rec.append(rec)
            continue
        po, pn = old.pages[pp.old], new.pages[pp.new]
        go, gn = load_gray(po.png_path), load_gray(pn.png_path)
        reg = register(go, gn)
        warped = warp_old_to_new(go, reg, gn.shape)
        blobs, frac = pixel_diff(warped, gn)
        tcands = diff_pages(po, pn) if (po.lines and pn.lines) else []
        pairs_eq = equal_word_pairs(po, pn) if (po.lines and pn.lines) else []
        cands, info = combine(tcands, blobs, frac, reg, max_candidates=args.max_candidates, equal_pairs=pairs_eq)
        rec.update({"old_png": po.png_path, "new_png": pn.png_path,
                    "old_size": [po.width, po.height], "new_size": [pn.width, pn.height],
                    "old_source": po.source, "new_source": pn.source,
                    "registration": f"{reg.method}({reg.inliers})", "changed_ink_frac": round(frac, 3),
                    "n_text_candidates": len(tcands), "n_blobs": len(blobs), "combine": info})
        page_pairs_rec.append(rec)
        print(f"    pair old p{po.number}↔new p{pn.number}: reg={reg.method}({reg.inliers}) ink-changed={frac:.3f} "
              f"text={len(tcands)} blobs={len(blobs)} → {len(cands)} candidates")
        co = cv2.imread(po.png_path, cv2.IMREAD_COLOR)
        cn = cv2.imread(pn.png_path, cv2.IMREAD_COLOR)
        for c in cands:
            ob, nb, png_o, png_n = crop_pair(co, cn, c, reg, old_page=po, new_page=pn)
            all_items.append((pi, c, ob, nb, png_o, png_n))
    timings["candidates"] = round(time.time() - t0, 1)

    page_pairs_rec_by_id = {(r["old_page"], r["new_page"]): r for r in page_pairs_rec}
    crops_dir = out / "crops"
    crops_dir.mkdir(exist_ok=True)
    records = []
    for k, (pi, c, ob, nb, png_o, png_n) in enumerate(all_items, 1):
        po_path = crops_dir / f"c{k:03d}_old.png"
        pn_path = crops_dir / f"c{k:03d}_new.png"
        po_path.write_bytes(png_o)
        pn_path.write_bytes(png_n)
        pp = pairs[pi]
        records.append({
            "id": k, "old_page": pp.old + 1, "new_page": pp.new + 1,
            "kind": c.kind, "op": c.op, "sources": c.sources,
            "old_bbox": [round(v, 1) for v in c.old_bbox] if c.old_bbox else None,
            "new_bbox": [round(v, 1) for v in c.new_bbox] if c.new_bbox else None,
            "old_anchor": c.old_anchor, "new_anchor": c.new_anchor,
            "crop_boxes": {"old": ob, "new": nb},
            "crops": {"old": str(po_path), "new": str(pn_path)},
            "hint": {"old_text": c.old_text, "new_text": c.new_text, "pixel_area": c.pixel_area},
            "verdict": None,
        })

    changes, rejected, unverified = [], [], []
    if args.no_verify or client is None:
        unverified = records
        print(f"[6/6] verification skipped ({len(records)} candidates)")
    else:
        t0 = time.time()
        print(f"[6/6] verifying {len(records)} candidates with {model_slug} ({args.workers} workers)")
        verdicts = verify_candidates(client, [(c, po, pn) for (_, c, _, _, po, pn) in all_items], workers=args.workers)
        for rec, v in zip(records, verdicts):
            rec["verdict"] = verdict_dict(v)
            if v.error:
                unverified.append(rec)
            elif v.changed and v.change_type not in ("none", "layout_only"):
                changes.append(rec)
            else:
                rejected.append(rec)
        # second opinion without the OCR hint for text changes on scanned pages
        recheck = [i for i, (rec, v) in enumerate(zip(records, verdicts))
                   if rec in changes and rec["kind"] == "text"
                   and v.change_type in ("text_edit", "number_change", "addition", "deletion")
                   and (page_pairs_rec_by_id[(rec["old_page"], rec["new_page"])]["old_source"] == "vlm"
                        or page_pairs_rec_by_id[(rec["old_page"], rec["new_page"])]["new_source"] == "vlm")]
        if recheck and not args.no_confirm:
            print(f"    hint-free re-check of {len(recheck)} text change(s) on scanned pages")
            blind = verify_candidates(client, [(all_items[i][1], all_items[i][4], all_items[i][5]) for i in recheck],
                                      workers=args.workers, blind=True)
            for i, bv in zip(recheck, blind):
                rec = records[i]
                rec["confirm"] = verdict_dict(bv)
                if bv.error is None and not (bv.changed and bv.change_type not in ("none", "layout_only")):
                    changes.remove(rec)
                    rec["verdict"]["note"] = "rejected: hint-free re-check saw no change"
                    rejected.append(rec)
        timings["verify"] = round(time.time() - t0, 1)
        n_before = len(changes)
        changes = dedupe_verified(changes)
        if len(changes) != n_before:
            print(f"    deduplicated {n_before - len(changes)} overlapping verdict(s)")
        lat = [v.latency_s for v in verdicts if v.latency_s]
        print(f"    {len(changes)} changes, {len(rejected)} rejected, {len(unverified)} errors; "
              f"mean latency {sum(lat) / len(lat):.1f}s" if lat else "    no verdicts")

    timings["total"] = round(time.time() - t_all, 1)
    record = {
        "old": {"pdf": str(Path(args.old).resolve()), "pages": len(old.pages)},
        "new": {"pdf": str(Path(args.new).resolve()), "pages": len(new.pages)},
        "dpi": args.dpi, "model": model_slug, "timings": timings,
        "page_pairs": page_pairs_rec,
        "changes": changes, "rejected": rejected, "unverified": unverified,
    }
    jp = write_json(out, record)
    hp = write_html(out, record)
    print(f"\nwrote {jp}\nwrote {hp}\ntimings: {json.dumps(timings)}")
    for c in changes:
        v = c["verdict"]
        where = " / ".join(x for x in (v.get("row_label"), v.get("column_header")) if x)
        print(f"  #{c['id']:3d} p{c['old_page']}→p{c['new_page']} {v['change_type']:18s} {v['confidence']:6s} "
              f"{where + ': ' if where else ''}'{v['old_text']}' → '{v['new_text']}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
