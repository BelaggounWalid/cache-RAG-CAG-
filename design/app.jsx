/* eslint-disable */

const { useState, useEffect, useRef } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "default",
  "accent": "teal",
  "density": "cozy",
  "showSuggestions": true,
  "showStatus": true,
  "userName": "Yanis L.",
  "botName": "Chacal"
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [activeId, setActiveId] = useState("c1");
  const [query, setQuery] = useState("");
  const [composerVal, setComposerVal] = useState("");
  const [thinking, setThinking] = useState(false);
  const [extraMsgs, setExtraMsgs] = useState([]);
  const [streaming, setStreaming] = useState(true);
  const convRef = useRef(null);

  // Apply theme/accent/density via data attrs on root
  useEffect(() => {
    const r = document.documentElement;
    r.setAttribute("data-theme",   tweaks.theme === "default" ? "" : tweaks.theme);
    r.setAttribute("data-accent",  tweaks.accent);
    r.setAttribute("data-density", tweaks.density);
  }, [tweaks.theme, tweaks.accent, tweaks.density]);

  // Stop streaming after 4s
  useEffect(() => {
    const t = setTimeout(() => setStreaming(false), 4000);
    return () => clearTimeout(t);
  }, []);

  const activeTitle =
    window.HISTORY.find(h => h.id === activeId)?.title || "Nouvelle conversation";

  const handleSend = (txt) => {
    setExtraMsgs(m => [...m, { role: "user", text: txt, time: nowTime() }]);
    setThinking(true);
    setTimeout(() => {
      setThinking(false);
      setExtraMsgs(m => [...m, {
        role: "bot",
        text: "Très bien — pour répondre précisément, je dois consulter la section adéquate du catalogue. Cette question nécessite un accès indexé que la démo ne couvre pas. Reformulez ou activez l'index complet.",
        time: nowTime()
      }]);
    }, 2400);
  };

  const handleNew = () => {
    setActiveId(null);
    setExtraMsgs([]);
    setThinking(false);
  };

  const handleCopy = (ref) => {
    if (navigator.clipboard) navigator.clipboard.writeText(ref);
    flashToast(`${ref} copié`);
  };

  // Auto-scroll to bottom on new content
  useEffect(() => {
    if (convRef.current) convRef.current.scrollTop = convRef.current.scrollHeight;
  }, [extraMsgs.length, thinking]);

  return (
    <>
      <div className="app">
        <Sidebar
          activeId={activeId}
          onPick={setActiveId}
          onNew={handleNew}
          query={query}
          setQuery={setQuery}
        />

        <div className="main">
          <TopBar title={activeTitle || "Nouvelle conversation"} />

          <div className="conv scroll" ref={convRef}>
            <div className="conv-inner">
              {activeId ? (
                <>
                  <UserMessage text="quelles sont les profilés qui composent Adaptation mur-rideau Elegance 52" time="14:32" />
                  <BotMessage streaming={streaming} onCopy={handleCopy} />

                  {extraMsgs.map((m, i) =>
                    m.role === "user"
                      ? <UserMessage key={i} text={m.text} time={m.time} />
                      : <SimpleBot key={i} text={m.text} time={m.time} />
                  )}
                  {thinking && <Thinking />}
                </>
              ) : (
                <EmptyState onPick={(q) => setComposerVal(q)} />
              )}
            </div>
          </div>

          <Composer onSend={handleSend} value={composerVal} setValue={setComposerVal} />
        </div>
      </div>

      <Tweaks tweaks={tweaks} setTweak={setTweak} />
      <Toast />
    </>
  );
}

function SimpleBot({ text, time }) {
  return (
    <div className="msg bot">
      <div className="ava">CB</div>
      <div className="body">
        <div className="who">
          <span className="n">Chacal</span>
          <span className="t">{time}</span>
        </div>
        <p>{text}</p>
        <div className="actions">
          <button className="act"><Ic.Copy /></button>
          <button className="act"><Ic.Refresh /></button>
          <div className="act-spacer" />
          <button className="act ok"><Ic.Up /></button>
          <button className="act no"><Ic.Down /></button>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onPick }) {
  return (
    <div className="empty">
      <div className="badge">● Index prêt · 2 184 chunks</div>
      <h1>Bonjour, comment puis-je vous aider ?</h1>
      <p>Interrogez le catalogue SAPA Performance 70 GTI/GTI+. Citations et références à l'appui.</p>
      <div className="grid">
        {window.STARTERS.map((s, i) => (
          <button key={i} className="card" onClick={() => onPick(s.q)}>
            <div className="lbl">{s.lbl}</div>
            <div className="q">{s.q}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ---------- Tweaks panel ---------- */
function Tweaks({ tweaks, setTweak }) {
  return (
    <TweaksPanel title="Tweaks" defaultOpen={false}>
      <TweakSection title="Thème">
        <TweakRadio
          label="Ambiance"
          value={tweaks.theme}
          onChange={v => setTweak("theme", v)}
          options={[
            { value: "default",  label: "Slate" },
            { value: "midnight", label: "Midnight" },
            { value: "warm",     label: "Warm" },
          ]}
        />
        <TweakSelect
          label="Accent"
          value={tweaks.accent}
          onChange={v => setTweak("accent", v)}
          options={[
            { value: "teal",   label: "Teal (mint)" },
            { value: "indigo", label: "Indigo" },
            { value: "amber",  label: "Amber" },
            { value: "lime",   label: "Lime" },
            { value: "orange", label: "Orange industriel" },
          ]}
        />
        <TweakRadio
          label="Densité"
          value={tweaks.density}
          onChange={v => setTweak("density", v)}
          options={[
            { value: "compact", label: "Compact" },
            { value: "cozy",    label: "Cozy" },
            { value: "roomy",   label: "Roomy" },
          ]}
        />
      </TweakSection>

      <TweakSection title="Contenu">
        <TweakToggle
          label="Suggestions au-dessus du composer"
          value={tweaks.showSuggestions}
          onChange={v => setTweak("showSuggestions", v)}
        />
        <TweakToggle
          label="Bandeau statut (Index prêt)"
          value={tweaks.showStatus}
          onChange={v => setTweak("showStatus", v)}
        />
        <TweakText
          label="Nom utilisateur"
          value={tweaks.userName}
          onChange={v => setTweak("userName", v)}
        />
        <TweakText
          label="Nom du bot"
          value={tweaks.botName}
          onChange={v => setTweak("botName", v)}
        />
      </TweakSection>
    </TweaksPanel>
  );
}

/* ---------- Tiny toast ---------- */
let toastEl = null;
function flashToast(msg) {
  if (!toastEl) toastEl = document.getElementById("__toast");
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastEl._t);
  toastEl._t = setTimeout(() => toastEl.classList.remove("show"), 1400);
}
function Toast() {
  return <div id="__toast" className="toast" />;
}

function nowTime() {
  const d = new Date();
  return d.getHours().toString().padStart(2,"0") + ":" + d.getMinutes().toString().padStart(2,"0");
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
