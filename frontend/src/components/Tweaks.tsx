import { useState } from "react";
import type { Tweaks as TweaksType } from "../types";

interface Props {
  tweaks: TweaksType;
  setTweak: <K extends keyof TweaksType>(k: K, v: TweaksType[K]) => void;
}

export function TweaksPanel({ tweaks, setTweak }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className={"twk-fab " + (open ? "is-open" : "")}
        onClick={() => setOpen((o) => !o)}
        aria-label="Préférences"
        title="Préférences"
      >
        <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth={1.4}>
          <circle cx="8" cy="8" r="2.2" />
          <path d="M8 1.8v1.6M8 12.6v1.6M14.2 8h-1.6M3.4 8H1.8m10.4-4.2-1.1 1.1M4.7 11.3l-1.1 1.1m0-8.8 1.1 1.1m6.5 6.5 1.1 1.1" />
        </svg>
      </button>

      {open && (
        <div className="twk-panel">
          <div className="twk-hd">
            <b>Préférences</b>
            <button className="twk-x" onClick={() => setOpen(false)}>
              ✕
            </button>
          </div>
          <div className="twk-body">
            <Section>Thème</Section>
            <Radio
              label="Ambiance"
              value={tweaks.theme}
              options={[
                { v: "default", l: "Slate" },
                { v: "midnight", l: "Midnight" },
                { v: "warm", l: "Warm" },
              ]}
              onChange={(v) => setTweak("theme", v as TweaksType["theme"])}
            />
            <Select
              label="Accent"
              value={tweaks.accent}
              options={[
                { v: "teal", l: "Teal (mint)" },
                { v: "indigo", l: "Indigo" },
                { v: "amber", l: "Amber" },
                { v: "lime", l: "Lime" },
                { v: "orange", l: "Orange industriel" },
              ]}
              onChange={(v) => setTweak("accent", v as TweaksType["accent"])}
            />
            <Radio
              label="Densité"
              value={tweaks.density}
              options={[
                { v: "compact", l: "Compact" },
                { v: "cozy", l: "Cozy" },
                { v: "roomy", l: "Roomy" },
              ]}
              onChange={(v) => setTweak("density", v as TweaksType["density"])}
            />

            <Section>Contenu</Section>
            <Toggle
              label="Suggestions au-dessus du composer"
              value={tweaks.showSuggestions}
              onChange={(v) => setTweak("showSuggestions", v)}
            />
            <Toggle
              label="Bandeau statut (Index prêt)"
              value={tweaks.showStatus}
              onChange={(v) => setTweak("showStatus", v)}
            />
            <Text
              label="Nom utilisateur"
              value={tweaks.userName}
              onChange={(v) => setTweak("userName", v)}
            />
            <Text
              label="Nom du bot"
              value={tweaks.botName}
              onChange={(v) => setTweak("botName", v)}
            />
          </div>
        </div>
      )}
    </>
  );
}

const Section = ({ children }: { children: React.ReactNode }) => (
  <div className="twk-sect">{children}</div>
);

function Radio({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { v: string; l: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="twk-row">
      <div className="twk-lbl">
        <span>{label}</span>
      </div>
      <div className="twk-seg">
        {options.map((o) => (
          <button
            key={o.v}
            className={"twk-seg-b " + (o.v === value ? "is-on" : "")}
            onClick={() => onChange(o.v)}
            type="button"
          >
            {o.l}
          </button>
        ))}
      </div>
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { v: string; l: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="twk-row twk-row-h">
      <div className="twk-lbl">
        <span>{label}</span>
      </div>
      <select
        className="twk-field"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.v} value={o.v}>
            {o.l}
          </option>
        ))}
      </select>
    </div>
  );
}

function Toggle({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="twk-row twk-row-h">
      <div className="twk-lbl">
        <span>{label}</span>
      </div>
      <button
        type="button"
        className={"twk-toggle " + (value ? "is-on" : "")}
        onClick={() => onChange(!value)}
      >
        <span className="twk-toggle-dot" />
      </button>
    </div>
  );
}

function Text({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="twk-row">
      <div className="twk-lbl">
        <span>{label}</span>
      </div>
      <input
        className="twk-field"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
