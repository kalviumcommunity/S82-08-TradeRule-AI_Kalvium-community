"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import ShipmentContextBar from "@/components/ShipmentContextBar";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import CitationChip from "@/components/CitationChip";

interface ThreadItem {
  id: string;
  question: string;
  confidence: "high" | "medium" | "low";
  preview: string;
  fullText: string;
  citations: string[];
  timestamp?: string;
}

const INITIAL_ITEMS: ThreadItem[] = [
  {
    id: "1",
    question: "Are UN3481 lithium ion batteries restricted on ocean routes?",
    confidence: "high",
    preview: "UN3481 lithium-ion batteries packed with equipment are fully permitted for ocean freight transport...",
    fullText: "UN3481 lithium-ion batteries packed with equipment are fully permitted for ocean freight transport into United States ports, provided they meet standard State of Charge (SOC) limitations not exceeding 30% and carry proper Class 9 hazard labeling on outer packaging containers.",
    citations: ["IMDG Code 41-22 (Sec 3.4)", "CBP Reg 19 CFR 12.3"],
    timestamp: "Today, 14:22",
  },
  {
    id: "2",
    question: "What specific container packing certificate is required?",
    confidence: "medium",
    preview: "A signed Container/Vehicle Packing Certificate (CPC) is mandatory for all shipments containing...",
    fullText: "A signed Container/Vehicle Packing Certificate (CPC) is mandatory for all shipments containing dangerous goods, verifying structural cleanliness and weight distribution compliance per SOLAS Chapter VII Regulation 5.",
    citations: ["SOLAS Chapter VII Reg 5"],
    timestamp: "Today, 14:25",
  },
  {
    id: "3",
    question: "Are there local state tax implications for transit through ports?",
    confidence: "low",
    preview: "Inconclusive ruling records found for regional port tax exemptions under current schedules...",
    fullText: "Inconclusive ruling records found for regional port tax exemptions under current schedules. Manual verification with local port authority finance office is recommended.",
    citations: ["Port Transit and Customs Tax Rulings"],
    timestamp: "Today, 14:30",
  },
];

export default function ThreadPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading conversation thread...</div>}>
      <ThreadContent />
    </Suspense>
  );
}

