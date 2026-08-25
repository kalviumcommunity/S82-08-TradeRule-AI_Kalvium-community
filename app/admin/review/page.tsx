"use client";

import { useState } from "react";
import ConfidenceBadge from "@/components/ConfidenceBadge";

interface AuditRow {
  question: string;
  confidence: "high" | "medium" | "low";
  citations: number;
  timestamp: string;
}

export default function AdminReviewPage() {
  const [filter, setFilter] = useState("all");

  const rows: AuditRow[] = [
    {
      question: "Are UN3481 lithium ion batteries restricted on ocean routes?",
      confidence: "high",
      citations: 2,
      timestamp: "2026-06-14 14:22",
    },
    {
      question: "What specific container packing certificate is required?",
      confidence: "medium",
      citations: 1,
      timestamp: "2026-06-14 13:05",
    },
    {
      question: "Are there local state tax implications for transit through ports?",
      confidence: "low",
      citations: 0,
      timestamp: "2026-06-14 11:40",
    },
    {
      question: "What documentation is needed for chemical compound transit?",
      confidence: "high",
      citations: 3,
      timestamp: "2026-06-14 09:15",
    },
  ];

  const filteredRows = rows.filter(
    (r) => filter === "all" || r.confidence === filter
  );

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Administration / Audit log</div>
          <h1>Confidence Review</h1>
          <p>Monitor answer quality and source coverage across recent compliance questions.</p>
        </div>
        <button type="button" className="btn-secondary">
          Export logs
        </button>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Total reviewed</span><strong>{rows.length}</strong></div>
        <div className="stat-card"><span>High confidence</span><strong>{rows.filter((row) => row.confidence === "high").length}</strong></div>
        <div className="stat-card"><span>Needs attention</span><strong>{rows.filter((row) => row.confidence === "low").length}</strong></div>
      </div>

      <div className="surface-panel mb-6">
        <label htmlFor="conf-filter">Filter confidence</label>
        <select id="conf-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Question</th>
              <th>Confidence</th>
              <th>Citations</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, idx) => (
              <tr key={idx}>
                <td>{row.question}</td>
                <td>
                  <ConfidenceBadge level={row.confidence} />
                </td>
                <td>{row.citations}</td>
                <td>{row.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}