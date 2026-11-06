"""VLM adjudication of candidates: one call per candidate, two crops in one
prompt (OLD, NEW), schema-constrained JSON, log-probs requested so a numeric
confidence can sit next to the model's self-reported one.

Crops are cut with a margin for context and upscaled so small table cells are
legible. The OLD crop comes from the text-diff box when the candidate has real
old words, otherwise from the NEW box mapped through the inverse homography.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

from doccompare.models.client import ModelClient
from doccompare.pages import Page
from doccompare.prompts import VERIFY_PROMPT, VERIFY_PROMPT_BLIND, VERIFY_SCHEMA
from doccompare.register import Registration, map_bbox
from doccompare.textdiff import BBox, Candidate


@dataclass
class Verdict:
    changed: bool | None
    change_type: str
    old_text: str
    new_text: str
    row_label: str
    column_header: str
    description: str
    confidence: str
    mean_logprob: float | None
    latency_s: float | None
    error: str | None = None
    raw: str = field(default="", repr=False)


def _expand(b: BBox, W: int, H: int, margin_px: float, margin_frac: float, min_w: float, min_h: float) -> list[int]:
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    mx = margin_px + margin_frac * w
    my = margin_px + margin_frac * h
    if w + 2 * mx < min_w:
        mx = (min_w - w) / 2
    if h + 2 * my < min_h:
        my = (min_h - h) / 2
    return [int(max(0, x0 - mx)), int(max(0, y0 - my)), int(min(W, x1 + mx)), int(min(H, y1 + my))]


def _crop_png(img: np.ndarray, box: list[int], target_min_h: int = 200, max_scale: float = 4.0,
              max_w: int = 1800) -> bytes:
    x0, y0, x1, y1 = box
    crop = img[y0:y1, x0:x1]
    if crop.size == 0:
        crop = np.full((40, 120, 3), 255, np.uint8)
    h, w = crop.shape[:2]
    s = min(max_scale, max(1.0, target_min_h / max(1, h)), max_w / max(1, w))
    if s > 1.0:
        crop = cv2.resize(crop, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    ok, buf = cv2.imencode(".png", crop)
    return buf.tobytes()


def _collect_logprobs(obj, acc: list[float], depth: int = 0) -> None:
    if depth > 6 or obj is None:
        return
    if isinstance(obj, (list, tuple)):
        for o in obj:
            _collect_logprobs(o, acc, depth + 1)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("logprob", "log_prob", "token_logprobs") and isinstance(v, (int, float)):
                acc.append(float(v))
            elif k in ("token_logprobs",) and isinstance(v, list):
                acc.extend(float(x) for x in v if isinstance(x, (int, float)))
            else:
                _collect_logprobs(v, acc, depth + 1)
        return
    d = getattr(obj, "__dict__", None)
    if d:
        _collect_logprobs({k: v for k, v in d.items() if not k.startswith("_")}, acc, depth + 1)


def _mean_logprob(lp) -> float | None:
    acc: list[float] = []
    _collect_logprobs(lp, acc)
    if not acc:
        return None
    return float(sum(acc) / len(acc))


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        s = s.rsplit("```", 1)[0]
    return s.strip()


def _row_extent(page: Page | None, box: BBox) -> BBox:
    """Widen `box` horizontally to every line that overlaps it vertically, so a
    table-cell crop also shows the row label at the left edge of the row."""
    if page is None or not page.lines:
        return box
    x0, y0, x1, y1 = box
    for l in page.lines:
        ly0, ly1 = l.bbox[1], l.bbox[3]
        if min(y1, ly1) - max(y0, ly0) > 0.4 * min(y1 - y0, max(1.0, ly1 - ly0)):
            x0, x1 = min(x0, l.bbox[0]), max(x1, l.bbox[2])
    return [x0, y0, x1, y1]


def crop_pair(old_img: np.ndarray, new_img: np.ndarray, cand: Candidate, reg: Registration,
              *, margin_px: float = 28, margin_frac: float = 0.25,
              old_page: Page | None = None, new_page: Page | None = None,
              row_context: bool = True) -> tuple[list[int], list[int], bytes, bytes]:
    Hn, Wn = new_img.shape[:2]
    Ho, Wo = old_img.shape[:2]
    nbox = _row_extent(new_page, cand.new_bbox) if row_context else cand.new_bbox
    nb = _expand(nbox, Wn, Hn, margin_px, margin_frac, 220, 90)
    # Exact text-layer boxes locate the OLD crop on their own (survives reflow).
    # VLM OCR boxes are approximate (line IoU ≈ 0.5), so for scanned pages the
    # OLD crop is the NEW crop mapped through the registration instead.
    exact_old = (old_page is None or old_page.source == "textlayer") and (new_page is None or new_page.source == "textlayer")
    if cand.kind == "text" and cand.old_bbox and not cand.old_anchor and (exact_old or not reg.ok):
        obox = _row_extent(old_page, cand.old_bbox) if row_context else cand.old_bbox
        ob = _expand(obox, Wo, Ho, margin_px, margin_frac, 220, 90)
    else:
        mapped = map_bbox([float(v) for v in nb], reg.inverse())
        ob = [int(max(0, mapped[0])), int(max(0, mapped[1])), int(min(Wo, mapped[2])), int(min(Ho, mapped[3]))]
        if cand.old_bbox and cand.old_anchor:
            ob = _expand(_union2(cand.old_bbox, [float(v) for v in ob]), Wo, Ho, 0, 0, 220, 90)
    return ob, nb, _crop_png(old_img, ob), _crop_png(new_img, nb)


def _union2(a: BBox, b: BBox) -> BBox:
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def verify_one(client: ModelClient, cand: Candidate, png_old: bytes, png_new: bytes, *, max_tokens: int = 4000,
               blind: bool = False) -> Verdict:
    if blind:
        prompt = VERIFY_PROMPT_BLIND
    else:
        prompt = VERIFY_PROMPT.format(kind=cand.op if cand.op == "moved_text" else (cand.kind if cand.kind == "visual" else cand.op),
                                      old_hint=cand.old_text[:200].replace('"', "'"),
                                      new_hint=cand.new_text[:200].replace('"', "'"))
    r = client.chat(prompt=prompt, images=[png_old, png_new], max_tokens=max_tokens, temperature=0.0,
                    json_mode=True, json_schema=VERIFY_SCHEMA, json_schema_name="verify", log_probs=1)
    if not r.error and not r.text.strip() and r.finish_reason == "length":
        # hidden reasoning ate the budget (Qwen 3.x); one retry with double budget
        r = client.chat(prompt=prompt, images=[png_old, png_new], max_tokens=max_tokens * 2, temperature=0.0,
                        json_mode=True, json_schema=VERIFY_SCHEMA, json_schema_name="verify", log_probs=1)
    if r.error or not r.text.strip():
        return Verdict(None, "error", "", "", "", "", "", "low", None, r.latency_s,
                       error=r.error or f"empty content (finish={r.finish_reason})", raw=r.text)
    try:
        j = json.loads(_strip_fences(r.text))
    except json.JSONDecodeError as e:
        return Verdict(None, "error", "", "", "", "", "", "low", None, r.latency_s,
                       error=f"json parse: {e}", raw=r.text)
    return Verdict(
        changed=bool(j.get("changed")),
        change_type=str(j.get("change_type", "none")),
        old_text=str(j.get("old_text", "")),
        new_text=str(j.get("new_text", "")),
        row_label=str(j.get("row_label", "") or ""),
        column_header=str(j.get("column_header", "") or ""),
        description=str(j.get("description", "") or ""),
        confidence=str(j.get("confidence", "low")),
        mean_logprob=_mean_logprob(r.logprobs),
        latency_s=r.latency_s,
        raw=r.text,
    )


def verify_candidates(client: ModelClient, items: list[tuple[Candidate, bytes, bytes]], *, workers: int = 4,
                      blind: bool = False) -> list[Verdict]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda it: verify_one(client, it[0], it[1], it[2], blind=blind), items))


def verdict_dict(v: Verdict) -> dict:
    d = asdict(v)
    d.pop("raw", None)
    if v.mean_logprob is not None:
        d["token_prob"] = round(math.exp(v.mean_logprob), 4)
    return d
