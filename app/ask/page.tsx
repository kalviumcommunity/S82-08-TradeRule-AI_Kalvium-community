"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ShipmentContextBar from "@/components/ShipmentContextBar";

export default function QuestionInputPage() {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const exampleQuestions = [
    "Are UN3481 lithium ion batteries restricted on ocean routes?",
    "What specific customs declarations are required for entry at Los Angeles?",
    "Is a certificate of origin mandatory under current trade agreements?",
  ];

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion }),
      });

      if (!response.ok) {
        router.push("/result-error");
        return;
      }

      const payload = await response.json();
      const answer = payload.answer ?? "No relevant answer was returned by the backend.";
      const answerParam = encodeURIComponent(answer);
      const questionParam = encodeURIComponent(trimmedQuestion);

      router.push(`/result?answer=${answerParam}&question=${questionParam}`);
    } catch {
      router.push("/result-error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div>
      <ShipmentContextBar />
      <div className="section-heading">
        <div>
          <div className="page-kicker">Step 2 of 3 / Ask the rules engine</div>
          <h1>Question Input</h1>
          <p>Ask specific compliance questions regarding your active shipment profile.</p>
        </div>
        <div className="stat-card">
          <span>Response mode</span>
          <strong>Evidence-led</strong>
        </div>
      </div>

      <div className="surface-panel">
        <div className="mb-5">
          <h2 className="text-xl mb-1">What do you need to verify?</h2>
          <p className="text-sm text-slate-500 mb-0">Use a specific route, document, product, or restriction in your question.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="question">Compliance Question</label>
            <textarea
              id="question"
              name="question"
              className="form-textarea"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask specific questions regarding tariffs, restricted substances, or clearance requirements..."
            />
          </div>

          <div className="mb-5">
            <div className="form-label">Suggested questions</div>
            {exampleQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                className="chip cursor-pointer text-left"
                onClick={() => setQuestion(q)}
              >
                {q}
              </button>
            ))}
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={isLoading}>
              {isLoading ? "Getting Answer..." : "Get Answer"}
            </button>
            <button type="button" className="btn-secondary" onClick={() => setQuestion("")}>
              Clear question
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}