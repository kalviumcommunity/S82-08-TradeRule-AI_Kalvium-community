const agreements = [
  { carrier: "Maersk Line", lanes: "Asia -> United States", effective: "Jan 01, 2026", documents: "12" },
  { carrier: "MSC Mediterranean", lanes: "Europe -> Canada", effective: "Feb 15, 2026", documents: "08" },
  { carrier: "DHL Global Forwarding", lanes: "Global air freight", effective: "Mar 04, 2026", documents: "15" },
  { carrier: "FedEx Express", lanes: "United States -> Australia", effective: "Apr 20, 2026", documents: "06" },
];

export default function CarrierAgreementsPage() {
  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Knowledge base / Carrier terms</div>
          <h1>Carrier Agreements</h1>
          <p>Review active carrier terms that can change documentation, routing, and handling requirements.</p>
        </div>
        <button type="button" className="btn-secondary">Export terms</button>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Active agreements</span><strong>18</strong></div>
        <div className="stat-card"><span>Covered carriers</span><strong>09</strong></div>
        <div className="stat-card"><span>Expiring this quarter</span><strong>03</strong></div>
      </div>

      <div className="surface-panel mb-6">
        <div className="page-kicker mb-2">Operational note</div>
        <p className="text-ink text-sm">Carrier terms are checked alongside country regulations when a shipment profile is evaluated.</p>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Carrier</th><th>Primary lanes</th><th>Effective</th><th>Source documents</th></tr>
          </thead>
          <tbody>
            {agreements.map((agreement) => (
              <tr key={agreement.carrier}>
                <td><strong>{agreement.carrier}</strong></td>
                <td>{agreement.lanes}</td>
                <td>{agreement.effective}</td>
                <td>{agreement.documents}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
