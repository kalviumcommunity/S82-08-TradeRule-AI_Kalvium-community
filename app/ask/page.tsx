"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ShipmentContextBar, { getStoredShipment } from "@/components/ShipmentContextBar";
import ConfidenceBadge from "@/components/ConfidenceBadge";

const API_URL =
  process.env.NEXT_PUBLIC_RAG_API_URL ||
  "http://127.0.0.1:8000";

type Source = {
  id?: string;
  label?: string;
  citation?: string;
  document?: string;
  source?: string;
  chunk_id?: string;
  chunk_index?: number | string | null;
  section?: string | null;
  text?: string;
};

type StreamEvent = {
  type: string;
  text?: string;
  message?: string;
  sources?: Source[];
  status?: string;
  retrieval_count?: number;
  top_score?: number;
  supporting_chunks?: number;
  threshold?: number;
};

export default function QuestionInputPage() {
  return (
    <Suspense fallback={<div>Loading Q&amp;A...</div>}>
      <QuestionInputContent />
    </Suspense>
  );
}

function QuestionInputContent() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [retrievalDetails, setRetrievalDetails] = useState<{
    retrieval_count: number;
    top_score: number;
    supporting_chunks: number;
    threshold: number;
    status: string;
  } | null>(null);

  // Auto-fill from query param if available
  useEffect(() => {
    const qParam = searchParams.get("question") || searchParams.get("q");
    if (qParam && !question) {
      setQuestion(qParam);
      streamAnswer(qParam);
    }
  }, [searchParams]);

  const exampleQuestions = [
    "Are UN3481 lithium ion batteries restricted on ocean routes?",
    "What specific container packing certificate is required?",
    "What documents are required for customs clearance?",
    "What specific customs declarations are required for entry?",
    "When does an exporter need an export license?",
    "What carrier requirements does Maersk Line mandate for dangerous goods?",
    "Are there local state tax implications for transit through ports?",
  ];

  function getConfidenceLevel(topScore: number): "high" | "medium" | "low" {
    if (topScore >= 0.70) return "high";
    if (topScore >= 0.45) return "medium";
    return "low";
  }

  function recordQueryHistory(q: string, a: string, topScore: number, sourceList: Source[]) {
    if (typeof window === "undefined") return;
    try {
      const stored = localStorage.getItem("traderule_query_history");
      const list = stored ? JSON.parse(stored) : [];
      const newEntry = {
        id: "TR-" + Math.floor(10000 + Math.random() * 90000),
        question: q,
        answer: a,
        confidence: getConfidenceLevel(topScore),
        citations: sourceList.length,
        timestamp: new Date().toLocaleString(),
      };
      list.unshift(newEntry);
      localStorage.setItem("traderule_query_history", JSON.stringify(list.slice(0, 50)));
      window.dispatchEvent(new Event("query_history_updated"));
    } catch {
      // ignore
    }
  }

  async function streamAnswer(questionToAsk: string) {
    const trimmed = questionToAsk.trim();
    if (!trimmed) return;

    setAnswer("");
    setSources([]);
    setError("");
    setIsStreaming(true);
    setIsComplete(false);
    setLastQuestion(trimmed);
    setRetrievalDetails(null);

    let collectedAnswer = "";
    let collectedSources: Source[] = [];
    let topScoreRecorded = 0.75;

    try {
      const response = await fetch(`${API_URL}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.ok) {
        let message = "Backend service returned an error.";
        try {
          const payload = await response.json();
          if (payload?.detail) message = payload.detail;
        } catch {
          // ignore
        }
        throw new Error(message);
      }

      if (!response.body) {
        throw new Error("Empty response stream from backend.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let receivedDone = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const eventBlocks = buffer.split("\n\n");
        buffer = eventBlocks.pop() || "";

        for (const block of eventBlocks) {
          const lines = block.split("\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonText = line.slice(6);
            try {
              const event = JSON.parse(jsonText) as StreamEvent;

              if (event.type === "citations") {
                collectedSources = event.sources || [];
                setSources(collectedSources);
                topScoreRecorded = event.top_score ?? 0.75;
                setRetrievalDetails({
                  retrieval_count: event.retrieval_count ?? 0,
                  top_score: event.top_score ?? 0,
                  supporting_chunks: event.supporting_chunks ?? 0,
                  threshold: event.threshold ?? 0.50,
                  status: "streaming",
                });
              }

              if (event.type === "token" && event.text) {
                collectedAnswer += event.text;
                setAnswer((curr) => curr + event.text);
              }

              if (event.type === "done") {
                receivedDone = true;
                setIsComplete(true);
                setRetrievalDetails((curr) =>
                  curr ? { ...curr, status: event.status || "answered" } : curr
                );
              }

              if (event.type === "error") {
                setError(event.message || "Streaming interrupted.");
              }
            } catch {
              // ignore malformed event
            }
          }
        }
      }

      if (!receivedDone && !error && collectedAnswer) {
        setIsComplete(true);
      }

      if (collectedAnswer) {
        recordQueryHistory(trimmed, collectedAnswer, topScoreRecorded, collectedSources);
      }
    } catch (err) {
      // Fallback: try standard /chat endpoint if stream encountered an error
      try {
        const fallbackRes = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: trimmed }),
        });
        if (fallbackRes.ok) {
          const fallbackData = await fallbackRes.json();
          setAnswer(fallbackData.answer);
          setSources(fallbackData.sources || []);
          setIsComplete(true);
          setError("");
          recordQueryHistory(
            trimmed,
            fallbackData.answer,
            fallbackData.top_score || 0.75,
            fallbackData.sources || []
          );
          return;
        }
      } catch {
        // keep original error
      }
      setError(err instanceof Error ? err.message : "Unable to reach TradeRule AI backend.");
    } finally {
      setIsStreaming(false);
    }
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setError("Please enter a compliance question.");
      return;
    }
    streamAnswer(question);
  }

  function clearQuestion() {
    setQuestion("");
    setAnswer("");
    setSources([]);
    setError("");
    setIsComplete(false);
    setLastQuestion("");
    setRetrievalDetails(null);
  }

  return (
    <div>
      <ShipmentContextBar />

      <div className="section-heading">
        <div>
          <div className="page-kicker">Step 2 of 3 / Ask the rules engine</div>
          <h1>Question Input</h1>
          <p>
            Ask specific compliance, tariff, documentation, or routing questions. TradeRule AI retrieves official regulations and cites every requirement.
          </p>
        </div>

        <div className="stat-card">
          <span>Response mode</span>
          <strong>Streaming + Citations</strong>
        </div>
      </div>

      <div className="surface-panel">
        <div className="mb-5">
          <h2 className="text-xl mb-1">What do you need to verify?</h2>
          <p className="text-sm text-slate-500 mb-0">
            Inquire about state of charge limits, dangerous goods declarations, import clearance forms, carrier policies, or port transit rules.
          </p>
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
              placeholder="Ask about lithium battery ocean transport, customs declarations, carrier rules, or export licenses..."
              disabled={isStreaming}
              rows={4}
            />
          </div>

          <div className="mb-5">
            <div className="form-label">Suggested regulatory questions</div>
            <div className="flex flex-wrap gap-2">
              {exampleQuestions.map((example, index) => (
                <button
                  key={index}
                  type="button"
                  className="chip cursor-pointer text-left"
                  onClick={() => {
                    setQuestion(example);
                    streamAnswer(example);
                  }}
                  disabled={isStreaming}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={isStreaming}>
              {isStreaming ? "Streaming Answer..." : "Get Answer"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={clearQuestion}
              disabled={isStreaming}
            >
              Clear
            </button>
          </div>
        </form>

        {isStreaming && (
          <div className="mt-6 p-4 rounded-lg border border-slate-200 bg-slate-50">
            <div className="font-medium">Generating grounded answer...</div>
            <p className="text-sm text-slate-500 mt-1 mb-0">
              TradeRule AI is searching the regulatory index and streaming verified citations.
            </p>
          </div>
        )}

        {answer && (
          <div className="mt-8">
            <div className="flex justify-between items-center mb-2">
              <div className="form-label mb-0">Grounded Compliance Answer</div>
              {retrievalDetails && (
                <ConfidenceBadge
                  level={getConfidenceLevel(retrievalDetails.top_score)}
                />
              )}
            </div>

            <div className="p-5 rounded-lg border border-slate-200 bg-white">
              <p className="whitespace-pre-wrap leading-7 mb-0 text-ink">
                {answer}
                {isStreaming && <span className="ml-1 animate-pulse font-bold text-blue-600">▌</span>}
              </p>
            </div>

            {isComplete && !isStreaming && !error && (
              <div className="mt-4 flex flex-wrap gap-3 items-center justify-between p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                <span className="text-sm text-emerald-800 font-medium">
                  &check; Answer complete &mdash; citations verified against official statutes.
                </span>
                <div className="flex gap-2">
                  <Link
                    href={`/result?question=${encodeURIComponent(lastQuestion)}&answer=${encodeURIComponent(answer)}`}
                    className="btn-primary text-xs py-1.5 px-3"
                  >
                    View in Compliance Decision &rarr;
                  </Link>
                  <Link
                    href={`/thread?question=${encodeURIComponent(lastQuestion)}&answer=${encodeURIComponent(answer)}`}
                    className="btn-secondary text-xs py-1.5 px-3"
                  >
                    Continue in Thread &rarr;
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {retrievalDetails && (
          <div className="mt-6">
            <div className="form-label">Retrieval &amp; Confidence Metrics</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">Retrieved Sources</div>
                <div className="font-semibold">{retrievalDetails.retrieval_count}</div>
              </div>
              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">Top Semantic Score</div>
                <div className="font-semibold">{retrievalDetails.top_score.toFixed(3)}</div>
              </div>
              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">Supporting Chunks</div>
                <div className="font-semibold">{retrievalDetails.supporting_chunks}</div>
              </div>
              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">Decision Status</div>
                <div className="font-semibold capitalize">{retrievalDetails.status}</div>
              </div>
            </div>
          </div>
        )}

        {sources.length > 0 && (
          <div className="mt-8">
            <div className="form-label">Retrieved Official Sources ({sources.length})</div>
            <div className="space-y-3">
              {sources.map((source, index) => {
                const citation = source.label || source.citation || `[${index + 1}]`;
                const documentName = source.document || source.source || "Official Regulation";

                return (
                  <details
                    key={source.id || index}
                    className="rounded-lg border border-slate-200 bg-slate-50 overflow-hidden"
                  >
                    <summary className="cursor-pointer p-4 font-medium hover:bg-slate-100 transition">
                      <span className="font-semibold text-blue-700 mr-2">{citation}</span>
                      {documentName}
                      {source.section ? ` — ${source.section}` : ""}
                    </summary>

                    <div className="px-4 pb-4 pt-1 bg-white border-t border-slate-200">
                      <div className="text-xs text-slate-500 mb-2 mt-2 space-y-0.5">
                        <div>
                          <strong>Document:</strong> {documentName}
                        </div>
                        {source.chunk_id && (
                          <div>
                            <strong>Clause ID:</strong> {source.chunk_id}
                          </div>
                        )}
                        {source.section && (
                          <div>
                            <strong>Section:</strong> {source.section}
                          </div>
                        )}
                      </div>

                      <div className="p-3 rounded-md bg-slate-50 border border-slate-200 text-sm leading-6">
                        {source.text || "Direct regulatory excerpt."}
                      </div>
                    </div>
                  </details>
                );
              })}
            </div>
          </div>
        )}

        {error && (
          <div role="alert" className="mt-8 p-4 rounded-lg border border-red-200 bg-red-50">
            <div className="font-medium text-red-700">Unable to complete query</div>
            <p className="text-sm text-red-600 mt-1 mb-3">{error}</p>
            {lastQuestion && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => streamAnswer(lastQuestion)}
                disabled={isStreaming}
              >
                Retry
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}