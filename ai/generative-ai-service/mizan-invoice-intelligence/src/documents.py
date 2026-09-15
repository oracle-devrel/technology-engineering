"""Turn PDFs and images into model-ready invoice pages.

Author: Ali Ottoman
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pymupdf
from PIL import Image, ImageOps


@dataclass(frozen=True)
class DocumentPages:
    filename: str
    images: list[bytes]
    text_by_page: list[str]

    @property
    def page_count(self) -> int:
        return len(self.images)


def _to_jpeg(image: Image.Image, max_dimension: int, quality: int) -> bytes:
    """Normalize orientation, size, and colour before inference."""

    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, "white")
        image = Image.alpha_composite(canvas, rgba).convert("RGB")
    else:
        image = image.convert("RGB")
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def _render_pdf(
    filename: str,
    file_bytes: bytes,
    dpi: int,
    max_pages: int,
    max_dimension: int,
    quality: int,
) -> DocumentPages:
    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"{filename} is not a readable PDF.") from exc

    try:
        if document.needs_pass:
            raise ValueError(f"{filename} is password protected.")
        if document.page_count == 0:
            raise ValueError(f"{filename} has no pages.")
        if document.page_count > max_pages:
            raise ValueError(
                f"{filename} has {document.page_count} pages; this demo accepts "
                f"up to {max_pages} pages per invoice."
            )

        matrix = pymupdf.Matrix(dpi / 72, dpi / 72)
        images: list[bytes] = []
        texts: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            images.append(_to_jpeg(image, max_dimension, quality))
            texts.append(page.get_text("text").strip())
        return DocumentPages(filename=filename, images=images, text_by_page=texts)
    finally:
        document.close()


def _render_image(
    filename: str,
    file_bytes: bytes,
    max_dimension: int,
    quality: int,
) -> DocumentPages:
    try:
        image = Image.open(io.BytesIO(file_bytes))
        rendered = _to_jpeg(image, max_dimension, quality)
    except Exception as exc:
        raise ValueError(f"{filename} is not a readable image.") from exc
    return DocumentPages(filename=filename, images=[rendered], text_by_page=[""])


def load_document(
    filename: str,
    file_bytes: bytes,
    *,
    dpi: int,
    max_pages: int,
    max_dimension: int,
    quality: int,
) -> DocumentPages:
    """Load a PDF or common image type without writing it to disk."""

    if filename.lower().endswith(".pdf"):
        return _render_pdf(filename, file_bytes, dpi, max_pages, max_dimension, quality)
    return _render_image(filename, file_bytes, max_dimension, quality)
