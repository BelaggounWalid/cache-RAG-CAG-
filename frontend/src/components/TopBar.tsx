import { Ic } from "./Icons";
import type { IndexStatus } from "../types";

interface Props {
  title: string;
  topK: number;
  setTopK: (n: number) => void;
  status: IndexStatus | null;
  showStatus: boolean;
}

export function TopBar({ title, topK, setTopK, status, showStatus }: Props) {
  return (
    <div className="topbar">
      <div className="tb-title">
        <div className="crumb">
          {status?.catalog ?? "SAPA Performance 70 GTI/GTI+"} · Catalogue
        </div>
        <div className="name">{title}</div>
      </div>
      {showStatus && (
        <div className="tb-status">
          <span className={"led " + (status?.ready ? "" : "off")} />
          {status
            ? status.ready
              ? `Index prêt · ${status.n_chunks.toLocaleString("fr-FR")} chunks`
              : "Index non chargé"
            : "Chargement…"}
        </div>
      )}
      <div className="tb-spacer" />
      <button
        className="tb-btn ghost"
        title="Nombre de passages récupérés"
        onClick={() => {
          const v = prompt("top_k (3–20) :", String(topK));
          const n = Number(v);
          if (Number.isFinite(n) && n >= 3 && n <= 20) setTopK(n);
        }}
      >
        <Ic.Filter /> top_k <code>{topK}</code>
      </button>
      <button className="tb-btn ghost">
        <Ic.Db /> Index
      </button>
      <button className="tb-btn">
        <Ic.Share /> Partager
      </button>
    </div>
  );
}
