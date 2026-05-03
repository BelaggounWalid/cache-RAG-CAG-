"""Adaptive chunking by page type.

- TEXT/MIXED: split by paragraphs into ~500 token chunks (chars≈token*4 heuristic).
- NOMENCLATURE/TABLE/PERFORMANCE/VITRAGE: 1 page = 1 chunk (preserve structure).
- COUPE/PLAN_DEBIT/PLAN_MONTAGE: 1 page = 1 chunk + image metadata.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from ..config import settings
from ..ingest.pdf_loader import iter_pages
from ..models import PageInfo, PageType

CHUNK_CHARS = 2000  # ≈ 500 tokens
OVERLAP = 200


def _load_structured_by_page() -> dict[int, list[str]]:
    """Return {page: [serialized_structured_blob, ...]} for VLM data so the RAG
    indexes the *content* of complex tables, not just the mojibake text.
    """
    p = settings.output_dir / "structured.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out: dict[int, list[str]] = {}
    for bucket, rows in data.items():
        for r in rows:
            page = r.get("page")
            if not page:
                continue
            # Serialize as compact key=value text for embeddings.
            parts = [f"[{bucket}]"]
            for k, v in r.items():
                if k in ("page", "section_l1", "section_l2") or v is None:
                    continue
                if isinstance(v, list):
                    if not v:
                        continue
                    if all(isinstance(x, dict) for x in v):
                        for x in v:
                            parts.append(
                                "("
                                + ", ".join(f"{kk}={vv}" for kk, vv in x.items() if vv is not None)
                                + ")"
                            )
                    else:
                        parts.append(f"{k}=" + ", ".join(str(x) for x in v))
                else:
                    parts.append(f"{k}={v}")
            out.setdefault(page, []).append(" ".join(parts))
    return out


@dataclass
class Chunk:
    chunk_id: str
    page: int
    section_l1: str | None
    section_l2: str | None
    page_type: str
    text: str
    codes: list[str]
    catalog: str = "perf70_gti"
    image_path: str | None = None  # for visual chunks
    is_visual: bool = False


def _split_text(text: str, page: int) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - OVERLAP
    return chunks


def chunk_corpus(infos: list[PageInfo]) -> list[Chunk]:
    by_page = {p.page_num: p for p in infos}
    structured_by_page = _load_structured_by_page()
    chunks: list[Chunk] = []
    for raw in iter_pages(settings.pdf_path):
        info = by_page.get(raw.page_num)
        if info is None:
            continue
        if info.page_type in {PageType.BLANK, PageType.COVER}:
            continue
        is_visual = info.page_type in {
            PageType.COUPE,
            PageType.PLAN_DEBIT,
            PageType.PLAN_MONTAGE,
        }
        page_image = None
        if is_visual:
            from ..cache import file_sha256

            pdf_hash = file_sha256(settings.pdf_path)[:12]
            page_image = str(settings.pages_png_dir / pdf_hash / f"p{info.page_num:04d}.png")
        if info.page_type in {PageType.TEXT, PageType.MIXED}:
            for j, piece in enumerate(_split_text(raw.text_clean, raw.page_num)):
                if not piece.strip():
                    continue
                chunks.append(
                    Chunk(
                        chunk_id=f"p{info.page_num:04d}_t{j}",
                        page=info.page_num,
                        section_l1=info.section_l1,
                        section_l2=info.section_l2,
                        page_type=info.page_type.value,
                        text=piece,
                        codes=info.codes,
                    )
                )
        else:
            # Append VLM-extracted structured rows (serialized) to make the chunk
            # actually searchable — raw PyMuPDF text on these pages is often empty
            # or jumbled.
            structured_blobs = structured_by_page.get(info.page_num, [])
            enriched = raw.text_clean
            if structured_blobs:
                enriched = (
                    raw.text_clean
                    + "\n\n--- DONNÉES STRUCTURÉES ---\n"
                    + "\n".join(structured_blobs)
                ).strip()
            chunks.append(
                Chunk(
                    chunk_id=f"p{info.page_num:04d}",
                    page=info.page_num,
                    section_l1=info.section_l1,
                    section_l2=info.section_l2,
                    page_type=info.page_type.value,
                    text=enriched,
                    codes=info.codes,
                    image_path=page_image,
                    is_visual=is_visual,
                )
            )
    out = settings.output_dir / "chunks.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    return chunks
