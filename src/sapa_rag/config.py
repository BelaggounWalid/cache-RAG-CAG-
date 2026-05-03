from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
# Load .env explicitly first so env vars are available regardless of CWD.
# override=True so the .env wins over an empty env var inherited from the shell.
load_dotenv(ROOT / ".env", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = ""
    pdf_path: Path = ROOT / "pdfs" / "perf70_gti_kpfppfr_04_2023.pdf"
    output_dir: Path = ROOT / "data" / "output"
    pages_png_dir: Path = ROOT / "data" / "pages_png"
    png_dpi: int = 200

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pages_png_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
