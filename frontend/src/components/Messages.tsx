import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Ic } from "./Icons";
import type { Citation, Message } from "../types";
import { api } from "../api/client";

const flashToast = (msg: string) => {
  const el = document.getElementById("__toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout((el as any)._t);
  (el as any)._t = setTimeout(() => el.classList.remove("show"), 1400);
};

const initials = (name: string) =>
  name
    .split(" ")
    .map((s) => s[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

export function UserMessage({ msg, userName }: { msg: Message; userName: string }) {
  return (
    <div className="msg user">
      <div className="ava">{initials(userName)}</div>
      <div className="body">
        <div className="who">
          <span className="n">Vous</span>
          <span className="t">{msg.time}</span>
        </div>
        <p>{msg.text}</p>
      </div>
    </div>
  );
}

export function BotMessage({
  msg,
  streaming,
  botName,
  conversationId,
  onRegenerate,
}: {
  msg: Message;
  streaming?: boolean;
  botName: string;
  conversationId?: string;
  onRegenerate?: () => void;
}) {
  const onCopy = () => {
    if (navigator.clipboard) navigator.clipboard.writeText(msg.text);
    flashToast("Réponse copiée");
  };
  const onCopyRef = (ref: string) => {
    if (navigator.clipboard) navigator.clipboard.writeText(ref);
    flashToast(`${ref} copié`);
  };
  const sendFeedback = async (helpful: boolean) => {
    if (!conversationId) return;
    try {
      await api.feedback({
        conversation_id: conversationId,
        message_id: msg.id,
        helpful,
      });
      flashToast(helpful ? "Merci !" : "Feedback enregistré");
    } catch {
      flashToast("Échec feedback");
    }
  };

  const citations = msg.citations ?? [];

  return (
    <div className="msg bot">
      <div className="ava">{initials(botName)}</div>
      <div className="body">
        <div className="who">
          <span className="n">{botName}</span>
          <span className="t">
            {msg.time}
            {citations.length ? ` · ${citations.length} sources` : ""}
          </span>
          {citations.length > 0 && <span className="badge">RAG</span>}
        </div>

        <BotBody text={msg.text} onCopyRef={onCopyRef} streaming={streaming} />

        {citations.length > 0 && (
          <div className="sources">
            <div className="sources-label">Sources citées · {citations.length}</div>
            <div className="source-chips">
              {citations.map((c, i) => (
                <SourceChip key={i} c={c} />
              ))}
            </div>
          </div>
        )}

        <div className="actions">
          <button className="act" title="Copier" onClick={onCopy}>
            <Ic.Copy />
          </button>
          {onRegenerate && (
            <button className="act" title="Régénérer" onClick={onRegenerate}>
              <Ic.Refresh />
            </button>
          )}
          <button className="act" title="Partager">
            <Ic.Share />
          </button>
          <button className="act" title="Épingler">
            <Ic.Pin />
          </button>
          <div className="act-spacer" />
          <span className="act-meta">helpful?</span>
          <button className="act ok" title="Réponse utile" onClick={() => sendFeedback(true)}>
            <Ic.Up />
          </button>
          <button className="act no" title="Réponse incorrecte" onClick={() => sendFeedback(false)}>
            <Ic.Down />
          </button>
        </div>
      </div>
    </div>
  );
}

// Render bot body with full markdown (GFM) support: tables, lists, headings, code,
// plus a custom <code> renderer that turns SAPA product codes into clickable copy chips.
function BotBody({
  text,
  onCopyRef,
  streaming,
}: {
  text: string;
  onCopyRef: (ref: string) => void;
  streaming?: boolean;
}) {
  return (
    <div className="bot-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // p: ({ children }) => <p>{children}</p>,
          code: ({ className, children, ...props }) => {
            const text = String(children ?? "");
            // Inline code that looks like a product reference → clickable copy.
            if (!className && /^S[A-Z0-9]{1,3}[0-9][A-Z0-9]{2,5}$/.test(text.trim())) {
              return (
                <code
                  {...props}
                  onClick={() => onCopyRef(text.trim())}
                  style={{ cursor: "pointer" }}
                  title={`Copier ${text.trim()}`}
                >
                  {children}
                </code>
              );
            }
            return <code className={className} {...props}>{children}</code>;
          },
          a: ({ href, children, ...props }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
      {streaming && <span className="cursor" />}
    </div>
  );
}

const CODE_RE = /\b(S[A-Z0-9]{1,3}[0-9][A-Z0-9]{2,5}|p\.\s*\d+)\b/g;

function renderInline(text: string, onCopyRef: (ref: string) => void) {
  const parts: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  CODE_RE.lastIndex = 0;
  while ((m = CODE_RE.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    parts.push(
      <code
        key={m.index}
        onClick={() => onCopyRef(tok)}
        style={{ cursor: "pointer" }}
        title={`Copier ${tok}`}
      >
        {tok}
      </code>
    );
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function SourceChip({ c }: { c: Citation }) {
  const label =
    c.section_l2 || c.section_l1 || (c.page_type ? `[${c.page_type}]` : "Source");
  return (
    <a
      className="src-chip"
      href={api.pageImageUrl(c.page)}
      target="_blank"
      rel="noopener"
      title={`${c.section_l1 ?? ""} > ${c.section_l2 ?? ""}`.trim()}
    >
      <Ic.Source />
      {label}
      <span className="pg">p.{c.page}</span>
    </a>
  );
}
