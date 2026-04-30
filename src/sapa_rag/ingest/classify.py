"""Classify each PDF page into a PageType using TOC section + heuristics."""
from __future__ import annotations
from ..models import PageType
from .pdf_loader import RawPage


# Substrings (lowercased) used to override / refine TOC-based classification.
KW_PERFORMANCE = ("performance thermique", "coefficient ud", "uf moyen", "isolation thermique")
KW_VITRAGE = ("tableau de vitrage", "parclose", "vitrage")
KW_NOMENCLATURE = ("récapitulatif des profil", "recapitulatif des profil", "liste de symbol")
KW_PLAN_MONTAGE = ("plans de montage", "directives", "drainage", "usinage")
KW_PLAN_DEBIT = ("plans de débits", "plans de debits", "plan de débit", "plan de debit")
KW_COUPE = ("coupe ", "coupes", "f70-sec", "?f70-sec")


def _section_match(l1: str | None, l2: str | None, keys: tuple[str, ...]) -> bool:
    blob = f"{(l1 or '').lower()} || {(l2 or '').lower()}"
    return any(k in blob for k in keys)


def classify_page(
    raw: RawPage,
    section_l1: str | None,
    section_l2: str | None,
) -> PageType:
    if raw.page_num <= 2:
        return PageType.COVER
    if raw.is_likely_blank:
        return PageType.BLANK

    text_lower = raw.text_clean.lower()
    l1l = (section_l1 or "").lower()

    # Strongest signals first: explicit keywords in page text
    if any(k in text_lower for k in KW_PERFORMANCE):
        return PageType.PERFORMANCE
    if any(k in text_lower for k in KW_VITRAGE) and "tableau" in text_lower:
        return PageType.VITRAGE
    if any(k in text_lower for k in KW_NOMENCLATURE):
        return PageType.NOMENCLATURE

    # TOC-based routing
    if "plans de d" in l1l or _section_match(section_l1, section_l2, KW_PLAN_DEBIT):
        return PageType.PLAN_DEBIT
    if "plans de montage" in l1l or "quincaillerie" in l1l and "montage" in l1l:
        return PageType.PLAN_MONTAGE
    if l1l.startswith("coupes") or _section_match(section_l1, section_l2, KW_COUPE):
        return PageType.COUPE
    if "fiche technique" in l1l or "profilés divers" in l1l or "profiles divers" in l1l:
        # Usually a profile sheet: drawing-heavy + few codes
        if raw.n_drawings > 200 or raw.n_images >= 1:
            return PageType.NOMENCLATURE
        return PageType.MIXED
    if "outils" in l1l:
        return PageType.PLAN_MONTAGE  # tooling pages behave like assembly diagrams
    if "isolation" in l1l or "vitrage" in l1l:
        return PageType.VITRAGE
    if "accessoires" in l1l or "choix de la quincaillerie" in l1l:
        # Tables of references
        return PageType.TABLE
    if "informations g" in l1l:  # 'Informations générales'
        return PageType.TEXT
    if "annexes" in l1l:
        return PageType.TEXT

    # Fallbacks based on geometry
    if raw.n_drawings > 5000:
        return PageType.COUPE
    if len(raw.text_clean) > 800:
        return PageType.TEXT
    return PageType.MIXED
