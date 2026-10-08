"""Combine text-diff candidates with pixel-diff blobs into one candidate list
per page pair, then cap the count so verification cost stays bounded.

Rules
- a blob that intersects a text candidate's NEW box is absorbed (box grows,
  pixel evidence recorded)
- a blob touching no text candidate becomes a `visual` candidate; its OLD box
  is the blob mapped through the inverse homography
- when a page is heavily reflowed (changed-ink fraction above REFLOW_FRAC and
  text candidates exist) pixel blobs are dropped: every line moved, so blobs
  carry no information the text diff does not already have
- over the cap, the two nearest candidates are merged until under it
"""
from __future__ import annotations

from doccompare.register import Blob, Registration, map_bbox
from doccompare.textdiff import BBox, Candidate, _union

REFLOW_FRAC = 0.45


def _intersects(a: BBox, b: BBox, gap: float = 0.0, gap_y: float | None = None) -> bool:
    """Boxes touch within `gap` px horizontally and `gap_y` px vertically.
    Vertical tolerance must stay below the inter-line gap (≈10 px at 200 dpi),
    or two adjacent table rows collapse into one candidate."""
    gy = gap if gap_y is None else gap_y
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gy < b[1] or b[3] + gy < a[1])


def _iou(a: BBox, b: BBox) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


ABSORB_GAP_X = 24.0
ABSORB_GAP_Y = 4.0


def combine(text_cands: list[Candidate], blobs: list[Blob], changed_frac: float,
            reg: Registration, *, max_candidates: int = 40,
            equal_pairs: list[tuple[BBox, BBox]] | None = None) -> tuple[list[Candidate], dict]:
    info = {"text": len(text_cands), "blobs": len(blobs), "changed_frac": round(changed_frac, 3),
            "blobs_dropped_reflow": False, "merged_over_cap": 0, "blobs_on_moved_text": 0}
    cands = [c for c in text_cands]
    reflow = bool(text_cands) and changed_frac > REFLOW_FRAC
    if reflow:
        info["blobs_dropped_reflow"] = True
        blobs = []
    inv = reg.inverse()
    if not reflow:
        # same layout: an insert's OLD box / a delete's NEW box is best located by
        # mapping the real box across the registration, not by neighbouring words
        for c in cands:
            if c.new_anchor and c.old_bbox and not c.old_anchor:
                c.new_bbox = map_bbox(c.old_bbox, reg.H)
            elif c.old_anchor and c.new_bbox and not c.new_anchor:
                c.old_bbox = map_bbox(c.new_bbox, inv)
    for bl in blobs:
        hit = None
        for c in cands:
            if c.new_bbox and _intersects(c.new_bbox, bl.bbox, ABSORB_GAP_X, ABSORB_GAP_Y):
                hit = c
                break
        if hit is not None:
            hit.new_bbox = _union([hit.new_bbox, bl.bbox])
            if hit.old_bbox and not hit.old_anchor:
                hit.old_bbox = _union([hit.old_bbox, map_bbox(bl.bbox, inv)])
            hit.pixel_area += bl.area
            if "pixeldiff" not in hit.sources:
                hit.sources.append("pixeldiff")
        else:
            old_region = map_bbox(bl.bbox, inv)
            cand = Candidate(kind="visual", op="pixel", old_bbox=old_region,
                             new_bbox=list(bl.bbox), pixel_area=bl.area, sources=["pixeldiff"])
            # Unchanged words inside the blob that sit elsewhere on the NEW page mean
            # the text moved (a line above was removed or added). Extend the NEW crop
            # to where those words went, so the verifier sees the same text twice and
            # reports layout_only instead of a phantom deletion. Words that did not
            # move (a stamp over unchanged text) leave the crop as it is.
            moved = [nb for ob, nb in (equal_pairs or []) if _intersects(ob, old_region)
                     and _dist(nb, bl.bbox) > 3.0]
            if moved:
                target = _union(moved)
                if _dist(target, bl.bbox) < 400:
                    cand.new_bbox = _union([cand.new_bbox, target])
                    cand.op = "moved_text"
                    info["blobs_on_moved_text"] += 1
            cands.append(cand)
    while len(cands) > max_candidates:
        best, bi, bj = None, -1, -1
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                d = _dist(cands[i].new_bbox, cands[j].new_bbox)
                if best is None or d < best:
                    best, bi, bj = d, i, j
        a, b = cands[bi], cands[bj]
        a.new_bbox = _union([a.new_bbox, b.new_bbox])
        a.old_bbox = _union([a.old_bbox, b.old_bbox]) if a.old_bbox and b.old_bbox else (a.old_bbox or b.old_bbox)
        a.old_text = (a.old_text + " " + b.old_text).strip()
        a.new_text = (a.new_text + " " + b.new_text).strip()
        a.pixel_area += b.pixel_area
        a.sources = sorted(set(a.sources + b.sources))
        a.kind = "text" if "textdiff" in a.sources else "visual"
        del cands[bj]
        info["merged_over_cap"] += 1
    cands.sort(key=lambda c: (c.new_bbox[1], c.new_bbox[0]))
    return cands, info


