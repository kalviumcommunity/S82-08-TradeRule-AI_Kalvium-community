import ShipmentContextBar from "@/components/ShipmentContextBar";
import Link from "next/link";

export default function SystemErrorPage() {
  return (
    <div>
      <ShipmentContextBar />

      <div className="alert-panel error mb-6">
        <div className="icon-circle">!</div>
          <div>
            <div className="page-kicker mb-2">Service interruption</div>
            <h2>Document retrieval failed</h2>
            <p className="mb-0">
              The vector index database encountered a timeout during semantic search processing. This is a technical failure rather than a compliance restriction.
            </p>
          </div>
      </div>

      <div className="form-actions">
        <Link href="/result" className="btn-secondary">
          Retry search
        </Link>
        <Link href="/ask" className="btn-primary">Edit question</Link>
      </div>
    </div>
  );
}