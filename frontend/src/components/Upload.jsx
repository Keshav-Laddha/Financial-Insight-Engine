import { useState } from "react";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");

  const handleUpload = async () => {
    if (!file) return alert("Please select a PDF file first");
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Step 1: Upload the file
      const uploadRes = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });
      const uploadData = await uploadRes.json();
      
      if (!uploadRes.ok) {
        alert(uploadData.detail || "Upload failed");
        return;
      }

      // Step 2: If upload successful, call extraction endpoint with the file_id
      const fileId = uploadData.file_id;
      const extractRes = await fetch(`http://127.0.0.1:8000/extract-text/${fileId}`, {
        method: "POST",
      });
      
      const extractData = await extractRes.json();
      
      if (extractRes.ok) {
        // Display the extracted text from the OCR process
        setResult(extractData.extracted_text || JSON.stringify(extractData, null, 2));
      } else {
        alert(extractData.detail || "Text extraction failed");
        // Still show upload success even if extraction fails
        setResult(`File uploaded successfully but extraction failed.\nUpload Data: ${JSON.stringify(uploadData, null, 2)}`);
      }

    } catch (err) {
      alert("Upload failed. Check if backend is running and CORS is configured.");
      console.error(err);
    }
    setLoading(false);
  };

  
  return (
    <div style={styles.container}>
      <h1 style={styles.title}>📊 Financial Document Analyzer</h1>
      <p style={styles.subtitle}>Upload your quarterly or annual PDF report below</p>

      <div style={styles.uploadBox}>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
          style={styles.input}
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          style={styles.button}
        >
          {loading ? "⏳ Uploading..." : "🚀 Upload & Analyze"}
        </button>
      </div>

      <div style={styles.resultBox}>
        <h3 style={styles.resultTitle}>🧾 Extracted Text:</h3>
        <pre style={styles.resultArea}>
          {result ? result : "No data yet. Upload a file to analyze."}
        </pre>
      </div>
    </div>
  );
}

const styles = {
  container: {
    fontFamily: "Inter, sans-serif",
    textAlign: "center",
    padding: "2rem",
    minHeight: "100vh",
    background: "linear-gradient(135deg, #e8f0ff, #f9faff)",
  },
  title: {
    fontSize: "2.5rem",
    fontWeight: "700",
    color: "#2c3e50",
  },
  subtitle: {
    color: "#34495e",
    marginBottom: "2rem",
  },
  uploadBox: {
    background: "white",
    padding: "2rem",
    borderRadius: "16px",
    boxShadow: "0 6px 20px rgba(0,0,0,0.1)",
    display: "inline-block",
  },
  input: {
    marginRight: "1rem",
  },
  button: {
    background: "#007bff",
    color: "white",
    border: "none",
    borderRadius: "8px",
    padding: "0.6rem 1.2rem",
    cursor: "pointer",
    fontWeight: "600",
  },
  resultBox: {
    marginTop: "3rem",
    textAlign: "left",
    display: "inline-block",
    maxWidth: "80%",
  },
  resultTitle: {
    color: "#2c3e50",
  },
  resultArea: {
    background: "#f4f6f8",
    padding: "1rem",
    borderRadius: "10px",
    maxHeight: "400px",
    overflowY: "auto",
    whiteSpace: "pre-wrap",
    fontSize: "0.95rem",
    color: "#333",
  },
};
