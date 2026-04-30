"""Docling-based parser: layout-aware text + structured tables.

Docling produces a DoclingDocument tree where tables are first-class objects
(rows × cells), unlike PyMuPDF which returns positional text fragments.

Why we kept PyMuPDF:
  - For *rasterization* only (page → PNG for VLM input). PyMuPDF is fast and
    gives identical results to anything else for that task.
  - For TOC reading (`doc.get_toc()`), which is solid.
  - As a fallback if Docling fails on a corrupt page.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..logging_setup import log


@dataclass
class TableCell:
    row: int
    col: int
    text: str
    row_span: int = 1
    col_span: int = 1


@dataclass
class StructuredTable:
    page: int
    n_rows: int
    n_cols: int
    cells: list[TableCell] = field(default_factory=list)

    def to_markdown(self) -> str:
        if not self.cells:
            return ""
        grid: list[list[str]] = [["" for _ in range(self.n_cols)] for _ in range(self.n_rows)]
        for c in self.cells:
            if 0 <= c.row < self.n_rows and 0 <= c.col < self.n_cols:
                grid[c.row][c.col] = c.text.replace("\n", " ").strip()
        rows = ["| " + " | ".join(r) + " |" for r in grid]
        sep = "| " + " | ".join(["---"] * self.n_cols) + " |"
        if rows:
            rows.insert(1, sep)
        return "\n".join(rows)


@dataclass
class StructuredPage:
    page: int
    text: str                    # Markdown-style serialization (headings, paragraphs, lists)
    tables: list[StructuredTable] = field(default_factory=list)

    @property
    def text_with_tables(self) -> str:
        if not self.tables:
            return self.text
        parts = [self.text]
        for i, t in enumerate(self.tables, 1):
            parts.append(f"\n--- TABLE {i} (p.{t.page}) ---\n{t.to_markdown()}")
        return "\n".join(parts)


@lru_cache(maxsize=1)
def _converter():
    """Lazily build a Docling converter. Heavy import (torch + layout model).

    We use the *fast* TableFormer model — ~4x lighter on RAM than 'accurate',
    crucial for 480-page catalogs with vector-heavy pages on consumer CPU.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

    pipeline = PdfPipelineOptions()
    pipeline.do_ocr = False  # PDF is native text, no OCR needed
    pipeline.do_table_structure = True
    pipeline.table_structure_options.do_cell_matching = True
    pipeline.table_structure_options.mode = TableFormerMode.FAST

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)},
    )


SLICE_SIZE = 25  # pages per Docling pass (memory cap)


def _split_pdf(pdf_path: Path, pages: list[int]) -> Path:
    """Build a temp PDF containing only the given page numbers (1-indexed)."""
    import fitz, tempfile
    src = fitz.open(pdf_path)
    dst = fitz.open()
    try:
        for p in pages:
            dst.insert_pdf(src, from_page=p - 1, to_page=p - 1)
        tmp = Path(tempfile.gettempdir()) / f"docling_slice_{pages[0]}_{pages[-1]}.pdf"
        dst.save(str(tmp))
        return tmp
    finally:
        src.close()
        dst.close()


