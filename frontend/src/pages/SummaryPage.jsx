import React, { useEffect, useState } from "react";
import { api } from "../utils/api";
import { useSearchParams } from "react-router-dom";

const LATEST_SUMMARY_ID = "LAST_SUMMARY_FILE_ID";
const LATEST_SUMMARY_DATA = "LAST_SUMMARY_DATA";

export default function SummaryPage() {
  const [params] = useSearchParams();

  const fileId = params.get("id") || localStorage.getItem(LATEST_SUMMARY_ID);

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  // Safe bulletify (never crashes)
  const bulletify = (text) => {
    if (!text || typeof text !== "string") return <li>No summary available.</li>;

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

    const cachedId = localStorage.getItem(LATEST_SUMMARY_ID);
    const cachedData = localStorage.getItem(LATEST_SUMMARY_DATA);

    // ⭐ Load cached summary if valid
    if (cachedId === fileId && cachedData) {
      try {
        const parsed = JSON.parse(cachedData);

        if (parsed && parsed.summary) {
          setSummary(parsed);
          setLoading(false);
          return;
        }
      } catch {}
    }

    // Fetch fresh
    async function loadSummary() {
      try {
        const data = await api.getSummary(fileId);

        // Validate backend response shape
        if (!data || !data.summary) {
          throw new Error("Summary not found for this file.");
        }

        localStorage.setItem(LATEST_SUMMARY_ID, fileId);
        localStorage.setItem(LATEST_SUMMARY_DATA, JSON.stringify(data));

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

  if (error || !summary) {
    return (
      <div className="page">
        <div className="page-header">
          <h2>Company Summary</h2>
          <p className="muted text-red">{error || "No summary available."}</p>
        </div>
        <div className="card">
          <div className="alert alert-error">{error || "No summary available."}</div>
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

        <ul style={{ paddingLeft: "20px" }}>
          {bulletify(summary.summary)}
        </ul>

        <hr style={{ margin: "18px 0" }} />

        <p className="muted text-sm">
          <strong>Pages scanned:</strong> {summary.start_page} → {summary.end_page}
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