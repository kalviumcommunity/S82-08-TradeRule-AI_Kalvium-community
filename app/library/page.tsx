"use client";

import { useState } from "react";
import Link from "next/link";

interface Regulation {
  title: string;
  scope: string;
  category: string;
  statute: string;
  updated: string;
  status: "Current" | "Review due";
  summary: string;
  sampleQuestion: string;
}

const REGULATIONS: Regulation[] = [
  {
    title: "IMDG Code Amendment 41-22",
    scope: "Global Maritime / IMO",
    category: "Dangerous Goods",
    statute: "IMDG Code Sec 3.4 / SP 188, 230, 376",
    updated: "Jun 12, 2026",
    status: "Current",
    summary:
      "Regulates maritime carriage of lithium-ion batteries (UN3480/UN3481). Mandates <= 30% State of Charge (SOC), Class 9 labeling, and DGD.",
    sampleQuestion: "Are UN3481 lithium ion batteries restricted on ocean routes?",
  },
  {
    title: "SOLAS Carriage of Dangerous Goods",
    scope: "International Waters",
    category: "Maritime Safety",
    statute: "SOLAS Chapter VII Reg 5",
    updated: "Jun 11, 2026",
    status: "Current",
    summary:
      "Requires signed Container/Vehicle Packing Certificate (CPC) certifying structural integrity, segregation, and weight distribution.",
    sampleQuestion: "What specific container packing certificate is required?",
  },
  {
    title: "United States Commercial Entry Controls",
    scope: "United States",
    category: "Customs",
    statute: "CBP Reg 19 CFR 12.3 & Part 141",
    updated: "Jun 10, 2026",
    status: "Current",
    summary:
      "Formal commercial entry declarations, submission of CBP Form 7501 and CBP Form 3461 via ACE, commercial invoice, and continuous customs bond.",
    sampleQuestion: "What specific customs declarations are required for entry?",
  },
  {
    title: "Customs Clearance Documentation Standards",
    scope: "Global Customs",
    category: "Customs",
    statute: "WCO Revised Kyoto Convention",
    updated: "Jun 08, 2026",
    status: "Current",
    summary:
      "Standard clearance documentation: commercial invoice, packing list, bill of lading/air waybill, certificate of origin, and import permits.",
    sampleQuestion: "What documents are required for customs clearance?",
  },
  {
    title: "Export Administration Regulations (EAR)",
    scope: "United States / Global",
    category: "Export Controls",
    statute: "15 CFR Parts 730-774 (CCL / ECCN)",
    updated: "Jun 05, 2026",
    status: "Current",
    summary:
      "Commerce Control List licensing triggers, denied party screening, dual-use technological controls, and Automated Export System (AES) filing.",
    sampleQuestion: "When does an exporter need an export license?",
  },
  {
    title: "Industrial Chemical Compounds Transit Protocol",
    scope: "Multilateral Transit",
    category: "Hazardous Materials",
    statute: "GHS / TSCA / REACH Standards",
    updated: "May 29, 2026",
    status: "Review due",
    summary:
      "Mandates 16-section Safety Data Sheets (SDS), signed Dangerous Goods Declarations (DGD), technical chemical names, and emergency contact.",
    sampleQuestion: "What documentation is needed for chemical compound transit?",
  },
  {
    title: "Textiles & Apparel Tariff Classification Guide",
    scope: "United States & Canada",
    category: "Tariff Classification",
    statute: "HTSUS Chapter 61/62 & 16 CFR Part 303",
    updated: "May 20, 2026",
    status: "Current",
    summary:
      "Rules of origin (yarn-forward test), mandatory fiber composition percentages by weight, and country of origin labeling.",
    sampleQuestion: "What are the rules of origin and classification requirements for apparel?",
  },
  {
    title: "Regional Port Authority Transit & Tax Rulings",
    scope: "Regional Ports",
    category: "Port Regulations",
    statute: "US Import-Export Clause & Port Tariffs",
    updated: "May 15, 2026",
    status: "Review due",
    summary:
      "In-bond transit exemptions from state ad valorem property taxes, municipal wharfage assessments, and terminal handling charges (THC).",
    sampleQuestion: "Are there local state tax implications for transit through ports?",
  },
];

