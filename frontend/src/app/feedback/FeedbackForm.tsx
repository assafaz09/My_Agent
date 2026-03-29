"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Loader2, Send } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import { feedbackApi } from "@/services/api";

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

export function FeedbackForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || message.trim().length < 5) {
      toast.error("Please write at least a few words.");
      return;
    }
    setSubmitting(true);
    try {
      await feedbackApi.submit({
        message: message.trim(),
        name: name.trim() || undefined,
        email: email.trim() || undefined,
        _gotcha: honeypot || undefined,
      });
      toast.success("Thanks — your feedback was sent.");
      setMessage("");
      setName("");
      setEmail("");
      setHoneypot("");
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#ebe8f6] via-[#f4f1fb] to-[#e8e3f5] text-zinc-800">
      <Toaster position="top-right" toastOptions={TOAST_OPTIONS} />

      <header className="relative z-10 border-b border-violet-200/60 bg-white/65 backdrop-blur-xl shadow-sm shadow-violet-200/20">
        <div className="mx-auto flex max-w-lg items-center gap-4 px-5 py-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/80 px-3 py-2 text-sm font-medium text-violet-800 shadow-sm transition hover:border-violet-300 hover:bg-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to chat
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-lg px-5 py-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-violet-200/80 bg-white/90 p-8 shadow-lg shadow-violet-200/30 backdrop-blur-md"
        >
          <h1 className="font-sans text-2xl font-extrabold tracking-normal text-zinc-900">
            Send feedback
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            Tell me what worked, what didn&apos;t, or what you&apos;d like to see
            next. Your message goes straight to my inbox.
          </p>

          <form onSubmit={handleSubmit} className="relative mt-8 space-y-5">
            <div
              className="pointer-events-none absolute h-0 w-0 overflow-hidden opacity-0"
              aria-hidden
            >
              <input
                id="_gotcha"
                name="_gotcha"
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
              />
            </div>

            <div>
              <label
                htmlFor="fb-name"
                className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-zinc-500"
              >
                Name <span className="font-normal normal-case">(optional)</span>
              </label>
              <input
                id="fb-name"
                type="text"
                maxLength={120}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-violet-200/90 bg-white px-4 py-3 text-[15px] text-zinc-800 outline-none ring-violet-400/40 transition focus:border-violet-400 focus:ring-2"
                placeholder="Your name"
              />
            </div>

            <div>
              <label
                htmlFor="fb-email"
                className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-zinc-500"
              >
                Email <span className="font-normal normal-case">(optional)</span>
              </label>
              <input
                id="fb-email"
                type="email"
                maxLength={200}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-violet-200/90 bg-white px-4 py-3 text-[15px] text-zinc-800 outline-none ring-violet-400/40 transition focus:border-violet-400 focus:ring-2"
                placeholder="So I can reply if needed"
              />
            </div>

            <div>
              <label
                htmlFor="fb-message"
                className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-zinc-500"
              >
                Message
              </label>
              <textarea
                id="fb-message"
                required
                minLength={5}
                maxLength={8000}
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full resize-y rounded-xl border border-violet-200/90 bg-white px-4 py-3 text-[15px] text-zinc-800 outline-none ring-violet-400/40 transition focus:border-violet-400 focus:ring-2"
                placeholder="Your thoughts…"
              />
            </div>

            <motion.button
              type="submit"
              disabled={submitting}
              whileHover={{ scale: submitting ? 1 : 1.02 }}
              whileTap={{ scale: submitting ? 1 : 0.98 }}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-violet-300/50 transition disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Sending…
                </>
              ) : (
                <>
                  <Send className="h-5 w-5" />
                  Send feedback
                </>
              )}
            </motion.button>
          </form>
        </motion.div>
      </main>
    </div>
  );
}
