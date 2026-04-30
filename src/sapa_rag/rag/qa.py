"""Q&A on top of Qdrant hybrid retrieval, with multimodal injection of visual chunks.

Latency optimizations:
  * embedders + Qdrant client are singletons (see rag/index.py)
  * the system prompt is cached (Anthropic prompt caching, ~5-min TTL, ~90% cheaper on hit)
  * exact-question result memoization (in-process, 256 entries)
"""
from __future__ import annotations
import base64
import hashlib
import re
import time
from pathlib import Path

from ..config import settings
from ..vlm.extractor import MODEL, get_client
from ..logging_setup import log
from .index import hybrid_search

CODE_RE = re.compile(r"\bS[A-Z0-9]{1,3}[0-9][A-Z0-9]{2,5}\b")

SYSTEM = (
    "Tu es un assistant technique pour le catalogue SAPA Performance 70 GTI/GTI+, "
    "un système de menuiserie aluminium pour porte grand trafic.\n\n"
    "VOCABULAIRE MÉTIER (à respecter strictement) :\n"
    "- VITRAGE = le panneau de verre lui-même (épaisseur G en mm, composition double/triple, valeur Ug). "
    "  Le catalogue NE vend PAS de verre, il liste les épaisseurs G acceptées par le système (3 à 53 mm).\n"
    "- PARCLOSE = baguette aluminium qui maintient le vitrage (codes SGC...). NE PAS confondre avec un vitrage.\n"
    "- DORMANT = cadre fixe scellé au mur (codes SP248..).\n"
    "- OUVRANT = vantail mobile (codes SP248..).\n"
    "- TRAVERSE / PLINTHE / SEUIL = profils horizontaux ; SEUIL PMR = seuil aux normes accessibilité.\n"
    "- DIMENSION DE VITRAGE = cotes L (largeur) et H (hauteur) du verre, distinctes des cotes de parclose.\n"
    "- Ud / Uf / Ug / Psi = coefficients thermiques (porte / châssis / vitrage / intercalaire).\n\n"
    "RÈGLES DE RÉPONSE :\n"
    "1. Réponds UNIQUEMENT à partir des extraits fournis.\n"
    "2. Cite systématiquement la page (format: p. XX) et la section TOC.\n"
    "3. Si la question utilise un terme ambigu (ex: 'vitrage' alors que le catalogue parle de 'parclose'), "
    "   commence par clarifier la distinction puis donne ce que le catalogue contient effectivement.\n"
    "4. Si l'information n'est pas dans les extraits, dis-le explicitement — n'invente pas.\n"
    "5. Sois concis : factuel, valeurs numériques exactes, pas de remplissage."
)


def route(query: str) -> dict:
    q = query.lower()
    boost: list[str] = []
    if any(k in q for k in ["ud", "uf", "ug", "thermique", "isolation"]):
        boost.append("performance")
    if any(k in q for k in ["vitrage", "parclose", "épaisseur", "epaisseur"]):
        boost.extend(["vitrage", "plan_debit"])
    if any(k in q for k in ["coupe", "section"]):
        boost.append("coupe")
    if any(k in q for k in ["débit", "debit", "dimension", "taille", "cote"]):
        boost.append("plan_debit")
    if any(k in q for k in ["montage", "assemblage", "usinage"]):
        boost.append("plan_montage")
    if any(k in q for k in ["profilé", "profile", "dormant", "ouvrant"]):
        boost.append("nomenclature")
    if any(k in q for k in ["porte", "vantail", "vantaux", "pmr", "seuil"]):
        boost.append("plan_debit")
    return {"boost": list(dict.fromkeys(boost))}


def _img_block(p: Path) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.standard_b64encode(p.read_bytes()).decode(),
        },
    }


# In-process answer memo: same question + same top_k → same answer.
_ANSWER_CACHE: dict[str, dict] = {}
_ANSWER_CACHE_MAX = 128


def _cache_key(query: str, top_k: int) -> str:
    blob = f"{query}|{top_k}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def answer(
    query: str,
    top_k: int = 8,
    use_cache: bool = True,
    history: list[dict] | None = None,
) -> dict:
    """Answer a query.

    `history` is the conversation context: a list of {"role": "user"|"bot", "text": str}.
    The LAST entry should be the current user query (or omit and pass it via `query`).
    Memo is keyed only on the current query — multi-turn answers are not memoized.
    """
    has_history = bool(history and len(history) > 1)
    if use_cache and not has_history:
        # Only memoize one-shot questions; multi-turn replies depend on prior context.
        key = _cache_key(query, top_k)
        if key in _ANSWER_CACHE:
            log.info("answer_cache_hit", key=key)
            return _ANSWER_CACHE[key]

    t0 = time.time()
    routing = route(query)
    raw = hybrid_search(query, top_k=top_k * 2)
    boost = set(routing["boost"])
    if boost:
        raw.sort(key=lambda h: (h.get("page_type") in boost, h.get("score") or 0), reverse=True)
    hits = raw[:top_k]
    t_retrieval = time.time() - t0

    text_parts = []
    images = []
    for i, h in enumerate(hits, 1):
        text_parts.append(
            f"[#{i} | p.{h['page']} | {h.get('section_l1') or ''} > {h.get('section_l2') or ''} | type={h['page_type']}]\n"
            f"{h['text'][:1500]}"
        )
        if h.get("is_visual") and h.get("image_path"):
            ip = Path(h["image_path"])
            if ip.exists() and len(images) < 3:
                images.append(_img_block(ip))

    context = "\n\n---\n\n".join(text_parts)

    # Build conversation messages: prior turns + current user turn with retrieved context.
    messages: list[dict] = []
    if has_history:
        # `history` ends with the current user query; we drop the last entry and rebuild it
        # below with the retrieved context attached.
        for turn in history[:-1]:
            role = "assistant" if turn["role"] == "bot" else "user"
            messages.append({"role": role, "content": turn["text"]})

    user_content: list[dict] = [*images]
    user_content.append(
        {
            "type": "text",
            "text": f"Question: {query}\n\nExtraits du catalogue:\n{context}\n\nRéponds en citant les pages.",
        }
    )
    messages.append({"role": "user", "content": user_content})

    client = get_client()
    t1 = time.time()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    )
    t_llm = time.time() - t1
    text = "".join(b.text for b in msg.content if b.type == "text")

    usage = getattr(msg, "usage", None)
    cache_read = getattr(usage, "cache_read_input_tokens", 0) if usage else 0
    cache_create = getattr(usage, "cache_creation_input_tokens", 0) if usage else 0
    log.info(
        "answer_metrics",
        retrieval_ms=int(t_retrieval * 1000),
        llm_ms=int(t_llm * 1000),
        cache_read_tokens=cache_read,
        cache_create_tokens=cache_create,
    )

    out = {
        "answer": text,
        "citations": [
            {
                "page": h["page"],
                "section_l1": h.get("section_l1"),
                "section_l2": h.get("section_l2"),
                "score": h.get("score"),
                "page_type": h.get("page_type"),
            }
            for h in hits
        ],
        "routing": routing,
        "metrics": {
            "retrieval_ms": int(t_retrieval * 1000),
            "llm_ms": int(t_llm * 1000),
            "cache_read_tokens": cache_read,
            "cache_create_tokens": cache_create,
        },
    }

    if use_cache and not has_history:
        if len(_ANSWER_CACHE) >= _ANSWER_CACHE_MAX:
            _ANSWER_CACHE.pop(next(iter(_ANSWER_CACHE)))
        _ANSWER_CACHE[_cache_key(query, top_k)] = out

    return out
