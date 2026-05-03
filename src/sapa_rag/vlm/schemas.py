"""Strict Pydantic schemas for VLM-extracted records."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileItem(BaseModel):
    code: str = Field(..., description="Code produit, ex: SP24806")
    designation: str | None = Field(None, description="Nom court / désignation")
    famille: str | None = Field(None, description="Dormant, Ouvrant, Traverse, Plinthe, Seuil, ...")
    page_ref: int | None = Field(None, description="Page de référence détaillée si indiquée")


class ProfileExtraction(BaseModel):
    items: list[ProfileItem] = Field(default_factory=list)


class PerformanceItem(BaseModel):
    serie: str | None = None
    chassis: str | None = None
    dormant_code: str | None = None
    ouvrant_code: str | None = None
    parclose_code: str | None = None
    largeur_m: float | None = None
    hauteur_m: float | None = None
    isolation: str | None = None
    intercalaire: str | None = None
    psi: float | None = None
    ug: float | None = None
    ud: float | None = None
    uf_moyen: float | None = None


class PerformanceExtraction(BaseModel):
    items: list[PerformanceItem] = Field(default_factory=list)


class VitrageItem(BaseModel):
    epaisseur_mm: float | None = Field(None, description="Épaisseur de vitrage G en mm")
    parclose_code: str | None = None
    parclose_code_alt: str | None = None
    clip_code: str | None = None
    x_mm: float | None = Field(None, description="Cote X en mm")
    type_parclose: str | None = Field(None, description="Standard, Tubulaire, ...")


class VitrageExtraction(BaseModel):
    items: list[VitrageItem] = Field(default_factory=list)


class CoupeAnnotation(BaseModel):
    configuration: str | None = Field(None, description="Ex: Porte 1 vantail ouverture intérieure")
    codes_visibles: list[str] = Field(default_factory=list)
    cotes_principales: list[str] = Field(default_factory=list)
    legende: str | None = None


class CoupeExtraction(BaseModel):
    coupes: list[CoupeAnnotation] = Field(default_factory=list)


class AccessoireQty(BaseModel):
    code: str | None = None  # parfois absent (ligne sans code, ex: "Vis 4.2 x 16")
    designation: str | None = None
    qte: str | None = None  # peut être "1 paire", "2L+4H", "48", etc.


class PlanDebitItem(BaseModel):
    """Une ligne du tableau 'Plans de débits' pour UNE configuration de porte."""

    configuration: str | None = Field(
        None, description="Ex: Porte 1 vantail ouverture intérieure avec seuil PMR"
    )
    code_plan: str | None = Field(None, description="Référence plan ex: F70-CMP-040-1")
    profiles_dormant: list[AccessoireQty] = Field(
        default_factory=list, description="Lignes section DORMANT (code, désignation, débit L/H)"
    )
    profiles_ouvrant: list[AccessoireQty] = Field(default_factory=list)
    profiles_divers: list[AccessoireQty] = Field(
        default_factory=list, description="DIVERS: rejet d'eau, seuil PMR, etc."
    )
    parclose: list[AccessoireQty] = Field(
        default_factory=list, description="Lignes section PARCLOSE"
    )
    accessoires: list[AccessoireQty] = Field(default_factory=list)
    joints: list[AccessoireQty] = Field(default_factory=list)
    dimension_vitrage_l: str | None = Field(
        None, description="Cote L de la 'DIMENSION DE VITRAGE', ex: 'L-276'"
    )
    dimension_vitrage_h: str | None = Field(
        None, description="Cote H de la 'DIMENSION DE VITRAGE', ex: 'H-233.5'"
    )
    quantite_vitrage: int | None = None


class PlanDebitExtraction(BaseModel):
    items: list[PlanDebitItem] = Field(default_factory=list)
