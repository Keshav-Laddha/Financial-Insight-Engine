import UploadComponent from "../components/UploadComponent";

export default function UploadPage() {
  return (
    <div className="page-centered">
      <h2>Upload Document</h2>
      <p className="muted">Upload PDFs, documents, or statements.</p>

      <div className="card">
        <UploadComponent />
      </div>
    </div>
  );
}
