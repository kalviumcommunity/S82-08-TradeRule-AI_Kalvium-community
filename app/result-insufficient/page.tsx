import ShipmentContextBar from "@/components/ShipmentContextBar";
import Link from "next/link";

export default function InsufficientInfoPage() {
  return (
    <div>
      <ShipmentContextBar />

      <div className="alert-panel mb-6">
        <div className="icon-circle">?</div>
        <div>
          <div className="page-kicker mb-2">Manual review recommended</div>
          <h2>Insufficient information</h2>
          <p>
            No supporting document or binding ruling was found matching specific regional textile quotas for this exact sub-category code.
          </p>
          <p className="text-xs mb-0 font-medium">
            <em>Suggestion: Rephrase your query or contact the trade compliance department directly.</em>
          </p>
        </div>
      </div>

      <div className="form-actions">
        <Link href="/ask" className="btn-secondary">
          Return to Question Input
        </Link>
        <Link href="/thread" className="btn-primary">Continue thread</Link>
      </div>
    </div>
  );
}