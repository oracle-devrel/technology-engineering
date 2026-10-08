"""Page alignment between two document versions (inserted / removed pages).

Needleman-Wunsch over a page-similarity matrix. Similarity = Jaccard over
word 3-gram shingles of the page text; pages without text (scanned, no OCR)
fall back to a coarse image correlation. Pairing a page costs `sim - PAIR_T`,
leaving a page unpaired costs `GAP`, so two unrelated pages are left unpaired
instead of forced together.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import cv2
import numpy as np

from doccompare.pages import Document, Page

PAIR_T = 0.20
GAP = -0.05


@dataclass
class PagePair:
    old: int | None      # page index in old doc (None = inserted page)
    new: int | None      # page index in new doc (None = removed page)
    similarity: float


def _shingles(p: Page, n: int = 4) -> set[str]:
    """Character n-grams over the de-spaced text: script-agnostic (works for
    CJK where \\w+ tokens are whole runs) and tolerant of OCR word splits."""
    t = re.sub(r"\s+", "", unicodedata.normalize("NFC", p.text).lower())
    if len(t) < n:
        return {t} if t else set()
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def _thumb(p: Page) -> np.ndarray:
    img = cv2.imread(p.png_path, cv2.IMREAD_GRAYSCALE)
    t = cv2.resize(img, (64, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
    t -= t.mean()
    n = np.linalg.norm(t)
    return t / n if n > 0 else t


def page_similarity(a: Page, b: Page) -> float:
    """max(text Jaccard, 0.8 × image correlation): OCR noise on two scans of
    the same form can push text similarity near zero while the images agree."""
    sa, sb = _shingles(a), _shingles(b)
    text_sim = len(sa & sb) / len(sa | sb) if (sa and sb) else 0.0
    ta, tb = _thumb(a), _thumb(b)
    img_sim = float(max(0.0, (ta * tb).sum()))
    return max(text_sim, 0.8 * img_sim)


def align_pages(old: Document, new: Document) -> list[PagePair]:
    A, B = old.pages, new.pages
    n, m = len(A), len(B)
    if n == 1 and m == 1:
        # two single pages fed deliberately: always compare them
        return [PagePair(0, 0, page_similarity(A[0], B[0]))]
    S = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            S[i, j] = page_similarity(A[i], B[j])
    dp = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP
    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] + GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = max(dp[i - 1, j - 1] + S[i - 1, j - 1] - PAIR_T,
                           dp[i - 1, j] + GAP, dp[i, j - 1] + GAP)
    pairs: list[PagePair] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and abs(dp[i, j] - (dp[i - 1, j - 1] + S[i - 1, j - 1] - PAIR_T)) < 1e-9:
            pairs.append(PagePair(i - 1, j - 1, float(S[i - 1, j - 1])))
            i, j = i - 1, j - 1
        elif i > 0 and abs(dp[i, j] - (dp[i - 1, j] + GAP)) < 1e-9:
            pairs.append(PagePair(i - 1, None, 0.0))
            i -= 1
        else:
            pairs.append(PagePair(None, j - 1, 0.0))
            j -= 1
    pairs.reverse()
    return pairs
