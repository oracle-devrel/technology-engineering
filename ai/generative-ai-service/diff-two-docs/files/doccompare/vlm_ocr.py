"""Tiled VLM OCR for scanned pages (no OCI Document Understanding).

Box frame: measured against PDF text layers (Qwen 3.8 27B on OCI, 200 dpi,
900 px tiles), the model's line boxes matched the truth far better when read
as a 0-1000 frame (IoU 0.47 sparse / 0.24 dense page) than as pixels (0.05 /
0.03), so `frame="norm1000"` is the default. Another model may answer in
pixels: set `--ocr-frame pixel`, or `auto` to decide per tile.

Why tiles: a vision model asked to transcribe a whole dense page is slow
(minutes, thousands of tokens) and its boxes are poor (line IoU ≈ 0.1). On
tiles of ~900 px the boxes become good enough to *locate* text; the exact
crops used for verification come from the registration and pixel diff anyway.
"""
from __future__ import annotations

import io
import json
import math
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from PIL import Image

from doccompare.models.client import ModelClient
from doccompare.pages import Line, Word
from doccompare.prompts import FRAME_DESC, OCR_SCHEMA, OCR_TILE_PROMPT
from doccompare.tile import Tile, tile_image


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        s = s.rsplit("```", 1)[0]
    return s.strip()


def _norm(t: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", t)).lower()


def _iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _tile_lines(client: ModelClient, tile: Tile, frame: str, max_tokens: int) -> tuple[list[Line], dict]:
    tw, th = tile.size
    prompt = OCR_TILE_PROMPT.format(w=tw, h=th, frame_desc=FRAME_DESC["pixel" if frame == "auto" else frame])
    r = client.chat(prompt=prompt, images=[tile.png_bytes], max_tokens=max_tokens,
                    temperature=0.0, json_mode=True, json_schema=OCR_SCHEMA, json_schema_name="ocr")
    meta = {"tile": tile.index, "bbox_in_page": tile.bbox_in_page, "latency_s": r.latency_s,
            "finish": r.finish_reason, "error": r.error, "completion_tokens": r.completion_tokens}
    if r.error or not r.text.strip():
        meta["parsed"] = 0
        return [], meta
    try:
        data = json.loads(_strip_fences(r.text))
    except json.JSONDecodeError:
        meta["parsed"] = 0
        meta["raw"] = r.text[:500]
        return [], meta
    ox, oy = tile.bbox_in_page[0], tile.bbox_in_page[1]
    out: list[Line] = []
    for item in data.get("lines", []):
        text = unicodedata.normalize("NFC", str(item.get("text", ""))).strip()
        b = item.get("bbox")
        if not text or not (isinstance(b, list) and len(b) == 4):
            continue
        try:
            x0, y0, x1, y1 = (float(v) for v in b)
        except (TypeError, ValueError):
            continue
        f = frame
        if f == "auto":
            # pixel unless a coordinate exceeds the tile, which only a 0-1000 frame explains
            f = "norm1000" if (x1 > tw * 1.02 or y1 > th * 1.02) and max(tw, th) < 1000 else "pixel"
        if f == "norm1000":
            x0, x1 = x0 * tw / 1000.0, x1 * tw / 1000.0
            y0, y1 = y0 * th / 1000.0, y1 * th / 1000.0
        x0, x1 = sorted((max(0.0, x0), min(float(tw), x1)))
        y0, y1 = sorted((max(0.0, y0), min(float(th), y1)))
        if x1 - x0 < 1 or y1 - y0 < 1:
            continue
        bbox = [x0 + ox, y0 + oy, x1 + ox, y1 + oy]
        out.append(Line(text=text, bbox=bbox, words=_split_words(text, bbox)))
    meta["parsed"] = len(out)
    return out, meta


def _split_words(text: str, bbox: list[float]) -> list[Word]:
    """Approximate word boxes: split the line box proportionally to character counts."""
    parts = text.split()
    if not parts:
        return []
    total = sum(len(p) for p in parts) + (len(parts) - 1)
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    words: list[Word] = []
    cursor = 0
    for p in parts:
        wx0 = x0 + width * cursor / total
        wx1 = x0 + width * (cursor + len(p)) / total
        words.append(Word(text=p, bbox=[wx0, y0, wx1, y1]))
        cursor += len(p) + 1
    return words


def _dedupe(lines: list[Line]) -> list[Line]:
    """Drop duplicate lines captured in tile overlaps: same text, vertical
    centres within a line height, horizontal ranges overlapping. Boxes from
    two tiles rarely agree well enough for an IoU test, so this is looser."""
    lines = sorted(lines, key=lambda l: (l.bbox[1], l.bbox[0]))
    kept: list[Line] = []
    for l in lines:
        n = _norm(l.text)
        cy = (l.bbox[1] + l.bbox[3]) / 2
        h = max(8.0, l.bbox[3] - l.bbox[1])
        dup = False
        for k in kept:
            kcy = (k.bbox[1] + k.bbox[3]) / 2
            if abs(kcy - cy) > max(12.0, 0.9 * h):
                continue
            if _norm(k.text) != n:
                continue
            xo = min(k.bbox[2], l.bbox[2]) - max(k.bbox[0], l.bbox[0])
            if xo > 0.3 * min(k.bbox[2] - k.bbox[0], l.bbox[2] - l.bbox[0]):
                dup = True
                break
        if not dup:
            kept.append(l)
    return kept


def make_ocr(
    client: ModelClient,
    *,
    frame: str = "norm1000",
    max_tile_px: int = 900,
    overlap: float = 0.10,
    workers: int = 4,
    max_tokens: int = 8000,
    debug_dir: str | Path | None = None,
) -> Callable[[bytes], list[Line]]:
    """Return an `ocr(png_bytes) -> list[Line]` callable for pages.load_document."""
    counter = {"n": 0}

    def ocr(png_bytes: bytes) -> list[Line]:
        img = Image.open(io.BytesIO(png_bytes))
        W, H = img.size
        grid = (max(1, math.ceil(H / max_tile_px)), max(1, math.ceil(W / max_tile_px)))
        tiles = tile_image(png_bytes, grid=grid, overlap=overlap)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(lambda t: _tile_lines(client, t, frame, max_tokens), tiles))
        lines = [l for ls, _ in results for l in ls]
        if debug_dir:
            counter["n"] += 1
            d = Path(debug_dir)
            d.mkdir(parents=True, exist_ok=True)
            (d / f"ocr_{counter['n']:03d}.json").write_text(
                json.dumps({"grid": grid, "tiles": [m for _, m in results]}, indent=1))
        return _dedupe(lines)

    return ocr
