"""Qdrant index with hybrid search.

Singletons: embedders + Qdrant client are loaded once and reused. Without this,
each query re-loads the e5-large model (~15s) and re-opens the embedded Qdrant
DB (~2s) — the dominant latency cost.
"""

from __future__ import annotations

import json
import threading
import uuid
from functools import lru_cache

from ..config import settings
from ..logging_setup import log

COLLECTION = "sapa_perf70"

DENSE_MODEL = "intfloat/multilingual-e5-large"  # 1024-dim multilingue FR fort
DENSE_DIM = 1024
SPARSE_MODEL = "Qdrant/bm25"

_LOCK = threading.RLock()


@lru_cache(maxsize=1)
def _dense_embedder():
    from fastembed import TextEmbedding

    log.info("loading_dense_embedder", model=DENSE_MODEL)
    return TextEmbedding(model_name=DENSE_MODEL)


@lru_cache(maxsize=1)
def _sparse_embedder():
    from fastembed import SparseTextEmbedding

    log.info("loading_sparse_embedder", model=SPARSE_MODEL)
    return SparseTextEmbedding(model_name=SPARSE_MODEL)


@lru_cache(maxsize=1)
def _client():
    from qdrant_client import QdrantClient

    log.info("opening_qdrant", path=str(settings.output_dir / "qdrant_local"))
    return QdrantClient(path=str(settings.output_dir / "qdrant_local"))


def warmup() -> None:
    """Pre-load every singleton + run a tiny query so first user request is fast."""
    with _LOCK:
        _dense_embedder()
        _sparse_embedder()
        _client()
        try:
            hybrid_search("warmup", top_k=1)
        except Exception as exc:
            log.warning("warmup_query_failed", err=str(exc))
        log.info("warmup_done")


def build_index(chunks: list[dict] | None = None) -> int:
    """Index chunks into Qdrant. Returns number indexed."""
    from qdrant_client import models as qm

    if chunks is None:
        path = settings.output_dir / "chunks.jsonl"
        chunks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    log.info("loading_embedders", dense=DENSE_MODEL, sparse=SPARSE_MODEL)
    dense = _dense_embedder()
    sparse = _sparse_embedder()

    client = _client()
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config={
            "dense": qm.VectorParams(size=DENSE_DIM, distance=qm.Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": qm.SparseVectorParams(),
        },
    )

    # E5 expects "passage:" / "query:" prefix conventions.
    texts = [f"passage: {c['text']}" for c in chunks]
    log.info("embedding_dense", n=len(texts))
    dense_vecs = list(dense.embed(texts, batch_size=32))
    log.info("embedding_sparse", n=len(texts))
    sparse_vecs = list(sparse.embed(texts, batch_size=32))

    points = []
    for c, dv, sv in zip(chunks, dense_vecs, sparse_vecs):
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['catalog']}/{c['chunk_id']}"))
        points.append(
            qm.PointStruct(
                id=pid,
                vector={
                    "dense": dv.tolist(),
                    "sparse": qm.SparseVector(
                        indices=sv.indices.tolist(),
                        values=sv.values.tolist(),
                    ),
                },
                payload=c,
            )
        )

    BATCH = 64
    for i in range(0, len(points), BATCH):
        client.upsert(collection_name=COLLECTION, points=points[i : i + BATCH])
    log.info("indexed", n=len(points))
    return len(points)


# Per-query result cache (lifetime = process). Key: (query, top_k, frozenset(page_types or []))
_QUERY_CACHE: dict = {}
_QUERY_CACHE_MAX = 256


def hybrid_search(query: str, top_k: int = 8, page_types: list[str] | None = None) -> list[dict]:
    cache_key = (query, top_k, frozenset(page_types or []))
    if cache_key in _QUERY_CACHE:
        return _QUERY_CACHE[cache_key]

    from qdrant_client import models as qm

    dense = _dense_embedder()
    sparse = _sparse_embedder()
    dv = next(iter(dense.embed([f"query: {query}"])))
    sv = next(iter(sparse.embed([query])))

    client = _client()
    flt = None
    if page_types:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="page_type", match=qm.MatchAny(any=page_types))]
        )

    res = client.query_points(
        collection_name=COLLECTION,
        prefetch=[
            qm.Prefetch(query=dv.tolist(), using="dense", limit=top_k * 4),
            qm.Prefetch(
                query=qm.SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist()),
                using="sparse",
                limit=top_k * 4,
            ),
        ],
        query=qm.FusionQuery(fusion=qm.Fusion.RRF),
        query_filter=flt,
        limit=top_k,
        with_payload=True,
    ).points
    out = [{"score": p.score, **p.payload} for p in res]

    if len(_QUERY_CACHE) >= _QUERY_CACHE_MAX:
        _QUERY_CACHE.pop(next(iter(_QUERY_CACHE)))
    _QUERY_CACHE[cache_key] = out
    return out
