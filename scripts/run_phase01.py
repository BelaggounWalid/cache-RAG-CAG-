"""Convenience launcher: python scripts/run_phase01.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sapa_rag.cli import app  # noqa

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "phase01"]
    app()
