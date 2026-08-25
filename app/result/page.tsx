import ShipmentContextBar from "@/components/ShipmentContextBar";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import CitationChip from "@/components/CitationChip";

export default function ComplianceAnswerPage() {
  return (
    <div>
      <ShipmentContextBar />

      <div className="section-heading">
        <div>
          <div className="page-kicker">Step 3 of 3 / Compliance decision</div>
          <h1>Compliance Result</h1>
          <p>Review the answer, required documents, and sources before continuing.</p>
        </div>
        <ConfidenceBadge level="high" />
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Confidence</span><strong>High</strong></div>
        <div className="stat-card"><span>Sources found</span><strong>02</strong></div>
        <div className="stat-card"><span>Route status</span><strong>Cleared</strong></div>
      </div>

      <div className="surface-panel mb-6">
        <div className="page-kicker mb-2">Decision summary</div>
        <p className="text-ink text-base mb-4">
          UN3481 lithium-ion batteries packed with equipment are fully permitted for ocean freight transport into United States ports, provided they meet standard State of Charge (SOC) limitations not exceeding 30% and carry proper Class 9 hazard labeling on outer packaging containers.
        </p>

        <h2>Required Documents / Restrictions</h2>
        <ul className="text-ink-muted mb-5 pl-5 list-disc space-y-1 text-sm">
          <li>Dangerous Goods Declaration (DGD) signed by shipper</li>
          <li>Bill of Lading with clear UN number entry</li>
          <li>Maximum State of Charge restriction (max 30% capacity)</li>
        </ul>

        <h2>Sources</h2>
        <div>
          <CitationChip>IMDG Code 41-22 (Sec 3.4)</CitationChip>
          <CitationChip>CBP Reg 19 CFR 12.3</CitationChip>
        </div>
      </div>

      <div className="surface-panel">
        <h2 className="text-xl mb-1">Continue the review</h2>
        <p className="text-sm text-slate-500 mb-4">Ask a follow-up question while this shipment context is active.</p>
        <form action="/thread" method="GET">
          <div className="mb-4">
            <label htmlFor="followup">Ask a follow-up question</label>
            <textarea
              id="followup"
              name="followup"
              className="form-textarea"
              placeholder="Inquire further about documentation, packaging standards, or port restrictions..."
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">
              Send Follow-up
            </button>
            <button type="reset" className="btn-secondary">
              Clear question
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}