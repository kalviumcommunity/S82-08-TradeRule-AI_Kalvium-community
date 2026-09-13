"use client";

import { useState } from "react";
import ShipmentContextBar from "@/components/ShipmentContextBar";

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
  const [question, setQuestion] =
    useState("");

  const [answer, setAnswer] =
    useState("");

  const [sources, setSources] =
    useState<Source[]>([]);

  const [isStreaming, setIsStreaming] =
    useState(false);

  const [isComplete, setIsComplete] =
    useState(false);

  const [error, setError] =
    useState("");

  const [lastQuestion, setLastQuestion] =
    useState("");

  const [
    retrievalDetails,
    setRetrievalDetails,
  ] = useState<{
    retrieval_count: number;
    top_score: number;
    supporting_chunks: number;
    threshold: number;
    status: string;
  } | null>(null);

  const exampleQuestions = [
    "When does an exporter need an export license?",
    "What specific customs declarations are required for entry?",
    "What documents are required for customs clearance?",
  ];

  // ==========================================================
  // STREAM ANSWER
  // ==========================================================

  async function streamAnswer(
    questionToAsk: string
  ) {
    setAnswer("");
    setSources([]);
    setError("");
    setIsStreaming(true);
    setIsComplete(false);
    setLastQuestion(questionToAsk);
    setRetrievalDetails(null);

    try {
      const response = await fetch(
        `${API_URL}/query/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            question:
              questionToAsk,
          }),
        }
      );

      if (!response.ok) {
        let message =
          "The backend could not start the streaming response.";

        try {
          const payload =
            await response.json();

          if (payload?.detail) {
            message =
              payload.detail;
          }
        } catch {
          // Keep default message.
        }

        throw new Error(message);
      }

      if (!response.body) {
        throw new Error(
          "The backend returned an empty stream."
        );
      }

      const reader =
        response.body.getReader();

      const decoder =
        new TextDecoder();

      let buffer = "";

      let receivedDoneEvent =
        false;

      while (true) {
        const {
          value,
          done,
        } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(
          value,
          {
            stream: true,
          }
        );

        const eventBlocks =
          buffer.split(
            "\n\n"
          );

        buffer =
          eventBlocks.pop() ||
          "";

        for (const block of eventBlocks) {
          const lines =
            block.split("\n");

          for (const line of lines) {
            if (
              !line.startsWith(
                "data: "
              )
            ) {
              continue;
            }

            const jsonText =
              line.slice(6);

            try {
              const event =
                JSON.parse(
                  jsonText
                ) as StreamEvent;

              // --------------------------------------------
              // CITATIONS EVENT
              // --------------------------------------------

              if (
                event.type ===
                "citations"
              ) {
                setSources(
                  event.sources ||
                    []
                );

                setRetrievalDetails(
                  {
                    retrieval_count:
                      event.retrieval_count ??
                      0,

                    top_score:
                      event.top_score ??
                      0,

                    supporting_chunks:
                      event.supporting_chunks ??
                      0,

                    threshold:
                      event.threshold ??
                      0,

                    status:
                      "streaming",
                  }
                );
              }

              // --------------------------------------------
              // TOKEN EVENT
              // --------------------------------------------

              if (
                event.type ===
                "token"
              ) {
                setAnswer(
                  (current) =>
                    current +
                    (event.text ||
                      "")
                );
              }

              // --------------------------------------------
              // DONE EVENT
              // --------------------------------------------

              if (
                event.type ===
                "done"
              ) {
                receivedDoneEvent =
                  true;

                setIsComplete(
                  true
                );

                setRetrievalDetails(
                  (current) =>
                    current
                      ? {
                          ...current,
                          status:
                            event.status ||
                            "answered",
                        }
                      : current
                );
              }

              // --------------------------------------------
              // ERROR EVENT
              // --------------------------------------------

              if (
                event.type ===
                "error"
              ) {
                setError(
                  event.message ||
                    "The answer stopped streaming."
                );

                setIsComplete(
                  false
                );
              }
            } catch {
              // Ignore malformed individual SSE events.
            }
          }
        }
      }

      // If stream ended without a done event,
      // treat it as interrupted.
      if (
        !receivedDoneEvent &&
        !error
      ) {
        setError(
          "The answer stream ended unexpectedly. Please retry."
        );

        setIsComplete(false);
      }
    } catch (requestError) {
      if (
        requestError instanceof
        Error
      ) {
        setError(
          requestError.message
        );
      } else {
        setError(
          "Unable to connect to the TradeRule AI backend."
        );
      }

      setIsComplete(false);
    } finally {
      setIsStreaming(false);
    }
  }

  // ==========================================================
  // FORM SUBMIT
  // ==========================================================

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const trimmedQuestion =
      question.trim();

    if (!trimmedQuestion) {
      setError(
        "Please enter a compliance question."
      );

      return;
    }

    await streamAnswer(
      trimmedQuestion
    );
  }

  // ==========================================================
  // RETRY
  // ==========================================================

  function retryAnswer() {
    if (!lastQuestion) {
      return;
    }

    streamAnswer(
      lastQuestion
    );
  }

  // ==========================================================
  // CLEAR
  // ==========================================================

  function clearQuestion() {
    setQuestion("");
    setAnswer("");
    setSources([]);
    setError("");
    setIsComplete(false);
    setLastQuestion("");
    setRetrievalDetails(null);
  }

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div>
      <ShipmentContextBar />

      {/* ================================================== */}
      {/* PAGE HEADER */}
      {/* ================================================== */}

      <div className="section-heading">
        <div>
          <div className="page-kicker">
            Step 2 of 3 / Ask the rules engine
          </div>

          <h1>
            Question Input
          </h1>

          <p>
            Ask specific compliance
            questions regarding your
            active shipment profile.
          </p>
        </div>

        <div className="stat-card">
          <span>
            Response mode
          </span>

          <strong>
            Streaming + Evidence
          </strong>
        </div>
      </div>

      {/* ================================================== */}
      {/* QUESTION PANEL */}
      {/* ================================================== */}

      <div className="surface-panel">

        <div className="mb-5">
          <h2 className="text-xl mb-1">
            What do you need to verify?
          </h2>

          <p className="text-sm text-slate-500 mb-0">
            Use a specific route,
            document, product, or
            restriction in your
            question.
          </p>
        </div>

        {/* ================================================== */}
        {/* FORM */}
        {/* ================================================== */}

        <form
          onSubmit={handleSubmit}
        >
          <div className="mb-4">

            <label
              htmlFor="question"
            >
              Compliance Question
            </label>

            <textarea
              id="question"
              name="question"
              className="form-textarea"
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              placeholder="Ask about tariffs, restricted substances, licenses, or clearance requirements..."
              disabled={
                isStreaming
              }
              rows={6}
            />

          </div>

          {/* ================================================= */}
          {/* SUGGESTIONS */}
          {/* ================================================= */}

          <div className="mb-5">

            <div className="form-label">
              Suggested questions
            </div>

            {exampleQuestions.map(
              (
                example,
                index
              ) => (
                <button
                  key={index}
                  type="button"
                  className="chip cursor-pointer text-left"
                  onClick={() =>
                    setQuestion(
                      example
                    )
                  }
                  disabled={
                    isStreaming
                  }
                >
                  {example}
                </button>
              )
            )}

          </div>

          {/* ================================================= */}
          {/* ACTION BUTTONS */}
          {/* ================================================= */}

          <div className="form-actions">

            <button
              type="submit"
              className="btn-primary"
              disabled={
                isStreaming
              }
            >
              {isStreaming
                ? "Streaming..."
                : "Get Answer"}
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={
                clearQuestion
              }
              disabled={
                isStreaming
              }
            >
              Clear question
            </button>

          </div>
        </form>

        {/* ================================================== */}
        {/* STREAMING STATUS */}
        {/* ================================================== */}

        {isStreaming && (
          <div className="mt-6 p-4 rounded-lg border border-slate-200 bg-slate-50">

            <div className="font-medium">
              Generating answer...
            </div>

            <p className="text-sm text-slate-500 mt-1 mb-0">
              TradeRule AI is retrieving
              supporting evidence and
              streaming the answer
              progressively.
            </p>

          </div>
        )}

        {/* ================================================== */}
        {/* ANSWER */}
        {/* ================================================== */}

        {answer && (
          <div className="mt-8">

            <div className="form-label">
              Grounded Answer
            </div>

            <div className="p-5 rounded-lg border border-slate-200 bg-white">

              <p className="whitespace-pre-wrap leading-7 mb-0">
                {answer}

                {isStreaming && (
                  <span className="ml-1">
                    ▌
                  </span>
                )}
              </p>

            </div>

            {/* COMPLETION STATUS */}

            {isComplete &&
              !isStreaming &&
              !error && (
                <div className="mt-2 text-sm text-slate-500">
                  ✓ Answer completed
                  and citations were
                  validated.
                </div>
              )}

          </div>
        )}

        {/* ================================================== */}
        {/* RETRIEVAL DETAILS */}
        {/* ================================================== */}

        {retrievalDetails && (
          <div className="mt-8">

            <div className="form-label">
              Retrieval Details
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">
                  Retrieved
                </div>

                <div className="font-semibold">
                  {
                    retrievalDetails.retrieval_count
                  }
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">
                  Top score
                </div>

                <div className="font-semibold">
                  {retrievalDetails.top_score.toFixed(
                    3
                  )}
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">
                  Supporting chunks
                </div>

                <div className="font-semibold">
                  {
                    retrievalDetails.supporting_chunks
                  }
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white">
                <div className="text-xs text-slate-500">
                  Status
                </div>

                <div className="font-semibold">
                  {
                    retrievalDetails.status
                  }
                </div>
              </div>

            </div>

          </div>
        )}

        {/* ================================================== */}
        {/* SOURCES */}
        {/* ================================================== */}

        {sources.length > 0 && (
          <div className="mt-8">

            <div className="form-label">
              Retrieved Sources
            </div>

            <div className="space-y-3">

              {sources.map(
                (
                  source,
                  index
                ) => {

                  const citation =
                    source.label ||
                    source.citation ||
                    `[${index + 1}]`;

                  const documentName =
                    source.document ||
                    source.source ||
                    "Unknown source";

                  return (
                    <details
                      key={
                        source.id ||
                        `${source.chunk_id || "source"}-${index}`
                      }
                      className="rounded-lg border border-slate-200 bg-slate-50"
                    >

                      {/* SOURCE HEADER */}

                      <summary className="cursor-pointer p-4 font-medium">

                        {citation}{" "}

                        {documentName}

                        {" — "}

                        {source.chunk_id ||
                          "Unknown chunk"}

                      </summary>

                      {/* SOURCE CONTENT */}

                      <div className="px-4 pb-4">

                        <div className="text-sm text-slate-600 mb-3 space-y-1">

                          <div>
                            <strong>
                              Document:
                            </strong>{" "}
                            {
                              documentName
                            }
                          </div>

                          <div>
                            <strong>
                              Chunk ID:
                            </strong>{" "}
                            {
                              source.chunk_id ||
                              "N/A"
                            }
                          </div>

                          {source.section && (
                            <div>
                              <strong>
                                Section:
                              </strong>{" "}
                              {
                                source.section
                              }
                            </div>
                          )}

                          {source.chunk_index !==
                            undefined &&
                            source.chunk_index !==
                              null && (
                              <div>
                                <strong>
                                  Chunk index:
                                </strong>{" "}
                                {
                                  source.chunk_index
                                }
                              </div>
                            )}

                        </div>

                        {/* ACTUAL RETRIEVED TEXT */}

                        <div className="p-4 rounded-md border border-slate-200 bg-white">

                          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                            Retrieved source text
                          </div>

                          <p className="text-sm leading-6 whitespace-pre-wrap mb-0">
                            {source.text ||
                              "Source text was not returned."}
                          </p>

                        </div>

                      </div>

                    </details>
                  );
                }
              )}

            </div>

          </div>
        )}

        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div
            role="alert"
            className="mt-8 p-4 rounded-lg border border-red-200 bg-red-50"
          >

            <div className="font-medium text-red-700">
              {answer
                ? "Streaming interrupted"
                : "Unable to get an answer"}
            </div>

            <p className="text-sm text-red-600 mt-1 mb-3">
              {error}
            </p>

            {lastQuestion && (
              <button
                type="button"
                className="btn-secondary"
                onClick={
                  retryAnswer
                }
                disabled={
                  isStreaming
                }
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