def parse_pdf(pdf_path: Path) -> tuple[list[StructuredPage], list[tuple[int, str, int]]]:
    """Run Docling on the full PDF. Returns (pages, toc).

    Disk-cached: a SHA256 of the PDF bytes is the cache key. Once parsed, the
    structured representation is reused across runs — Docling's slowness is
    paid only on a brand-new PDF.

    TOC is filled from PyMuPDF (Docling does not expose it cleanly yet).
    """
    from ..cache import file_sha256, cache as _disk_cache

    pdf_hash = file_sha256(pdf_path)[:16]
    cache_key = f"docling:v1:{pdf_hash}"
    cached = _disk_cache.get(cache_key)
    if cached is not None:
        log.info("docling_cache_hit", pdf=str(pdf_path), key=cache_key)
        pages = [_page_from_dict(p) for p in cached["pages"]]
        toc = [tuple(t) for t in cached["toc"]]
        return pages, toc

    log.info("docling_parse_start", pdf=str(pdf_path))
    import fitz, gc
    src = fitz.open(pdf_path)
    total = src.page_count
    src.close()

    conv = _converter()
    by_page: dict[int, StructuredPage] = {}

    # Process in slices to keep RAM bounded.
    slice_starts = list(range(1, total + 1, SLICE_SIZE))
    for s_idx, start in enumerate(slice_starts, 1):
        end = min(start + SLICE_SIZE - 1, total)
        page_nums = list(range(start, end + 1))
        log.info("docling_slice", slice=s_idx, total=len(slice_starts), pages=f"{start}-{end}")

        slice_pdf = _split_pdf(pdf_path, page_nums)
        try:
            try:
                result = conv.convert(str(slice_pdf))
                doc = result.document
            except Exception as exc:
                log.error("docling_slice_failed", slice=s_idx, err=str(exc))
                continue

            # Map slice-local page number (1..N) back to global.
            local_to_global = {i + 1: page_nums[i] for i in range(len(page_nums))}

            for p in doc.pages.values():
                gpage = local_to_global.get(p.page_no, p.page_no)
                by_page.setdefault(gpage, StructuredPage(page=gpage, text=""))

            text_buffers: dict[int, list[str]] = {pn: [] for pn in by_page}
            for item, _level in doc.iterate_items():
                prov = getattr(item, "prov", None) or []
                if not prov:
                    continue
                gpage = local_to_global.get(prov[0].page_no, prov[0].page_no)
                page = by_page.setdefault(gpage, StructuredPage(page=gpage, text=""))

                cls = type(item).__name__
                if cls == "TextItem":
                    text_buffers.setdefault(gpage, []).append(item.text)
                elif cls == "SectionHeaderItem":
                    level = getattr(item, "level", 1) or 1
                    text_buffers.setdefault(gpage, []).append(f"{'#' * min(level, 6)} {item.text}")
                elif cls == "ListItem":
                    text_buffers.setdefault(gpage, []).append(f"- {item.text}")
                elif cls == "TableItem":
                    rows = item.data.num_rows if item.data else 0
                    cols = item.data.num_cols if item.data else 0
                    cells = []
                    if item.data and item.data.table_cells:
                        for tc in item.data.table_cells:
                            cells.append(
                                TableCell(
                                    row=tc.start_row_offset_idx,
                                    col=tc.start_col_offset_idx,
                                    text=tc.text or "",
                                    row_span=tc.end_row_offset_idx - tc.start_row_offset_idx,
                                    col_span=tc.end_col_offset_idx - tc.start_col_offset_idx,
                                )
                            )
                    page.tables.append(StructuredTable(page=gpage, n_rows=rows, n_cols=cols, cells=cells))

            for pn, buf in text_buffers.items():
                if buf:
                    cur = by_page.get(pn)
                    if cur is None:
                        continue
                    cur.text = _clean(("\n".join(buf)) if not cur.text else (cur.text + "\n" + "\n".join(buf)))
        finally:
            try:
                slice_pdf.unlink()
            except Exception:
                pass
            gc.collect()

    log.info("docling_parse_done", n_pages=len(by_page))
    pages = sorted(by_page.values(), key=lambda p: p.page)

    # TOC via PyMuPDF (kept here because Docling's TOC story is weak as of 2.x).
    import fitz
    fdoc = fitz.open(pdf_path)
    try:
        toc = [(lvl, _clean(title), pg) for lvl, title, pg in fdoc.get_toc()]
    finally:
        fdoc.close()

    # Persist to disk cache so the next run is instantaneous.
    payload = {
        "pages": [_page_to_dict(p) for p in pages],
        "toc": [list(t) for t in toc],
    }
    _disk_cache.set(cache_key, payload)
    log.info("docling_cache_write", key=cache_key, pages=len(pages))

    return pages, toc


def _page_to_dict(p: StructuredPage) -> dict:
    return {
        "page": p.page,
        "text": p.text,
        "tables": [
            {
                "page": t.page,
                "n_rows": t.n_rows,
                "n_cols": t.n_cols,
                "cells": [
                    {"row": c.row, "col": c.col, "text": c.text,
                     "row_span": c.row_span, "col_span": c.col_span}
                    for c in t.cells
                ],
            }
            for t in p.tables
        ],
    }


def _page_from_dict(d: dict) -> StructuredPage:
    return StructuredPage(
        page=d["page"],
        text=d["text"],
        tables=[
            StructuredTable(
                page=t["page"],
                n_rows=t["n_rows"],
                n_cols=t["n_cols"],
                cells=[TableCell(**c) for c in t["cells"]],
            )
            for t in d["tables"]
        ],
    )


def _clean(t: str) -> str:
    t = t.replace(" ", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
