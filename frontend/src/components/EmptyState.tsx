import { STARTERS } from "../data/starters";
import type { IndexStatus } from "../types";

export function EmptyState({
  onPick,
  status,
  showStatus,
  botName,
}: {
  onPick: (q: string) => void;
  status: IndexStatus | null;
  showStatus: boolean;
  botName: string;
}) {
  return (
    <div className="empty">
      {showStatus && status && (
        <div className="badge">
          ● {status.ready ? "Index prêt" : "Index non chargé"} ·{" "}
          {status.n_chunks.toLocaleString("fr-FR")} chunks
        </div>
      )}
      <h1>Bonjour, comment puis-je vous aider ?</h1>
      <p>
        Interrogez le catalogue {status?.catalog ?? "SAPA"}. {botName} cite les
        pages et sections à l'appui.
      </p>
      <div className="grid">
        {STARTERS.map((s, i) => (
          <button key={i} className="card" onClick={() => onPick(s.q)}>
            <div className="lbl">{s.lbl}</div>
            <div className="q">{s.q}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
