const regulations = [
  { title: "United States import controls", scope: "United States", category: "Customs", updated: "Jun 14, 2026", status: "Current" },
  { title: "EU battery transport requirements", scope: "European Union", category: "Dangerous goods", updated: "Jun 12, 2026", status: "Current" },
  { title: "Canada textile classification guide", scope: "Canada", category: "Tariff classification", updated: "Jun 08, 2026", status: "Current" },
  { title: "Vietnam chemical transit rules", scope: "Vietnam", category: "Restricted goods", updated: "May 29, 2026", status: "Review due" },
];

export default function RegulationsLibraryPage() {
  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Knowledge base / Country rules</div>
          <h1>Regulations Library</h1>
          <p>Browse the customs and shipping rules TradeRule AI uses to evaluate shipment routes.</p>
        </div>
        <a href="/admin/upload" className="btn-primary">Add source</a>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Active sources</span><strong>128</strong></div>
        <div className="stat-card"><span>Countries covered</span><strong>24</strong></div>
        <div className="stat-card"><span>Review due</span><strong>07</strong></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Source</th><th>Scope</th><th>Category</th><th>Updated</th><th>Status</th></tr>
          </thead>
          <tbody>
            {regulations.map((regulation) => (
              <tr key={regulation.title}>
                <td><strong>{regulation.title}</strong></td>
                <td>{regulation.scope}</td>
                <td>{regulation.category}</td>
                <td>{regulation.updated}</td>
                <td><span className={regulation.status === "Current" ? "badge-high" : "badge-medium"}>{regulation.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
