import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex justify-center items-center min-h-[60vh]">
      <div className="surface-panel text-center max-w-md w-full">
        <div className="page-kicker mb-2">Navigation checkpoint</div>
        <div className="icon-circle mx-auto mb-4">?</div>
        <h2>Something went wrong</h2>
        <p className="mb-6">
          The requested compliance workspace route or resource could not be found within the operational directory.
        </p>
        <Link href="/" className="btn-primary">
          Return to Shipment Intake
        </Link>
      </div>
    </div>
  );
}