"use client";

import { useState } from "react";
import ShipmentContextBar from "@/components/ShipmentContextBar";

const API_URL =
  process.env.NEXT_PUBLIC_RAG_API_URL ||
  "http://127.0.0.1:8000";

type Source = {
  citation?: string;
  source?: string;
  chunk_id?: string;
  chunk_index?: number | string | null;
};

type QueryResponse = {
  answer?: string;
  sources?: Source[];
  status?: string;
  retrieval_count?: number;
  top_score?: number;
  supporting_chunks?: number;
  threshold?: number;
  reason?: string;
};

export default function QuestionInputPage() {
  const [question, setQuestion] = useState("");

  const [isLoading, setIsLoading] =
    useState(false);

  const [responseData, setResponseData] =
    useState<QueryResponse | null>(null);

  const [error, setError] =
    useState("");

  const exampleQuestions = [
    "When does an exporter need an export license?",
    "What specific customs declarations are required for entry?",
    "What documents are required for customs clearance?",
  ];

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

    setIsLoading(true);
    setError("");
    setResponseData(null);

    try {
      const response = await fetch(
        `${API_URL}/query`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            question: trimmedQuestion,
          }),
        }
      );

      if (!response.ok) {
        let message =
          "The backend could not process your question.";

        try {
          const errorPayload =
            await response.json();

          if (errorPayload?.detail) {
            message =
              errorPayload.detail;
          }
        } catch {
          // Keep default error message.
        }

        throw new Error(message);
      }

      const payload: QueryResponse =
        await response.json();

      setResponseData(payload);
    } catch (requestError) {
      if (
        requestError instanceof Error
      ) {
        setError(
          requestError.message
        );
      } else {
        setError(
          "Unable to connect to the TradeRule AI backend."
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  function clearQuestion() {
    setQuestion("");
    setResponseData(null);
    setError("");
  }

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

          <h1>Question Input</h1>

          <p>
            Ask specific compliance questions
            regarding your active shipment profile.
          </p>
        </div>

        <div className="stat-card">
          <span>Response mode</span>
          <strong>Evidence-led</strong>
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
            Use a specific route, document,
            product, or restriction in your
            question.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* QUESTION INPUT */}

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
              disabled={isLoading}
              rows={6}
            />
          </div>

          {/* SUGGESTED QUESTIONS */}

          <div className="mb-5">
            <div className="form-label">
              Suggested questions
            </div>

            {exampleQuestions.map(
              (example, index) => (
                <button
                  key={index}
                  type="button"
                  className="chip cursor-pointer text-left"
                  onClick={() =>
                    setQuestion(
                      example
                    )
                  }
                  disabled={isLoading}
                >
                  {example}
                </button>
              )
            )}
          </div>

          {/* ACTION BUTTONS */}

          <div className="form-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading
                ? "Searching..."
                : "Get Answer"}
            </button>

            <button
              type="button"
              className="btn-secondary"
              onClick={clearQuestion}
              disabled={isLoading}
            >
              Clear question
            </button>
          </div>
        </form>

        {/* ================================================== */}
        {/* LOADING STATE */}
        {/* ================================================== */}

        {isLoading && (
          <div className="mt-6 p-4 rounded-lg border border-slate-200 bg-slate-50">
            <div className="font-medium">
              Searching compliance
              knowledge...
            </div>

            <p className="text-sm text-slate-500 mt-1 mb-0">
              TradeRule AI is retrieving
              relevant rules and generating
              a grounded answer.
            </p>
          </div>
        )}

        {/* ================================================== */}
        {/* ERROR STATE */}
        {/* ================================================== */}

        {error && !isLoading && (
          <div className="mt-6 p-4 rounded-lg border border-red-200 bg-red-50">
            <div className="font-medium text-red-700">
              Unable to get an answer
            </div>

            <p className="text-sm text-red-600 mt-1 mb-0">
              {error}
            </p>
          </div>
        )}

        {/* ================================================== */}
        {/* ANSWER + SOURCES */}
        {/* ================================================== */}

        {responseData &&
          !isLoading && (
            <div className="mt-8">

              {/* ============================================ */}
              {/* ANSWER */}
              {/* ============================================ */}

              <div className="mb-6">
                <div className="form-label">
                  Grounded Answer
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white">
                  <p className="whitespace-pre-wrap leading-7 mb-0">
                    {responseData.answer ||
                      "No relevant answer was returned by the backend."}
                  </p>
                </div>
              </div>

              {/* ============================================ */}
              {/* SOURCES */}
              {/* ============================================ */}

              <div className="mb-6">
                <div className="form-label">
                  Retrieved Sources
                </div>

                {responseData.sources &&
                responseData.sources.length >
                  0 ? (
                  <div className="space-y-3">

                    {responseData.sources.map(
                      (source, index) => (
                        <div
                          key={`${source.chunk_id || "source"}-${index}`}
                          className="p-4 rounded-lg border border-slate-200 bg-slate-50"
                        >
                          {/* SOURCE NAME */}

                          <div className="font-medium">
                            [
                            {source.citation ||
                              index + 1}
                            ]{" "}
                            {source.source ||
                              "Unknown source"}
                          </div>

                          {/* SOURCE METADATA */}

                          <div className="text-sm text-slate-600 mt-2 space-y-1">

                            <div>
                              <strong>
                                Chunk ID:
                              </strong>{" "}
                              {source.chunk_id ||
                                "N/A"}
                            </div>

                            <div>
                              <strong>
                                Chunk index:
                              </strong>{" "}
                              {source.chunk_index ??
                                "N/A"}
                            </div>

                          </div>
                        </div>
                      )
                    )}

                  </div>
                ) : (
                  <div className="p-4 rounded-lg border border-slate-200 bg-slate-50 text-sm text-slate-500">
                    No source information
                    was returned.
                  </div>
                )}
              </div>

              {/* ============================================ */}
              {/* RETRIEVAL DETAILS */}
              {/* ============================================ */}

              <div className="mb-4">
                <div className="form-label">
                  Retrieval Details
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

                  {/* RETRIEVED COUNT */}

                  <div className="p-3 rounded-lg border border-slate-200 bg-white">
                    <div className="text-xs text-slate-500">
                      Retrieved
                    </div>

                    <div className="font-semibold">
                      {
                        responseData.retrieval_count ??
                        0
                      }
                    </div>
                  </div>

                  {/* TOP SCORE */}

                  <div className="p-3 rounded-lg border border-slate-200 bg-white">
                    <div className="text-xs text-slate-500">
                      Top score
                    </div>

                    <div className="font-semibold">
                      {responseData.top_score !==
                      undefined
                        ? responseData.top_score.toFixed(
                            3
                          )
                        : "N/A"}
                    </div>
                  </div>

                  {/* SUPPORTING CHUNKS */}

                  <div className="p-3 rounded-lg border border-slate-200 bg-white">
                    <div className="text-xs text-slate-500">
                      Supporting chunks
                    </div>

                    <div className="font-semibold">
                      {
                        responseData.supporting_chunks ??
                        0
                      }
                    </div>
                  </div>

                  {/* STATUS */}

                  <div className="p-3 rounded-lg border border-slate-200 bg-white">
                    <div className="text-xs text-slate-500">
                      Status
                    </div>

                    <div className="font-semibold">
                      {responseData.status ||
                        "N/A"}
                    </div>
                  </div>

                </div>
              </div>

              {/* ============================================ */}
              {/* REASON */}
              {/* ============================================ */}

              {responseData.reason && (
                <div className="mt-4 p-4 rounded-lg border border-slate-200 bg-slate-50">
                  <div className="text-sm font-medium">
                    Retrieval explanation
                  </div>

                  <p className="text-sm text-slate-500 mt-1 mb-0">
                    {responseData.reason}
                  </p>
                </div>
              )}

            </div>
          )}
      </div>
    </div>
  );
}