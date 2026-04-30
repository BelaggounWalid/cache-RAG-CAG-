"""Phase 2: VLM-driven structured extraction on page-typed images."""
from __future__ import annotations
import json
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

from .config import settings
from .models import PageInfo, PageType
from .ingest.rasterize import rasterize_pages
from .vlm.extractor import extract
from .vlm.schemas import (
    ProfileExtraction,
    PerformanceExtraction,
    VitrageExtraction,
    CoupeExtraction,
    PlanDebitExtraction,
)
from .logging_setup import log

console = Console()


PAGETYPE_TO_SCHEMA = {
    PageType.NOMENCLATURE: ProfileExtraction,
    PageType.PERFORMANCE: PerformanceExtraction,
    PageType.VITRAGE: VitrageExtraction,
    PageType.COUPE: CoupeExtraction,
    PageType.PLAN_DEBIT: PlanDebitExtraction,
}


def load_manifest() -> list[PageInfo]:
    manifest = settings.output_dir / "pages_manifest.json"
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    return [PageInfo(**r) for r in raw]


def select_pages(infos: list[PageInfo], types: set[PageType]) -> list[PageInfo]:
    return [p for p in infos if p.page_type in types]


def run(types: set[PageType] | None = None, limit: int | None = None) -> dict:
    """Extract structured rows from VLM. Returns dict of lists per schema name."""
    infos = load_manifest()
    target_types = types or set(PAGETYPE_TO_SCHEMA.keys())
    selected = [p for p in infos if p.page_type in target_types]
    if limit:
        selected = selected[:limit]

    page_nums = [p.page_num for p in selected]
    log.info("rasterize_target", n=len(page_nums))
    pngs = rasterize_pages(page_nums)

    # Merge with previous results so re-runs are additive (cache makes them cheap).
    prev_path = settings.output_dir / "structured.json"
    if prev_path.exists():
        out = json.loads(prev_path.read_text(encoding="utf-8"))
        out.setdefault("plan_debit", [])
    else:
        out = {
            "profiles": [],
            "performance": [],
            "vitrage": [],
            "coupes": [],
            "plan_debit": [],
        }
    schema_to_bucket = {
        ProfileExtraction: "profiles",
        PerformanceExtraction: "performance",
        VitrageExtraction: "vitrage",
        CoupeExtraction: "coupes",
        PlanDebitExtraction: "plan_debit",
    }
    # Track which (page, schema) combos we already have to avoid duplicates.
    seen_keys = {(r.get("page"), bucket) for bucket, rows in out.items() for r in rows if isinstance(r, dict)}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("VLM extraction", total=len(selected))
        for p in selected:
            schema_cls = PAGETYPE_TO_SCHEMA[p.page_type]
            try:
                result = extract(pngs[p.page_num], schema_cls)
            except Exception as exc:
                log.error("vlm_fail", page=p.page_num, err=str(exc))
                progress.advance(task)
                continue
            bucket = schema_to_bucket[schema_cls]
            # Drop any previous rows for this (page, bucket) — additive but page-replacing.
            out[bucket] = [r for r in out[bucket] if r.get("page") != p.page_num]
            for item in (
                getattr(result, "items", None)
                or getattr(result, "coupes", None)
                or []
            ):
                d = item.model_dump()
                d["page"] = p.page_num
                d["section_l1"] = p.section_l1
                d["section_l2"] = p.section_l2
                out[bucket].append(d)
            progress.advance(task)

    out_path = settings.output_dir / "structured.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("structured_saved", path=str(out_path), counts={k: len(v) for k, v in out.items()})
    return out
