from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class PageType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    NOMENCLATURE = "nomenclature"
    COUPE = "coupe"
    PLAN_DEBIT = "plan_debit"
    PLAN_MONTAGE = "plan_montage"
    PERFORMANCE = "performance"
    VITRAGE = "vitrage"
    COVER = "cover"
    BLANK = "blank"
    MIXED = "mixed"


class PageInfo(BaseModel):
    page_num: int = Field(..., description="1-indexed page number")
    text_len: int
    n_images: int
    n_drawings: int
    section_l1: str | None = None
    section_l2: str | None = None
    page_type: PageType = PageType.MIXED
    codes: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    code: str
    family: str | None = None
    description: str | None = None
    page: int
    catalog: str = "perf70_gti"


class Accessory(BaseModel):
    code: str
    category: str | None = None
    description: str | None = None
    page: int
    catalog: str = "perf70_gti"


class PerformanceRow(BaseModel):
    config: str
    serie: str | None = None
    largeur: float | None = None
    hauteur: float | None = None
    ug: float | None = None
    ud: float | None = None
    uf: float | None = None
    intercalaire: str | None = None
    isolation: str | None = None
    page: int
    catalog: str = "perf70_gti"


class CodeMention(BaseModel):
    code: str
    page: int
    section_l1: str | None = None
    section_l2: str | None = None
    page_type: PageType
    catalog: str = "perf70_gti"
