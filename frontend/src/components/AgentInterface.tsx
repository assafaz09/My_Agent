"use client";

import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  memo,
} from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  User,
  Bot,
  Globe,
  Sparkles,
  MessageCircle,
  MessageSquareText,
} from "lucide-react";
import {
  chatApi,
  type ChatRequest,
  type ChatResponse,
} from "@/services/api";
import toast, { Toaster } from "react-hot-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: string[];
}

type BlobMotion = { x: number; y: number; scale: number };

const CHAT_LANGUAGE = "en" as const;

const TOAST_OPTIONS = {
  style: {
    background: "rgba(255, 255, 255, 0.92)",
    backdropFilter: "blur(12px)",
    color: "#27272a",
    border: "1px solid rgba(139, 92, 246, 0.22)",
    borderRadius: "14px",
    boxShadow: "0 8px 32px -8px rgba(109, 40, 217, 0.2)",
  },
} as const;

/** Snappy spring so background motion reads clearly on each send */
const springMesh = {
  type: "spring" as const,
  stiffness: 58,
  damping: 13,
  mass: 0.78,
};

function randomInRange(min: number, max: number) {
  return min + Math.random() * (max - min);
}

/** Skips re-renders while typing in the textarea (same messages + loading). */
const ChatMessages = memo(function ChatMessages({
  messages,
  isLoading,
}: {
  messages: Message[];
  isLoading: boolean;
}) {
  return (
    <>
      {messages.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative pt-4 text-center"
        >
          <div className="pointer-events-none absolute left-1/2 top-0 h-px w-32 -translate-x-1/2 bg-gradient-to-r from-transparent via-violet-400 to-transparent" />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.15, type: "spring", stiffness: 120 }}
            className="relative mx-auto mb-10 inline-flex"
          >
            <div className="absolute inset-0 scale-150 rounded-full bg-violet-400/25 blur-3xl" />
            <div className="relative rounded-[2rem] border border-violet-200/70 bg-white/75 p-8 shadow-lg shadow-violet-200/40 ring-1 ring-white/80 backdrop-blur-md">
              <MessageCircle
                className="h-14 w-14 text-violet-600"
                strokeWidth={1.25}
              />
            </div>
          </motion.div>
          <motion.h2
            className="font-sans text-4xl font-extrabold leading-snug tracking-normal text-zinc-900 sm:text-5xl"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <span className="bg-gradient-to-r from-violet-600 via-fuchsia-600 to-cyan-600 bg-clip-text text-transparent">
              Hi there
            </span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="mx-auto mt-5 max-w-md text-base leading-relaxed text-zinc-600"
          >
            English or Hebrew — ask whatever you&apos;re curious about.
          </motion.p>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-10 flex flex-wrap justify-center gap-2"
          >
            {["Background", "Projects", "Contact", "Hebrew"].map((tag, i) => (
              <span
                key={tag}
                className="rounded-lg border border-violet-200/80 bg-white/70 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-zinc-600 shadow-sm"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                {tag}
              </span>
            ))}
          </motion.div>
        </motion.div>
      )}

      <AnimatePresence>
        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 16, filter: "blur(4px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ delay: index * 0.04, duration: 0.35 }}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div className="max-w-[min(100%,36rem)]">
              <div
                className={`flex items-start gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div
                  className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border shadow-lg ${
                    message.role === "user"
                      ? "border-cyan-500/30 bg-gradient-to-br from-cyan-500/80 to-violet-600/80"
                      : "border-violet-500/30 bg-gradient-to-br from-violet-600/90 to-fuchsia-700/80"
                  }`}
                >
                  {message.role === "user" ? (
                    <User className="h-4 w-4 text-white" />
                  ) : (
                    <Bot className="h-4 w-4 text-white" />
                  )}
                </div>
                <div
                  className={`min-w-0 rounded-2xl px-5 py-4 shadow-lg ${
                    message.role === "user"
                      ? "border border-cyan-300/60 bg-gradient-to-br from-cyan-500/90 via-violet-600 to-fuchsia-600 text-white shadow-cyan-200/50 ring-1 ring-white/30"
                      : "border border-violet-200/90 bg-white/90 text-zinc-800 shadow-violet-200/30 ring-1 ring-white/90 backdrop-blur-md"
                  }`}
                >
                  <p
                    dir="auto"
                    style={{ unicodeBidi: "plaintext" }}
                    className="whitespace-pre-wrap leading-relaxed text-[15px]"
                  >
                    {message.content}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {isLoading && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-start"
        >
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-violet-500/30 bg-gradient-to-br from-violet-600/90 to-fuchsia-700/80 shadow-lg">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="rounded-2xl border border-violet-200/90 bg-white/90 px-5 py-4 shadow-md backdrop-blur-md">
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-2 w-2 rounded-full bg-violet-500"
                    animate={{
                      opacity: [0.35, 1, 0.35],
                      y: [0, -4, 0],
                    }}
                    transition={{
                      duration: 0.9,
                      repeat: Infinity,
                      delay: i * 0.15,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </>
  );
});

