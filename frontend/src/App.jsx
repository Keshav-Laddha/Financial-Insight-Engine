// App.jsx: This is your main application component. It's the root of your UI. Right now, it likely renders your Upload.jsx component. 
// You'll modify this later to add navigation, routes, and other pages (like the dashboard).
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import UploadedFilesPage from "./pages/UploadedFilesPage";
import SummaryPage from "./pages/SummaryPage";


export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/files" element={<UploadedFilesPage />} />
        <Route path="/summary" element={<SummaryPage />} />
      </Routes>
    </Layout>
  );
}
