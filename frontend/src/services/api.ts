const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://my-agent-swart.vercel.app";

const CHAT_TIMEOUT_MS = 30_000;

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
