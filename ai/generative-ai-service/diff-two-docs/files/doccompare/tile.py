"""Split a page image into overlapping tiles.

Vision models localise text far better on a ~900 px crop than on a whole
A4 page at 200-300 dpi, where small table text is downsampled away. Tiles
overlap a little so a line straddling a boundary is captured by at least one
tile; vlm_ocr.py translates tile-local boxes back to page coordinates and
drops the duplicates from the overlaps.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image


@dataclass
class Tile:
    index: tuple[int, int]              # (row, col), 0-based
    grid: tuple[int, int]               # (rows, cols)
    bbox_in_page: tuple[int, int, int, int]  # [x0, y0, x1, y1] in original page pixels
    size: tuple[int, int]               # (width, height) of the tile image
    png_bytes: bytes


def tile_image(
    png_bytes: bytes,
    *,
    grid: tuple[int, int] = (2, 2),
    overlap: float = 0.15,
) -> list[Tile]:
    """Split a page PNG into `grid` overlapping tiles.

    `overlap` is the fractional overlap added on each *interior* edge, relative
    to the tile's nominal (non-overlapping) width/height. With grid=(2,2) and
    overlap=0.15, each tile is roughly 65% of the page on each axis (50%
    nominal + 15% overlap on the inner edge).
    """
    rows, cols = grid
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    W, H = img.size

    base_w = W / cols
    base_h = H / rows
    ovx = int(base_w * overlap)
    ovy = int(base_h * overlap)

    tiles: list[Tile] = []
    for r in range(rows):
        for c in range(cols):
            x0 = max(0, int(c * base_w) - (ovx if c > 0 else 0))
            y0 = max(0, int(r * base_h) - (ovy if r > 0 else 0))
            x1 = min(W, int((c + 1) * base_w) + (ovx if c < cols - 1 else 0))
            y1 = min(H, int((r + 1) * base_h) + (ovy if r < rows - 1 else 0))
            crop = img.crop((x0, y0, x1, y1))
            buf = io.BytesIO()
            crop.save(buf, format="PNG", optimize=True)
            tiles.append(
                Tile(
                    index=(r, c),
                    grid=(rows, cols),
                    bbox_in_page=(x0, y0, x1, y1),
                    size=crop.size,
                    png_bytes=buf.getvalue(),
                )
            )
    return tiles
