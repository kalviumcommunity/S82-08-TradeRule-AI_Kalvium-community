"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

export interface ShipmentProfile {
  origin: string;
  destination: string;
  product: string;
  carrier: string;
  weight: number | string;
  transport: string;
}

export const DEFAULT_SHIPMENT: ShipmentProfile = {
  origin: "CN",
  destination: "US",
  product: "Lithium-ion Batteries / Electronics",
  carrier: "Maersk Line",
  weight: 1250,
  transport: "Ocean Freight (FCL)",
};

const PRODUCT_LABELS: Record<string, string> = {
  electronics: "Lithium-ion Batteries / Electronics",
  apparel: "Textiles & Apparel",
  chemicals: "Industrial Chemical Compounds",
  machinery: "Mechanical Parts",
};

const TRANSPORT_LABELS: Record<string, string> = {
  ocean: "Ocean Freight (FCL)",
  air: "Air Cargo",
  rail: "Rail Freight",
};

const CARRIER_LABELS: Record<string, string> = {
  maersk: "Maersk Line",
  msc: "MSC Mediterranean",
  fedex: "FedEx Express",
  dhl: "DHL Global Forwarding",
};

export function getStoredShipment(): ShipmentProfile {
  if (typeof window === "undefined") return DEFAULT_SHIPMENT;
  try {
    const saved = localStorage.getItem("traderule_active_shipment");
    if (saved) return JSON.parse(saved);
  } catch {
    // fallback
  }
  return DEFAULT_SHIPMENT;
}

export function saveStoredShipment(profile: ShipmentProfile) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem("traderule_active_shipment", JSON.stringify(profile));
    window.dispatchEvent(new Event("shipment_profile_updated"));
  } catch {
    // ignore
  }
}

export default function ShipmentContextBar() {
  const searchParams = useSearchParams();
  const [profile, setProfile] = useState<ShipmentProfile>(DEFAULT_SHIPMENT);

  useEffect(() => {
    // 1. Check if URL has query parameters
    const origin = searchParams.get("origin");
    const destination = searchParams.get("destination");
    const product = searchParams.get("product");
    const carrier = searchParams.get("carrier");
    const weight = searchParams.get("weight");
    const transport = searchParams.get("transport");

    if (origin || destination || product) {
      const newProfile: ShipmentProfile = {
        origin: origin || "CN",
        destination: destination || "US",
        product: (product && PRODUCT_LABELS[product]) || product || "Lithium-ion Batteries / Electronics",
        carrier: (carrier && CARRIER_LABELS[carrier]) || carrier || "Maersk Line",
        weight: weight || 1250,
        transport: (transport && TRANSPORT_LABELS[transport]) || transport || "Ocean Freight (FCL)",
      };
      setProfile(newProfile);
      saveStoredShipment(newProfile);
      return;
    }

    // 2. Read from localStorage
    setProfile(getStoredShipment());

    const handleUpdate = () => {
      setProfile(getStoredShipment());
    };
    window.addEventListener("shipment_profile_updated", handleUpdate);
    return () => window.removeEventListener("shipment_profile_updated", handleUpdate);
  }, [searchParams]);

  return (
    <div className="context-bar">
      <span>
        <strong>Shipment:</strong> {profile.origin} &rarr; {profile.destination} | {profile.product} |{" "}
        {profile.transport} ({Number(profile.weight).toLocaleString()} kg) | {profile.carrier}
      </span>
      <Link href="/" title="Change active shipment profile">
        Change
      </Link>
    </div>
  );
}