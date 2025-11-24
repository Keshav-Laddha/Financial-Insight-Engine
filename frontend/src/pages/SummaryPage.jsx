import React, { useEffect, useState } from "react";
import { api } from "../utils/api";
import { useSearchParams } from "react-router-dom";

export default function SummaryPage() {
  const [params] = useSearchParams();

  // Priority: ?id → last stored → error
  const fileId =
    params.get("id") || localStorage.getItem("LAST_SUMMARY_FILE_ID");

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  // Convert long paragraph -> bullet points
  const bulletify = (text) => {
    return text
      .split(". ")
      .filter((line) => line.trim().length > 0)
      .map((sentence, i) => (
        <li key={i} style={{ marginBottom: "8px" }}>
          {sentence.trim()}.
        </li>
      ));
  };

  useEffect(() => {
    if (!fileId) {
      setError("No file selected. Upload or select a file first.");
      setLoading(false);
      return;
    }

    async function loadSummary() {
      try {
        const data = await api.getSummary(fileId);

        // store for later auto-load
        localStorage.setItem("LAST_SUMMARY_FILE_ID", fileId);

        setSummary(data);
      } catch (err) {
        setError(err.message || "Failed to load summary.");
      } finally {
        setLoading(false);
      }
    }

    loadSummary();
  }, [fileId]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h2>Company Summary</h2>
          <p className="muted">Loading summary...</p>
        </div>
        <div className="card">
          <div className="loading-spinner">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-header">
          <h2>Company Summary</h2>
          <p className="muted text-red">{error}</p>
        </div>
        <div className="card">
          <div className="alert alert-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Company Summary</h2>
        <p className="muted">Generated using TextRank summarization.</p>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: "12px" }}>Summary</h3>

        <ul style={{ paddingLeft: "20px" }}>{bulletify(summary.summary)}</ul>

        <hr style={{ margin: "18px 0" }} />

        <p className="muted text-sm">
          <strong>Pages scanned:</strong> {summary.start_page} →{" "}
          {summary.end_page}
        </p>

        <details style={{ marginTop: "18px" }}>
          <summary className="muted" style={{ cursor: "pointer" }}>
            Show raw extracted text
          </summary>
          <pre
            style={{
              background: "#f5f5f5",
              padding: "12px",
              marginTop: "8px",
              whiteSpace: "pre-wrap",
              borderRadius: "6px",
            }}
          >
            {summary.mda_text}
          </pre>
        </details>
      </div>
    </div>
  );
}
