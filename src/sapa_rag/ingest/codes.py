"""Regex-based product code extraction.

Codes observed in the catalog:
  SP24806, SM22300, SGC0332, SJ27847, SVS5130, SRU0034, S210055, SA27522,
  S93084, S703570, SCO2279, SZ9A006, S512000
Pattern: 'S' + 1-3 letters/digits prefix + 3-6 digits/alphanums.
We use a permissive but precise regex.
"""
from __future__ import annotations
import re

# S + (1 to 3 capital letters OR digits) + 3 to 6 alphanumerics (mostly digits)
CODE_RE = re.compile(r"\bS[A-Z0-9]{1,3}[0-9][A-Z0-9]{2,5}\b")

# Known prefixes -> family hint
FAMILY_HINTS = {
    "SP": "Profilé",
    "SM": "Outil/Machine",
    "SGC": "Parclose",
    "SJ": "Joint",
    "SVS": "Vis",
    "SRU": "Rupture thermique",
    "SA": "Accessoire",
    "SCO": "Accessoire",
    "SZ": "Accessoire spécial",
    "S2": "Quincaillerie",
    "S5": "Quincaillerie",
    "S7": "Quincaillerie",
    "S9": "Quincaillerie",
}


def extract_codes(text: str) -> list[str]:
    if not text:
        return []
    seen = set()
    out = []
    for m in CODE_RE.findall(text):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def family_hint(code: str) -> str | None:
    for prefix in sorted(FAMILY_HINTS, key=len, reverse=True):
        if code.startswith(prefix):
            return FAMILY_HINTS[prefix]
    return None
