import { useState } from "react";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");

  const handleUpload = async () => {
    if (!file) return alert("Please select a PDF file first");
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/parse-file", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setText(data.text || "No text returned from backend");
    } catch (err) {
      alert("Error fetching data. Check backend or network.");
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h1>📄 Financial Document Analyzer</h1>
      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleUpload} style={{ marginLeft: "1rem" }}>
        {loading ? "Uploading..." : "Upload & Analyze"}
      </button>
      <div style={{ marginTop: "2rem", textAlign: "left" }}>
        <h3>Extracted Text:</h3>
        <pre
          style={{
            background: "#f5f5f5",
            padding: "1rem",
            borderRadius: "8px",
            maxHeight: "400px",
            overflowY: "auto",
          }}
        >
          {text}
        </pre>
      </div>
    </div>
  );
}