export default function RegulationsLibraryPage() {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const categories = [
    "all",
    "Customs",
    "Dangerous Goods",
    "Maritime Safety",
    "Export Controls",
    "Hazardous Materials",
    "Tariff Classification",
    "Port Regulations",
  ];

  const filteredRegulations = REGULATIONS.filter((reg) => {
    const matchesCategory = filter === "all" || reg.category === filter;
    const matchesSearch =
      search === "" ||
      reg.title.toLowerCase().includes(search.toLowerCase()) ||
      reg.scope.toLowerCase().includes(search.toLowerCase()) ||
      reg.statute.toLowerCase().includes(search.toLowerCase()) ||
      reg.summary.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Knowledge base / Country &amp; International rules</div>
          <h1>Regulations Library</h1>
          <p>
            Browse the active maritime conventions, customs statutes, hazardous goods codes, and carrier policies that TradeRule AI indexes to evaluate your routes.
          </p>
        </div>
        <Link href="/admin/upload" className="btn-primary">
          + Upload New Regulation
        </Link>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Active Regulations</span>
          <strong>{REGULATIONS.length}</strong>
        </div>
        <div className="stat-card">
          <span>Current &amp; Verified</span>
          <strong className="text-emerald-700">
            {REGULATIONS.filter((r) => r.status === "Current").length}
          </strong>
        </div>
        <div className="stat-card">
          <span>Review Scheduled</span>
          <strong className="text-amber-700">
            {REGULATIONS.filter((r) => r.status === "Review due").length}
          </strong>
        </div>
      </div>

      <div className="surface-panel mb-6 flex flex-wrap justify-between items-center gap-4">
        <div>
          <label htmlFor="cat-filter" className="sr-only">
            Filter category
          </label>
          <select
            id="cat-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="form-select text-sm py-1.5"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === "all" ? "All Categories" : cat}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 max-w-sm">
          <input
            type="text"
            className="form-input text-sm py-1.5"
            placeholder="Search regulations by title, statute, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-4">
        {filteredRegulations.map((reg, idx) => {
          const isExpanded = expandedIndex === idx;
          return (
            <div key={idx} className="surface-panel transition">
              <div className="flex justify-between items-start mb-2 gap-4">
                <div>
                  <span className="text-xs text-blue-700 font-semibold uppercase tracking-wider block mb-0.5">
                    {reg.category} &bull; {reg.scope}
                  </span>
                  <strong className="text-base text-ink block">{reg.title}</strong>
                  <span className="text-xs text-slate-500 font-mono">{reg.statute}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={
                      reg.status === "Current" ? "badge-high" : "badge-medium"
                    }
                  >
                    {reg.status}
                  </span>
                </div>
              </div>

              <p className="text-sm text-slate-600 mb-3">{reg.summary}</p>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 mt-2">
                <span className="text-xs text-slate-400">
                  Last verified: {reg.updated}
                </span>

                <div className="flex gap-2">
                  <Link
                    href={`/ask?question=${encodeURIComponent(reg.sampleQuestion)}`}
                    className="btn-primary text-xs py-1.5 px-3"
                  >
                    Query this Rule in Q&amp;A &rarr;
                  </Link>
                  <button
                    type="button"
                    className="btn-secondary text-xs py-1.5 px-3"
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                  >
                    {isExpanded ? "Hide Details" : "View Rule Scope"}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-3 p-3 bg-slate-50 rounded-md border border-slate-200 text-xs leading-5">
                  <div className="font-semibold text-slate-700 mb-1">Recommended Verification Question:</div>
                  <div className="text-blue-800 italic mb-2">&ldquo;{reg.sampleQuestion}&rdquo;</div>
                  <div className="font-semibold text-slate-700 mb-1">Statutory Context:</div>
                  <p className="mb-0 text-slate-600">{reg.summary} All requirements are indexed and cross-referenced in TradeRule AI semantic vector space.</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
