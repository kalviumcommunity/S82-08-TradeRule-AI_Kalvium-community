export default function ShipmentIntakePage() {
  return (
    <div>
      <div className="page-header">
        <div className="page-kicker">Step 1 of 3 / Shipment profile</div>
        <h1>Shipment Intake</h1>
        <p>Set the shipment context once. TradeRule AI will use it to surface the relevant compliance rules and supporting sources.</p>
      </div>

      <div className="intake-note">Required fields are marked by the active shipment profile.</div>

      <div className="dashboard-card">
        <form action="/ask" method="GET">
          <div className="grid grid-cols-2 gap-5 mb-5">
            <div>
              <label className="form-label" htmlFor="origin">Origin Country</label>
              <select id="origin" name="origin" className="form-select">
                <option value="CN">China (CN)</option>
                <option value="US">United States (US)</option>
                <option value="DE">Germany (DE)</option>
                <option value="VN">Vietnam (VN)</option>
              </select>
            </div>
            <div>
              <label className="form-label" htmlFor="destination">Destination Country</label>
              <select id="destination" name="destination" className="form-select">
                <option value="US">United States (US)</option>
                <option value="CA">Canada (CA)</option>
                <option value="GB">United Kingdom (GB)</option>
                <option value="AU">Australia (AU)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5 mb-5">
            <div>
              <label className="form-label" htmlFor="product">Product Category</label>
              <select id="product" name="product" className="form-select">
                <option value="electronics">Lithium-ion Batteries / Electronics</option>
                <option value="apparel">Textiles & Apparel</option>
                <option value="chemicals">Industrial Chemical Compounds</option>
                <option value="machinery">Mechanical Parts</option>
              </select>
            </div>
            <div>
              <label className="form-label" htmlFor="carrier">Carrier</label>
              <select id="carrier" name="carrier" className="form-select">
                <option value="maersk">Maersk Line</option>
                <option value="msc">MSC Mediterranean</option>
                <option value="fedex">FedEx Express</option>
                <option value="dhl">DHL Global Forwarding</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-5 mb-8">
            <div>
              <label className="form-label" htmlFor="weight">Weight (kg)</label>
              <input type="number" id="weight" name="weight" defaultValue={1250} className="form-input" />
            </div>
            <div>
              <label className="form-label" htmlFor="transport">Transport Type</label>
              <select id="transport" name="transport" className="form-select">
                <option value="ocean">Ocean Freight (FCL)</option>
                <option value="air">Air Cargo</option>
                <option value="rail">Rail Freight</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="primary-btn">
              Continue to Q&amp;A
            </button>
            <button type="reset" className="secondary-btn">
              Clear form
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}