"""Rasterize PDF pages to PNG (idempotent, hash-named)."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..cache import file_sha256
from ..config import settings
from ..logging_setup import log


def rasterize_pages(
    pages: list[int] | None = None,
    dpi: int | None = None,
    pdf_path: Path | None = None,
) -> dict[int, Path]:
    """Render specified pages (1-indexed) to PNG. Returns {page: png_path}."""
    pdf = pdf_path or settings.pdf_path
    dpi = dpi or settings.png_dpi
    pdf_hash = file_sha256(pdf)[:12]
    out_dir = settings.pages_png_dir / pdf_hash
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf)
    target = pages or list(range(1, doc.page_count + 1))
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    out: dict[int, Path] = {}
    try:
        for pn in target:
            png = out_dir / f"p{pn:04d}.png"
            out[pn] = png
            if png.exists():
                continue
            pix = doc[pn - 1].get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(png))
        log.info("rasterized", pages=len(target), dir=str(out_dir), dpi=dpi)
    finally:
        doc.close()
    return out
