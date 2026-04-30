import { useEffect, useRef, useState } from "react";
import { Ic } from "./Icons";
import { SUGGESTIONS } from "../data/starters";

interface Props {
  onSend: (text: string, opts: { rag: boolean; deep: boolean }) => void;
  value: string;
  setValue: (v: string) => void;
  showSuggestions: boolean;
  disabled?: boolean;
}

export function Composer({ onSend, value, setValue, showSuggestions, disabled }: Props) {
  const taRef = useRef<HTMLTextAreaElement>(null);
  const [ragOn, setRagOn] = useState(true);
  const [deepOn, setDeepOn] = useState(false);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim(), { rag: ragOn, deep: deepOn });
    setValue("");
  };

  return (
    <div className="composer-wrap">
      {showSuggestions && (
        <div className="suggest">
          {SUGGESTIONS.map((s, i) => (
            <button key={i} className="sg" onClick={() => setValue(s.txt)}>
              <span className="ic">{s.ic}</span> {s.txt}
            </button>
          ))}
        </div>
      )}

      <div className="composer">
        <textarea
          ref={taRef}
          rows={1}
          placeholder="Posez une question sur le catalogue… (Maj+Entrée pour saut de ligne)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <div className="cmp-row">
          <button
            className={"cmp-tool " + (ragOn ? "is-on" : "")}
            onClick={() => setRagOn(!ragOn)}
            title="Recherche dans l'index"
          >
            <Ic.Db /> RAG
          </button>
          <button
            className={"cmp-tool " + (deepOn ? "is-on" : "")}
            onClick={() => setDeepOn(!deepOn)}
            title="Mode raisonnement"
          >
            <Ic.Sparkle /> Deep
          </button>
          <button className="cmp-tool" title="Joindre un PDF">
            <Ic.Book /> PDF
          </button>
          <div className="cmp-spacer" />
          <span className="cmp-count">{value.length}/2000</span>
          <button className="cmp-send" onClick={submit} disabled={!value.trim() || disabled}>
            Envoyer <kbd>↵</kbd>
          </button>
        </div>
      </div>
    </div>
  );
}
