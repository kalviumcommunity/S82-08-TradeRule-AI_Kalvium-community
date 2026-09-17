"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface ShipmentRecord {
  id: string;
  route: string;
  product: string;
  carrier: string;
  result: "Cleared" | "Needs review";
  reviewed: string;
  question: string;
  answer: string;
}

const DEFAULT_SHIPMENTS: ShipmentRecord[] = [
  {
    id: "TR-10482",
    route: "CN -> US",
    product: "Lithium-ion batteries",
    carrier: "Maersk Line",
    result: "Cleared",
    reviewed: "Today, 14:22",
    question: "Are UN3481 lithium ion batteries restricted on ocean routes?",
    answer: "UN3481 lithium-ion batteries packed with equipment are permitted for ocean transport into US ports, provided they meet standard SOC <= 30% and carry Class 9 hazard labeling.",
  },
  {
    id: "TR-10481",
    route: "DE -> CA",
    product: "Textiles & apparel",
    carrier: "MSC Mediterranean",
    result: "Cleared",
    reviewed: "Today, 13:05",
    question: "What specific customs declarations are required for entry?",
    answer: "All shipments require formal entry declarations including CBP Form 7501, commercial invoice with HTSUS classification, packing list, and bill of lading.",
  },
  {
    id: "TR-10480",
    route: "VN -> US",
    product: "Industrial chemicals",
    carrier: "DHL Global Forwarding",
    result: "Needs review",
    reviewed: "Today, 11:40",
    question: "What documentation is needed for chemical compound transit?",
    answer: "Shipments containing industrial chemical compounds require a 16-section Safety Data Sheet (SDS), a signed Dangerous Goods Declaration (DGD), and TSCA/REACH compliance certification.",
  },
  {
    id: "TR-10479",
    route: "CN -> GB",
    product: "Mechanical parts",
    carrier: "FedEx Express",
    result: "Cleared",
    reviewed: "Yesterday, 16:18",
    question: "What documents are required for customs clearance?",
    answer: "Mandatory documents include commercial invoice, packing list, bill of lading / air waybill, certificate of origin, and import entry declaration.",
  },
];

export default function ShipmentHistoryPage() {
  const [shipments, setShipments] = useState<ShipmentRecord[]>(DEFAULT_SHIPMENTS);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("traderule_query_history");
        if (saved) {
          const list = JSON.parse(saved);
          if (Array.isArray(list) && list.length > 0) {
            const dynamicShipments: ShipmentRecord[] = list.map((item: any, idx: number) => ({
              id: item.id || `TR-${10490 + idx}`,
              route: "CN -> US",
              product: "Electronic Equipment",
              carrier: "Maersk Line",
              result: item.confidence === "low" ? "Needs review" : "Cleared",
              reviewed: item.timestamp || "Recent",
              question: item.question,
              answer: item.answer,
            }));
            // Merge unique
            setShipments([...dynamicShipments, ...DEFAULT_SHIPMENTS]);
          }
        }
      } catch {
        // ignore
      }
    }
  }, []);

  const filteredShipments = shipments.filter((s) => {
    const matchesFilter = filter === "all" || s.result === filter;
    const matchesSearch =
      search === "" ||
      s.id.toLowerCase().includes(search.toLowerCase()) ||
      s.route.toLowerCase().includes(search.toLowerCase()) ||
      s.product.toLowerCase().includes(search.toLowerCase()) ||
      s.question.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const clearedCount = shipments.filter((s) => s.result === "Cleared").length;
  const reviewCount = shipments.filter((s) => s.result === "Needs review").length;

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Operations / Recent checks</div>
          <h1>Shipment History</h1>
          <p>Revisit past shipment decisions, reviewed questions, and authoritative compliance outcomes.</p>
        </div>
        <Link href="/ask" className="btn-primary">
          + New Compliance Query
        </Link>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span>Total evaluations</span>
          <strong>{shipments.length}</strong>
        </div>
        <div className="stat-card">
          <span>Cleared routes</span>
          <strong className="text-emerald-700">{clearedCount}</strong>
        </div>
        <div className="stat-card">
          <span>Needs review</span>
          <strong className="text-amber-700">{reviewCount}</strong>
        </div>
      </div>

      <div className="surface-panel mb-6 flex flex-wrap justify-between items-center gap-4">
        <div className="flex gap-3 items-center">
          <div>
            <label htmlFor="status-filter" className="sr-only">
              Filter status
            </label>
            <select
              id="status-filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="form-select text-sm py-1.5"
            >
              <option value="all">All statuses ({shipments.length})</option>
              <option value="Cleared">Cleared ({clearedCount})</option>
              <option value="Needs review">Needs review ({reviewCount})</option>
            </select>
          </div>
        </div>

        <div className="flex-1 max-w-sm">
          <input
            type="text"
            className="form-input text-sm py-1.5"
            placeholder="Search by ID, route, product, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Shipment ID</th>
              <th>Trade Route</th>
              <th>Product Category</th>
              <th>Carrier</th>
              <th>Status</th>
              <th>Reviewed</th>
              <th>Decision Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredShipments.map((shipment, idx) => (
              <tr key={`${shipment.id}-${idx}`}>
                <td>
                  <strong>{shipment.id}</strong>
                </td>
                <td>{shipment.route}</td>
                <td>{shipment.product}</td>
                <td>{shipment.carrier}</td>
                <td>
                  <span
                    className={
                      shipment.result === "Cleared"
                        ? "badge-high"
                        : "badge-medium"
                    }
                  >
                    {shipment.result}
                  </span>
                </td>
                <td>{shipment.reviewed}</td>
                <td>
                  <Link
                    href={`/result?question=${encodeURIComponent(
                      shipment.question
                    )}&answer=${encodeURIComponent(shipment.answer)}`}
                    className="text-xs text-blue-600 font-semibold hover:underline"
                  >
                    View Decision &rarr;
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
