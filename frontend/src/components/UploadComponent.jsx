import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, validateFile, formatFileSize } from "../utils/api";
import { useSearchParams } from "react-router-dom";

const LAST_UPLOAD_KEY = "lastUploadResult";
const LAST_COMPANY_KEY = "latestCompanyName";
const SESSION_PREFIXES_TO_CLEAR = ["dashboard_", "summary_", "news_", "files_list"];

export default function UploadComponent() {
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [company, setCompany] = useState(() => localStorage.getItem(LAST_COMPANY_KEY));
  const [importantKpis, setImportantKpis] = useState(() =>
    JSON.parse(localStorage.getItem("LATEST_IMPORTANT_KPIS") || "{}")
  );
  const [params] = useSearchParams();
  const fileIdFromURL = params.get("fileId");




  // Load last upload result
  useEffect(() => {
    const lastResult = sessionStorage.getItem(LAST_UPLOAD_KEY);
    if (lastResult) {
      try {
        const parsed = JSON.parse(lastResult);
        setResult(parsed);
        setUploadProgress("complete");
        if (parsed?.upload?.company) {
          setCompany(parsed.upload.company);
        }
      } catch (err) {
        console.error("Failed to load last upload result:", err);
      }
    }
  }, []);


  // helper to clear session caches (prefix match)
  const clearSessionCaches = (keepForFileId = null) => {
    const keysToRemove = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const k = sessionStorage.key(i);
      if (!k) continue;
      for (const p of SESSION_PREFIXES_TO_CLEAR) {
        if (k.startsWith(p)) {
          // If keepForFileId provided and k === `dashboard_${keepForFileId}` skip removal
          if (keepForFileId && k === `dashboard_${keepForFileId}`) continue;
          keysToRemove.push(k);
          break;
        }
      }
    }
    keysToRemove.forEach((k) => sessionStorage.removeItem(k));
  };


  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) {
      setFile(null);
      setValidationError(null);
      return;
    }

    const validation = validateFile(selectedFile);
    if (!validation.isValid) {
      setValidationError(validation.errors.join(". "));
      setFile(null);
      return;
    }

    setValidationError(null);
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setUploadProgress("uploading");

    try {
      // Step 1 — Upload file
      const uploadData = await api.uploadFile(file);

      if (!uploadData.file_id) {
        throw new Error("Upload failed: No file ID returned");
      }

      setUploadProgress("analyzing");

      // Step 2 — Analyze file
      const analysisData = await api.analyzeFile(uploadData.file_id);
      setImportantKpis(analysisData.important_kpis || {}); //change

      // Save detected company
      const detectedCompany = uploadData.company || company || null;
      if (detectedCompany) {
        setCompany(detectedCompany);
        localStorage.setItem(LAST_COMPANY_KEY, detectedCompany);
      }

      // Store file for UploadedFiles page
      const fileInfo = {
        id: uploadData.file_id,
        stored_as: uploadData.stored_as, // IMPORTANT
        name: file.name,
        uploadedAt: new Date().toISOString(),
        size: file.size,
        type: file.type,
        company: detectedCompany,
      };

      const storedFiles = JSON.parse(localStorage.getItem("uploadedFiles") || "[]");
      storedFiles.unshift(fileInfo);
      localStorage.setItem("uploadedFiles", JSON.stringify(storedFiles));
      try {
        await api.saveFileMetadata(fileInfo);
      } catch (e) {
        // already handled in api.saveFileMetadata; optionally log
        console.warn("saveFileMetadata failed:", e);
      }


      // Full upload result
      const uploadResult = {
        upload: uploadData,
        analysis: analysisData,
      };

      setResult(uploadResult);
      setUploadProgress("complete");

      
      //localStorage.setItem("LAST_SUMMARY_FILE_ID", uploadData.file_id);

      localStorage.setItem("LATEST_FILE_ID", uploadData.file_id);
      localStorage.setItem("LATEST_ANALYSIS_DATA", JSON.stringify(analysisData));
      localStorage.setItem("LAST_SUMMARY_FILE_ID", uploadData.file_id);
      localStorage.removeItem("LAST_SUMMARY_DATA");   // ❗ VERY IMPORTANT

      // Clear previous session caches (force pages to re-fetch on first open for the new file)
      clearSessionCaches(/* keepForFileId = null */); // remove everything so fresh fetches happen

      sessionStorage.setItem(LAST_UPLOAD_KEY, JSON.stringify(uploadResult));

      // Clear input
      
      setFile(null);
      document.getElementById("fileInput").value = "";
      // ⭐ Redirect to Summary Page
      // navigate(`/summary?id=${uploadData.stored_as}`);

    } catch (err) {
      console.error(err);
      setError(err.message || "Upload and analysis failed");
      setUploadProgress("idle");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    async function loadExistingFile() {
      if (!fileIdFromURL) return;

      setLoading(true);
      setUploadProgress("analyzing");

      try {
        const analysisData = await api.analyzeFile(fileIdFromURL);

        setImportantKpis(analysisData.important_kpis || {});
        setResult({ upload: { file_id: fileIdFromURL }, analysis: analysisData });

        // Save locally so dashboard/summary also work
        localStorage.setItem("LATEST_FILE_ID", fileIdFromURL);
        localStorage.setItem("LATEST_ANALYSIS_DATA", JSON.stringify(analysisData));

        setUploadProgress("complete");
      } catch (err) {
        console.error(err);
        setError("Failed to load saved file analysis");
      } finally {
        setLoading(false);
      }
    }

    loadExistingFile();
  }, [fileIdFromURL]);


  const getProgressText = () => {
    switch (uploadProgress) {
      case "uploading": return "Uploading file...";
      case "analyzing": return "Analyzing document...";
      case "complete": return "Complete!";
      default: return "";
    }
  };

  return (
    <div>
      <div className="upload-area">
        <input
          id="fileInput"
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />

        <div className="upload-actions">
          <button
            className="btn"
            onClick={() => document.getElementById("fileInput").click()}
            disabled={loading}
          >
            Choose File
          </button>

          <button
            className="btn primary"
            onClick={handleUpload}
            disabled={loading || !file}
          >
            {loading ? getProgressText() : "Upload & Analyze"}
          </button>
        </div>

        <div className="hint">
          {file ? (
            <div className="file-info">
              <strong>{file.name}</strong>
              <span className="file-size">{formatFileSize(file.size)}</span>
            </div>
          ) : (
            <span>No file chosen</span>
          )}
        </div>

        {validationError && (
          <div className="alert alert-warning" style={{ marginTop: "12px" }}>
            {validationError}
          </div>
        )}

        <div className="file-hint">
          <small>Supported format: PDF only. Max size: 50MB</small>
        </div>
      </div>

      {/* EXISTING RESULT UI (unchanged) */}
      <div style={{ marginTop: 18 }}>
        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && (
          <div className="result">
            <h4>✅ Upload & Analysis Complete</h4>
            <div className="result-content">
              <div className="result-section">
                <h5>File Information</h5>
                <p><strong>File ID:</strong> {result.upload.file_id}</p>
                <p><strong>Status:</strong> {result.upload.message}</p>
                {company && <p><strong>Company:</strong> {company}</p>}
              </div>

              {/* ⭐ IMPORTANT KPIS SECTION ⭐ */}
              {importantKpis && (
                <div className="result-section" style={{ marginTop: "20px" }}>
                  <h5>Key Highlights (Data in ₹ Millions)</h5>

                  {/* earlier correct */}
                  {/* <div className="kpis-grid">
                    {Object.entries(importantKpis)
                      .filter(([key]) => key !== "ratios")
                      .map(([key, value]) => (
                        value !== null &&
                        <div key={key} className="kpi-item">
                          <span className="kpi-label">
                            {key.replace(/_/g, " ").toUpperCase()}
                          </span>
                          <span className="kpi-value">
                            {value.toLocaleString()}
                          </span>
                        </div>
                      ))}
                  </div> */}

                  <div className="kpis-grid">
                    {Object.entries(importantKpis)
                      .filter(([key]) => key !== "ratios")
                      .map(([key, value]) => {

                        if (typeof value === "object" && value !== null) {
                          // It's a period object -> show properly
                          return (
                            <div key={key} className="kpi-item">
                              <span className="kpi-label">{key.replace(/_/g, " ").toUpperCase()}</span>
                              <span className="kpi-value">
                                {`2025: ${value.latest ?? "-"}, 2024: ${value.prev1 ?? "-"}, 2023: ${value.prev2 ?? "-"}`}
                              </span>
                            </div>
                          );
                        }

                        // Normal KPI
                        return (
                          <div key={key} className="kpi-item">
                            <span className="kpi-label">{key.replace(/_/g, " ").toUpperCase()}</span>
                            <span className="kpi-value">{Number(value).toLocaleString()}</span>
                          </div>
                        );
                      })}
                  </div>


                  {/* --- RATIOS SECTION --- */}
                  {importantKpis.ratios && (
                    <>
                      <h5 style={{ marginTop: "16px" }}>Important Ratios</h5>
                      <div className="kpis-grid">
                        {Object.entries(importantKpis.ratios).map(([key, value]) => (
                          value !== null &&
                          <div key={key} className="kpi-item">
                            <span className="kpi-label">
                              {key.replace(/_/g, " ").toUpperCase()}
                            </span>
                            <span className="kpi-value">{value.toFixed(3)}</span>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {result.analysis?.kpis && (
                <div className="result-section">
                  <h5>Key Performance Indicators</h5>
                  <div className="kpis-grid">
                    {Object.entries(result.analysis.kpis).map(([key, value]) => (
                      <div key={key} className="kpi-item">
                        <span className="kpi-label">{key.replace(/_/g, " ")}</span>
                        <span className="kpi-value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.analysis?.trends && (
                <div className="result-section">
                  <h5>Trends</h5>
                  <pre className="result-json">
                    {JSON.stringify(result.analysis.trends, null, 2)}
                  </pre>
                </div>
              )}

              <div className="result-section">
                <h5>Full Analysis Data</h5>
                <details>
                  <summary>View detailed analysis</summary>
                  <pre className="result-json">
                    {JSON.stringify(result.analysis, null, 2)}
                  </pre>
                </details>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
}
// changes kiye hai bhai pls haggna mat