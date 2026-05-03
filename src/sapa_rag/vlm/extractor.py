"""Claude Sonnet 4.6 VLM extractor with strict tool-use schemas, retries, and cache."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TypeVar

from anthropic import Anthropic
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..cache import cached_call, file_sha256
from ..config import settings
from ..logging_setup import log
from .schemas import (
    CoupeExtraction,
    PerformanceExtraction,
    PlanDebitExtraction,
    ProfileExtraction,
    VitrageExtraction,
)

MODEL = "claude-sonnet-4-5-20250929"  # Latest Sonnet at writing time. Override via env if newer.

T = TypeVar("T", bound=BaseModel)

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _encode_image(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.standard_b64encode(data).decode(),
        },
    }


def _pydantic_to_tool(schema_cls: type[BaseModel], name: str, desc: str) -> dict:
    schema = schema_cls.model_json_schema()
    return {
        "name": name,
        "description": desc,
        "input_schema": schema,
    }


PROMPTS = {
    ProfileExtraction: (
        "extract_profiles",
        "Extrait la liste des profilés visibles sur cette page de catalogue technique aluminium SAPA. "
        "Pour chaque profilé : code (format S* + chiffres, ex: SP24806), désignation, famille (Dormant/Ouvrant/Traverse/Plinthe/Seuil/Parclose/Joint), "
        "et page_ref si elle est indiquée à côté du code (NR signifie 'numéro de référence', le nombre qui suit est la page).",
        "Tu vois une page d'un catalogue technique de menuiserie aluminium. "
        "Liste exhaustivement chaque profilé/référence visible. Si un champ est invisible, mets null.",
    ),
    PerformanceExtraction: (
        "extract_performance",
        "Extrait les performances thermiques (Ud, Uf, Ug, Psi) et les configurations associées (série, châssis, dormant, ouvrant, parclose, dimensions L×H, isolation, intercalaire). "
        "Une page contient typiquement plusieurs sous-tableaux : un sous-tableau = un item.",
        "Tu vois une page de performances thermiques d'un catalogue aluminium SAPA. "
        "Pour chaque tableau Ug→Ud, génère un item avec la configuration ET les valeurs Uf_moyen / Ud associés. "
        "Si Ud varie selon Ug, prends la valeur médiane (Ug=1.4) ou liste-les en plusieurs items.",
    ),
    VitrageExtraction: (
        "extract_vitrage",
        "Extrait le tableau de vitrage : pour chaque épaisseur G (mm), donne le code parclose, code parclose alternatif (variantes), code clip, cote X (mm), type (Standard/Tubulaire).",
        "Tu vois la page Tableau de vitrage. Une ligne du tableau = un item. Mets null si une cellule est vide.",
    ),
    CoupeExtraction: (
        "extract_coupes",
        "Décrit cette page de coupes techniques : configuration (ex: 'Porte 1 vantail ouverture intérieure avec seuil PMR'), codes produits visibles, cotes principales annotées, et une légende d'une phrase.",
        "Tu vois une page de coupes techniques. Identifie chaque coupe (souvent 1 ou 2 par page) et liste ce qui est annoté.",
    ),
    PlanDebitExtraction: (
        "extract_plan_debit",
        "Extrait le 'Plan de débits' complet visible sur cette page : "
        "configuration (titre de la porte), code plan (F70-CMP-...), "
        "et chaque tableau de la page : DORMANT, OUVRANT, DIVERS, PARCLOSE, ACCESSOIRES, JOINT. "
        "Pour chaque ligne, extrait code, désignation et quantité/débit (formule type 'L', 'H', 'L-109', '2L+4H', '1 paire'). "
        "Important : extrait aussi le tableau 'DIMENSION DE VITRAGE' (cote L, cote H, quantité).",
        "Tu vois une page 'Plans de débits' du catalogue SAPA. "
        "Génère 1 item par configuration de porte présente sur la page (souvent 1 ou 2). "
        "Sois EXHAUSTIF : chaque ligne du tableau doit apparaître. Si une cellule est vide, mets null.",
    ),
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call(image_path: Path, schema_cls: type[T]) -> T:
    tool_name, tool_desc, user_prompt = PROMPTS[schema_cls]
    tool = _pydantic_to_tool(schema_cls, tool_name, tool_desc)
    client = get_client()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[
            {
                "role": "user",
                "content": [
                    _encode_image(image_path),
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == tool_name:
            return schema_cls.model_validate(block.input)
    raise RuntimeError(f"No tool_use block in response for {tool_name}")


def extract(image_path: Path, schema_cls: type[T]) -> T:
    """Cached, retried VLM call."""
    img_hash = file_sha256(image_path)[:12]
    key = (img_hash, schema_cls.__name__, MODEL)

    def _do() -> dict:
        log.info("vlm_call", page=image_path.name, schema=schema_cls.__name__)
        result = _call(image_path, schema_cls)
        return result.model_dump()

    raw = cached_call("vlm", key, _do)
    return schema_cls.model_validate(raw)
