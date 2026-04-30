import type {
  ChatResponse,
  Conversation,
  ConversationSummary,
  IndexStatus,
} from "../types";

const BASE = "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  let r: Response;
  try {
    r = await fetch(BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (e) {
    throw new Error(
      `Backend injoignable (${BASE + path}) — démarre-le avec ` +
        `\`python scripts/run_api.py\``
    );
  }
  if (!r.ok) {
    const txt = (await r.text()) || "(corps vide — vérifie les logs du backend)";
    let detail = txt;
    try {
      const j = JSON.parse(txt);
      detail = j.detail || j.message || txt;
    } catch {
      /* not JSON, keep raw */
    }
    throw new Error(`${r.status} ${r.statusText} — ${detail}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  indexStatus: () => http<IndexStatus>("/index/status"),

  listConversations: () => http<ConversationSummary[]>("/conversations"),
  getConversation: (id: string) => http<Conversation>(`/conversations/${id}`),
  createConversation: () =>
    http<Conversation>("/conversations", { method: "POST" }),
  deleteConversation: (id: string) =>
    http<{ deleted: string }>(`/conversations/${id}`, { method: "DELETE" }),

  chat: (body: {
    conversation_id?: string | null;
    message: string;
    top_k?: number;
    rag?: boolean;
    deep?: boolean;
  }) =>
    http<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  feedback: (body: {
    conversation_id: string;
    message_id: string;
    helpful: boolean;
    comment?: string;
  }) =>
    http<{ ok: boolean }>("/feedback", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Streaming chat via SSE.
  // Returns an async generator yielding events: {type:"step"|"delta"|"done"|"error", ...}
  async *chatStream(body: {
    conversation_id?: string | null;
    message: string;
    top_k?: number;
    rag?: boolean;
    deep?: boolean;
  }): AsyncGenerator<any, void, void> {
    const r = await fetch(BASE + "/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok || !r.body) throw new Error(`Stream failed: ${r.status}`);
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        const m = line.match(/^data:\s*(.*)$/m);
        if (!m) continue;
        try {
          yield JSON.parse(m[1]);
        } catch {
          /* ignore parse errors on partial payloads */
        }
      }
    }
  },

  pageImageUrl: (page: number) => `${BASE}/pages/${page}`,
};
