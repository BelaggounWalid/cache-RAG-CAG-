from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PageType(str, Enum):
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
    section_l1: Optional[str] = None
    section_l2: Optional[str] = None
    page_type: PageType = PageType.MIXED
    codes: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    code: str
    family: Optional[str] = None
    description: Optional[str] = None
    page: int
    catalog: str = "perf70_gti"


class Accessory(BaseModel):
    code: str
    category: Optional[str] = None
    description: Optional[str] = None
    page: int
    catalog: str = "perf70_gti"


class PerformanceRow(BaseModel):
    config: str
    serie: Optional[str] = None
    largeur: Optional[float] = None
    hauteur: Optional[float] = None
    ug: Optional[float] = None
    ud: Optional[float] = None
    uf: Optional[float] = None
    intercalaire: Optional[str] = None
    isolation: Optional[str] = None
    page: int
    catalog: str = "perf70_gti"


class CodeMention(BaseModel):
    code: str
    page: int
    section_l1: Optional[str] = None
    section_l2: Optional[str] = None
    page_type: PageType
    catalog: str = "perf70_gti"
