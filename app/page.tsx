"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  DEFAULT_SHIPMENT,
  getStoredShipment,
  saveStoredShipment,
  ShipmentProfile,
} from "@/components/ShipmentContextBar";

export default function ShipmentIntakePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<ShipmentProfile>(DEFAULT_SHIPMENT);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setProfile(getStoredShipment());
    setMounted(true);
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setProfile((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    saveStoredShipment(profile);
    const params = new URLSearchParams({
      origin: profile.origin,
      destination: profile.destination,
      product: profile.product,
      carrier: profile.carrier,
      weight: String(profile.weight),
      transport: profile.transport,
    });
    router.push(`/ask?${params.toString()}`);
  };

  const handleReset = () => {
    setProfile(DEFAULT_SHIPMENT);
    saveStoredShipment(DEFAULT_SHIPMENT);
  };

  if (!mounted) {
    return null;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-kicker">Step 1 of 3 / Shipment profile</div>
        <h1>Shipment Intake</h1>
        <p>
          Set your shipment context once. TradeRule AI will evaluate compliance rules,
          customs declarations, hazardous materials restrictions, and carrier agreements based on this profile.
        </p>
      </div>

      <div className="intake-note">
        Required fields are marked by the active shipment profile. All subsequent Q&amp;A, audit reviews, and follow-up threads will adapt to this shipment.
      </div>

      <div className="stat-grid mb-6">
        <div className="stat-card">
          <span>Active Route</span>
          <strong>{profile.origin} &rarr; {profile.destination}</strong>
        </div>
        <div className="stat-card">
          <span>Selected Carrier</span>
          <strong>{profile.carrier}</strong>
        </div>
        <div className="stat-card">
          <span>Transport Mode</span>
          <strong>{profile.transport}</strong>
        </div>
      </div>

      <div className="dashboard-card">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-5 mb-5">
            <div>
              <label className="form-label" htmlFor="origin">
                Origin Country
              </label>
              <select
                id="origin"
                name="origin"
                className="form-select"
                value={profile.origin}
                onChange={handleChange}
              >
                <option value="CN">China (CN)</option>
                <option value="US">United States (US)</option>
                <option value="DE">Germany (DE)</option>
                <option value="VN">Vietnam (VN)</option>
              </select>
            </div>
            <div>
              <label className="form-label" htmlFor="destination">
                Destination Country
              </label>
              <select
                id="destination"
                name="destination"
                className="form-select"
                value={profile.destination}
                onChange={handleChange}
              >
                <option value="US">United States (US)</option>
                <option value="CA">Canada (CA)</option>
                <option value="GB">United Kingdom (GB)</option>
                <option value="AU">Australia (AU)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5 mb-5">
            <div>
              <label className="form-label" htmlFor="product">
                Product Category
              </label>
              <select
                id="product"
                name="product"
                className="form-select"
                value={profile.product}
                onChange={handleChange}
              >
                <option value="Lithium-ion Batteries / Electronics">
                  Lithium-ion Batteries / Electronics (UN3481)
                </option>
                <option value="Textiles & Apparel">Textiles &amp; Apparel</option>
                <option value="Industrial Chemical Compounds">
                  Industrial Chemical Compounds
                </option>
                <option value="Mechanical Parts">Mechanical Parts</option>
              </select>
            </div>
            <div>
              <label className="form-label" htmlFor="carrier">
                Carrier
              </label>
              <select
                id="carrier"
                name="carrier"
                className="form-select"
                value={profile.carrier}
                onChange={handleChange}
              >
                <option value="Maersk Line">Maersk Line</option>
                <option value="MSC Mediterranean">MSC Mediterranean</option>
                <option value="FedEx Express">FedEx Express</option>
                <option value="DHL Global Forwarding">DHL Global Forwarding</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5 mb-8">
            <div>
              <label className="form-label" htmlFor="weight">
                Weight (kg)
              </label>
              <input
                type="number"
                id="weight"
                name="weight"
                value={profile.weight}
                onChange={handleChange}
                className="form-input"
                min={1}
              />
            </div>
            <div>
              <label className="form-label" htmlFor="transport">
                Transport Type
              </label>
              <select
                id="transport"
                name="transport"
                className="form-select"
                value={profile.transport}
                onChange={handleChange}
              >
                <option value="Ocean Freight (FCL)">Ocean Freight (FCL)</option>
                <option value="Air Cargo">Air Cargo</option>
                <option value="Rail Freight">Rail Freight</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="primary-btn">
              Continue to Q&amp;A
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleReset}
            >
              Reset to default
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}