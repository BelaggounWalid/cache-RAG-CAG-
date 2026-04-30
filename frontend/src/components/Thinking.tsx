import { useEffect, useState } from "react";

const STEPS = [
  { id: "analysing", label: "Analyse de la question" },
  { id: "retrieving", label: "Recherche dans l'index" },
  { id: "extracting", label: "Extraction des passages" },
  { id: "synthesizing", label: "Synthèse de la réponse" },
];

export function Thinking({
  botName,
  externalStep,
}: {
  botName: string;
  externalStep?: string | null;
}) {
  // If a stream supplies the step, use it; otherwise auto-advance.
  const [step, setStep] = useState(0);
  useEffect(() => {
    if (externalStep) {
      const idx = STEPS.findIndex((s) => s.id === externalStep);
      if (idx >= 0) setStep(idx);
      return;
    }
    const t = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 600);
    return () => clearInterval(t);
  }, [externalStep]);

  return (
    <div className="msg bot">
      <div className="ava">
        {botName
          .split(" ")
          .map((s) => s[0])
          .join("")
          .toUpperCase()
          .slice(0, 2)}
      </div>
      <div className="body">
        <div className="who">
          <span className="n">{botName}</span>
          <span className="t">en cours…</span>
        </div>
        <div className="thinking">
          <div className="typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
          {STEPS.map((s, i) => (
            <span
              key={s.id}
              className={"step " + (i < step ? "done" : i === step ? "cur" : "")}
            >
              {i < step && "✓ "}
              {s.label}
              {i < STEPS.length - 1 ? " ›" : ""}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
