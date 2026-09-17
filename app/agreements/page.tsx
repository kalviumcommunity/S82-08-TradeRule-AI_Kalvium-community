"use client";

import { useState } from "react";
import Link from "next/link";

interface CarrierAgreement {
  carrier: string;
  lanes: string;
  effective: string;
  documents: string;
  keyRule: string;
  sampleQuestion: string;
}

const AGREEMENTS: CarrierAgreement[] = [
  {
    carrier: "Maersk Line",
    lanes: "Asia -> United States",
    effective: "Jan 01, 2026",
    documents: "12 clauses",
    keyRule:
      "Dangerous Goods Declarations (DGD) and Container Packing Certificates (CPC) required 48 hours prior to vessel cutoff. State of charge <= 30% for batteries.",
    sampleQuestion:
      "What carrier requirements does Maersk Line mandate for dangerous goods and battery transport?",
  },
  {
    carrier: "MSC Mediterranean",
    lanes: "Europe -> Canada",
    effective: "Feb 15, 2026",
    documents: "08 clauses",
    keyRule:
      "Advance electronic cargo manifest (ACI eManifest) 24 hours prior to loading. Dual-language (EN/FR) Safety Data Sheets for all chemical transit.",
    sampleQuestion:
      "What are MSC Mediterranean requirements for European chemical shipments to Canada?",
  },
  {
    carrier: "DHL Global Forwarding",
    lanes: "Global air freight",
    effective: "Mar 04, 2026",
    documents: "15 clauses",
    keyRule:
      "Full compliance with IATA Dangerous Goods Regulations (DGR). Lithium-ion batteries (UN3480) forbidden on passenger aircraft; Cargo Aircraft Only (CAO) label mandatory.",
    sampleQuestion:
      "What air freight dangerous goods rules does DHL Global Forwarding enforce for batteries?",
  },
  {
    carrier: "FedEx Express",
    lanes: "United States -> Australia",
    effective: "Apr 20, 2026",
    documents: "06 clauses",
    keyRule:
      "Australian Border Force (ABF) and DAFF biosecurity compliance. Mandatory ISPM 15 heat-treated wood packaging stamp and itemized AUD/USD valuations.",
    sampleQuestion:
      "What specific documentation does FedEx Express require for US to Australia air shipments?",
  },
];

export default function CarrierAgreementsPage() {
  const [search, setSearch] = useState("");

  const filtered = AGREEMENTS.filter(
    (a) =>
      search === "" ||
      a.carrier.toLowerCase().includes(search.toLowerCase()) ||
      a.lanes.toLowerCase().includes(search.toLowerCase()) ||
      a.keyRule.toLowerCase().includes(search.toLowerCase())
  );

  function handleExportTerms() {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(AGREEMENTS, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `carrier_agreements_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Knowledge base / Carrier terms</div>
          <h1>Carrier Agreements</h1>
          <p>
            Review active ocean and air carrier agreements that modify documentation deadlines, packaging thresholds, and hazardous cargo acceptance.
          </p>
        </div>
        <button type="button" className="btn-secondary" onClick={handleExportTerms}>
          Export Carrier Terms (.json)
        </button>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Active agreements</span>
          <strong>{AGREEMENTS.length}</strong>
        </div>
        <div className="stat-card">
          <span>Covered carriers</span>
          <strong>04 Major Lines</strong>
        </div>
        <div className="stat-card">
          <span>Global Lanes</span>
          <strong>Trans-Pacific &bull; Trans-Atlantic &bull; Air</strong>
        </div>
      </div>

      <div className="surface-panel mb-6 flex flex-wrap justify-between items-center gap-4">
        <div>
          <div className="page-kicker mb-1">Operational Guidance</div>
          <p className="text-ink text-sm mb-0">
            Carrier terms operate alongside country regulations. If a carrier specifies a stricter rule (e.g. 48h cutoff), the carrier condition governs dispatch.
          </p>
        </div>
        <div className="w-full sm:w-auto">
          <input
            type="text"
            className="form-input text-sm py-1.5"
            placeholder="Search carrier or lane..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Carrier</th>
              <th>Primary Trade Lanes</th>
              <th>Key Operational Conditions</th>
              <th>Effective Date</th>
              <th>Compliance Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((agreement) => (
              <tr key={agreement.carrier}>
                <td>
                  <strong className="text-ink">{agreement.carrier}</strong>
                  <div className="text-xs text-slate-500">{agreement.documents}</div>
                </td>
                <td>{agreement.lanes}</td>
                <td className="max-w-md text-xs leading-5">{agreement.keyRule}</td>
                <td>{agreement.effective}</td>
                <td>
                  <Link
                    href={`/ask?question=${encodeURIComponent(agreement.sampleQuestion)}`}
                    className="btn-primary text-xs py-1.5 px-3 whitespace-nowrap"
                  >
                    Verify in Q&amp;A &rarr;
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
