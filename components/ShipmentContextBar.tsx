import Link from "next/link";

export default function ShipmentContextBar() {
  return (
    <div className="context-bar">
      <span><strong>Shipment:</strong> CN &rarr; US | Electronics | Ocean Freight (1,250 kg)</span>
      <Link href="/">Change</Link>
    </div>
  );
}