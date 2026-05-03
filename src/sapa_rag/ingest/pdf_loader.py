"""PDF loader — Docling primary (layout-aware), PyMuPDF for rasterization & TOC.

Public surface kept identical so the rest of the pipeline is unchanged:
  - iter_pages(pdf_path) → yields RawPage(page_num, text, text_clean, n_images, n_drawings)
  - get_toc(pdf_path) → list[(level, title, page)]

Implementation: each call goes through Docling for *text* (markdown-style),
and falls back to PyMuPDF for the geometry counters (n_images / n_drawings)
that the page classifier relies on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import fitz

from ..logging_setup import log
from . import docling_parser as dp

_REPL = "�"


@dataclass
class RawPage:
    page_num: int
    text: str
    text_clean: str
    n_images: int
    n_drawings: int

    @property
    def is_likely_blank(self) -> bool:
        return len(self.text_clean) < 20 and self.n_drawings < 5 and self.n_images == 0


def clean_text(t: str) -> str:
    t = t.replace(_REPL, "?")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


@lru_cache(maxsize=4)
def _parse_cached(pdf_path_str: str):
    pages, toc = dp.parse_pdf(Path(pdf_path_str))
    return pages, toc


def _pymupdf_geometry(pdf_path: Path) -> dict[int, tuple[int, int]]:
    doc = fitz.open(pdf_path)
    out: dict[int, tuple[int, int]] = {}
    try:
        for i in range(doc.page_count):
            p = doc[i]
            out[i + 1] = (len(p.get_images()), len(p.get_drawings()))
    finally:
        doc.close()
    return out


def iter_pages(pdf_path: Path):
    pdf_path = Path(pdf_path)
    log.info("loader_start", pdf=str(pdf_path))
    try:
        pages, _toc = _parse_cached(str(pdf_path))
    except Exception as exc:
        log.warning("docling_failed_fallback_pymupdf", err=str(exc))
        yield from _iter_pages_pymupdf(pdf_path)
        return

    geom = _pymupdf_geometry(pdf_path)
    pymu_text: dict[int, str] = {}
    for sp in pages:
        n_img, n_draw = geom.get(sp.page, (0, 0))
        text = sp.text_with_tables  # tables already serialized in markdown
        # Per-page fallback: if Docling produced no text but the page is not blank,
        # backfill from PyMuPDF so we don't lose the content entirely.
        if len(text.strip()) < 10 and (n_draw > 0 or n_img > 0):
            if not pymu_text:
                pymu_text = _pymupdf_all_text(pdf_path)
            text = pymu_text.get(sp.page, text)
        yield RawPage(
            page_num=sp.page,
            text=text,
            text_clean=clean_text(text),
            n_images=n_img,
            n_drawings=n_draw,
        )


def _iter_pages_pymupdf(pdf_path: Path):
    """Pure-PyMuPDF iteration (used when Docling cannot run at all)."""
    doc = fitz.open(pdf_path)
    try:
        for i in range(doc.page_count):
            p = doc[i]
            txt = p.get_text() or ""
            yield RawPage(
                page_num=i + 1,
                text=txt,
                text_clean=clean_text(txt),
                n_images=len(p.get_images()),
                n_drawings=len(p.get_drawings()),
            )
    finally:
        doc.close()


def _pymupdf_all_text(pdf_path: Path) -> dict[int, str]:
    doc = fitz.open(pdf_path)
    try:
        return {i + 1: doc[i].get_text() or "" for i in range(doc.page_count)}
    finally:
        doc.close()


def get_toc(pdf_path: Path) -> list[tuple[int, str, int]]:
    _pages, toc = _parse_cached(str(Path(pdf_path)))
    return toc