export default function AgentInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [isTyping, setIsTyping] = useState(false);
  const [mesh, setMesh] = useState<{
    blobs: [BlobMotion, BlobMotion, BlobMotion, BlobMotion];
    grid: { x: number; y: number; rotate: number };
  }>({
    blobs: [
      { x: 0, y: 0, scale: 1 },
      { x: 0, y: 0, scale: 1 },
      { x: 0, y: 0, scale: 1 },
      { x: 0, y: 0, scale: 1 },
    ],
    grid: { x: 0, y: 0, rotate: 0 },
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const nudgeMesh = useCallback(() => {
    const drift = (mag: number) => (Math.random() - 0.5) * 2 * mag;
    setMesh({
      blobs: [
        { x: drift(200), y: drift(160), scale: randomInRange(0.72, 1.38) },
        { x: drift(180), y: drift(170), scale: randomInRange(0.75, 1.34) },
        { x: drift(150), y: drift(130), scale: randomInRange(0.78, 1.28) },
        { x: drift(165), y: drift(155), scale: randomInRange(0.74, 1.36) },
      ],
      grid: {
        x: drift(72),
        y: drift(72),
        rotate: drift(5.5),
      },
    });
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
  }, []);

  useEffect(() => {
    return () => {
      if (typingHideTimerRef.current !== null) {
        clearTimeout(typingHideTimerRef.current);
      }
    };
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    nudgeMesh();

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        message: input,
        session_id: sessionId,
        language: CHAT_LANGUAGE,
      };

      const response: ChatResponse = await chatApi.sendMessage(request);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      toast.error("Failed to send message. Please try again.");
      console.error("Chat error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    setIsTyping(true);

    const target = e.target;
    target.style.height = "auto";
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`;

    if (typingHideTimerRef.current !== null) {
      clearTimeout(typingHideTimerRef.current);
    }
    typingHideTimerRef.current = setTimeout(() => {
      typingHideTimerRef.current = null;
      setIsTyping(false);
    }, 1000);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#ebe8f6] via-[#f4f1fb] to-[#e8e3f5] text-zinc-800">
      <Toaster position="top-right" toastOptions={TOAST_OPTIONS} />

      {/* Ambient mesh — shifts on each send */}
      <div className="pointer-events-none fixed inset-0" aria-hidden>
        <motion.div
          className="absolute -top-40 right-[-10%] h-[28rem] w-[28rem] rounded-full bg-violet-500/35 blur-[120px]"
          animate={{
            x: mesh.blobs[0].x,
            y: mesh.blobs[0].y,
            scale: mesh.blobs[0].scale,
          }}
          transition={springMesh}
        />
        <motion.div
          className="absolute top-[35%] -left-32 h-[22rem] w-[22rem] rounded-full bg-fuchsia-500/30 blur-[100px]"
          animate={{
            x: mesh.blobs[1].x,
            y: mesh.blobs[1].y,
            scale: mesh.blobs[1].scale,
          }}
          transition={springMesh}
        />
        <div className="absolute bottom-[-5%] left-1/2 -translate-x-1/2">
          <motion.div
            className="h-72 w-[min(90%,56rem)] rounded-full bg-indigo-500/28 blur-[90px]"
            animate={{
              x: mesh.blobs[2].x,
              y: mesh.blobs[2].y,
              scale: mesh.blobs[2].scale,
            }}
            transition={springMesh}
          />
        </div>
        <motion.div
          className="absolute bottom-24 right-10 h-40 w-40 rounded-full bg-cyan-400/22 blur-[70px]"
          animate={{
            x: mesh.blobs[3].x,
            y: mesh.blobs[3].y,
            scale: mesh.blobs[3].scale,
          }}
          transition={springMesh}
        />
      </div>

      {/* Grid + vignette */}
      <motion.div
        className="pointer-events-none fixed inset-0 opacity-[0.55]"
        style={{
          transformOrigin: "50% 42%",
          backgroundImage: `
            linear-gradient(rgba(91, 33, 182, 0.07) 1px, transparent 1px),
            linear-gradient(90deg, rgba(91, 33, 182, 0.07) 1px, transparent 1px)
          `,
          backgroundSize: "72px 72px",
          maskImage:
            "radial-gradient(ellipse 75% 65% at 50% 42%, black 20%, transparent 72%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 75% 65% at 50% 42%, black 20%, transparent 72%)",
        }}
        animate={{
          x: mesh.grid.x,
          y: mesh.grid.y,
          rotate: mesh.grid.rotate,
        }}
        transition={{ ...springMesh, stiffness: 52, damping: 12 }}
        aria-hidden
      />

      {/* Scan-line shimmer (very subtle) */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.04] mix-blend-multiply"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(91, 33, 182, 0.08) 2px, rgba(91, 33, 182, 0.08) 3px)",
        }}
        aria-hidden
      />

      <header className="relative z-10 border-b border-violet-200/60 bg-white/65 backdrop-blur-xl shadow-sm shadow-violet-200/20">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:py-4">
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-4"
          >
            <div className="relative shrink-0">
              <div className="absolute inset-0 rounded-2xl bg-violet-400/50 blur-xl" />
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-violet-400/50 bg-gradient-to-br from-violet-600 to-fuchsia-600 shadow-[0_8px_28px_-6px_rgba(109,40,217,0.45)]">
                <Sparkles className="h-7 w-7 text-white" strokeWidth={1.75} />
              </div>
            </div>
            <div>
              <div className="flex flex-wrap items-baseline gap-3">
                <h1 className="font-sans text-2xl font-extrabold tracking-normal text-zinc-900 sm:text-3xl">
                  Assaf Azran
                </h1>
                <span
                  className="rounded-full border border-violet-300 bg-violet-100/90 px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-800"
                  title="This product is in beta"
                >
                  Beta
                </span>
              </div>
              <p className="mt-1 max-w-md text-sm text-zinc-600">
                Personal AI agent — one conversation, two languages.
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
            className="flex flex-wrap items-center justify-center gap-2 sm:justify-end"
          >
            <Link
              href="/feedback"
              className="inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/80 px-4 py-2 text-xs font-medium text-zinc-700 shadow-sm backdrop-blur-sm transition hover:border-violet-300 hover:bg-white"
            >
              <MessageSquareText className="h-3.5 w-3.5 text-violet-600" />
              Feedback
            </Link>
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/80 px-4 py-2 text-xs font-medium text-zinc-700 shadow-sm backdrop-blur-sm">
              <Globe className="h-3.5 w-3.5 text-violet-600" />
              English UI · Hebrew supported
            </div>
          </motion.div>
        </div>
      </header>

      <div className="relative z-10 flex h-[calc(100dvh-5.5rem)] flex-col sm:h-[calc(100vh-5.5rem)]">
        <main className="flex min-h-0 flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-8">
            <div className="mx-auto max-w-2xl space-y-8">
              <ChatMessages messages={messages} isLoading={isLoading} />
            </div>
            <div ref={messagesEndRef} />
          </div>

          <div className="relative border-t border-violet-200/70 bg-white/75 px-4 py-5 shadow-[0_-12px_40px_-24px_rgba(109,40,217,0.12)] backdrop-blur-2xl sm:px-8">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-300/80 to-transparent" />
            <div className="mx-auto max-w-2xl">
              <motion.div
                className={`group relative rounded-2xl border bg-white/95 shadow-[0_8px_40px_-12px_rgba(109,40,217,0.18)] transition-[border-color,box-shadow] duration-300 ${
                  isTyping
                    ? "border-violet-400 shadow-[0_0_36px_-8px_rgba(139,92,246,0.35)]"
                    : "border-violet-200/90 hover:border-violet-300"
                }`}
              >
                <textarea
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask in English or Hebrew…"
                  className="w-full resize-none rounded-2xl bg-transparent px-5 py-4 pr-16 text-[15px] text-zinc-800 placeholder:text-zinc-400 focus:outline-none"
                  rows={1}
                  style={{ minHeight: "56px", maxHeight: "120px" }}
                />
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="pointer-events-none absolute right-16 top-1/2 -translate-y-1/2"
                  >
                    <Sparkles className="h-4 w-4 text-violet-500" />
                  </motion.div>
                )}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.06 }}
                  whileTap={{ scale: 0.94 }}
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  className={`absolute right-2.5 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-xl transition-all ${
                    input.trim() && !isLoading
                      ? "bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-300/60"
                      : "cursor-not-allowed bg-zinc-200 text-zinc-400"
                  }`}
                  aria-label="Send message"
                >
                  <Send className="h-5 w-5" />
                </motion.button>
              </motion.div>
              <p className="mt-3 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
