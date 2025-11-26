import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatFileSize, formatDate, API_BASE_URL } from "../utils/api";

export default function UploadedFilesPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const fileList = await api.getFiles();
      setFiles(fileList);
    } catch (err) {
      console.error("Failed to load files:", err);
      setError(err.message || "Failed to load files");
    } finally {
      setLoading(false);
    }
  };

  const handleView = (storedAsOrId) => {
    // Prefer stored_as when available; fallback to id
    const filename = storedAsOrId;
    // If backend endpoint is available:
    const url = `${API_BASE_URL}/files/download/${encodeURIComponent(filename)}`;
    // open in new tab - ensure popup allowed by user gesture (click)
    window.open(url, "_blank");
  };

  const handleAnalyze = async (fileId) => {
    try {
      // Navigate to dashboard which will load the analysis
      navigate(`/dashboard?fileId=${fileId}`);
    } catch (err) {
      alert(`Failed to analyze file: ${err.message}`);
    }
  };

  const handleDelete = async (fileId, fileName) => {
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) {
      return;
    }

    setDeletingId(fileId);
    try {
      await api.deleteFile(fileId);
      // Reload files list
      await loadFiles();
    } catch (err) {
      console.error("Failed to delete file:", err);
      alert(`Failed to delete file: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownload = (fileId, fileName) => {
    // Note: This would require a backend endpoint to download files
    // For now, we'll show a message
    alert(
      `Download functionality requires a backend endpoint. File ID: ${fileId}`
    );
  };

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h2>Uploaded Files</h2>
          <p className="muted">Loading files...</p>
        </div>
        <div className="card">
          <div className="loading-spinner">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Uploaded Files</h2>
        <p className="muted">Files you uploaded (stored on server).</p>
        <button
          className="btn primary"
          onClick={loadFiles}
          style={{ marginTop: "12px" }}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="card">
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      <div className="card">
        {files.length === 0 ? (
          <div className="empty-state">
            <p>No files uploaded yet.</p>
            <p className="muted">
              Upload a file from the Upload page to get started.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="files-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Size</th>
                  <th>Type</th>
                  <th>Uploaded At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.id}>
                    <td>
                      <strong>{f.name}</strong>
                    </td>
                    <td>{f.size ? formatFileSize(f.size) : "N/A"}</td>
                    <td>
                      <span className="file-type-badge">
                        {f.type
                          ? f.type.split("/")[1]?.toUpperCase() || "FILE"
                          : f.name
                              .substring(f.name.lastIndexOf(".") + 1)
                              .toUpperCase()}
                      </span>
                    </td>
                    <td>{formatDate(f.uploadedAt)}</td>
                    <td>
                        <div className="action-buttons">
                        <button
                          className="btn small btn-primary"
                          onClick={() => navigate(`/upload?fileId=${f.stored_as || f.id}`)}
                          title="View"
                        >
                          View
                        </button>

                        <button
                          className="btn small"
                          onClick={() => handleAnalyze(f.stored_as || f.id)}
                          title="Analyze"
                        >
                          Analyze
                        </button>

                        <button
                          className="btn small"
                          onClick={() => navigate(`/summary?id=${f.stored_as || f.id}`)}
                          title="Company Summary"
                        >
                          Summary
                        </button>

                        <button
                          className="btn small btn-danger"
                          onClick={() => handleDelete(f.id, f.name)}
                          disabled={deletingId === f.id}
                          title="Delete"
                        >
                          {deletingId === f.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>

                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
