import { useState, useEffect } from "react";
import { api, validateFile, formatFileSize, ALLOWED_EXTENSIONS } from "../utils/api";

const LAST_UPLOAD_KEY = "lastUploadResult";
const LAST_COMPANY_KEY = "latestCompanyName";

export default function UploadComponent() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("idle"); // idle, uploading, analyzing, complete
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [company, setCompany] = useState(() => localStorage.getItem(LAST_COMPANY_KEY));

  // Load last upload result from sessionStorage on mount
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

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) {
      setFile(null);
      setValidationError(null);
      return;
    }

    // Validate file
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
      // Step 1: Upload the file
      const uploadData = await api.uploadFile(file);
      
      if (!uploadData.file_id) {
        throw new Error("Upload failed: No file ID returned");
      }

      setUploadProgress("analyzing");

      // Step 2: Analyze the file
      const analysisData = await api.analyzeFile(uploadData.file_id);

      // Store file info in localStorage for UploadedFilesPage
      const detectedCompany = uploadData.company || company || null;
      if (detectedCompany) {
        setCompany(detectedCompany);
        localStorage.setItem(LAST_COMPANY_KEY, detectedCompany);
      }

      const fileInfo = {
        id: uploadData.file_id,
        name: file.name,
        uploadedAt: new Date().toISOString(),
        size: file.size,
        type: file.type,
        company: detectedCompany,
      };

      const storedFiles = localStorage.getItem("uploadedFiles");
      const files = storedFiles ? JSON.parse(storedFiles) : [];
      files.unshift(fileInfo);
      localStorage.setItem("uploadedFiles", JSON.stringify(files));

      const uploadResult = {
        upload: uploadData,
        analysis: analysisData,
      };
      
      setResult(uploadResult);
      setUploadProgress("complete");

      // Store result in sessionStorage for tab-level persistence
      sessionStorage.setItem(LAST_UPLOAD_KEY, JSON.stringify(uploadResult));

      // Clear file input
      document.getElementById("fileInput").value = "";
      setFile(null);
    } catch (err) {
      console.error(err);
      setError(err.message || "Upload and analysis failed");
      setUploadProgress("idle");
    } finally {
      setLoading(false);
    }
  };

  const getProgressText = () => {
    switch (uploadProgress) {
      case "uploading":
        return "Uploading file...";
      case "analyzing":
        return "Analyzing document...";
      case "complete":
        return "Complete!";
      default:
        return "";
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
          <small>
            Supported format: PDF only. Max size: 50MB
          </small>
        </div>
      </div>

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
                <p>
                  <strong>File ID:</strong> {result.upload.file_id}
                </p>
                <p>
                  <strong>Status:</strong> {result.upload.message}
                </p>
                {company && (
                  <p>
                    <strong>Company:</strong> {company}
                  </p>
                )}
              </div>

              {result.analysis && (
                <>
                  {result.analysis.kpis && (
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

                  {result.analysis.trends && (
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
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
