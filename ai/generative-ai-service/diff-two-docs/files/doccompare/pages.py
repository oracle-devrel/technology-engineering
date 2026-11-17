"""Grounded page model: every line and word carries a pixel bbox on the
rendered page image. Two sources:

  textlayer : born-digital PDF, exact characters + exact boxes (no model)
  vlm       : scanned page, tiled VLM OCR (doccompare/vlm_ocr.py)

Per-page results are cached as JSON next to the rendered PNG so a re-run
never repeats a VLM call.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import pypdfium2 as pdfium

DEFAULT_DPI = 200  # render resolution; crops and boxes are in pixels at this dpi
from doccompare.textlayer import extract_lines

BBox = list[float]  # [x0, y0, x1, y1] in page pixels, origin top-left


@dataclass
class Word:
    text: str
    bbox: BBox


@dataclass
class Line:
    text: str
    bbox: BBox
    words: list[Word] = field(default_factory=list)


@dataclass
class Page:
    doc_id: str
    index: int                     # 0-based
    width: int
    height: int
    png_path: str
    source: str                    # "textlayer" | "vlm" | "none"
    lines: list[Line] = field(default_factory=list)

    @property
    def number(self) -> int:
        return self.index + 1

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)

    def words(self) -> list[Word]:
        return [w for l in self.lines for w in l.words]


@dataclass
class Document:
    doc_id: str
    pdf_path: str
    dpi: int
    pages: list[Page]


def _page_to_json(p: Page) -> dict:
    return asdict(p)


def _page_from_json(d: dict) -> Page:
    lines = [Line(text=l["text"], bbox=l["bbox"],
                  words=[Word(**w) for w in l.get("words", [])]) for l in d.get("lines", [])]
    return Page(doc_id=d["doc_id"], index=d["index"], width=d["width"], height=d["height"],
                png_path=d["png_path"], source=d["source"], lines=lines)


def load_document(
    pdf_path: str | Path,
    work_dir: str | Path,
    *,
    doc_id: str,
    dpi: int = DEFAULT_DPI,
    page_indices: list[int] | None = None,
    ocr: Callable[[bytes], list[Line]] | None = None,
    min_text_chars: int = 25,
    log: Callable[[str], None] = print,
) -> Document:
    """Render + ground every selected page. `ocr` is called with the page PNG
    bytes for pages whose text layer is empty (scanned); None → such pages get
    no text and are compared by pixels only."""
    pdf_path = Path(pdf_path)
    work_dir = Path(work_dir)
    pages_dir = work_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(pdf_path))
    indices = page_indices if page_indices is not None else list(range(len(pdf)))
    scale = dpi / 72.0
    pages: list[Page] = []
    for idx in indices:
        png_path = pages_dir / f"p{idx + 1:03d}.png"
        meta_path = pages_dir / f"p{idx + 1:03d}.lines.json"
        if meta_path.exists():
            cached = _page_from_json(json.loads(meta_path.read_text()))
            if Path(cached.png_path).exists() and (cached.source != "none" or ocr is None):
                pages.append(cached)
                continue
        page = pdf[idx]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil().convert("RGB")
        pil.save(png_path, format="PNG", optimize=True)
        W, H = pil.size

        lines = extract_lines(page, scale=scale, rendered_size=(W, H))
        n_chars = sum(len(l.text.replace(" ", "")) for l in lines)
        if n_chars >= min_text_chars:
            source = "textlayer"
        elif ocr is not None:
            log(f"    p{idx + 1}: no text layer → VLM OCR")
            lines = ocr(png_path.read_bytes())
            source = "vlm"
        else:
            lines = []
            source = "none"
        p = Page(doc_id=doc_id, index=idx, width=W, height=H, png_path=str(png_path),
                 source=source, lines=lines)
        meta_path.write_text(json.dumps(_page_to_json(p), ensure_ascii=False))
        pages.append(p)
    return Document(doc_id=doc_id, pdf_path=str(pdf_path), dpi=dpi, pages=pages)
