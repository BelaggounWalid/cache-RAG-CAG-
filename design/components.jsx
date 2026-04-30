/* eslint-disable */

const { useState, useEffect, useRef, useMemo } = React;

/* ---------- Sidebar ---------- */
function Sidebar({ activeId, onPick, onNew, query, setQuery }) {
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return window.HISTORY;
    return window.HISTORY.filter(h => h.title.toLowerCase().includes(q));
  }, [query]);

  return (
    <aside className="sidebar">
      <div className="sb-brand">
        <div className="sb-logo">CB</div>
        <div className="sb-name">
          Chacal Bot
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
          onChange={e => setQuery(e.target.value)}
        />
      </div>

      <div className="sb-list scroll">
        {window.HISTORY_GROUPS.map(grp => {
          const items = filtered.filter(h => h.group === grp.key);
          if (!items.length) return null;
          return (
            <div key={grp.key}>
              <div className="sb-section">
                <span>{grp.label}</span>
                <span>{items.length}</span>
              </div>
              {items.map(it => (
                <button
                  key={it.id}
                  className={"sb-item " + (it.id === activeId ? "is-active" : "")}
                  onClick={() => onPick(it.id)}
                >
                  <span className="ti">{it.title}</span>
                  <span className="meta">
                    <span>{it.meta}</span>
                  </span>
                </button>
              ))}
            </div>
          );
        })}
      </div>

      <div className="sb-foot">
        <div className="avatar">YL</div>
        <div className="who">
          <div className="n">Yanis L.</div>
          <div className="r">bureau d'études</div>
        </div>
        <button className="gear" title="Paramètres"><Ic.Cog /></button>
      </div>
    </aside>
  );
}

/* ---------- Top bar ---------- */
function TopBar({ title }) {
  return (
    <div className="topbar">
      <div className="tb-title">
        <div className="crumb">SAPA Performance 70 GTI/GTI+ · Catalogue</div>
        <div className="name">{title}</div>
      </div>
      <div className="tb-status">
        <span className="led" />
        Index prêt · 2 184 chunks
      </div>
      <div className="tb-spacer" />
      <button className="tb-btn ghost"><Ic.Filter /> top_k <code style={{fontFamily:'var(--font-mono)',color:'var(--accent)'}}>8</code></button>
      <button className="tb-btn ghost"><Ic.Db /> Index</button>
      <button className="tb-btn"><Ic.Share /> Partager</button>
    </div>
  );
}

/* ---------- Reference table ---------- */
function ProfileRefs({ items, onCopy }) {
  return (
    <div className="refs">
      <div className="refs-head">
        <span>#</span><span>Réf.</span><span>Désignation</span><span></span>
      </div>
      {items.map((p, i) => (
        <div className="refs-row" key={p.ref}>
          <span className="num">{String(i+1).padStart(2,'0')}</span>
          <span className="ref">{p.ref}</span>
          <span className="desc">{p.desc}</span>
          <button className="copy" onClick={() => onCopy(p.ref)} title={"Copier " + p.ref}>
            <Ic.Copy />
          </button>
        </div>
      ))}
    </div>
  );
}

