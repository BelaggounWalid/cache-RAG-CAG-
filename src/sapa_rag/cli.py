"""CLI: `python -m sapa_rag.cli {classify|excel|phase01|vlm|all}`."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from .config import settings
from .excel.exporter import build_excel
from .ingest.pipeline import run_classification, summarize
from .logging_setup import configure_logging
from .models import PageInfo, PageType

app = typer.Typer(help="SAPA RAG — Phase 0/1/2 CLI")
console = Console()
configure_logging()


@app.command()
def classify():
    """Classify every PDF page and dump pages_manifest.json."""
    infos = run_classification()
    s = summarize(infos)
    console.print_json(data=s)


@app.command()
def excel():
    """Build the Excel snapshot from the existing pages_manifest.json."""
    manifest = settings.output_dir / "pages_manifest.json"
    if not manifest.exists():
        console.print("[red]No manifest found. Run `classify` first.[/red]")
        raise typer.Exit(1)
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    infos = [PageInfo(**r) for r in raw]
    out = build_excel(infos)
    console.print(f"[green]Excel written:[/] {out}")


@app.command()
def phase01():
    """Run classification + Excel export end-to-end."""
    infos = run_classification()
    s = summarize(infos)
    table = Table(title="Pages by type")
    table.add_column("Type")
    table.add_column("Count", justify="right")
    for t, n in sorted(s["by_type"].items(), key=lambda x: -x[1]):
        table.add_row(t, str(n))
    console.print(table)
    console.print(f"Unique codes: [bold]{s['unique_codes']}[/]")
    out = build_excel(infos)
    console.print(f"[green]Excel written:[/] {out}")


@app.command()
def vlm(
    types: str | None = typer.Option(
        None,
        help="Comma-sep page types: nomenclature,performance,vitrage,coupe. Default: all four.",
    ),
    limit: int | None = typer.Option(None, help="Cap on pages (debug)"),
):
    """Run the VLM extractor on selected page-types and save structured.json."""
    from .extract_structured import run as run_vlm

    selected: set[PageType] | None = None
    if types:
        selected = {PageType(t.strip()) for t in types.split(",")}
    out = run_vlm(types=selected, limit=limit)
    console.print_json(data={k: len(v) for k, v in out.items()})


@app.command()
def all(
    vlm_limit: int | None = typer.Option(None, help="Cap VLM pages (cost control)"),
):
    """Phase 0 + Phase 1 + Phase 2 (VLM) + Excel rebuild."""
    infos = run_classification()
    s = summarize(infos)
    console.print_json(data=s)
    from .extract_structured import run as run_vlm

    run_vlm(limit=vlm_limit)
    out = build_excel(infos)
    console.print(f"[green]Excel written:[/] {out}")


@app.command()
def chunk():
    """Build chunks.jsonl for the RAG index."""
    from .rag.chunker import chunk_corpus

    manifest = settings.output_dir / "pages_manifest.json"
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    infos = [PageInfo(**r) for r in raw]
    chunks = chunk_corpus(infos)
    console.print(f"[green]Chunks:[/] {len(chunks)} -> {settings.output_dir / 'chunks.jsonl'}")


@app.command()
def index():
    """Build Qdrant index from chunks.jsonl (dense+sparse)."""
    from .rag.index import build_index

    n = build_index()
    console.print(f"[green]Indexed:[/] {n} chunks")


@app.command()
def ask(question: str):
    """One-shot Q&A on the indexed catalog."""
    from .rag.qa import answer

    res = answer(question)
    console.print(f"[bold]Routing:[/] {res['routing']}")
    console.print()
    console.print(res["answer"])
    console.print()
    console.print("[bold]Citations:[/]")
    for c in res["citations"]:
        console.print(
            f"  - p.{c['page']} | {c.get('section_l1')} > {c.get('section_l2')} | score={c.get('score'):.3f}"
        )


if __name__ == "__main__":
    app()
