"use client";

import { Suspense } from "react";
import ShipmentContextBar from "@/components/ShipmentContextBar";
import Link from "next/link";

export default function SystemErrorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <div>
        <ShipmentContextBar />

        <div className="alert-panel error mb-6">
          <div className="icon-circle">!</div>
          <div>
            <div className="page-kicker mb-2">Service interruption</div>
            <h2>Document retrieval failed</h2>
            <p className="mb-0">
              The vector index database encountered a temporary network delay. This is a technical connectivity event rather than a compliance restriction.
            </p>
          </div>
        </div>

        <div className="form-actions">
          <Link href="/result" className="btn-secondary">
            Retry search
          </Link>
          <Link href="/ask" className="btn-primary">
            Edit question in Q&amp;A &rarr;
          </Link>
        </div>
      </div>
    </Suspense>
  );
}