// Minimal stroke icons — direct port of design/icons.jsx.
const s = {
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export const Ic = {
  Plus: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.6}>
      <path d="M8 3v10M3 8h10" />
    </svg>
  ),
  Search: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.6}>
      <circle cx="7" cy="7" r="4.2" />
      <path d="M10.2 10.2 13 13" />
    </svg>
  ),
  Send: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.6}>
      <path d="m3 13 11-5-11-5 1.6 5L9 8l-4.4 0z" />
    </svg>
  ),
  Copy: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
      <path d="M3 10.5V3a.5.5 0 0 1 .5-.5h7" />
    </svg>
  ),
  Up: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.6}>
      <path d="M5 9.5 8 6l3 3.5" />
    </svg>
  ),
  Down: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.6}>
      <path d="M5 6.5 8 10l3-3.5" />
    </svg>
  ),
  Refresh: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <path d="M13 8a5 5 0 1 1-1.5-3.5L13 6V3" />
    </svg>
  ),
  Share: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <circle cx="12" cy="3.5" r="1.5" />
      <circle cx="4" cy="8" r="1.5" />
      <circle cx="12" cy="12.5" r="1.5" />
      <path d="m5.3 7.2 5.4-2.8M5.3 8.8l5.4 2.8" />
    </svg>
  ),
  Cog: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.4}>
      <circle cx="8" cy="8" r="2.2" />
      <path d="M8 1.8v1.6M8 12.6v1.6M14.2 8h-1.6M3.4 8H1.8m10.4-4.2-1.1 1.1M4.7 11.3l-1.1 1.1m0-8.8 1.1 1.1m6.5 6.5 1.1 1.1" />
    </svg>
  ),
  Source: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <path d="M3 3.5h6.5L13 7v5.5a1 1 0 0 1-1 1H3a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5z" />
      <path d="M9.5 3.5V7H13" />
    </svg>
  ),
  Filter: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <path d="M2.5 4h11l-4 5v4l-3-1.5V9l-4-5z" />
    </svg>
  ),
  Db: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.4}>
      <ellipse cx="8" cy="3.6" rx="5" ry="1.6" />
      <path d="M3 3.6v8.8c0 .9 2.2 1.6 5 1.6s5-.7 5-1.6V3.6" />
      <path d="M3 7.6c0 .9 2.2 1.6 5 1.6s5-.7 5-1.6" />
    </svg>
  ),
  Sparkle: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.4}>
      <path d="M8 2.5v3M8 10.5v3M2.5 8h3M10.5 8h3M4 4l1.6 1.6M10.4 10.4 12 12M12 4l-1.6 1.6M5.6 10.4 4 12" />
    </svg>
  ),
  Book: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.4}>
      <path d="M2.5 3.5h4a2 2 0 0 1 2 2v8a1.5 1.5 0 0 0-1.5-1.5h-4.5z" />
      <path d="M13.5 3.5h-4a2 2 0 0 0-2 2v8a1.5 1.5 0 0 1 1.5-1.5h4.5z" />
    </svg>
  ),
  Pin: () => (
    <svg viewBox="0 0 16 16" {...s} strokeWidth={1.4}>
      <path d="M9.5 2.5 13.5 6.5 11.5 7l-.5 4-3-3-3 3 3-3-3-3 4-.5z" />
    </svg>
  ),
  Trash: () => (
    <svg viewBox="0 0 16 16" {...s}>
      <path d="M3 4.5h10M6 4.5V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1.5M5 4.5v8a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-8" />
    </svg>
  ),
};
