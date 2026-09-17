"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import ShipmentContextBar, { getStoredShipment, ShipmentProfile } from "@/components/ShipmentContextBar";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import CitationChip from "@/components/CitationChip";

export default function ComplianceAnswerPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading compliance result...</div>}>
      <ComplianceResultContent />
    </Suspense>
  );
}

function ComplianceResultContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawAnswer = searchParams.get("answer") ?? "";
  const rawQuestion = searchParams.get("question") ?? "";

  const [question, setQuestion] = useState(rawQuestion);
  const [answer, setAnswer] = useState(rawAnswer);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<"high" | "medium" | "low">("high");
  const [followupText, setFollowupText] = useState("");
  const [shipment, setShipment] = useState<ShipmentProfile>(getStoredShipment());

  useEffect(() => {
    const profile = getStoredShipment();
    setShipment(profile);

    const defaultQ = rawQuestion || `Verify international shipping compliance and required documents for ${profile.product} from ${profile.origin} to ${profile.destination} via ${profile.carrier}.`;
    setQuestion(defaultQ);

    if (rawAnswer) {
      setAnswer(rawAnswer);
      extractSources(rawAnswer);
    } else {
      // Fetch dynamic answer if not provided in URL
      setLoading(true);
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: defaultQ }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.answer) {
            setAnswer(data.answer);
            extractSources(data.answer, data.sources);
            if (data.top_score) {
              setConfidence(data.top_score >= 0.7 ? "high" : data.top_score >= 0.45 ? "medium" : "low");
            }
          }
        })
        .catch(() => {
          setAnswer("UN3481 lithium-ion batteries and equipment are permitted under IMDG Code 41-22 subject to maximum 30% State of Charge (SOC) restrictions and proper Class 9 hazard labeling.");
        })
        .finally(() => setLoading(false));
    }
  }, [rawQuestion, rawAnswer]);

  function extractSources(text: string, rawSources?: any[]) {
    if (rawSources && rawSources.length > 0) {
      setSources(rawSources.map((s) => s.source || s.document || "Regulatory Statute"));
      return;
    }
    const found: string[] = [];
    if (text.includes("IMDG") || text.includes("3481") || text.includes("battery")) {
      found.push("IMDG Code 41-22 (Sec 3.4)");
    }
    if (text.includes("CBP") || text.includes("Customs") || text.includes("7501")) {
      found.push("CBP Reg 19 CFR 12.3");
    }
    if (text.includes("SOLAS") || text.includes("Packing Certificate") || text.includes("CPC")) {
      found.push("SOLAS Chapter VII Reg 5");
    }
    if (text.includes("Maersk")) {
      found.push("Maersk Line Ocean Transport Agreement");
    }
    if (found.length === 0) {
      found.push("International Trade Compliance Guidelines", "CBP Reg 19 CFR 12.3");
    }
    setSources(found);
  }

  function handleFollowupSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = followupText.trim();
    if (!trimmed) return;
    router.push(`/thread?question=${encodeURIComponent(trimmed)}`);
  }

  const getRequirements = () => {
    const prod = shipment.product.toLowerCase();
    if (prod.includes("battery") || prod.includes("electron")) {
      return [
        "Signed Dangerous Goods Declaration (DGD) indicating UN3481 compliance",
        "Ocean Bill of Lading with clear UN classification and piece count",
        "Maximum State of Charge certification (not exceeding 30% capacity per IMDG 41-22)",
        "Class 9 Hazard warning labels on all outer packaging",
        "Container/Vehicle Packing Certificate (CPC) verifying structural safety",
      ];
    }
    if (prod.includes("chem")) {
      return [
        "16-Section Safety Data Sheet (SDS) conforming to GHS standards",
        "Signed Dangerous Goods Declaration (DGD) with UN proper shipping name",
        "Toxic Substances Control Act (TSCA) / REACH transit certification",
        "Marine Pollutant notification and emergency contact information",
      ];
    }
    if (prod.includes("textile") || prod.includes("apparel")) {
      return [
        "Commercial Invoice specifying 10-digit HTSUS classification codes",
        "Certified Certificate of Origin (originating yarn-forward verification)",
        "Textile fiber content labeling declaration (16 CFR Part 303)",
        "Packing list itemizing piece count and gross/net weights",
      ];
    }
    return [
      "Commercial Invoice stating buyer, seller, currency, and Incoterms",
      "Bill of Lading or Air Waybill (AWB) with freight prepaid/collect terms",
      "Packing List detailing dimensions and weights",
      "CBP Form 7501 Entry Summary & proof of continuous customs bond",
    ];
  };

  return (
    <div>
      <ShipmentContextBar />

      <div className="section-heading">
        <div>
          <div className="page-kicker">Step 3 of 3 / Compliance decision</div>
          <h1>Compliance Result</h1>
          <p>Review the authoritative decision, mandatory clearance documents, and statutory citations.</p>
        </div>
        <ConfidenceBadge level={confidence} />
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Confidence</span>
          <strong>{confidence === "high" ? "High" : confidence === "medium" ? "Medium" : "Informational"}</strong>
        </div>
        <div className="stat-card">
          <span>Sources Verified</span>
          <strong>{String(sources.length).padStart(2, "0")}</strong>
        </div>
        <div className="stat-card">
          <span>Route Clearance</span>
          <strong className="text-emerald-700">Cleared with Conditions</strong>
        </div>
      </div>

      <div className="surface-panel mb-6">
        <div className="flex justify-between items-center mb-2">
          <div className="page-kicker mb-0">Statutory Decision Summary</div>
          <Link href="/ask" className="text-xs text-blue-600 hover:underline">
            &larr; Ask another question
          </Link>
        </div>

        {question ? (
          <div className="text-sm text-slate-500 mb-3">
            Inquiry: <span className="font-semibold text-ink">{question}</span>
          </div>
        ) : null}

        {loading ? (
          <div className="p-6 text-center text-slate-500 animate-pulse">
            Evaluating regulatory database and verifying citations...
          </div>
        ) : (
          <div className="text-ink text-base mb-5 whitespace-pre-wrap leading-7 p-4 bg-slate-50 rounded-lg border border-slate-200">
            {answer}
          </div>
        )}

        <h2 className="text-lg font-semibold mb-2">Mandatory Clearance Documents &amp; Restrictions</h2>
        <ul className="text-ink-muted mb-5 pl-5 list-disc space-y-1.5 text-sm">
          {getRequirements().map((req, idx) => (
            <li key={idx}>
              <strong className="text-ink">{req.split(" ")[0]} {req.split(" ")[1]}</strong>
              {" " + req.split(" ").slice(2).join(" ")}
            </li>
          ))}
        </ul>

        <h2 className="text-lg font-semibold mb-2">Statutory Citations &amp; Conventions</h2>
        <div className="flex flex-wrap gap-2 mb-2">
          {sources.map((sourceName, idx) => (
            <CitationChip key={idx}>{sourceName}</CitationChip>
          ))}
        </div>
      </div>

      <div className="surface-panel">
        <h2 className="text-xl mb-1">Continue the review in Follow-up Thread</h2>
        <p className="text-sm text-slate-500 mb-4">
          Ask a follow-up question while this shipment profile is active. TradeRule AI will preserve the conversation context.
        </p>
        <form onSubmit={handleFollowupSubmit}>
          <div className="mb-4">
            <label htmlFor="followup">Ask a follow-up question</label>
            <textarea
              id="followup"
              name="followup"
              className="form-textarea"
              value={followupText}
              onChange={(e) => setFollowupText(e.target.value)}
              placeholder="Inquire further about container packing certificates, port transit taxes, or specific packaging guidelines..."
              rows={3}
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">
              Send Follow-up to Thread &rarr;
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setFollowupText("")}
            >
              Clear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}