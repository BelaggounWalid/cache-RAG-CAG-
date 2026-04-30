"""Phase 0 pipeline: classify all pages, extract codes, persist a manifest."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from ..config import settings
from ..models import PageInfo, PageType
from .pdf_loader import iter_pages, get_toc
from .sections import SectionMap
from .classify import classify_page
from .codes import extract_codes

console = Console()


def run_classification(pdf_path: Path | None = None) -> list[PageInfo]:
    settings.ensure_dirs()
    pdf = pdf_path or settings.pdf_path
    console.log(f"[bold]Loading[/] {pdf}")
    toc = get_toc(pdf)
    console.log(f"TOC entries: {len(toc)}")

    # Need total page count to build section map; iter once to count cheaply
    pages_raw = list(iter_pages(pdf))
    total = len(pages_raw)
    console.log(f"Total pages: {total}")

    sec_map = SectionMap.build(toc, total)

    infos: list[PageInfo] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Classifying pages", total=total)
        for raw in pages_raw:
            l1, l2 = sec_map.get(raw.page_num)
            ptype = classify_page(raw, l1, l2)
            codes = extract_codes(raw.text_clean)
            infos.append(
                PageInfo(
                    page_num=raw.page_num,
                    text_len=len(raw.text_clean),
                    n_images=raw.n_images,
                    n_drawings=raw.n_drawings,
                    section_l1=l1,
                    section_l2=l2,
                    page_type=ptype,
                    codes=codes,
                )
            )
            progress.advance(task)

    out = settings.output_dir / "pages_manifest.json"
    out.write_text(
        json.dumps([p.model_dump(mode="json") for p in infos], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    console.log(f"[green]Wrote[/] {out}")
    return infos


def summarize(infos: Iterable[PageInfo]) -> dict:
    by_type: dict[str, int] = {}
    code_set: set[str] = set()
    for p in infos:
        by_type[p.page_type.value] = by_type.get(p.page_type.value, 0) + 1
        code_set.update(p.codes)
    return {
        "total_pages": sum(by_type.values()),
        "by_type": by_type,
        "unique_codes": len(code_set),
    }
