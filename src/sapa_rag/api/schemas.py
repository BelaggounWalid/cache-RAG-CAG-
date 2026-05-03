from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    page: int
    section_l1: str | None = None
    section_l2: str | None = None
    score: float | None = None
    page_type: str | None = None
    text_preview: str | None = None


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)
    top_k: int = 8
    rag: bool = True
    deep: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[Citation]
    routing: dict
    latency_ms: int


class Message(BaseModel):
    id: str
    role: Literal["user", "bot"]
    text: str
    time: str
    citations: list[Citation] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    meta: str  # e.g. "Aujourd'hui · 14:32"
    group: Literal["today", "yesterday", "week", "older"]
    n_messages: int = 0


class Conversation(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[Message] = Field(default_factory=list)


class IndexStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    ready: bool
    n_chunks: int
    catalog: str
    model_dense: str
    model_sparse: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    message_id: str
    helpful: bool
    comment: str | None = None
