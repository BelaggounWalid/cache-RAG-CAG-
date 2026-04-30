import { useMemo } from "react";
import { Ic } from "./Icons";
import { HISTORY_GROUPS } from "../data/starters";
import type { ConversationSummary, Tweaks } from "../types";

interface Props {
  conversations: ConversationSummary[];
  activeId: string | null;
  onPick: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  query: string;
  setQuery: (q: string) => void;
  tweaks: Tweaks;
}

export function Sidebar({
  conversations,
  activeId,
  onPick,
  onNew,
  onDelete,
  query,
  setQuery,
  tweaks,
}: Props) {
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((h) => h.title.toLowerCase().includes(q));
  }, [query, conversations]);

  return (
    <aside className="sidebar">
      <div className="sb-brand">
        <div className="sb-logo">CB</div>
        <div className="sb-name">
          {tweaks.botName} Bot
          <small>RAG · v0.4</small>
        </div>
      </div>

      <button className="sb-new" onClick={onNew}>
        <Ic.Plus /> Nouvelle conversation
        <kbd>⌘N</kbd>
      </button>

      <div className="sb-search">
        <Ic.Search />
        <input
          placeholder="Rechercher dans l'historique"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="sb-list scroll">
        {HISTORY_GROUPS.map((grp) => {
          const items = filtered.filter((h) => h.group === grp.key);
          if (!items.length) return null;
          return (
            <div key={grp.key}>
              <div className="sb-section">
                <span>{grp.label}</span>
                <span>{items.length}</span>
              </div>
              {items.map((it) => (
                <button
                  key={it.id}
                  className={"sb-item " + (it.id === activeId ? "is-active" : "")}
                  onClick={() => onPick(it.id)}
                >
                  <span className="ti">{it.title}</span>
                  <span className="meta">
                    <span>{it.meta}</span>
                    <span
                      className="trash"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("Supprimer cette conversation ?")) onDelete(it.id);
                      }}
                      title="Supprimer"
                    >
                      <Ic.Trash />
                    </span>
                  </span>
                </button>
              ))}
            </div>
          );
        })}
        {!filtered.length && (
          <div className="sb-empty">Aucune conversation</div>
        )}
      </div>

      <div className="sb-foot">
        <div className="avatar">
          {tweaks.userName
            .split(" ")
            .map((s) => s[0])
            .join("")
            .toUpperCase()
            .slice(0, 2)}
        </div>
        <div className="who">
          <div className="n">{tweaks.userName}</div>
          <div className="r">bureau d'études</div>
        </div>
        <button className="gear" title="Paramètres">
          <Ic.Cog />
        </button>
      </div>
    </aside>
  );
}
