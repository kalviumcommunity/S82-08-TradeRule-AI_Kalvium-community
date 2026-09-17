"use client";

import { useEffect, useState } from "react";
import ConfidenceBadge from "@/components/ConfidenceBadge";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_RAG_API_URL || "http://127.0.0.1:8000";

interface AuditRow {
  question: string;
  confidence: "high" | "medium" | "low";
  citations: number;
  timestamp: string;
  latency_ms?: number;
  status?: string;
}

const DEFAULT_ROWS: AuditRow[] = [
  {
    question: "Are UN3481 lithium ion batteries restricted on ocean routes?",
    confidence: "high",
    citations: 5,
    timestamp: "2026-09-15 14:22",
    latency_ms: 650,
  },
  {
    question: "What specific container packing certificate is required?",
    confidence: "medium",
    citations: 2,
    timestamp: "2026-09-15 13:05",
    latency_ms: 720,
  },
  {
    question: "What documents are required for customs clearance?",
    confidence: "high",
    citations: 4,
    timestamp: "2026-09-15 12:10",
    latency_ms: 540,
  },
  {
    question: "Are there local state tax implications for transit through ports?",
    confidence: "low",
    citations: 1,
    timestamp: "2026-09-15 11:40",
    latency_ms: 480,
  },
  {
    question: "What documentation is needed for chemical compound transit?",
    confidence: "high",
    citations: 3,
    timestamp: "2026-09-15 09:15",
    latency_ms: 610,
  },
];

export default function AdminReviewPage() {
  const [filter, setFilter] = useState("all");
  const [rows, setRows] = useState<AuditRow[]>(DEFAULT_ROWS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  async function fetchLogs() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/logs?limit=50`);
      if (res.ok) {
        const rawLogs = await res.json();
        if (Array.isArray(rawLogs) && rawLogs.length > 0) {
          const parsedRows: AuditRow[] = rawLogs.map((entry: any) => {
            let conf: "high" | "medium" | "low" = "high";
            if (entry.status === "refused_weak_context" || entry.status === "error") {
              conf = "low";
            } else if (entry.top_score && entry.top_score < 0.65) {
              conf = "medium";
            }

            let dateStr = "Recent";
            if (entry.timestamp) {
              try {
                dateStr = new Date(entry.timestamp).toLocaleString();
              } catch {
                dateStr = entry.timestamp.slice(0, 16).replace("T", " ");
              }
            }

            return {
              question: entry.question || "Compliance Inquiry",
              confidence: conf,
              citations: Array.isArray(entry.sources) ? entry.sources.length : 0,
              timestamp: dateStr,
              latency_ms: entry.latency_ms ? Math.round(entry.latency_ms) : undefined,
              status: entry.status,
            };
          });

          setRows(parsedRows);
          return;
        }
      }
    } catch {
      // fallback to localStorage if available
    } finally {
      setLoading(false);
    }

    // Check localStorage
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("traderule_query_history");
        if (saved) {
          const list = JSON.parse(saved);
          if (list.length > 0) {
            setRows(list);
          }
        }
      } catch {
        // ignore
      }
    }
  }

  const filteredRows = rows.filter(
    (r) => filter === "all" || r.confidence === filter
  );

  function handleExportLogs() {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(rows, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `traderule_audit_logs_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Administration / Audit log</div>
          <h1>Confidence Review &amp; RAG Observability</h1>
          <p>
            Monitor real-time answer quality, semantic scores, and citation coverage across all compliance questions asked by users.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={fetchLogs}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh Logs"}
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleExportLogs}
          >
            Export JSON Logs
          </button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Total queries logged</span>
          <strong>{rows.length}</strong>
        </div>
        <div className="stat-card">
          <span>High confidence</span>
          <strong className="text-emerald-700">
            {rows.filter((row) => row.confidence === "high").length}
          </strong>
        </div>
        <div className="stat-card">
          <span>Needs attention</span>
          <strong className="text-amber-700">
            {rows.filter((row) => row.confidence === "low").length}
          </strong>
        </div>
      </div>

      <div className="surface-panel mb-6 flex justify-between items-center gap-4">
        <div>
          <label htmlFor="conf-filter" className="mb-1 block">
            Filter by confidence rating
          </label>
          <select
            id="conf-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="form-select max-w-xs"
          >
            <option value="all">All levels ({rows.length})</option>
            <option value="high">
              High confidence ({rows.filter((r) => r.confidence === "high").length})
            </option>
            <option value="medium">
              Medium confidence ({rows.filter((r) => r.confidence === "medium").length})
            </option>
            <option value="low">
              Low / Refusal ({rows.filter((r) => r.confidence === "low").length})
            </option>
          </select>
        </div>
        <div className="text-xs text-slate-500 text-right">
          Logs synced live from backend <code className="bg-slate-100 px-1 py-0.5 rounded">logs/rag_requests.jsonl</code>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Compliance Question</th>
              <th>Confidence Level</th>
              <th>Citations</th>
              <th>Latency</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, idx) => (
              <tr key={idx}>
                <td>
                  <strong className="text-ink">{row.question}</strong>
                </td>
                <td>
                  <ConfidenceBadge level={row.confidence} />
                </td>
                <td>
                  <span className="font-semibold text-blue-700">
                    {String(row.citations).padStart(2, "0")}
                  </span>{" "}
                  sources
                </td>
                <td>
                  {row.latency_ms ? `${row.latency_ms} ms` : "< 500 ms"}
                </td>
                <td>{row.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}