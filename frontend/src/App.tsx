import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "./api/client";
import { useTweaks } from "./hooks/useTweaks";
import type {
  ChatResponse,
  Citation,
  Conversation,
  ConversationSummary,
  IndexStatus,
  Message,
} from "./types";

import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { Composer } from "./components/Composer";
import { BotMessage, UserMessage } from "./components/Messages";
import { Thinking } from "./components/Thinking";
import { EmptyState } from "./components/EmptyState";
import { TweaksPanel } from "./components/Tweaks";

export default function App() {
  const { tweaks, setTweak } = useTweaks();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [active, setActive] = useState<Conversation | null>(null);
  const [query, setQuery] = useState("");
  const [composerVal, setComposerVal] = useState("");
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [topK, setTopK] = useState(8);

  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [thinkingStep, setThinkingStep] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const convRef = useRef<HTMLDivElement>(null);
  // Tracks which conv id we already have loaded locally. Prevents a race where
  // setActiveId() triggers a re-fetch that clobbers the optimistic user message.
  const loadedIdRef = useRef<string | null>(null);

  const refreshConversations = useCallback(async () => {
    try {
      const list = await api.listConversations();
      setConversations(list);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  // ---------- bootstrap (with retry until backend is reachable) ----------
  useEffect(() => {
    let cancelled = false;
    let attempt = 0;
    const tick = async () => {
      try {
        const s = await api.indexStatus();
        if (cancelled) return;
        setStatus(s);
        setError(null); // clear any stale "backend down" error
        refreshConversations();
      } catch (e) {
        attempt += 1;
        if (cancelled) return;
        setError(String(e));
        // Retry every 2s up to 10 times — covers "backend was just started".
        if (attempt < 10) setTimeout(tick, 2000);
      }
    };
    tick();
    return () => {
      cancelled = true;
    };
  }, [refreshConversations]);

  // ---------- load active conversation ----------
  useEffect(() => {
    if (!activeId) {
      setActive(null);
      loadedIdRef.current = null;
      return;
    }
    // Skip refetch when we already loaded this id locally (just created or just sent).
    if (loadedIdRef.current === activeId) return;
    loadedIdRef.current = activeId;
    api.getConversation(activeId).then(setActive).catch((e) => setError(String(e)));
  }, [activeId]);

  // ---------- shortcuts ----------
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "n") {
        e.preventDefault();
        handleNew();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // ---------- auto scroll ----------
  useEffect(() => {
    if (convRef.current)
      convRef.current.scrollTop = convRef.current.scrollHeight;
  }, [active?.messages.length, streamingText, thinkingStep]);

  const handleNew = () => {
    setActiveId(null);
    setActive(null);
    setStreamingText(null);
    setThinkingStep(null);
    setError(null);
  };

  const handleSend = async (
    text: string,
    opts: { rag: boolean; deep: boolean }
  ) => {
    setError(null);
    setBusy(true);
    setStreamingText("");
    setThinkingStep("analysing");

    // Optimistic conversation creation if missing.
    let convId = activeId;
    if (!convId) {
      try {
        const conv = await api.createConversation();
        convId = conv.id;
        // Mark as already-loaded BEFORE setActiveId to defuse the load effect's refetch.
        loadedIdRef.current = conv.id;
        setActive(conv);
        setActiveId(conv.id);
      } catch (e) {
        setError(String(e));
        setBusy(false);
        return;
      }
    }

    // Optimistic user message in UI.
    const localUser: Message = {
      id: "tmp-" + Date.now(),
      role: "user",
      text,
      time: new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
    };
    setActive((c) =>
      c
        ? { ...c, messages: [...c.messages, localUser] }
        : c
    );

    let finalCitations: Citation[] = [];
    let finalText = "";

    try {
      for await (const ev of api.chatStream({
        conversation_id: convId,
        message: text,
        top_k: topK,
        rag: opts.rag,
        deep: opts.deep,
      })) {
        if (ev.type === "step") {
          setThinkingStep(ev.step);
        } else if (ev.type === "delta") {
          setThinkingStep(null);
          finalText += ev.text;
          setStreamingText(finalText);
        } else if (ev.type === "done") {
          finalCitations = ev.citations || [];
          setActive((c) => {
            if (!c) return c;
            const botMsg: Message = {
              id: ev.message_id,
              role: "bot",
              text: finalText,
              time: new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
              citations: finalCitations,
            };
            return { ...c, messages: [...c.messages, botMsg] };
          });
          setStreamingText(null);
          setThinkingStep(null);
        } else if (ev.type === "error") {
          setError(ev.message || "Erreur de traitement");
          setStreamingText(null);
          setThinkingStep(null);
        }
      }
      refreshConversations();
    } catch (e) {
      // Fallback to non-streaming.
      try {
        const r: ChatResponse = await api.chat({
          conversation_id: convId,
          message: text,
          top_k: topK,
          rag: opts.rag,
          deep: opts.deep,
        });
        const botMsg: Message = {
          id: r.message_id,
          role: "bot",
          text: r.answer,
          time: new Date().toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          citations: r.citations,
        };
        setActive((c) => (c ? { ...c, messages: [...c.messages, botMsg] } : c));
        refreshConversations();
      } catch (e2) {
        setError(String(e2));
      }
    } finally {
      setBusy(false);
      setStreamingText(null);
      setThinkingStep(null);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteConversation(id);
      if (activeId === id) handleNew();
      refreshConversations();
    } catch (e) {
      setError(String(e));
    }
  };

  const title = active?.title ?? "Nouvelle conversation";

  return (
    <>
      <div className="app">
        <Sidebar
          conversations={conversations}
          activeId={activeId}
          onPick={setActiveId}
          onNew={handleNew}
          onDelete={handleDelete}
          query={query}
          setQuery={setQuery}
          tweaks={tweaks}
        />

        <div className="main">
          <TopBar
            title={title}
            topK={topK}
            setTopK={setTopK}
            status={status}
            showStatus={tweaks.showStatus}
          />

          {error && (
            <div className="err-banner">
              {error}
              <button onClick={() => setError(null)}>✕</button>
            </div>
          )}

          <div className="conv scroll" ref={convRef}>
            <div className="conv-inner">
              {active && active.messages.length > 0 ? (
                <>
                  {active.messages.map((m) =>
                    m.role === "user" ? (
                      <UserMessage key={m.id} msg={m} userName={tweaks.userName} />
                    ) : (
                      <BotMessage
                        key={m.id}
                        msg={m}
                        botName={tweaks.botName}
                        conversationId={active.id}
                      />
                    )
                  )}
                  {streamingText !== null && (
                    <BotMessage
                      msg={{
                        id: "stream",
                        role: "bot",
                        text: streamingText,
                        time: new Date().toLocaleTimeString("fr-FR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        }),
                      }}
                      streaming
                      botName={tweaks.botName}
                    />
                  )}
                  {busy && thinkingStep && (
                    <Thinking botName={tweaks.botName} externalStep={thinkingStep} />
                  )}
                </>
              ) : (
                <EmptyState
                  onPick={(q) => setComposerVal(q)}
                  status={status}
                  showStatus={tweaks.showStatus}
                  botName={tweaks.botName}
                />
              )}
            </div>
          </div>

          <Composer
            onSend={handleSend}
            value={composerVal}
            setValue={setComposerVal}
            showSuggestions={tweaks.showSuggestions}
            disabled={busy}
          />
        </div>
      </div>

      <TweaksPanel tweaks={tweaks} setTweak={setTweak} />
      <div id="__toast" className="toast" />
    </>
  );
}
