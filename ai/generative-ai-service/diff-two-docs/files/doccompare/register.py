"""Image registration + pixel diff: change candidates that do not depend on OCR.

register()   ORB features + RANSAC homography old→new, estimated on a
             downscaled copy and rescaled. Falls back to identity when the
             estimate is unreliable (few inliers, implausible warp).
pixel_diff() binarise both pages, tolerate `tol` px of residual misalignment
             by comparing each page's ink against the *dilated* ink of the
             other, then merge changed pixels into blobs.

Scanned re-issues of a certificate keep their layout, so this path catches a
replaced digit, an added stamp or signature, a handwritten note. Reflowed
born-digital text defeats pixel diff; textdiff.py covers that case and the
caller decides how to combine the two (see candidates.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

BBox = list[float]


@dataclass
class Registration:
    H: np.ndarray            # 3x3, maps OLD page pixels → NEW page pixels
    ok: bool
    inliers: int
    method: str              # "orb" | "identity"

    def inverse(self) -> np.ndarray:
        return np.linalg.inv(self.H)


@dataclass
class Blob:
    bbox: BBox               # in NEW page pixels
    area: int                # changed pixels inside bbox


def load_gray(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)
    return img


def _plausible(H: np.ndarray, w: int, h: int) -> bool:
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    warped = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
    disp = np.abs(warped - corners.reshape(-1, 2)).max()
    a = H[:2, :2]
    scale = np.sqrt(abs(np.linalg.det(a)))
    return disp < 0.25 * max(w, h) and 0.7 < scale < 1.4 and abs(H[2, 0]) < 1e-3 and abs(H[2, 1]) < 1e-3


def register(old: np.ndarray, new: np.ndarray, *, max_side: int = 1400, min_inliers: int = 40) -> Registration:
    identity = Registration(np.eye(3), False, 0, "identity")
    s = min(1.0, max_side / max(old.shape[0], old.shape[1], new.shape[0], new.shape[1]))
    o = cv2.resize(old, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else old
    n = cv2.resize(new, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else new
    orb = cv2.ORB_create(nfeatures=6000, fastThreshold=10)
    ko, do = orb.detectAndCompute(o, None)
    kn, dn = orb.detectAndCompute(n, None)
    if do is None or dn is None or len(ko) < min_inliers or len(kn) < min_inliers:
        return identity
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = matcher.knnMatch(do, dn, k=2)
    good = [m for m, k in (p for p in knn if len(p) == 2) if m.distance < 0.75 * k.distance]
    if len(good) < min_inliers:
        return identity
    src = np.float32([ko[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kn[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    if H is None:
        return identity
    inl = int(mask.sum())
    if inl < min_inliers:
        return identity
    S = np.diag([s, s, 1.0])
    H_full = np.linalg.inv(S) @ H @ S
    if not _plausible(H_full, old.shape[1], old.shape[0]):
        return identity
    return Registration(H_full, True, inl, "orb")


def warp_old_to_new(old: np.ndarray, reg: Registration, new_shape: tuple[int, int]) -> np.ndarray:
    h, w = new_shape[:2]
    if reg.method == "identity" and old.shape[:2] == (h, w):
        return old
    return cv2.warpPerspective(old, reg.H, (w, h), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def _ink(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, 31, 15)


def pixel_diff(
    old_warped: np.ndarray,
    new: np.ndarray,
    *,
    tol: int = 3,
    merge_px: int = 14,
    min_area: int = 120,
    min_side: int = 6,
    max_blobs: int = 80,
) -> tuple[list[Blob], float]:
    """Return (blobs in NEW frame, changed-ink fraction of the page)."""
    a, b = _ink(old_warped), _ink(new)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))
    da, db = cv2.dilate(a, k), cv2.dilate(b, k)
    diff = cv2.bitwise_or(cv2.bitwise_and(a, cv2.bitwise_not(db)),
                          cv2.bitwise_and(b, cv2.bitwise_not(da)))
    diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ink_total = int(cv2.countNonZero(a) + cv2.countNonZero(b))
    frac = (cv2.countNonZero(diff) / ink_total) if ink_total else 0.0
    merged = cv2.dilate(diff, cv2.getStructuringElement(cv2.MORPH_RECT, (merge_px, merge_px)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(merged, connectivity=8)
    blobs: list[Blob] = []
    for i in range(1, n):
        x, y, w, h, _ = stats[i]
        area = int(cv2.countNonZero(diff[y:y + h, x:x + w]))
        if area < min_area or w < min_side or h < min_side:
            continue
        pad = merge_px // 2
        blobs.append(Blob([float(max(0, x - pad)), float(max(0, y - pad)),
                           float(min(new.shape[1], x + w + pad)), float(min(new.shape[0], y + h + pad))], area))
    blobs.sort(key=lambda b: -b.area)
    return blobs[:max_blobs], float(frac)


def map_bbox(bbox: BBox, H: np.ndarray) -> BBox:
    x0, y0, x1, y1 = bbox
    pts = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]).reshape(-1, 1, 2)
    w = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
    return [float(w[:, 0].min()), float(w[:, 1].min()), float(w[:, 0].max()), float(w[:, 1].max())]
