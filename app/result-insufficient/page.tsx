"use client";

import { Suspense } from "react";
import ShipmentContextBar from "@/components/ShipmentContextBar";
import Link from "next/link";

export default function InsufficientInfoPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <div>
        <ShipmentContextBar />

        <div className="alert-panel mb-6">
          <div className="icon-circle">?</div>
          <div>
            <div className="page-kicker mb-2">Manual review recommended</div>
            <h2>Specific regulatory clause not matched</h2>
            <p>
              No specific statutory ruling was found matching this exact sub-category code in the indexed regulatory database.
            </p>
            <p className="text-xs mb-0 font-medium">
              <em>Suggestion: Rephrase your query in Question Input or ask in the Follow-up Thread.</em>
            </p>
          </div>
        </div>

        <div className="form-actions">
          <Link href="/ask" className="btn-secondary">
            Return to Question Input
          </Link>
          <Link href="/thread" className="btn-primary">
            Ask in Follow-up Thread &rarr;
          </Link>
        </div>
      </div>
    </Suspense>
  );
}