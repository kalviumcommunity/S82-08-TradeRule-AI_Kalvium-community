export default function AdminUploadPage() {
  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Administration / Knowledge base</div>
          <h1>Document Upload</h1>
          <p>Upload official regulatory schedules, customs bulletins, or compliance manifests.</p>
        </div>
        <div className="stat-card"><span>Indexed documents</span><strong>03</strong></div>
      </div>

      <div className="upload-zone cursor-pointer">
        <input type="file" id="file-upload" className="hidden" />
        <label htmlFor="file-upload" className="cursor-pointer mb-0">
          <strong>Drag and drop regulatory files here</strong>
          <span>Supports PDF, XML, and official customs schedules (.csv)</span>
        </label>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Upload Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>IMDG_Code_Amendment_41-22.pdf</td>
              <td>2026-06-12</td>
              <td>
                <span className="badge-high">Indexed</span>
              </td>
            </tr>
            <tr>
              <td>CBP_Customs_Bulletin_Vol60.pdf</td>
              <td>2026-06-10</td>
              <td>
                <span className="badge-high">Indexed</span>
              </td>
            </tr>
            <tr>
              <td>EU_Battery_Regulation_2023.xml</td>
              <td>2026-06-05</td>
              <td>
                <span className="badge-medium">Processing</span>
              </td>
            </tr>
            <tr>
              <td>
                Unverified_Tariff_Schedule_Q2.csv
                <div className="mt-1">
                  <span className="chip text-confidence-low border-confidence-low mb-0">
                    Missing required metadata: country, document type.
                  </span>
                </div>
              </td>
              <td>2026-06-01</td>
              <td>
                <span className="badge-low">Rejected</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}