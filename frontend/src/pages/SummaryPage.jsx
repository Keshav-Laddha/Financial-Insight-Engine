import React, { useEffect, useState } from "react";
import { api } from "../utils/api";
import { useSearchParams } from "react-router-dom";
import jsPDF from "jspdf";
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

  const downloadSummaryPDF = () => {
    if (!summary) {
      alert("No summary available to download");
      return;
    }

    const doc = new jsPDF({ unit: "pt", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 40;
    let y = margin;

    // ===== HEADER =====
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("Company Financial Summary", pageWidth / 2, y, { align: "center" });
    y += 30;

    // Company
    doc.setFontSize(13);
    doc.setFont("helvetica", "normal");
    if (summary.company) {
      doc.text(`Company: ${summary.company}`, margin, y);
      y += 20;
    }

    // Pages scanned
    doc.text(
      `Pages Scanned: ${summary.start_page} → ${summary.end_page}`,
      margin,
      y
    );
    y += 20;

    // Date
    doc.text(`Generated On: ${new Date().toLocaleString()}`, margin, y);
    y += 30;

    // ===== SUMMARY SECTION =====
    doc.setFont("helvetica", "bold");
    doc.setFontSize(15);
    doc.text("Key Highlights", margin, y);
    y += 20;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);

    const bulletLines = (summary.summary || "")
      .split(". ")
      .filter((l) => l.trim().length > 0)
      .map((l) => "• " + l.trim() + ".");

    bulletLines.forEach((line) => {
      const wrapped = doc.splitTextToSize(line, pageWidth - margin * 2);

      if (y + wrapped.length * 16 > doc.internal.pageSize.getHeight() - 40) {
        doc.addPage();
        y = margin;
      }

      doc.text(wrapped, margin + 10, y);
      y += wrapped.length * 16;
    });

    // ===== OPTIONAL KPIs SECTION =====
    if (summary.kpis) {
      y += 20;
      if (y > doc.internal.pageSize.getHeight() - 60) {
        doc.addPage();
        y = margin;
      }

      doc.setFont("helvetica", "bold");
      doc.setFontSize(15);
      doc.text("Key Performance Indicators", margin, y);
      y += 20;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(12);

      Object.entries(summary.kpis).forEach(([key, value]) => {
        const line = `• ${key.replace(/_/g, " ").toUpperCase()}: ${value}`;
        const wrapped = doc.splitTextToSize(line, pageWidth - margin * 2);

        if (y + wrapped.length * 16 > doc.internal.pageSize.getHeight() - 40) {
          doc.addPage();
          y = margin;
        }

        doc.text(wrapped, margin + 10, y);
        y += wrapped.length * 16;
      });
    }

    // ===== SAVE =====
    const filename =
      summary.company?.replace(/[^a-zA-Z0-9]/g, "_") ||
      "Financial_Summary_Report";

    doc.save(`${filename}_Summary.pdf`);
  };

  // useEffect(() => {
  //   if (!fileId) {
  //     setError("No file selected. Upload or select a file first.");
  //     setLoading(false);
  //     return;
  //   }

  //   const cachedId = localStorage.getItem(LATEST_SUMMARY_ID);
  //   const cachedData = localStorage.getItem(LATEST_SUMMARY_DATA);

  //   // ⭐ Load cached summary if valid
  //   if (cachedId === fileId && cachedData) {
  //     try {
  //       const parsed = JSON.parse(cachedData);

  //       if (parsed && parsed.summary) {
  //         setSummary(parsed);
  //         setLoading(false);
  //         return;
  //       }
  //     } catch {}
  //   }

  //   // Fetch fresh
  //   async function loadSummary() {
  //     try {
  //       const data = await api.getSummary(fileId);

  //       // Validate backend response shape
  //       if (!data || !data.summary) {
  //         throw new Error("Summary not found for this file.");
  //       }

  //       localStorage.setItem(LATEST_SUMMARY_ID, fileId);
  //       localStorage.setItem(LATEST_SUMMARY_DATA, JSON.stringify(data));

  //       setSummary(data);
  //     } catch (err) {
  //       setError(err.message || "Failed to load summary.");
  //     } finally {
  //       setLoading(false);
  //     }
  //   }

  //   loadSummary();
  // }, [fileId]);

  useEffect(() => {
    if (!fileId) {
      setError("No file selected. Upload or select a file first.");
      setLoading(false);
      return;
    }

    const cacheKey = `summary_${fileId}`;
    const cached = sessionStorage.getItem(cacheKey);

    // If cached -> use it immediately
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (parsed && parsed.summary) {
          setSummary(parsed);
          setLoading(false);
          return;
        }
      } catch (e) {
        console.warn("Failed to parse summary cache", e);
      }
    }

    // Fetch fresh if no cache
    let cancelled = false;
    async function loadSummary() {
      try {
        const data = await api.getSummary(fileId);
        if (!data || !data.summary) {
          throw new Error("Summary not found for this file.");
        }
        if (!cancelled) {
          sessionStorage.setItem(cacheKey, JSON.stringify(data));
          setSummary(data);
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load summary.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadSummary();

    return () => { cancelled = true; };
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

        {/* Download PDF Button */}
        <div style={{ marginBottom: "15px" }}>
          <button className="btn primary" onClick={downloadSummaryPDF}>
            Download Summary PDF
          </button>
        </div>

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