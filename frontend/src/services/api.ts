const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://my-agent-swart.vercel.app";

const CHAT_TIMEOUT_MS = 30_000;

/** Formspree form endpoint: https://formspree.io/f/yourFormId */
function getFormspreeEndpoint(): string {
  const full = process.env.NEXT_PUBLIC_FORMSPREE_URL?.trim();
  if (full) return full.replace(/\/$/, "");
  const id = process.env.NEXT_PUBLIC_FORMSPREE_FORM_ID?.trim();
  if (id) return `https://formspree.io/f/${id}`;
  return "";
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  language?: "en" | "he";
}

export interface ChatResponse {
  response: string;
  session_id: string;
  language: string;
  sources: string[];
  timestamp: string;
}

export const chatApi = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        signal: controller.signal,
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `HTTP ${res.status}`);
      }
      return (await res.json()) as ChatResponse;
    } finally {
      clearTimeout(t);
    }
  },
};

const FORMSPREE_TIMEOUT_MS = 25_000;

export interface FeedbackPayload {
  message: string;
  name?: string;
  email?: string;
  /** Formspree honeypot — must stay empty */
  _gotcha?: string;
}

export const feedbackApi = {
  submit: async (data: FeedbackPayload): Promise<{ ok: boolean }> => {
    const endpoint = getFormspreeEndpoint();
    if (!endpoint) {
      throw new Error(
        "Feedback is not configured. Set NEXT_PUBLIC_FORMSPREE_URL or NEXT_PUBLIC_FORMSPREE_FORM_ID in frontend/.env",
      );
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FORMSPREE_TIMEOUT_MS);
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          name: data.name?.trim() || "",
          email: data.email?.trim() || "",
          message: data.message.trim(),
          _subject: "Personal AI agent — feedback",
          _gotcha: data._gotcha?.trim() || "",
        }),
        signal: controller.signal,
      });

      const text = await res.text().catch(() => "");
      if (!res.ok) {
        let detail = text || `HTTP ${res.status}`;
        try {
          const j = JSON.parse(text) as { error?: string; errors?: unknown };
          if (typeof j.error === "string") detail = j.error;
        } catch {
          /* keep text */
        }
        throw new Error(detail);
      }

      try {
        return text ? (JSON.parse(text) as { ok: boolean }) : { ok: true };
      } catch {
        return { ok: true };
      }
    } finally {
      clearTimeout(timer);
    }
  },
};
