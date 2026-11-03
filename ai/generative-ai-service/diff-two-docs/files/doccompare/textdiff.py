"""Deterministic, structure-aware text diff between two grounded pages.

Word sequences (reading order) are aligned with difflib's longest-matching-
block algorithm; every replace/insert/delete opcode becomes a candidate that
carries the exact old/new strings and the union of the word boxes involved on
each side. An insert has no old words, so its old-side box is the gap between
the neighbouring old words (an *anchor*) — the verifier still gets a crop.

Normalisation is deliberately minimal (Unicode NFC only). Confusables such as
O/0 are *not* folded: a Q345B→Q34513 difference must reach the verifier, which
decides whether it is a real change or an OCR artefact.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from doccompare.pages import Page, Word

BBox = list[float]


@dataclass
class Candidate:
    kind: str                       # "text" | "visual"
    op: str                         # replace | insert | delete | pixel
    old_bbox: BBox | None           # OLD page pixels (None if unknown)
    new_bbox: BBox | None           # NEW page pixels
    old_text: str = ""
    new_text: str = ""
    old_anchor: bool = False        # old_bbox is a neighbour-derived anchor, not real text
    new_anchor: bool = False
    pixel_area: int = 0
    sources: list[str] = field(default_factory=list)


def _union(boxes: list[BBox]) -> BBox:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def _norm(t: str) -> str:
    return unicodedata.normalize("NFC", t)


def _anchor(words: list[Word], i: int, page: Page) -> BBox:
    """Box between words[i-1] and words[i] (gap where something was inserted/removed)."""
    prev = words[i - 1].bbox if i - 1 >= 0 else None
    nxt = words[i].bbox if i < len(words) else None
    if prev and nxt and abs(prev[1] - nxt[1]) < max(8.0, 0.8 * (prev[3] - prev[1])):
        return [min(prev[0], nxt[0]), min(prev[1], nxt[1]), max(prev[2], nxt[2]), max(prev[3], nxt[3])]
    b = nxt or prev
    if b is None:
        return [0.0, 0.0, float(page.width), float(min(page.height, 200))]
    return list(b)


def _group_by_line(words: list[Word]) -> list[list[Word]]:
    groups: list[list[Word]] = []
    for w in words:
        if groups and abs(groups[-1][-1].bbox[1] - w.bbox[1]) < 0.7 * max(1.0, w.bbox[3] - w.bbox[1]):
            groups[-1].append(w)
        else:
            groups.append([w])
    return groups


def diff_pages(old: Page, new: Page) -> list[Candidate]:
    ow, nw = old.words(), new.words()
    a = [_norm(w.text) for w in ow]
    b = [_norm(w.text) for w in nw]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    cands: list[Candidate] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        o_words, n_words = ow[i1:i2], nw[j1:j2]
        if op == "replace" and (len(o_words) > 12 or len(n_words) > 12):
            # long rewrite: split per line so crops stay small
            og, ng = _group_by_line(o_words), _group_by_line(n_words)
            for k in range(max(len(og), len(ng))):
                ol = og[k] if k < len(og) else []
                nl = ng[k] if k < len(ng) else []
                cands.append(_make(op, ol, nl, ow, nw, i1, j1, old, new))
            continue
        cands.append(_make(op, o_words, n_words, ow, nw, i1, j1, old, new))
    return _merge_close(cands)


def equal_word_pairs(old: Page, new: Page) -> list[tuple[BBox, BBox]]:
    """(old box, new box) for every word the diff considers unchanged. Lets the
    pixel-diff stage tell a *moved* line (same words, new position) from a real
    visual change such as a stamp drawn over unchanged text."""
    ow, nw = old.words(), new.words()
    sm = SequenceMatcher(None, [_norm(w.text) for w in ow], [_norm(w.text) for w in nw], autojunk=False)
    pairs: list[tuple[BBox, BBox]] = []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            pairs.append((ow[blk.a + k].bbox, nw[blk.b + k].bbox))
    return pairs


def _make(op, o_words, n_words, ow, nw, i1, j1, old, new) -> Candidate:
    if o_words:
        ob, oa = _union([w.bbox for w in o_words]), False
    else:
        ob, oa = _anchor(ow, i1, old), True
    if n_words:
        nb, na = _union([w.bbox for w in n_words]), False
    else:
        nb, na = _anchor(nw, j1, new), True
    return Candidate(kind="text", op=op, old_bbox=ob, new_bbox=nb,
                     old_text=" ".join(w.text for w in o_words),
                     new_text=" ".join(w.text for w in n_words),
                     old_anchor=oa, new_anchor=na, sources=["textdiff"])


def _close(a: BBox, b: BBox, gap: float, gap_y: float = 4.0) -> bool:
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gap_y < b[1] or b[3] + gap_y < a[1])


def _merge_close(cands: list[Candidate], gap: float = 18.0) -> list[Candidate]:
    """Merge text candidates whose NEW boxes touch (same cell / same line)."""
    out: list[Candidate] = []
    for c in sorted(cands, key=lambda c: (c.new_bbox[1], c.new_bbox[0])):
        if out and _close(out[-1].new_bbox, c.new_bbox, gap) and _close(out[-1].old_bbox, c.old_bbox, gap * 3):
            p = out[-1]
            p.new_bbox = _union([p.new_bbox, c.new_bbox])
            p.old_bbox = _union([p.old_bbox, c.old_bbox])
            p.old_text = (p.old_text + " " + c.old_text).strip()
            p.new_text = (p.new_text + " " + c.new_text).strip()
            p.op = "replace" if p.op != c.op else p.op
            p.old_anchor = p.old_anchor and c.old_anchor
            p.new_anchor = p.new_anchor and c.new_anchor
        else:
            out.append(c)
    return out
