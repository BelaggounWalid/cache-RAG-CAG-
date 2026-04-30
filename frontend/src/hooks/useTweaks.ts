import { useEffect, useState } from "react";
import type { Tweaks } from "../types";

const KEY = "chacal.tweaks.v1";

const DEFAULTS: Tweaks = {
  theme: "default",
  accent: "teal",
  density: "cozy",
  showSuggestions: true,
  showStatus: true,
  userName: "Yanis L.",
  botName: "Chacal",
};

export function useTweaks() {
  const [tweaks, setTweaks] = useState<Tweaks>(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<Tweaks>) };
    } catch {}
    return DEFAULTS;
  });

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(tweaks));
    } catch {}
    const r = document.documentElement;
    r.setAttribute("data-theme", tweaks.theme === "default" ? "" : tweaks.theme);
    r.setAttribute("data-accent", tweaks.accent);
    r.setAttribute("data-density", tweaks.density);
  }, [tweaks]);

  const setTweak = <K extends keyof Tweaks>(k: K, v: Tweaks[K]) =>
    setTweaks((t) => ({ ...t, [k]: v }));

  return { tweaks, setTweak };
}