def _dist(a: BBox, b: BBox) -> float:
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return (dx * dx + dy * dy) ** 0.5


def dedupe_verified(changes: list[dict], *, min_iou: float = 0.15, gap: float = 10.0, gap_y: float = 3.0) -> list[dict]:
    """Collapse verified changes that describe the same spot (overlapping NEW
    boxes on the same page pair, same change_type). Keeps the first (highest
    confidence first), records the merged ids under `merged_ids`."""
    rank = {"high": 0, "medium": 1, "low": 2}
    ordered = sorted(changes, key=lambda c: (rank.get((c.get("verdict") or {}).get("confidence", "low"), 3), c["id"]))
    kept: list[dict] = []
    for c in ordered:
        v = c.get("verdict") or {}
        dup = None
        for k in kept:
            kv = k.get("verdict") or {}
            if (k["old_page"], k["new_page"]) != (c["old_page"], c["new_page"]):
                continue
            a, b = k["new_bbox"], c["new_bbox"]
            same_text = (_nt(kv.get("new_text")) == _nt(v.get("new_text"))
                         and _nt(kv.get("old_text")) == _nt(v.get("old_text")))
            # the verifier saw the same change through two overlapping crops
            # (neighbouring OCR-noise candidates on a scanned page): same strings,
            # crops overlap → one change, whatever the type label
            ka, ca = (k.get("crop_boxes") or {}).get("new"), (c.get("crop_boxes") or {}).get("new")
            if same_text and (_nt(v.get("new_text")) or _nt(v.get("old_text"))) and ka and ca \
                    and (_iou(ka, ca) >= 0.3 or _contains_center(ka, b) or _contains_center(ca, a)):
                dup = k
                break
            if kv.get("change_type") != v.get("change_type"):
                continue
            overlap = _iou(a, b) >= min_iou or (_intersects(a, b, gap, gap_y) and (
                _contains_center(a, b) or _contains_center(b, a)))
            if overlap and (same_text or _iou(a, b) >= 0.5):
                dup = k
                break
        if dup is None:
            kept.append(c)
        else:
            dup.setdefault("merged_ids", []).append(c["id"])
            dup["new_bbox"] = _union([dup["new_bbox"], c["new_bbox"]])
            if dup.get("old_bbox") and c.get("old_bbox"):
                dup["old_bbox"] = _union([dup["old_bbox"], c["old_bbox"]])
    return sorted(kept, key=lambda c: c["id"])


def _contains_center(a: BBox, b: BBox) -> bool:
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return a[0] <= cx <= a[2] and a[1] <= cy <= a[3]


def _nt(t) -> str:
    import re as _re
    return _re.sub(r"\s+", "", str(t or "")).lower()