/* ---------- Bot message ---------- */
function BotMessage({ streaming, onCopy }) {
  return (
    <div className="msg bot">
      <div className="ava">CB</div>
      <div className="body">
        <div className="who">
          <span className="n">Chacal</span>
          <span className="t">14:32 · 1.2 s · 8 sources</span>
          <span className="badge">RAG</span>
        </div>

        <h3>Composition de l'Adaptation mur-rideau Elegance 52</h3>
        <p>
          D'après la <code>p. 217</code> (section <em>« COUPES — Adaptation mur-rideau Elegance 52 »</em>),
          l'adaptation est composée de <strong>11 profilés</strong> répartis sur la coupe verticale et la traverse basse.
        </p>

        <ProfileRefs items={window.PROFILES} onCopy={onCopy} />

        <p style={{marginTop:'12px', color:'var(--fg-2)', fontSize:'13.5px'}}>
          Le profilé <code>SP24808</code> est interchangeable avec <code>SJ28377</code> selon l'épaisseur de remplissage
          (cf. tableau de compatibilités p. 218).
          {streaming && <span className="cursor" />}
        </p>

        <div className="sources">
          <div className="sources-label">Sources citées · 3</div>
          <div className="source-chips">
            {window.SOURCES.map((s, i) => (
              <button key={i} className="src-chip" title={s.section}>
                <Ic.Source />
                {s.doc.replace('Catalogue SAPA ', '')}
                <span className="pg">p.{s.page}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="actions">
          <button className="act" title="Copier"><Ic.Copy /></button>
          <button className="act" title="Régénérer"><Ic.Refresh /></button>
          <button className="act" title="Partager"><Ic.Share /></button>
          <button className="act" title="Épingler"><Ic.Pin /></button>
          <div className="act-spacer" />
          <span className="act-meta">helpful?</span>
          <button className="act ok" title="Réponse utile"><Ic.Up /></button>
          <button className="act no" title="Réponse incorrecte"><Ic.Down /></button>
        </div>
      </div>
    </div>
  );
}

/* ---------- User message ---------- */
function UserMessage({ text, time = "14:32" }) {
  return (
    <div className="msg user">
      <div className="ava">YL</div>
      <div className="body">
        <div className="who">
          <span className="n">Vous</span>
          <span className="t">{time}</span>
        </div>
        <p>{text}</p>
      </div>
    </div>
  );
}

/* ---------- Thinking pipeline ---------- */
function Thinking() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStep(s => Math.min(s + 1, 3)), 600);
    return () => clearInterval(t);
  }, []);
  const steps = [
    "Analyse de la question",
    "Recherche dans l'index (top_k=8)",
    "Extraction des passages",
    "Synthèse de la réponse",
  ];
  return (
    <div className="msg bot">
      <div className="ava">CB</div>
      <div className="body">
        <div className="who">
          <span className="n">Chacal</span>
          <span className="t">en cours…</span>
        </div>
        <div className="thinking">
          <div className="typing"><span></span><span></span><span></span></div>
          {steps.map((s, i) => (
            <span key={i} className={"step " + (i < step ? "done" : i === step ? "cur" : "")}>
              {i < step && "✓ "}{s}{i < steps.length - 1 ? " ›" : ""}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------- Composer ---------- */
function Composer({ onSend, value, setValue }) {
  const taRef = useRef(null);
  const [ragOn, setRagOn] = useState(true);
  const [deepOn, setDeepOn] = useState(false);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="composer-wrap">
      <div className="suggest">
        {window.SUGGESTIONS.map((s, i) => (
          <button key={i} className="sg" onClick={() => setValue(s.txt)}>
            <span className="ic">{s.ic}</span> {s.txt}
          </button>
        ))}
      </div>

      <div className="composer">
        <textarea
          ref={taRef}
          rows={1}
          placeholder="Posez une question sur le catalogue… (Maj+Entrée pour saut de ligne)"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
          }}
        />
        <div className="cmp-row">
          <button className={"cmp-tool " + (ragOn ? "is-on" : "")} onClick={() => setRagOn(!ragOn)} title="Recherche dans l'index">
            <Ic.Db /> RAG
          </button>
          <button className={"cmp-tool " + (deepOn ? "is-on" : "")} onClick={() => setDeepOn(!deepOn)} title="Mode raisonnement">
            <Ic.Sparkle /> Deep
          </button>
          <button className="cmp-tool" title="Joindre un PDF"><Ic.Book /> PDF</button>
          <div className="cmp-spacer" />
          <span className="cmp-count">{value.length}/2000</span>
          <button className="cmp-send" onClick={submit} disabled={!value.trim()}>
            Envoyer <kbd>↵</kbd>
          </button>
        </div>
      </div>
    </div>
  );
}

window.Sidebar = Sidebar;
window.TopBar = TopBar;
window.BotMessage = BotMessage;
window.UserMessage = UserMessage;
window.Thinking = Thinking;
window.Composer = Composer;
