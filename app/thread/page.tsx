"use client";

import { useState } from "react";
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
}

export default function ThreadPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const items: ThreadItem[] = [
    {
      id: "1",
      question: "Are UN3481 lithium ion batteries restricted on ocean routes?",
      confidence: "high",
      preview: "UN3481 lithium-ion batteries packed with equipment are fully permitted for ocean freight transport...",
      fullText: "UN3481 lithium-ion batteries packed with equipment are fully permitted for ocean freight transport into United States ports, provided they meet standard State of Charge (SOC) limitations not exceeding 30% and carry proper Class 9 hazard labeling on outer packaging containers.",
      citations: ["IMDG Code 41-22 (Sec 3.4)", "CBP Reg 19 CFR 12.3"],
    },
    {
      id: "2",
      question: "What specific container packing certificate is required?",
      confidence: "medium",
      preview: "A signed Container/Vehicle Packing Certificate (CPC) is mandatory for all shipments containing...",
      fullText: "A signed Container/Vehicle Packing Certificate (CPC) is mandatory for all shipments containing dangerous goods, verifying structural cleanliness and weight distribution compliance.",
      citations: ["SOLAS Chapter VII Reg 5"],
    },
    {
      id: "3",
      question: "Are there local state tax implications for transit through ports?",
      confidence: "low",
      preview: "Inconclusive ruling records found for regional port tax exemptions under current schedules...",
      fullText: "Inconclusive ruling records found for regional port tax exemptions under current schedules. Manual verification with local port authority finance office is recommended.",
      citations: [],
    },
  ];

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div>
      <ShipmentContextBar />
      <div className="section-heading">
        <div>
          <div className="page-kicker">Conversation history / Active shipment</div>
          <h1>Follow-up Thread</h1>
          <p>Review previous answers and keep the compliance conversation in one place.</p>
        </div>
        <div className="stat-card"><span>Questions in thread</span><strong>{items.length}</strong></div>
      </div>

      {items.map((item) => {
        const isExpanded = expandedId === item.id;
        return (
          <div key={item.id} className="surface-panel mb-4">
            <div className="flex justify-between items-center mb-2">
              <strong className="text-base text-ink">{item.question}</strong>
              <ConfidenceBadge level={item.confidence} />
            </div>
            <p className="text-sm mb-3">{item.preview}</p>

            {isExpanded && (
              <div className="mb-4 pt-3 border-t border-border text-sm text-ink">
                <p className="mb-3">{item.fullText}</p>
                {item.citations.length > 0 && (
                  <div>
                    {item.citations.map((c, idx) => (
                      <CitationChip key={idx}>{c}</CitationChip>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              type="button"
              className="btn-secondary text-xs py-2 px-4"
              onClick={() => toggleExpand(item.id)}
            >
              {isExpanded ? "Collapse" : "Expand"}
            </button>
          </div>
        );
      })}

      <div className="surface-panel mt-6">
        <h2 className="text-xl mb-1">Ask a follow-up</h2>
        <p className="text-sm text-slate-500 mb-4">Keep the same shipment context while you refine the decision.</p>
        <form action="/thread" method="GET">
          <div className="mb-4">
            <label htmlFor="next-query">Continue conversation</label>
            <textarea
              id="next-query"
              name="query"
              className="form-textarea"
              placeholder="Ask another question regarding this shipment context..."
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">
              Send Query
            </button>
            <button type="reset" className="btn-secondary">
              Clear query
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}