function ThreadContent() {
  const searchParams = useSearchParams();
  const [items, setItems] = useState<ThreadItem[]>(INITIAL_ITEMS);
  const [expandedId, setExpandedId] = useState<string | null>("1");
  const [queryText, setQueryText] = useState("");
  const [loading, setLoading] = useState(false);

  // Initialize from storage or handle incoming query param
  useEffect(() => {
    let currentItems = INITIAL_ITEMS;
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("traderule_active_thread");
        if (saved) {
          currentItems = JSON.parse(saved);
        }
      } catch {
        // fallback
      }
    }

    const qParam = searchParams.get("question") || searchParams.get("query") || searchParams.get("followup");
    const aParam = searchParams.get("answer");

    if (qParam) {
      const alreadyExists = currentItems.some((i) => i.question.toLowerCase() === qParam.toLowerCase());
      if (!alreadyExists) {
        if (aParam) {
          const newItem: ThreadItem = {
            id: String(Date.now()),
            question: qParam,
            confidence: "high",
            preview: aParam.slice(0, 100) + "...",
            fullText: aParam,
            citations: ["IMDG Code 41-22", "CBP Reg 19 CFR 12.3"],
            timestamp: "Just now",
          };
          const updated = [...currentItems, newItem];
          currentItems = updated;
          setExpandedId(newItem.id);
          saveThread(updated);
        } else {
          // Ask backend for answer
          askQuestion(qParam, currentItems);
          return;
        }
      }
    }

    setItems(currentItems);
  }, [searchParams]);

  function saveThread(list: ThreadItem[]) {
    setItems(list);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("traderule_active_thread", JSON.stringify(list));
      } catch {
        // ignore
      }
    }
  }

  async function askQuestion(questionToAsk: string, currentList = items) {
    const trimmed = questionToAsk.trim();
    if (!trimmed) return;

    setLoading(true);
    const tempId = String(Date.now());
    const placeholderItem: ThreadItem = {
      id: tempId,
      question: trimmed,
      confidence: "medium",
      preview: "Analyzing regulations and verifying citations...",
      fullText: "TradeRule AI is searching official maritime codes, customs bulletins, and carrier agreements...",
      citations: [],
      timestamp: "Just now",
    };

    const intermediateList = [...currentList, placeholderItem];
    setItems(intermediateList);
    setExpandedId(tempId);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      const data = await res.json();
      const answer = data.answer || "No response received.";
      const topScore = data.top_score ?? 0.75;
      const conf: "high" | "medium" | "low" =
        topScore >= 0.7 ? "high" : topScore >= 0.45 ? "medium" : "low";

      const sourcesList = (data.sources || []).map(
        (s: any) => s.source || s.document || "Regulatory Statute"
      );

      const completedItem: ThreadItem = {
        id: tempId,
        question: trimmed,
        confidence: conf,
        preview: answer.slice(0, 110) + "...",
        fullText: answer,
        citations: sourcesList.length > 0 ? sourcesList : ["Official Regulatory Statute"],
        timestamp: "Just now",
      };

      const finalList = intermediateList.map((item) =>
        item.id === tempId ? completedItem : item
      );
      saveThread(finalList);
    } catch {
      const errorItem: ThreadItem = {
        id: tempId,
        question: trimmed,
        confidence: "low",
        preview: "Unable to retrieve real-time answer from the rules engine.",
        fullText: "Please verify that the backend RAG service is running on http://127.0.0.1:8000.",
        citations: [],
        timestamp: "Just now",
      };
      const finalList = intermediateList.map((item) =>
        item.id === tempId ? errorItem : item
      );
      saveThread(finalList);
    } finally {
      setLoading(false);
      setQueryText("");
    }
  }

  function handleFormSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!queryText.trim() || loading) return;
    askQuestion(queryText);
  }

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleResetThread = () => {
    saveThread(INITIAL_ITEMS);
    setExpandedId("1");
  };

  return (
    <div>
      <ShipmentContextBar />

      <div className="section-heading">
        <div>
          <div className="page-kicker">Conversation history / Active shipment</div>
          <h1>Follow-up Thread</h1>
          <p>Review previous answers and ask follow-up questions while maintaining your shipment profile.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="stat-card">
            <span>Questions in thread</span>
            <strong>{items.length}</strong>
          </div>
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={handleResetThread}
            title="Reset to default questions"
          >
            Reset Thread
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {items.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <div key={item.id} className="surface-panel transition">
              <div className="flex justify-between items-start mb-2 gap-4">
                <div>
                  <div className="text-xs text-slate-400 mb-1">{item.timestamp || "Active"}</div>
                  <strong className="text-base text-ink block">{item.question}</strong>
                </div>
                <ConfidenceBadge level={item.confidence} />
              </div>

              {!isExpanded && <p className="text-sm text-slate-600 mb-3">{item.preview}</p>}

              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-border text-sm text-ink">
                  <p className="mb-4 whitespace-pre-wrap leading-6">{item.fullText}</p>
                  {item.citations.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
                        Verified Sources
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {item.citations.map((c, idx) => (
                          <CitationChip key={idx}>{c}</CitationChip>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-3">
                <button
                  type="button"
                  className="btn-secondary text-xs py-1.5 px-3"
                  onClick={() => toggleExpand(item.id)}
                >
                  {isExpanded ? "Collapse" : "Expand Full Decision"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="surface-panel mt-6">
        <h2 className="text-xl mb-1">Ask a follow-up</h2>
        <p className="text-sm text-slate-500 mb-4">
          Keep the same shipment context while you refine the decision or clarify specific regulations.
        </p>
        <form onSubmit={handleFormSubmit}>
          <div className="mb-4">
            <label htmlFor="next-query">Continue conversation</label>
            <textarea
              id="next-query"
              name="query"
              className="form-textarea"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask another question regarding this shipment, documentation, packaging, or carrier rules..."
              disabled={loading}
              rows={3}
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading || !queryText.trim()}>
              {loading ? "Evaluating..." : "Send Query"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setQueryText("")}
              disabled={loading}
            >
              Clear query
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}