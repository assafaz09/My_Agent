import type { Metadata } from "next";
import { FeedbackForm } from "./FeedbackForm";

export const metadata: Metadata = {
  title: "Feedback — Assaf Azran",
  description:
    "Send feedback about Assaf Azran's personal AI agent — English UI, Hebrew supported.",
};

export default function FeedbackPage() {
  return <FeedbackForm />;
}
