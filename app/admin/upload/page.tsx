"use client";

import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_RAG_API_URL || "http://127.0.0.1:8000";

interface DocumentRow {
  filename: string;
  upload_date: string;
  status: string;
  note?: string;
}

const DEFAULT_DOCUMENTS: DocumentRow[] = [
  {
    filename: "IMDG_Code_Amendment_41-22.pdf",
    upload_date: "2026-06-12",
    status: "Indexed",
  },
  {
    filename: "SOLAS_Chapter_VII_Carriage_of_Dangerous_Goods.pdf",
    upload_date: "2026-06-11",
    status: "Indexed",
  },
  {
    filename: "CBP_Customs_Bulletin_Vol60.pdf",
    upload_date: "2026-06-10",
    status: "Indexed",
  },
  {
    filename: "Carrier_Agreements_and_Routing_Guide.md",
    upload_date: "2026-06-08",
    status: "Indexed",
  },
  {
    filename: "Industrial_Chemicals_Transit_Compliance.md",
    upload_date: "2026-06-06",
    status: "Indexed",
  },
  {
    filename: "TradeRule_AI_System_Guide.md",
    upload_date: "2026-06-05",
    status: "Indexed",
  },
  {
    filename: "Textile_Quotas_and_Tariff_Classification_Guide.md",
    upload_date: "2026-06-04",
    status: "Indexed",
  },
];

export default function AdminUploadPage() {
  const [documents, setDocuments] = useState<DocumentRow[]>(DEFAULT_DOCUMENTS);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);

  useEffect(() => {
    fetchDocumentsList();
  }, []);

  async function fetchDocumentsList() {
    try {
      const res = await fetch(`${API_BASE_URL}/documents/list`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setDocuments(data);
        }
      }
    } catch {
      // Keep defaults
    }
  }

  async function handleFileSelected(file: File) {
    if (!file) return;

    setUploading(true);
    setStatusMessage({
      type: "info",
      text: `Uploading and indexing "${file.name}" into Qdrant vector store...`,
    });

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE_URL}/documents`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        let err = "Upload failed.";
        try {
          const payload = await res.json();
          if (payload?.detail) err = payload.detail;
        } catch {
          // ignore
        }
        throw new Error(err);
      }

      const result = await res.json();
      setStatusMessage({
        type: "success",
        text: `Successfully indexed "${result.filename}" (${result.summary?.total_chunks || 1} chunks generated).`,
      });

      // Refresh list
      fetchDocumentsList();
    } catch (err) {
      setStatusMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Document upload failed.",
      });
    } finally {
      setUploading(false);
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelected(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelected(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  // Quick helper to upload a sample schedule for demonstration
  async function handleUploadSample() {
    const sampleText = `# Port Transit and Wharfage Schedule 2026\n\nAll containerized shipments discharging at United States West Coast ports are subject to standard harbor maintenance fees (0.125% ad valorem) and port authority terminal handling charges (THC). Continuous bond cargo moving in in-bond transit (IT) to inland destinations is exempt from municipal ad valorem property tax.\n`;
    const sampleBlob = new Blob([sampleText], { type: "text/markdown" });
    const sampleFile = new File([sampleBlob], "Port_Transit_Tariff_Schedule_2026.md", {
      type: "text/markdown",
    });
    handleFileSelected(sampleFile);
  }

  return (
    <div>
      <div className="section-heading">
        <div>
          <div className="page-kicker">Administration / Knowledge base</div>
          <h1>Document Upload &amp; Vector Indexing</h1>
          <p>
            Upload regulatory schedules, maritime conventions, customs bulletins, or carrier agreements. Documents are automatically parsed, chunked, embedded, and indexed into Qdrant.
          </p>
        </div>
        <div className="stat-card">
          <span>Indexed documents</span>
          <strong>{String(documents.length).padStart(2, "0")}</strong>
        </div>
      </div>

      <div
        className="upload-zone cursor-pointer"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          accept=".pdf,.txt,.md"
          onChange={handleInputChange}
          disabled={uploading}
        />
        <label htmlFor="file-upload" className="cursor-pointer mb-0 block">
          <strong>
            {uploading
              ? "Indexing document in Qdrant..."
              : "Click to browse or drag and drop regulatory files here"}
          </strong>
          <span>Supports official regulatory files (.pdf, .md, .txt) &mdash; Max 10MB</span>
        </label>
      </div>

      <div className="flex justify-between items-center my-4">
        <span className="text-xs text-slate-500">
          Tip: Uploaded files are immediately searchable in the Q&amp;A engine and follow-up threads.
        </span>
        <button
          type="button"
          className="btn-secondary text-xs"
          onClick={handleUploadSample}
          disabled={uploading}
        >
          + Index Sample Port Schedule (.md)
        </button>
      </div>

      {statusMessage && (
        <div
          className={`p-4 rounded-lg border mb-6 text-sm ${
            statusMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : statusMessage.type === "error"
              ? "bg-red-50 border-red-200 text-red-800"
              : "bg-blue-50 border-blue-200 text-blue-800"
          }`}
        >
          {statusMessage.text}
        </div>
      )}

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
            {documents.map((doc, idx) => (
              <tr key={idx}>
                <td>
                  <strong>{doc.filename}</strong>
                  {doc.note && (
                    <div className="mt-1">
                      <span className="chip text-confidence-low border-confidence-low mb-0">
                        {doc.note}
                      </span>
                    </div>
                  )}
                </td>
                <td>{doc.upload_date}</td>
                <td>
                  <span
                    className={
                      doc.status === "Indexed"
                        ? "badge-high"
                        : doc.status === "Processing"
                        ? "badge-medium"
                        : "badge-low"
                    }
                  >
                    {doc.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}