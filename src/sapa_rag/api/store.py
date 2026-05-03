"""Lightweight conversation store backed by a JSON file (good enough for V1)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime

from ..config import settings
from .schemas import Conversation, ConversationSummary, Message

_LOCK = threading.RLock()
_PATH = settings.output_dir / "conversations.json"


def _now_human() -> str:
    return datetime.now().strftime("%H:%M")


def _group_for(ts: float) -> str:
    age_hours = (time.time() - ts) / 3600
    if age_hours < 24:
        return "today"
    if age_hours < 48:
        return "yesterday"
    if age_hours < 24 * 7:
        return "week"
    return "older"


def _meta_for(ts: float) -> str:
    age_hours = (time.time() - ts) / 3600
    dt = datetime.fromtimestamp(ts)
    if age_hours < 24:
        return f"Aujourd'hui · {dt.strftime('%H:%M')}"
    if age_hours < 48:
        return f"Hier · {dt.strftime('%H:%M')}"
    return dt.strftime("%d %b · %H:%M")


def _load() -> dict[str, dict]:
    if not _PATH.exists():
        return {}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save(data: dict[str, dict]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_conversations() -> list[ConversationSummary]:
    with _LOCK:
        data = _load()
    out: list[ConversationSummary] = []
    for conv in sorted(data.values(), key=lambda c: -c.get("updated_at", 0)):
        out.append(
            ConversationSummary(
                id=conv["id"],
                title=conv.get("title") or "Nouvelle conversation",
                meta=_meta_for(conv.get("updated_at", time.time())),
                group=_group_for(conv.get("updated_at", time.time())),
                n_messages=len(conv.get("messages", [])),
            )
        )
    return out


def get(conv_id: str) -> Conversation | None:
    with _LOCK:
        data = _load()
    if conv_id not in data:
        return None
    raw = data[conv_id]
    return Conversation(
        id=raw["id"],
        title=raw.get("title") or "Nouvelle conversation",
        created_at=datetime.fromtimestamp(raw.get("created_at", time.time())).isoformat(),
        messages=[Message(**m) for m in raw.get("messages", [])],
    )


def create(title: str | None = None) -> Conversation:
    with _LOCK:
        data = _load()
        cid = uuid.uuid4().hex[:12]
        now = time.time()
        data[cid] = {
            "id": cid,
            "title": title or "Nouvelle conversation",
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        _save(data)
    return Conversation(
        id=cid,
        title=data[cid]["title"],
        created_at=datetime.fromtimestamp(now).isoformat(),
        messages=[],
    )


def append_message(conv_id: str, msg: Message, set_title_if_empty: bool = False) -> None:
    with _LOCK:
        data = _load()
        if conv_id not in data:
            return
        conv = data[conv_id]
        conv.setdefault("messages", []).append(msg.model_dump())
        conv["updated_at"] = time.time()
        if (
            set_title_if_empty
            and (not conv.get("title") or conv["title"] == "Nouvelle conversation")
            and msg.role == "user"
        ):
            conv["title"] = msg.text[:60].strip()
        _save(data)


def delete(conv_id: str) -> bool:
    with _LOCK:
        data = _load()
        if conv_id in data:
            del data[conv_id]
            _save(data)
            return True
    return False
