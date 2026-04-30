"""Post-VLM: rebuild Excel V3 + (optional) build Qdrant index."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sapa_rag.config import settings
from sapa_rag.models import PageInfo
from sapa_rag.excel.exporter import build_excel
from sapa_rag.logging_setup import configure_logging, log


def main(do_index: bool = False):
    configure_logging()
    manifest = json.loads((settings.output_dir / "pages_manifest.json").read_text(encoding="utf-8"))
    infos = [PageInfo(**r) for r in manifest]

    structured = json.loads((settings.output_dir / "structured.json").read_text(encoding="utf-8"))
    log.info("structured_loaded", **{k: len(v) for k, v in structured.items()})

    out = build_excel(infos, output_path=settings.output_dir / "catalog_perf70_gti_v3.xlsx")
    print(f"Excel V3: {out}")

    if do_index:
        from sapa_rag.rag.index import build_index
        n = build_index()
        print(f"Indexed {n} chunks")


if __name__ == "__main__":
    do_index = "--index" in sys.argv
    main(do_index=do_index)
