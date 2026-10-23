"""Exact text + geometry from a born-digital PDF via pypdfium2's text page.

Character boxes come back in PDF user space (points, origin bottom-left, on
the *unrotated* page); we map them onto the rendered image (pixels, origin
top-left, rotation applied) so every word lines up with the PNG the VLM and
the pixel-diff see.
"""
from __future__ import annotations

import unicodedata

import pypdfium2 as pdfium

from typing import TYPE_CHECKING
if TYPE_CHECKING:  # avoid import cycle at runtime
    from doccompare.pages import Line, Word


def _to_pixels(box, W_pt: float, H_pt: float, rotation: int, scale: float) -> list[float]:
    """(l, b, r, t) in PDF points → [x0, y0, x1, y1] pixels on the rendered page."""
    l, b, r, t = box
    corners = [(l, b), (l, t), (r, b), (r, t)]
    pts = []
    for x, y in corners:
        if rotation == 0:
            px, py = x, H_pt - y
        elif rotation == 90:
            px, py = y, x
        elif rotation == 180:
            px, py = W_pt - x, y
        else:  # 270
            px, py = H_pt - y, W_pt - x
        pts.append((px * scale, py * scale))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def _union(boxes: list[list[float]]) -> list[float]:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def extract_lines(page: pdfium.PdfPage, *, scale: float, rendered_size: tuple[int, int]) -> list["Line"]:
    from doccompare.pages import Line, Word

    W_pt, H_pt = page.get_size()
    rotation = page.get_rotation()
    tp = page.get_textpage()
    text = tp.get_text_range()
    n = min(len(text), tp.count_chars())

    # 1) chars → (char, pixel box); split lines on newline chars AND on big
    #    vertical jumps (some generators emit no newlines inside a block)
    raw_lines: list[list[tuple[str, list[float]]]] = [[]]
    prev_mid = None
    prev_h = None
    for i in range(n):
        ch = text[i]
        if ch in "\r\n":
            if raw_lines[-1]:
                raw_lines.append([])
            prev_mid = None
            continue
        box = _to_pixels(tp.get_charbox(i), W_pt, H_pt, rotation, scale)
        if box[2] - box[0] <= 0 and box[3] - box[1] <= 0:
            if ch.isspace():
                raw_lines[-1].append((ch, box))
            continue
        mid = (box[1] + box[3]) / 2
        h = max(1.0, box[3] - box[1])
        if prev_mid is not None and abs(mid - prev_mid) > 0.6 * max(h, prev_h or h) and raw_lines[-1]:
            raw_lines.append([])
        raw_lines[-1].append((ch, box))
        prev_mid, prev_h = mid, h

    # 2) lines → words (split on whitespace), boxes = union of char boxes
    lines: list[Line] = []
    for chars in raw_lines:
        words: list[Word] = []
        cur: list[tuple[str, list[float]]] = []

        def flush():
            nonlocal cur
            ink = [(c, b) for c, b in cur if not c.isspace() and (b[2] - b[0]) > 0]
            if ink:
                words.append(Word(text=unicodedata.normalize("NFC", "".join(c for c, _ in ink)),
                                  bbox=_union([b for _, b in ink])))
            cur = []

        for c, b in chars:
            if c.isspace():
                flush()
            else:
                cur.append((c, b))
        flush()
        if not words:
            continue
        lines.append(Line(text=" ".join(w.text for w in words),
                          bbox=_union([w.bbox for w in words]), words=words))
    lines.sort(key=lambda l: (round(l.bbox[1] / 4), l.bbox[0]))
    return lines
