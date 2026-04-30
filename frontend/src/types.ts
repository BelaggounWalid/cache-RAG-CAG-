export interface Citation {
  page: number;
  section_l1?: string | null;
  section_l2?: string | null;
  score?: number | null;
  page_type?: string | null;
  text_preview?: string | null;
}

export interface Message {
  id: string;
  role: "user" | "bot";
  text: string;
  time: string;
  citations?: Citation[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  meta: string;
  group: "today" | "yesterday" | "week" | "older";
  n_messages: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  messages: Message[];
}

export interface IndexStatus {
  ready: boolean;
  n_chunks: number;
  catalog: string;
  model_dense: string;
  model_sparse: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: Citation[];
  routing: { boost?: string[] };
  latency_ms: number;
}

export interface Tweaks {
  theme: "default" | "midnight" | "warm";
  accent: "teal" | "indigo" | "amber" | "lime" | "orange";
  density: "compact" | "cozy" | "roomy";
  showSuggestions: boolean;
  showStatus: boolean;
  userName: string;
  botName: string;
}
