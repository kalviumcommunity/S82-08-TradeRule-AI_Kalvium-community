const shipments = [
  { id: "TR-10482", route: "CN -> US", product: "Lithium-ion batteries", result: "Cleared", reviewed: "Today, 14:22" },
  { id: "TR-10481", route: "DE -> CA", product: "Textiles & apparel", result: "Cleared", reviewed: "Today, 13:05" },
  { id: "TR-10480", route: "VN -> US", product: "Industrial chemicals", result: "Needs review", reviewed: "Today, 11:40" },
  { id: "TR-10479", route: "CN -> GB", product: "Mechanical parts", result: "Cleared", reviewed: "Yesterday, 16:18" },
];

export default function ShipmentHistoryPage() {
  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Operations / Recent checks</div>
          <h1>Shipment History</h1>
          <p>Revisit shipment decisions and the route context used by the compliance review.</p>
        </div>
        <a href="/ask" className="btn-primary">New shipment</a>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Checks this month</span><strong>246</strong></div>
        <div className="stat-card"><span>Cleared</span><strong>218</strong></div>
        <div className="stat-card"><span>Needs review</span><strong>28</strong></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Shipment</th><th>Route</th><th>Product</th><th>Result</th><th>Reviewed</th></tr>
          </thead>
          <tbody>
            {shipments.map((shipment) => (
              <tr key={shipment.id}>
                <td><strong>{shipment.id}</strong></td>
                <td>{shipment.route}</td>
                <td>{shipment.product}</td>
                <td><span className={shipment.result === "Cleared" ? "badge-high" : "badge-medium"}>{shipment.result}</span></td>
                <td>{shipment.reviewed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
