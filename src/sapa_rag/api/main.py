"""FastAPI app for the Chacal Bot RAG frontend."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from ..config import settings
from ..logging_setup import configure_logging, log
from . import store
from .schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    Conversation,
    ConversationSummary,
    FeedbackRequest,
    IndexStatus,
    Message,
)

configure_logging()
app = FastAPI(title="SAPA RAG — Chacal Bot API", version="0.1.0")


@app.on_event("startup")
def _warmup():
    """Pre-load embedders + Qdrant + run a no-op query so the first user request is fast."""
    try:
        from ..rag.index import warmup

        warmup()
        log.info("api_ready")
    except Exception as exc:
        log.error("warmup_failed", err=str(exc))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Index status
# ---------------------------------------------------------------------------
@app.get("/api/index/status", response_model=IndexStatus)
def index_status() -> IndexStatus:
    qdrant_dir = settings.output_dir / "qdrant_local"
    chunks_path = settings.output_dir / "chunks.jsonl"
    n_chunks = 0
    if chunks_path.exists():
        n_chunks = sum(1 for _ in chunks_path.open("r", encoding="utf-8"))
    return IndexStatus(
        ready=qdrant_dir.exists() and n_chunks > 0,
        n_chunks=n_chunks,
        catalog="SAPA Performance 70 GTI/GTI+",
        model_dense="intfloat/multilingual-e5-large",
        model_sparse="Qdrant/bm25",
    )


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------
@app.get("/api/conversations", response_model=list[ConversationSummary])
def list_conversations():
    return store.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
def create_conversation():
    return store.create()


@app.get("/api/conversations/{conv_id}", response_model=Conversation)
def get_conversation(conv_id: str):
    conv = store.get(conv_id)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return conv


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if not store.delete(conv_id):
        raise HTTPException(404, "Conversation not found")
    return {"deleted": conv_id}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def _build_history(conv_id: str, current_query: str, max_turns: int = 6) -> list[dict]:
    """Build [{role, text}] history from the persisted conversation, capped to max_turns
    most recent turns + the current user query at the end."""
    conv = store.get(conv_id)
    if conv is None:
        return [{"role": "user", "text": current_query}]
    msgs = conv.messages[-max_turns * 2 :]
    history = [{"role": m.role, "text": m.text} for m in msgs]
    history.append({"role": "user", "text": current_query})
    return history


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    from ..rag.qa import answer

    conv_id = req.conversation_id
    if conv_id is None:
        conv_id = store.create().id

    # Build history BEFORE persisting the new user msg (avoids duplicating the current query).
    history = _build_history(conv_id, req.message)

    user_msg = Message(
        id=uuid.uuid4().hex[:8],
        role="user",
        text=req.message,
        time=datetime.now().strftime("%H:%M"),
    )
    store.append_message(conv_id, user_msg, set_title_if_empty=True)

    t0 = time.time()
    if req.rag:
        try:
            res = answer(req.message, top_k=req.top_k, history=history)
        except Exception as exc:
            log.error("chat_fail", err=str(exc))
            raise HTTPException(500, f"RAG error: {exc}") from exc
    else:
        # No-RAG path: direct LLM (kept simple)
        from ..vlm.extractor import MODEL, get_client

        msg = get_client().messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": req.message}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        res = {"answer": text, "citations": [], "routing": {"boost": []}}

    latency_ms = int((time.time() - t0) * 1000)

    citations = [Citation(**c) for c in res.get("citations", [])]
    bot_msg = Message(
        id=uuid.uuid4().hex[:8],
        role="bot",
        text=res["answer"],
        time=datetime.now().strftime("%H:%M"),
        citations=citations,
    )
    store.append_message(conv_id, bot_msg)

    return ChatResponse(
        conversation_id=conv_id,
        message_id=bot_msg.id,
        answer=res["answer"],
        citations=citations,
        routing=res.get("routing") or {},
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# Streaming chat (SSE) — emits {type:"delta",text:...} and {type:"done",payload:{...}}
# ---------------------------------------------------------------------------
@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """Real-streaming: tokens flow from Anthropic to the client as they arrive."""
    from ..rag.index import hybrid_search
    from ..rag.qa import _ANSWER_CACHE, SYSTEM, _cache_key, _img_block, route
    from ..vlm.extractor import MODEL, get_client

    conv_id = req.conversation_id or store.create().id
    history = _build_history(conv_id, req.message)
    has_history = len(history) > 1

    user_msg = Message(
        id=uuid.uuid4().hex[:8],
        role="user",
        text=req.message,
        time=datetime.now().strftime("%H:%M"),
    )
    store.append_message(conv_id, user_msg, set_title_if_empty=True)

    def gen():
        # Memo hit → emit final answer in one shot, no LLM call.
        # We only memoize one-shot questions (no history).
        ckey = _cache_key(req.message, req.top_k)
        if not has_history and ckey in _ANSWER_CACHE:
            cached = _ANSWER_CACHE[ckey]
            yield f"data: {json.dumps({'type': 'step', 'step': 'cache_hit'})}\n\n"
            yield f"data: {json.dumps({'type': 'delta', 'text': cached['answer']}, ensure_ascii=False)}\n\n"
            bot_msg = Message(
                id=uuid.uuid4().hex[:8],
                role="bot",
                text=cached["answer"],
                time=datetime.now().strftime("%H:%M"),
                citations=[Citation(**c) for c in cached.get("citations", [])],
            )
            store.append_message(conv_id, bot_msg)
            payload = {
                "type": "done",
                "conversation_id": conv_id,
                "message_id": bot_msg.id,
                "citations": [c.model_dump() for c in bot_msg.citations],
                "routing": cached.get("routing") or {},
                "cached": True,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            return

        # 1. retrieval
        yield 'data: {"type":"step","step":"analysing"}\n\n'
        routing = route(req.message)
        yield 'data: {"type":"step","step":"retrieving"}\n\n'
        try:
            raw = hybrid_search(req.message, top_k=req.top_k * 2)
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': f'retrieval: {exc}'})}\n\n"
            return
        boost = set(routing["boost"])
        if boost:
            raw.sort(key=lambda h: (h.get("page_type") in boost, h.get("score") or 0), reverse=True)
        hits = raw[: req.top_k]

        # 2. build context + images
        yield 'data: {"type":"step","step":"extracting"}\n\n'
        text_parts = []
        images: list[dict] = []
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
        user_content: list[dict] = [*images]
        user_content.append(
            {
                "type": "text",
                "text": f"Question: {req.message}\n\nExtraits du catalogue:\n{context}\n\nRéponds en citant les pages.",
            }
        )

        # Build messages with prior turns (if any).
        messages_for_llm: list[dict] = []
        if has_history:
            for turn in history[:-1]:
                role = "assistant" if turn["role"] == "bot" else "user"
                messages_for_llm.append({"role": role, "content": turn["text"]})
        messages_for_llm.append({"role": "user", "content": user_content})

        # 3. real Anthropic streaming
        yield 'data: {"type":"step","step":"synthesizing"}\n\n'
        full_text = ""
        try:
            with get_client().messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=messages_for_llm,
            ) as stream:
                for tok in stream.text_stream:
                    if not tok:
                        continue
                    full_text += tok
                    yield f"data: {json.dumps({'type': 'delta', 'text': tok}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': f'llm: {exc}'})}\n\n"
            return

        # 4. persist + final event
        citations = [
            Citation(
                page=h["page"],
                section_l1=h.get("section_l1"),
                section_l2=h.get("section_l2"),
                score=h.get("score"),
                page_type=h.get("page_type"),
            )
            for h in hits
        ]
        bot_msg = Message(
            id=uuid.uuid4().hex[:8],
            role="bot",
            text=full_text,
            time=datetime.now().strftime("%H:%M"),
            citations=citations,
        )
        store.append_message(conv_id, bot_msg)
        # Only memoize one-shot answers (no prior turns).
        if not has_history:
            _ANSWER_CACHE[ckey] = {
                "answer": full_text,
                "citations": [c.model_dump() for c in citations],
                "routing": routing,
                "metrics": {},
            }

        payload = {
            "type": "done",
            "conversation_id": conv_id,
            "message_id": bot_msg.id,
            "citations": [c.model_dump() for c in citations],
            "routing": routing,
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


def _word_chunks(text: str, size: int = 8):
    words = text.split(" ")
    for i in range(0, len(words), size):
        yield " ".join(words[i : i + size]) + (" " if i + size < len(words) else "")


# ---------------------------------------------------------------------------
# Page assets
# ---------------------------------------------------------------------------
@app.get("/api/pages/{page}")
def page_image(page: int):
    """Serve a page PNG (rasterized at ingestion time)."""
    from ..cache import file_sha256

    pdf_hash = file_sha256(settings.pdf_path)[:12]
    candidate = settings.pages_png_dir / pdf_hash / f"p{page:04d}.png"
    if not candidate.exists():
        raise HTTPException(404, f"No raster for page {page}")
    return FileResponse(candidate, media_type="image/png")


# ---------------------------------------------------------------------------
# Feedback (stored in JSONL)
# ---------------------------------------------------------------------------
@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    p = settings.output_dir / "feedback.jsonl"
    rec = {
        "ts": datetime.now().isoformat(),
        **req.model_dump(),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "sapa-rag"}
