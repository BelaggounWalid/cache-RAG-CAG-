"""Lance le backend FastAPI : python scripts/run_api.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "sapa_rag.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT / "src")],
    )
