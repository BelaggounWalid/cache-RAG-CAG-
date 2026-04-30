"""diskcache-backed idempotency layer for VLM calls and other expensive ops."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from diskcache import Cache

from .config import settings

_CACHE_DIR = settings.output_dir / "_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
cache = Cache(str(_CACHE_DIR))


def stable_key(*parts) -> str:
    blob = json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def cached_call(namespace: str, key_parts: tuple, fn, *args, **kwargs):
    key = f"{namespace}:{stable_key(*key_parts)}"
    if key in cache:
        return cache[key]
    result = fn(*args, **kwargs)
    cache[key] = result
    return result


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
