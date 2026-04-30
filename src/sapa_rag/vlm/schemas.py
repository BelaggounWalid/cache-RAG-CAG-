"""Strict Pydantic schemas for VLM-extracted records."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class ProfileItem(BaseModel):
    code: str = Field(..., description="Code produit, ex: SP24806")
    designation: Optional[str] = Field(None, description="Nom court / désignation")
    famille: Optional[str] = Field(None, description="Dormant, Ouvrant, Traverse, Plinthe, Seuil, ...")
    page_ref: Optional[int] = Field(None, description="Page de référence détaillée si indiquée")


class ProfileExtraction(BaseModel):
    items: list[ProfileItem] = Field(default_factory=list)


class PerformanceItem(BaseModel):
    serie: Optional[str] = None
    chassis: Optional[str] = None
    dormant_code: Optional[str] = None
    ouvrant_code: Optional[str] = None
    parclose_code: Optional[str] = None
    largeur_m: Optional[float] = None
    hauteur_m: Optional[float] = None
    isolation: Optional[str] = None
    intercalaire: Optional[str] = None
    psi: Optional[float] = None
    ug: Optional[float] = None
    ud: Optional[float] = None
    uf_moyen: Optional[float] = None


class PerformanceExtraction(BaseModel):
    items: list[PerformanceItem] = Field(default_factory=list)


class VitrageItem(BaseModel):
    epaisseur_mm: Optional[float] = Field(None, description="Épaisseur de vitrage G en mm")
    parclose_code: Optional[str] = None
    parclose_code_alt: Optional[str] = None
    clip_code: Optional[str] = None
    x_mm: Optional[float] = Field(None, description="Cote X en mm")
    type_parclose: Optional[str] = Field(None, description="Standard, Tubulaire, ...")


class VitrageExtraction(BaseModel):
    items: list[VitrageItem] = Field(default_factory=list)


class CoupeAnnotation(BaseModel):
    configuration: Optional[str] = Field(None, description="Ex: Porte 1 vantail ouverture intérieure")
    codes_visibles: list[str] = Field(default_factory=list)
    cotes_principales: list[str] = Field(default_factory=list)
    legende: Optional[str] = None


class CoupeExtraction(BaseModel):
    coupes: list[CoupeAnnotation] = Field(default_factory=list)


class AccessoireQty(BaseModel):
    code: Optional[str] = None  # parfois absent (ligne sans code, ex: "Vis 4.2 x 16")
    designation: Optional[str] = None
    qte: Optional[str] = None  # peut être "1 paire", "2L+4H", "48", etc.


class PlanDebitItem(BaseModel):
    """Une ligne du tableau 'Plans de débits' pour UNE configuration de porte."""
    configuration: Optional[str] = Field(None, description="Ex: Porte 1 vantail ouverture intérieure avec seuil PMR")
    code_plan: Optional[str] = Field(None, description="Référence plan ex: F70-CMP-040-1")
    profiles_dormant: list[AccessoireQty] = Field(default_factory=list, description="Lignes section DORMANT (code, désignation, débit L/H)")
    profiles_ouvrant: list[AccessoireQty] = Field(default_factory=list)
    profiles_divers: list[AccessoireQty] = Field(default_factory=list, description="DIVERS: rejet d'eau, seuil PMR, etc.")
    parclose: list[AccessoireQty] = Field(default_factory=list, description="Lignes section PARCLOSE")
    accessoires: list[AccessoireQty] = Field(default_factory=list)
    joints: list[AccessoireQty] = Field(default_factory=list)
    dimension_vitrage_l: Optional[str] = Field(None, description="Cote L de la 'DIMENSION DE VITRAGE', ex: 'L-276'")
    dimension_vitrage_h: Optional[str] = Field(None, description="Cote H de la 'DIMENSION DE VITRAGE', ex: 'H-233.5'")
    quantite_vitrage: Optional[int] = None


class PlanDebitExtraction(BaseModel):
    items: list[PlanDebitItem] = Field(default_factory=list)
