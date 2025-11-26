// import { useState, useEffect, useMemo } from "react";
// import { useSearchParams } from "react-router-dom";
// import {
//   BarChart,
//   Bar,
//   AreaChart,
//   Area,
//   XAxis,
//   YAxis,
//   Tooltip,
//   CartesianGrid,
//   ResponsiveContainer,
// } from "recharts";
// import { api, API_BASE_URL } from "../utils/api";
// import {
//   transformAnalysisData,
//   prepareTrendDataForChart,
//   formatLargeNumber,
// } from "../utils/dataTransform";
// import LineChartComponent from "../components/charts/LineChartComponent";
// import PieChartComponent from "../components/charts/PieChartComponent";
// import ComparisonChart from "../components/charts/ComparisonChart";

// const COMPANY_STORAGE_KEY = "latestCompanyName";

// export default function DashboardPage() {
//   const [searchParams] = useSearchParams();
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [analysisData, setAnalysisData] = useState(null);
//   const [selectedFileId, setSelectedFileId] = useState(null);
//   const [files, setFiles] = useState([]);
//   const [news, setNews] = useState([]);
//   const [newsLoading, setNewsLoading] = useState(false);
//   const [newsError, setNewsError] = useState(null);
//   const [currentCompany, setCurrentCompany] = useState(
//     () => localStorage.getItem(COMPANY_STORAGE_KEY) || ""
//   );

//   // ========== SAFETY HELPERS ==========
//   const safeNumber = (v) =>
//     typeof v === "number" && !Number.isNaN(v) && Number.isFinite(v);

//   const shortenLabel = (label, max = 14) =>
//     typeof label === "string" && label.length > max
//       ? `${label.slice(0, max)}…`
//       : label;

//   const formatKpiLabel = (key) => key.replace(/_/g, " ").toUpperCase();

//   // ========== LOAD FILE LIST ==========
//   useEffect(() => {
//     loadFiles();
//   }, []);

//   const loadFiles = async () => {
//     try {
//       const fileList = await api.getFiles();
//       setFiles(fileList);

//       const fileIdFromUrl = searchParams.get("fileId");
//       if (fileList.length > 0) {
//         setSelectedFileId(fileIdFromUrl || fileList[0].id);
//       } else {
//         setLoading(false);
//       }
//     } catch (err) {
//       console.error("Failed to load files:", err);
//       setError("Failed to load files. Please upload a file first.");
//       setLoading(false);
//     }
//   };

//   // ========== SELECT FILE BASED ON URL ==========
//   useEffect(() => {
//     const fileIdFromUrl = searchParams.get("fileId");
//     if (fileIdFromUrl) {
//       setSelectedFileId(fileIdFromUrl);
//     }
//   }, [searchParams]);

//   // ========== LOAD ANALYSIS FOR SELECTED FILE ==========
//   useEffect(() => {
//     if (selectedFileId) {
//       loadAnalysisData(selectedFileId);
//     }
//   }, [selectedFileId]);

//   const loadAnalysisData = async (fileId) => {
//     setLoading(true);
//     setError(null);

//     try {
//       const rawData = await api.analyzeFile(fileId);
//       const transformed = transformAnalysisData(rawData);
//       setAnalysisData(transformed);
//       if (transformed?.company_name) {
//         setCurrentCompany(transformed.company_name);
//         localStorage.setItem(COMPANY_STORAGE_KEY, transformed.company_name);
//       }
//     } catch (err) {
//       console.error("Failed to load analysis:", err);
//       setError(err.message || "Failed to load analysis data");
//       setAnalysisData(null);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const revenueTrend = useMemo(() => {
//     if (!analysisData?.pnl_periods) return [];
//     return analysisData.pnl_periods
//       .filter(p => safeNumber(p.revenue))
//       .map(p => ({
//         period: p.period,
//         revenue: p.revenue,
//       }));
//   }, [analysisData]);

//   const profitTrend = useMemo(() => {
//     if (!analysisData?.pnl_periods) return [];
//     return analysisData.pnl_periods
//       .filter(p => safeNumber(p.net_profit))
//       .map(p => ({
//         period: p.period,
//         net_profit: p.net_profit,
//       }));
//   }, [analysisData]);

//   const assetBreakdown = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];

//     return analysisData.balance_sheet
//       .filter(row => row.section === "assets" && safeNumber(row.value))
//       .slice(0, 6)  // top 6 components
//       .map(row => ({
//         name: row.label,
//         value: row.value
//       }));
//   }, [analysisData]);

//   const liabilityBreakdown = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];

//     return analysisData.balance_sheet
//       .filter(row => row.section === "liabilities" && safeNumber(row.value))
//       .slice(0, 6)
//       .map(row => ({
//         name: row.label,
//         value: row.value
//       }));
//   }, [analysisData]);

//   const ratioBars = useMemo(() => {
//     const ratios = analysisData?.kpis?.ratios || {};
//     return Object.entries(ratios)
//       .filter(([_, v]) => safeNumber(v))
//       .map(([k, v]) => ({
//         name: k.replace(/_/g, " ").toUpperCase(),
//         value: Number(v.toFixed(4))
//       }));
//   }, [analysisData]);


//   // ========== PREPARE CHART DATA ==========
//   const trendData = useMemo(() => {
//     if (!analysisData?.trends) return [];
//     return prepareTrendDataForChart(analysisData.trends).filter((d) =>
//       safeNumber(d.revenue)
//     );
//   }, [analysisData]);

//   // const numericKpis = useMemo(() => {
//   //   if (!analysisData?.kpis) return [];
//   //   return Object.entries(analysisData.kpis || {}).filter(
//   //     ([, value]) => safeNumber(value)
//   //   );
//   // }, [analysisData]);

//   const numericKpis = useMemo(() => {
//     if (!analysisData?.kpis) return [];

//     // flatten KPIs + ratios
//     const merged = {
//       ...analysisData.kpis,
//       ...(analysisData.kpis.ratios || {})
//     };

//     return Object.entries(merged).filter(
//       ([, value]) => safeNumber(value)
//     );
//   }, [analysisData]);


//   const isFinancialMetric = (key, value) => {
//     const lower = key.toLowerCase();
//     const keywords = [
//       "revenue",
//       "income",
//       "profit",
//       "asset",
//       "liabil",
//       "equity",
//       "cash",
//       "capital",
//       "expense",
//       "turnover",
//       "total",
//     ];
//     return (
//       keywords.some((k) => lower.includes(k)) ||
//       Math.abs(value) >= 1e6 ||
//       key.includes("total")
//     );
//   };

//   const financialKpiData = useMemo(
//     () =>
//       numericKpis
//         .filter(([key, value]) => isFinancialMetric(key, value))
//         .map(([key, value]) => ({ name: formatKpiLabel(key), value })),
//     [numericKpis]
//   );

//   const ratioKpiData = useMemo(
//     () =>
//       numericKpis
//         .filter(([key, value]) => !isFinancialMetric(key, value))
//         .map(([key, value]) => ({
//           name: formatKpiLabel(key),
//           value,
//           unit: key.includes("_pct") ? "%" : "",
//         })),
//     [numericKpis]
//   );

//   const safeBalanceSheet = useMemo(() => {
//     return (analysisData?.balance_sheet || []).filter((item) =>
//       safeNumber(item?.value)
//     );
//   }, [analysisData]);

//   const safePnL = useMemo(() => {
//     if (!analysisData?.pnl) return {};
//     return Object.fromEntries(
//       Object.entries(analysisData.pnl).filter(([_, v]) => safeNumber(v))
//     );
//   }, [analysisData]);

//   const safeCashFlow = useMemo(() => {
//     if (!analysisData?.cash_flow) return {};
//     return Object.fromEntries(
//       Object.entries(analysisData.cash_flow).filter(([_, v]) => safeNumber(v))
//     );
//   }, [analysisData]);

//   const hasVisualizations =
//     trendData.length > 0 ||
//     financialKpiData.length > 0 ||
//     ratioKpiData.length > 0 ||
//     safeBalanceSheet.length > 0 ||
//     Object.keys(safePnL).length > 0 ||
//     Object.keys(safeCashFlow).length > 0 ||
//     news.length > 0;

//   // ========== FETCH NEWS WHEN COMPANY CHANGES ==========
//   useEffect(() => {
//     const nameFromStorage = localStorage.getItem(COMPANY_STORAGE_KEY) || "";
//     if (!currentCompany && nameFromStorage) {
//       setCurrentCompany(nameFromStorage);
//     }
//   }, [currentCompany]);

//   useEffect(() => {
//     const trimmed = currentCompany?.trim();
//     if (!trimmed) {
//       setNews([]);
//       setNewsError(null);
//       setNewsLoading(false);
//       return;
//     }

//     let cancelled = false;

//     const fetchNews = async () => {
//       setNewsLoading(true);
//       setNewsError(null);

//       try {
//         const response = await fetch(
//           `${API_BASE_URL}/news/${encodeURIComponent(trimmed)}`
//         );
//         let payload = null;
//         try {
//           payload = await response.json();
//         } catch {
//           payload = null;
//         }

//         if (!response.ok) {
//           const message =
//             (payload && (payload.detail || payload.message)) ||
//             "Unable to fetch news right now.";
//           throw new Error(message);
//         }

//         const articles = Array.isArray(payload)
//           ? payload
//           : payload?.articles || [];

//         if (!cancelled) {
//           setNews(articles);
//         }
//       } catch (err) {
//         if (!cancelled) {
//           setNews([]);
//           setNewsError(err.message || "Unable to fetch news right now.");
//         }
//       } finally {
//         if (!cancelled) {
//           setNewsLoading(false);
//         }
//       }
//     };

//     fetchNews();

//     return () => {
//       cancelled = true;
//     };
//   }, [currentCompany]);

//   // ========== RENDER STATES ==========
//   if (loading && !analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//           <p className="muted">Loading financial insights...</p>
//         </div>
//         <div className="card">
//           <div className="loading-spinner">Loading...</div>
//         </div>
//       </div>
//     );
//   }

//   if (error && !analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//         </div>
//         <div className="card">
//           <div className="alert alert-error">{error}</div>
//           {files.length === 0 && <p>Please upload a file first.</p>}
//         </div>
//       </div>
//     );
//   }

//   if (!analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//         </div>
//         <div className="card">No analysis data available.</div>
//       </div>
//     );
//   }

//   // ========== MAIN DASHBOARD UI ==========
//   return (
//     <div className="page">
//       <div className="page-header">
//         <h2>Insights Dashboard</h2>
//         <p className="muted">Key financial metrics and trends</p>

//         {files.length > 0 && (
//           <select
//             className="file-selector"
//             value={selectedFileId || ""}
//             onChange={(e) => setSelectedFileId(e.target.value)}
//             style={{
//               marginTop: "12px",
//               padding: "8px 12px",
//               borderRadius: "8px",
//               border: "1px solid #cbd5e1",
//             }}
//           >
//             {files.map((file) => (
//               <option key={file.id} value={file.id}>
//                 {file.name}
//               </option>
//             ))}
//           </select>
//         )}
//       </div>

//       {/* KPI Cards
//       {numericKpis.length > 0 && (
//         <div className="kpi-cards-grid">
//           {numericKpis.map(([key, value]) => (
//             <div key={key} className="kpi-card">
//               <div className="kpi-card-label">{key.replace(/_/g, " ")}</div>
//               <div className="kpi-card-value">
//                 {key.includes("_pct") || key.includes("ratio")
//                   ? `${value.toFixed(2)}${key.includes("_pct") ? "%" : ""}`
//                   : formatLargeNumber(value)}
//               </div>
//             </div>
//           ))}
//         </div>
//       )} */}

//       {/* === IMPORTANT KPIs SECTION === */}
//       {analysisData?.kpis && (
//         <div style={{ marginBottom: "32px" }}>
//           <h3 style={{ marginBottom: "12px" }}>Important KPIs</h3>

//           <div className="kpi-cards-grid">
//             {Object.entries(analysisData.kpis)
//               .filter(([k, v]) =>
//                 ["total_assets", "total_equity", "total_liabilities", "revenue", "net_profit", "net_cash_flow"]
//                   .includes(k) && safeNumber(v)
//               )
//               .map(([key, value]) => (
//                 <div key={key} className="kpi-card">
//                   <div className="kpi-card-label">{formatKpiLabel(key)}</div>
//                   <div className="kpi-card-value">{formatLargeNumber(value)}</div>
//                 </div>
//               ))}
//           </div>
//         </div>
//       )}

//       {/* === IMPORTANT RATIOS SECTION === */}
//       {analysisData?.kpis?.ratios && (
//         <div style={{ marginBottom: "32px" }}>
//           <h3 style={{ marginBottom: "12px" }}>Important Ratios</h3>

//           <div className="kpi-cards-grid">
//             {Object.entries(analysisData.kpis.ratios)
//               .filter(([_, v]) => safeNumber(v))
//               .map(([key, value]) => (
//                 <div key={key} className="kpi-card">
//                   <div className="kpi-card-label">{formatKpiLabel(key)}</div>
//                   <div className="kpi-card-value">{value.toFixed(3)}</div>
//                 </div>
//               ))}
//           </div>
//         </div>
//       )}

//       {/* Trend Chart */}
//       {trendData.length > 0 && (
//         <div className="card">
//           <h3>Revenue Trends</h3>
//           <div style={{ width: "100%", height: 300, marginTop: 20 }}>
//             <ResponsiveContainer>
//               <AreaChart data={trendData}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis
//                   dataKey="period"
//                   tickFormatter={(v) => shortenLabel(v, 18)}
//                 />
//                 <YAxis tickFormatter={(v) => formatLargeNumber(v)} />
//                 <Tooltip formatter={(v) => formatLargeNumber(v)} />
//                 <Area
//                   type="monotone"
//                   dataKey="revenue"
//                   stroke="#1976d2"
//                   fill="#1976d2"
//                   fillOpacity={0.6}
//                 />
//               </AreaChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* Financial KPI Bar Chart */}
//       {financialKpiData.length > 0 && (
//         <div className="card">
//           <h3>Financial KPIs</h3>
//           <div style={{ width: "100%", height: 320, marginTop: 20 }}>
//             <ResponsiveContainer>
//               <BarChart data={financialKpiData}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis
//                   dataKey="name"
//                   tickFormatter={(v) => shortenLabel(v, 16)}
//                 />
//                 <YAxis tickFormatter={(v) => formatLargeNumber(v)} />
//                 <Tooltip formatter={(v) => formatLargeNumber(v)} />
//                 <Bar dataKey="value" fill="#1976d2" />
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* Ratio KPI Chart */}
//       {ratioKpiData.length > 0 && (
//         <div className="card">
//           <h3>Ratio & Efficiency KPIs</h3>
//           <div style={{ width: "100%", height: ratioKpiData.length * 45 }}>
//             <ResponsiveContainer>
//               <BarChart data={ratioKpiData} layout="vertical">
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis
//                   type="number"
//                   tickFormatter={(v) => Number(v).toFixed(2)}
//                 />
//                 <YAxis type="category" dataKey="name" width={180} />
//                 <Tooltip />
//                 <Bar dataKey="value" fill="#f97316" />
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {revenueTrend.length > 1 && (
//         <LineChartComponent
//           title="Revenue Trend"
//           color="#1976d2"
//           data={revenueTrend}
//           dataKey="revenue"
//         />
//       )}

//       {profitTrend.length > 1 && (
//         <LineChartComponent
//           title="Net Profit Trend"
//           color="#008000"
//           data={profitTrend}
//           dataKey="net_profit"
//         />
//       )}

//       {assetBreakdown.length > 2 && (
//         <PieChartComponent
//           title="Asset Breakdown"
//           data={assetBreakdown}
//         />
//       )}

//       {liabilityBreakdown.length > 2 && (
//         <PieChartComponent
//           title="Liability Breakdown"
//           data={liabilityBreakdown}
//         />
//       )}

//       {ratioBars.length > 0 && (
//         <div className="card">
//           <h3>Financial Ratios</h3>
//           <div style={{ width: "100%", height: ratioBars.length * 45 }}>
//             <ResponsiveContainer>
//               <BarChart data={ratioBars} layout="vertical">
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis type="number" tickFormatter={(v) => v.toFixed(3)} />
//                 <YAxis type="category" dataKey="name" width={180} />
//                 <Tooltip />
//                 <Bar dataKey="value" fill="#9c27b0" />
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}



//       {/* Company News */}
//       {currentCompany && (
//         <div className="card">
//           <div className="news-header">
//             <div>
//               <h3>Latest news on {currentCompany}</h3>
//               <p className="muted">Stay on top of recent developments.</p>
//             </div>
//             {newsLoading && <span className="muted">Fetching news…</span>}
//           </div>

//           {newsError && (
//             <div className="alert alert-warning" style={{ marginTop: 12 }}>
//               {newsError}
//             </div>
//           )}

//           {!newsLoading && !newsError && news.length === 0 && (
//             <p className="muted" style={{ marginTop: 12 }}>
//               No recent news articles available.
//             </p>
//           )}

//           {news.length > 0 && (
//             <div className="news-grid">
//               {news.map((article, idx) => (
//                 <article key={article.url || idx} className="news-card">
//                   {article.image ? (
//                     <div
//                       className="news-img"
//                       style={{ backgroundImage: `url(${article.image})` }}
//                     />
//                   ) : (
//                     <div className="news-img news-img--placeholder">
//                       No image
//                     </div>
//                   )}
//                   <div className="news-body">
//                     <h4 className="news-title">{article.title}</h4>
//                     <p className="news-desc">
//                       {article.description || "No description available."}
//                     </p>
//                     {article.url && (
//                       <a
//                         className="news-btn"
//                         href={article.url}
//                         target="_blank"
//                         rel="noopener noreferrer"
//                       >
//                         Read More →
//                       </a>
//                     )}
//                   </div>
//                 </article>
//               ))}
//             </div>
//           )}
//         </div>
//       )}

//       {/* Balance sheet pie */}
//       {safeBalanceSheet.length > 0 && (
//         <PieChartComponent
//           title="Balance Sheet Distribution"
//           data={safeBalanceSheet.slice(0, 6)}
//         />
//       )}

//       {/* P&L Comparison */}
//       {Object.keys(safePnL).length > 0 && (
//         <ComparisonChart
//           title="Profit & Loss Overview"
//           data={[
//             {
//               name: "Financial Metrics",
//               ...safePnL,
//             },
//           ]}
//           dataKeys={Object.keys(safePnL)}
//         />
//       )}

//       {/* Balance Sheet Line Graph */}
//       {safeBalanceSheet.length > 0 && (
//         <LineChartComponent
//           title="Balance Sheet Items Trend"
//           color="#66bb6a"
//           data={safeBalanceSheet.slice(0, 10).map((item, idx) => ({
//             period: item.name || `Item ${idx + 1}`,
//             value: item.value,
//           }))}
//           dataKey="value"
//         />
//       )}

//       {/* Raw Data (fallback) */}
//       {!hasVisualizations && (
//         <div className="card">
//           <h3>Analysis Data Available</h3>
//           <p className="muted">
//             No charts could be drawn — dataset structure may not match expected format.
//           </p>

//           <details>
//             <summary>View raw analysis JSON</summary>
//             <pre className="result-json">
//               {JSON.stringify(analysisData, null, 2)}
//             </pre>
//           </details>
//         </div>
//       )}
//     </div>
//   );
// }






// import { useState, useEffect, useMemo } from "react";
// import { useSearchParams } from "react-router-dom";
// import {
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   Tooltip,
//   CartesianGrid,
//   ResponsiveContainer,
// } from "recharts";
// import { api, API_BASE_URL } from "../utils/api";
// import { transformAnalysisData, formatLargeNumber } from "../utils/dataTransform";
// import PieChartComponent from "../components/charts/PieChartComponent";

// const COMPANY_STORAGE_KEY = "latestCompanyName";

// export default function DashboardPage() {
//   const [searchParams] = useSearchParams();
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [analysisData, setAnalysisData] = useState(null);
//   const [selectedFileId, setSelectedFileId] = useState(null);
//   const [files, setFiles] = useState([]);
//   const [news, setNews] = useState([]);
//   const [newsLoading, setNewsLoading] = useState(false);
//   const [newsError, setNewsError] = useState(null);
//   const [currentCompany, setCurrentCompany] = useState(
//     () => localStorage.getItem(COMPANY_STORAGE_KEY) || ""
//   );

//   // Helper
//   const safeNum = (v) =>
//     typeof v === "number" && !isNaN(v) && isFinite(v);

//   const formatLabel = (key) => key.replace(/_/g, " ").toUpperCase();

//   // Load files
//   useEffect(() => {
//     loadFiles();
//   }, []);

//   const loadFiles = async () => {
//     try {
//       const fileList = await api.getFiles();
//       setFiles(fileList);

//       const idFromUrl = searchParams.get("fileId");
//       setSelectedFileId(idFromUrl || (fileList[0]?.id || null));
//     } catch (err) {
//       setError("Failed to load files.");
//       setLoading(false);
//     }
//   };

//   // Load analysis
//   useEffect(() => {
//     if (selectedFileId) loadAnalysisData(selectedFileId);
//   }, [selectedFileId]);

//   const loadAnalysisData = async (fileId) => {
//     setLoading(true);
//     try {
//       const raw = await api.analyzeFile(fileId);
//       const parsed = transformAnalysisData(raw);
//       setAnalysisData(parsed);

//       if (parsed?.company_name) {
//         setCurrentCompany(parsed.company_name);
//         localStorage.setItem(COMPANY_STORAGE_KEY, parsed.company_name);
//       }
//     } catch (err) {
//       setError("Failed to load analysis.");
//       setAnalysisData(null);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // KPI Lists
//   const kpis = analysisData?.kpis || {};
//   const ratios = kpis?.ratios || {};

//   const importantKpis = [
//     "total_assets",
//     "total_equity",
//     "total_liabilities",
//     "revenue",
//     "net_profit",
//     "net_cash_flow",
//   ];

//   const kpiList = importantKpis
//     .filter((k) => safeNum(kpis[k]))
//     .map((k) => ({ key: k, value: kpis[k] }));

//   const ratioList = Object.entries(ratios)
//     .filter(([_, v]) => safeNum(v))
//     .map(([k, v]) => ({ key: k, value: v }));

//   // Financial KPI Bar Chart Data
//   const financialChart = kpiList.map((item) => ({
//     name: formatLabel(item.key),
//     value: item.value,
//   }));

//   // Asset breakdown pie
//   const assetPie = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];
//     return analysisData.balance_sheet
//       .filter((r) => r.section === "assets" && safeNum(r.value))
//       .slice(0, 6)
//       .map((r) => ({ name: r.label, value: r.value }));
//   }, [analysisData]);

//   // Liability breakdown pie
//   const liabilityPie = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];
//     return analysisData.balance_sheet
//       .filter((r) => r.section === "liabilities" && safeNum(r.value))
//       .slice(0, 6)
//       .map((r) => ({ name: r.label, value: r.value }));
//   }, [analysisData]);

//   // Load company news
//   useEffect(() => {
//     const name = currentCompany?.trim();
//     if (!name) return;

//     let cancelled = false;
//     const getNews = async () => {
//       setNewsLoading(true);
//       try {
//         const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(name)}`);
//         const data = await res.json();
//         if (!cancelled) setNews(Array.isArray(data) ? data : data.articles || []);
//       } catch {
//         if (!cancelled) setNewsError("Unable to fetch news.");
//       } finally {
//         if (!cancelled) setNewsLoading(false);
//       }
//     };
//     getNews();

//     return () => (cancelled = true);
//   }, [currentCompany]);

//   // Render states
//   if (loading && !analysisData) return <div className="page">Loading…</div>;
//   if (error && !analysisData) return <div className="page">{error}</div>;

//   // UI Start
//   return (
//     <div className="page">
//       <div className="page-header">
//         <h2>Insights Dashboard</h2>
//         <p className="muted">Key financial metrics and insights</p>

//         {files.length > 0 && (
//           <select
//             className="file-selector"
//             value={selectedFileId}
//             onChange={(e) => setSelectedFileId(e.target.value)}
//           >
//             {files.map((f) => (
//               <option key={f.id} value={f.id}>
//                 {f.name}
//               </option>
//             ))}
//           </select>
//         )}
//       </div>

//       {/* KPIs */}
//       {kpiList.length > 0 && (
//         <div>
//           <h3>Important KPIs</h3>
//           <div className="kpi-cards-grid">
//             {kpiList.map(({ key, value }) => (
//               <div key={key} className="kpi-card">
//                 <div className="kpi-card-label">{formatLabel(key)}</div>
//                 <div className="kpi-card-value">{formatLargeNumber(value)}</div>
//               </div>
//             ))}
//           </div>
//         </div>
//       )}

//       {/* Ratios */}
//       {ratioList.length > 0 && (
//         <div>
//           <h3>Important Ratios</h3>
//           <div className="kpi-cards-grid">
//             {ratioList.map(({ key, value }) => (
//               <div key={key} className="kpi-card">
//                 <div className="kpi-card-label">{formatLabel(key)}</div>
//                 <div className="kpi-card-value">{value.toFixed(3)}</div>
//               </div>
//             ))}
//           </div>
//         </div>
//       )}

//       {/* Financial KPI Bar Chart */}
//       {financialChart.length > 0 && (
//         <div className="card">
//           <h3>Financial KPI Overview</h3>
//           <div style={{ width: "100%", height: 320 }}>
//             <ResponsiveContainer>
//               <BarChart data={financialChart}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis dataKey="name" />
//                 <YAxis tickFormatter={formatLargeNumber} />
//                 <Tooltip formatter={formatLargeNumber} />
//                 <Bar dataKey="value" fill="#1976d2" />
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* Asset Breakdown */}
//       {assetPie.length > 0 && (
//         <PieChartComponent title="Asset Breakdown" data={assetPie} />
//       )}

//       {/* Liability Breakdown */}
//       {liabilityPie.length > 0 && (
//         <PieChartComponent title="Liability Breakdown" data={liabilityPie} />
//       )}

//       {/* News */}
//       {currentCompany && (
//         <div className="card">
//           <h3>Latest News</h3>
//           {newsError && <p className="alert alert-warning">{newsError}</p>}
//           {!newsLoading && news.length === 0 && <p>No recent news available.</p>}
//           <div className="news-grid">
//             {news.map((n, idx) => (
//               <article className="news-card" key={idx}>
//                 <div
//                   className="news-img"
//                   style={{ backgroundImage: `url(${n.image || ""})` }}
//                 />
//                 <div className="news-body">
//                   <h4>{n.title}</h4>
//                   <p>{n.description}</p>
//                   <a href={n.url} target="_blank" rel="noopener noreferrer">
//                     Read More →
//                   </a>
//                 </div>
//               </article>
//             ))}
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }





// // DashboardPage.jsx
// import { useState, useEffect, useMemo } from "react";
// import { useSearchParams } from "react-router-dom";
// import {
//   BarChart,
//   Bar,
//   AreaChart,
//   Area,
//   XAxis,
//   YAxis,
//   Tooltip,
//   CartesianGrid,
//   ResponsiveContainer,
//   Line,
//   Legend,
// } from "recharts";
// import { api, API_BASE_URL } from "../utils/api";
// import {
//   transformAnalysisData,
//   formatLargeNumber,
// } from "../utils/dataTransform";
// import LineChartComponent from "../components/charts/LineChartComponent";
// import PieChartComponent from "../components/charts/PieChartComponent";
// import ComparisonChart from "../components/charts/ComparisonChart";

// const COMPANY_STORAGE_KEY = "latestCompanyName";

// export default function DashboardPage() {
//   const [searchParams] = useSearchParams();
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [analysisData, setAnalysisData] = useState(null);
//   const [selectedFileId, setSelectedFileId] = useState(null);
//   const [files, setFiles] = useState([]);
//   const [news, setNews] = useState([]);
//   const [newsLoading, setNewsLoading] = useState(false);
//   const [newsError, setNewsError] = useState(null);
//   const [currentCompany, setCurrentCompany] = useState(
//     () => localStorage.getItem(COMPANY_STORAGE_KEY) || ""
//   );

//   // ========== HELPERS ==========
//   const safeNumber = (v) =>
//     typeof v === "number" && !Number.isNaN(v) && Number.isFinite(v);

//   const shortenLabel = (label, max = 14) =>
//     typeof label === "string" && label.length > max
//       ? `${label.slice(0, max)}…`
//       : label;

//   const formatKpiLabel = (key) => key.replace(/_/g, " ").toUpperCase();

//   // Given row.values like {col_1: x, col_2: y, ...}
//   // return object {2025: valOrNull, 2024: ..., 2023: ...} or null if none found
//   const extractLastThreeYearsFromValues = (valuesObj = {}) => {
//     if (!valuesObj || typeof valuesObj !== "object") return null;
//     const keys = Object.keys(valuesObj).map((k) => k.toLowerCase());
//     // decide mapping per your confirmation
//     // if has col_5 => 5 cols mapping
//     if (keys.includes("col_5")) {
//       // col_3 -> 2025, col_4 -> 2024, col_5 -> 2023
//       return {
//         2025: safeNumber(valuesObj["col_3"]) ? valuesObj["col_3"] : null,
//         2024: safeNumber(valuesObj["col_4"]) ? valuesObj["col_4"] : null,
//         2023: safeNumber(valuesObj["col_5"]) ? valuesObj["col_5"] : null,
//       };
//     }
//     // else if has col_4 => 4 cols mapping
//     if (keys.includes("col_4")) {
//       // col_2 -> 2025, col_3 -> 2024, col_4 -> 2023
//       return {
//         2025: safeNumber(valuesObj["col_2"]) ? valuesObj["col_2"] : null,
//         2024: safeNumber(valuesObj["col_3"]) ? valuesObj["col_3"] : null,
//         2023: safeNumber(valuesObj["col_4"]) ? valuesObj["col_4"] : null,
//       };
//     }
//     // unknown mapping - try to fallback to last three columns in insertion order
//     const presentKeys = Object.keys(valuesObj);
//     if (presentKeys.length >= 3) {
//       const last3 = presentKeys.slice(-3);
//       // assume last3[0] -> 2025, last3[1] -> 2024, last3[2] -> 2023
//       return {
//         2025: safeNumber(valuesObj[last3[0]]) ? valuesObj[last3[0]] : null,
//         2024: safeNumber(valuesObj[last3[1]]) ? valuesObj[last3[1]] : null,
//         2023: safeNumber(valuesObj[last3[2]]) ? valuesObj[last3[2]] : null,
//       };
//     }
//     return null;
//   };

//   // try to find a row label in a section (balance_sheet / pnl / cash_flow)
//   const findRowByKeywords = (sectionRows = [], keywords = []) => {
//     if (!Array.isArray(sectionRows)) return null;
//     const lowKeywords = keywords.map((k) => k.toLowerCase());
//     for (const row of sectionRows) {
//       const lbl = (row.label || "").toLowerCase();
//       if (!lbl) continue;
//       if (lowKeywords.some((k) => lbl.includes(k))) return row;
//     }
//     return null;
//   };

//   // ========== LOAD FILE LIST ==========
//   useEffect(() => {
//     loadFiles();
//   }, []);

//   const loadFiles = async () => {
//     try {
//       const fileList = await api.getFiles();
//       setFiles(fileList);

//       const fileIdFromUrl = searchParams.get("fileId");
//       if (fileList.length > 0) {
//         setSelectedFileId(fileIdFromUrl || fileList[0].id);
//       } else {
//         setLoading(false);
//       }
//     } catch (err) {
//       console.error("Failed to load files:", err);
//       setError("Failed to load files. Please upload a file first.");
//       setLoading(false);
//     }
//   };

//   // ========== SELECT FILE FROM URL ==========
//   useEffect(() => {
//     const fileIdFromUrl = searchParams.get("fileId");
//     if (fileIdFromUrl) {
//       setSelectedFileId(fileIdFromUrl);
//     }
//   }, [searchParams]);

//   // ========== LOAD ANALYSIS FOR SELECTED FILE ==========
//   useEffect(() => {
//     if (selectedFileId) {
//       loadAnalysisData(selectedFileId);
//     }
//   }, [selectedFileId]);

//   const loadAnalysisData = async (fileId) => {
//     setLoading(true);
//     setError(null);

//     try {
//       const rawData = await api.analyzeFile(fileId);
//       const transformed = transformAnalysisData(rawData);
//       setAnalysisData(transformed);
//       if (transformed?.company_name) {
//         setCurrentCompany(transformed.company_name);
//         localStorage.setItem(COMPANY_STORAGE_KEY, transformed.company_name);
//       }
//     } catch (err) {
//       console.error("Failed to load analysis:", err);
//       setError(err.message || "Failed to load analysis data");
//       setAnalysisData(null);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // ========== BUILD MULTI-YEAR KPI DATA ==========
//   // Important KPIs we want multi-year for
//   const IMPORTANT_KPIS = [
//     { key: "total_assets", label: "Total Assets", bsKeywords: ["total assets"] },
//     { key: "total_equity", label: "Total Equity", bsKeywords: ["total equity", "total shareholders", "shareholders funds"] },
//     { key: "total_liabilities", label: "Total Liabilities", bsKeywords: ["total liabilities", "total liabilities and equity"] },
//     { key: "revenue", label: "Revenue", pnlKeywords: ["total income", "total revenue", "revenue", "sales"] },
//     { key: "net_profit", label: "Net Profit", pnlKeywords: ["profit for the year", "profit for the period", "profit after tax", "net profit"] },
//     { key: "net_cash_flow", label: "Net Cash Flow", cfKeywords: ["net cash", "net cash flow", "net (decrease)/increase in cash", "net cash from operating"] },
//   ];

//   // produce grouped data for the grouped KPI chart.
//   const groupedKpiChart = useMemo(() => {
//     if (!analysisData) return [];
//     // years order (x-axis will be KPI name, we will create keys for each year)
//     const years = [2025, 2024, 2023];

//     // for each KPI, try to find a multi-year row in balance_sheet/pnl/cash_flow
//     const rowsBS = analysisData.balance_sheet || [];
//     const rowsPnL = analysisData.pnl_rows || analysisData.pnl || []; // sometimes pnl might be array of rows or object
//     const rowsCF = analysisData.cash_flow || [];

//     // helper to extract last-3 for a KPI
//     const extractForKpi = (kpi) => {
//       // search in balance sheet if bsKeywords provided
//       if (kpi.bsKeywords) {
//         const row = findRowByKeywords(rowsBS, kpi.bsKeywords);
//         if (row && row.values) {
//           const by = extractLastThreeYearsFromValues(row.values);
//           if (by) return by;
//         }
//       }
//       // search P&L rows
//       if (kpi.pnlKeywords) {
//         // if analysisData.pnl is object with keys containing values, we can't use multi-year. check pnl_rows array
//         if (Array.isArray(rowsPnL)) {
//           const row = findRowByKeywords(rowsPnL, kpi.pnlKeywords);
//           if (row && row.values) {
//             const by = extractLastThreeYearsFromValues(row.values);
//             if (by) return by;
//           }
//         }
//       }
//       // search cashflow
//       if (kpi.cfKeywords) {
//         const row = findRowByKeywords(rowsCF, kpi.cfKeywords);
//         if (row && row.values) {
//           const by = extractLastThreeYearsFromValues(row.values);
//           if (by) return by;
//         }
//       }
//       // fallback: maybe analysisData.kpis has a single value (latest). Put it in 2025 only.
//       const scalar = analysisData.kpis && analysisData.kpis[kpi.key];
//       if (safeNumber(scalar)) {
//         return { 2025: scalar, 2024: null, 2023: null };
//       }
//       return null;
//     };

//     // Build object shaped { name: KPI_LABEL, y2025: x, y2024: x, y2023: x }
//     const chart = [];
//     for (const kpi of IMPORTANT_KPIS) {
//       const vals = extractForKpi(kpi);
//       if (!vals) continue;
//       chart.push({
//         name: kpi.label.toUpperCase(),
//         y2025: safeNumber(vals[2025]) ? vals[2025] : null,
//         y2024: safeNumber(vals[2024]) ? vals[2024] : null,
//         y2023: safeNumber(vals[2023]) ? vals[2023] : null,
//       });
//     }
//     return chart;
//   }, [analysisData]);

//   // determine which years actually have any data (so we don't draw empty series)
//   const availableYears = useMemo(() => {
//     if (!groupedKpiChart || groupedKpiChart.length === 0) return [];
//     const years = [2025, 2024, 2023];
//     return years.filter((y) =>
//       groupedKpiChart.some((row) => safeNumber(row[`y${y}`]))
//     );
//   }, [groupedKpiChart]);

//   // compute y-domain (min,max) across groupedKpiChart and include some padding
//   const kpiValueDomain = useMemo(() => {
//     if (!groupedKpiChart || groupedKpiChart.length === 0) return null;
//     let min = Infinity;
//     let max = -Infinity;
//     for (const row of groupedKpiChart) {
//       for (const y of [2025, 2024, 2023]) {
//         const v = row[`y${y}`];
//         if (safeNumber(v)) {
//           if (v < min) min = v;
//           if (v > max) max = v;
//         }
//       }
//     }
//     if (min === Infinity || max === -Infinity) return null;
//     // padding
//     const pad = Math.max(Math.abs(max - min) * 0.12, Math.max(Math.abs(max) * 0.05, 1));
//     return [Math.floor(min - pad), Math.ceil(max + pad)];
//   }, [groupedKpiChart]);

//   // ===== revenue & net profit series (simple last-3 from pnl rows if available) =====
//   const revenueSeries = useMemo(() => {
//     if (!analysisData) return [];
//     // try find a row in pnl rows with revenue label
//     const pnlRows = analysisData.pnl_rows || analysisData.pnl || [];
//     const row = findRowByKeywords(Array.isArray(pnlRows) ? pnlRows : [], ["total revenue", "total income", "revenue", "sales"]);
//     const by = row && row.values ? extractLastThreeYearsFromValues(row.values) : null;
//     if (!by) return [];
//     // transform to array sorted by year ascending for line chart: 2023,2024,2025
//     return [
//       { year: 2023, value: safeNumber(by[2023]) ? by[2023] : null },
//       { year: 2024, value: safeNumber(by[2024]) ? by[2024] : null },
//       { year: 2025, value: safeNumber(by[2025]) ? by[2025] : null },
//     ].filter((d) => d.value !== null);
//   }, [analysisData]);

//   const netProfitSeries = useMemo(() => {
//     if (!analysisData) return [];
//     const pnlRows = analysisData.pnl_rows || analysisData.pnl || [];
//     const row = findRowByKeywords(Array.isArray(pnlRows) ? pnlRows : [], ["net profit", "profit for the year", "profit for the period", "profit after tax"]);
//     const by = row && row.values ? extractLastThreeYearsFromValues(row.values) : null;
//     if (!by) return [];
//     return [
//       { year: 2023, value: safeNumber(by[2023]) ? by[2023] : null },
//       { year: 2024, value: safeNumber(by[2024]) ? by[2024] : null },
//       { year: 2025, value: safeNumber(by[2025]) ? by[2025] : null },
//     ].filter((d) => d.value !== null);
//   }, [analysisData]);

//   // ===== asset / liability latest-year pies (use 2025 if available else fallback to single latest col) =====
//   const assetPie = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];
//     const rows = analysisData.balance_sheet.filter((r) => r.section === "assets" && safeNumber(r.value));
//     // Prefer latest column 2025 values if rows have multi-year values
//     const res = rows.map((r) => {
//       if (r.values) {
//         const by = extractLastThreeYearsFromValues(r.values);
//         if (by && safeNumber(by[2025])) {
//           return { name: r.label, value: by[2025] };
//         }
//       }
//       // fallback to scalar value field
//       if (safeNumber(r.value)) return { name: r.label, value: r.value };
//       return null;
//     }).filter(Boolean);
//     return res.slice(0, 6);
//   }, [analysisData]);

//   const liabilityPie = useMemo(() => {
//     if (!analysisData?.balance_sheet) return [];
//     const rows = analysisData.balance_sheet.filter((r) => r.section === "liabilities" && safeNumber(r.value));
//     const res = rows.map((r) => {
//       if (r.values) {
//         const by = extractLastThreeYearsFromValues(r.values);
//         if (by && safeNumber(by[2025])) {
//           return { name: r.label, value: by[2025] };
//         }
//       }
//       if (safeNumber(r.value)) return { name: r.label, value: r.value };
//       return null;
//     }).filter(Boolean);
//     return res.slice(0, 6);
//   }, [analysisData]);

//   // ===== Ratio list (latest single values) =====
//   const ratioList = useMemo(() => {
//     const ratios = (analysisData?.kpis && analysisData.kpis.ratios) || {};
//     return Object.entries(ratios)
//       .filter(([_, v]) => safeNumber(v))
//       .map(([k, v]) => ({ key: k, label: formatKpiLabel(k), value: v }));
//   }, [analysisData]);

//   // ========== NEWS ==========
//   useEffect(() => {
//     const nameFromStorage = localStorage.getItem(COMPANY_STORAGE_KEY) || "";
//     if (!currentCompany && nameFromStorage) {
//       setCurrentCompany(nameFromStorage);
//     }
//   }, [currentCompany]);

//   useEffect(() => {
//     const trimmed = currentCompany?.trim();
//     if (!trimmed) {
//       setNews([]);
//       setNewsError(null);
//       setNewsLoading(false);
//       return;
//     }

//     let cancelled = false;

//     const fetchNews = async () => {
//       setNewsLoading(true);
//       setNewsError(null);

//       try {
//         const response = await fetch(
//           `${API_BASE_URL}/news/${encodeURIComponent(trimmed)}`
//         );
//         let payload = null;
//         try {
//           payload = await response.json();
//         } catch {
//           payload = null;
//         }

//         if (!response.ok) {
//           const message =
//             (payload && (payload.detail || payload.message)) ||
//             "Unable to fetch news right now.";
//           throw new Error(message);
//         }

//         const articles = Array.isArray(payload)
//           ? payload
//           : payload?.articles || [];

//         if (!cancelled) {
//           setNews(articles);
//         }
//       } catch (err) {
//         if (!cancelled) {
//           setNews([]);
//           setNewsError(err.message || "Unable to fetch news right now.");
//         }
//       } finally {
//         if (!cancelled) {
//           setNewsLoading(false);
//         }
//       }
//     };

//     fetchNews();

//     return () => {
//       cancelled = true;
//     };
//   }, [currentCompany]);

//   // ========== RENDER STATES ==========
//   if (loading && !analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//           <p className="muted">Loading financial insights...</p>
//         </div>
//         <div className="card">
//           <div className="loading-spinner">Loading...</div>
//         </div>
//       </div>
//     );
//   }

//   if (error && !analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//         </div>
//         <div className="card">
//           <div className="alert alert-error">{error}</div>
//           {files.length === 0 && <p>Please upload a file first.</p>}
//         </div>
//       </div>
//     );
//   }

//   if (!analysisData) {
//     return (
//       <div className="page">
//         <div className="page-header">
//           <h2>Insights Dashboard</h2>
//         </div>
//         <div className="card">No analysis data available.</div>
//       </div>
//     );
//   }

//   // ===== Main UI =====
//   return (
//     <div className="page">
//       <div className="page-header">
//         <h2>Insights Dashboard</h2>
//         <p className="muted">Key financial metrics and trends</p>

//         {files.length > 0 && (
//           <select
//             className="file-selector"
//             value={selectedFileId || ""}
//             onChange={(e) => setSelectedFileId(e.target.value)}
//             style={{
//               marginTop: "12px",
//               padding: "8px 12px",
//               borderRadius: "8px",
//               border: "1px solid #cbd5e1",
//             }}
//           >
//             {files.map((file) => (
//               <option key={file.id} value={file.id}>
//                 {file.name}
//               </option>
//             ))}
//           </select>
//         )}
//       </div>

//       {/* Important KPIs (single value cards) */}
//       {analysisData?.kpis && (
//         <div style={{ marginBottom: "24px" }}>
//           <h3 style={{ marginBottom: "8px" }}>Important KPIs</h3>
//           <div className="kpi-cards-grid">
//             {["total_assets","total_equity","total_liabilities","revenue","net_profit","net_cash_flow"].map((k) => {
//               const v = analysisData.kpis[k];
//               if (!safeNumber(v)) return null;
//               return (
//                 <div key={k} className="kpi-card">
//                   <div className="kpi-card-label">{formatKpiLabel(k)}</div>
//                   <div className="kpi-card-value">{formatLargeNumber(v)}</div>
//                 </div>
//               );
//             })}
//           </div>
//         </div>
//       )}

//       {/* Important Ratios */}
//       {ratioList.length > 0 && (
//         <div style={{ marginBottom: "24px" }}>
//           <h3 style={{ marginBottom: "8px" }}>Important Ratios</h3>
//           <div className="kpi-cards-grid">
//             {ratioList.map((r) => (
//               <div key={r.key} className="kpi-card">
//                 <div className="kpi-card-label">{r.label}</div>
//                 <div className="kpi-card-value">{Number(r.value).toFixed(3)}</div>
//               </div>
//             ))}
//           </div>
//         </div>
//       )}

//       {/* Grouped KPI chart for last 3 years */}
//       {groupedKpiChart.length > 0 && availableYears.length > 0 && (
//         <div className="card" style={{ marginBottom: 24 }}>
//           <h3>Financial KPI Overview</h3>
//           <div style={{ width: "100%", height: 360 }}>
//             <ResponsiveContainer>
//               <BarChart data={groupedKpiChart} margin={{ top: 10, right: 30, left: 10, bottom: 60 }}>
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis dataKey="name" angle={-15} textAnchor="end" interval={0} height={60} />
//                 <YAxis
//                   tickFormatter={(v) => formatLargeNumber(v)}
//                   domain={kpiValueDomain || ["auto", "auto"]}
//                 />
//                 <Tooltip formatter={(v) => formatLargeNumber(v)} />
//                 <Legend />
//                 {/* Dynamically render bars for available years */}
//                 {availableYears.includes(2025) && <Bar dataKey="y2025" name="2025" fill="#1976d2" />}
//                 {availableYears.includes(2024) && <Bar dataKey="y2024" name="2024" fill="#4caf50" />}
//                 {availableYears.includes(2023) && <Bar dataKey="y2023" name="2023" fill="#f97316" />}
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* Revenue & Net Profit Trends (lines across the 3 years) */}
//       {revenueSeries.length > 0 && (
//         <LineChartComponent
//           title="Revenue Trend (last 3 years)"
//           color="#1976d2"
//           data={revenueSeries.map(d => ({ period: d.year.toString(), value: d.value }))}
//           dataKey="value"
//         />
//       )}
//       {netProfitSeries.length > 0 && (
//         <LineChartComponent
//           title="Net Profit Trend (last 3 years)"
//           color="#008000"
//           data={netProfitSeries.map(d => ({ period: d.year.toString(), value: d.value }))}
//           dataKey="value"
//         />
//       )}

//       {/* Asset / Liability breakdown pies */}
//       {assetPie.length > 0 && <PieChartComponent title="Asset Breakdown (latest year)" data={assetPie} />}
//       {liabilityPie.length > 0 && <PieChartComponent title="Liability Breakdown (latest year)" data={liabilityPie} />}

//       {/* Ratio bars */}
//       {ratioList.length > 0 && (
//         <div className="card" style={{ marginBottom: 24 }}>
//           <h3>Ratios (latest)</h3>
//           <div style={{ width: "100%", height: Math.min(300, ratioList.length * 50) }}>
//             <ResponsiveContainer>
//               <BarChart
//                 data={ratioList.map(r => ({ name: r.label, value: r.value }))}
//                 layout="vertical"
//                 margin={{ left: 10, right: 10 }}
//               >
//                 <CartesianGrid strokeDasharray="3 3" />
//                 <XAxis type="number" />
//                 <YAxis dataKey="name" type="category" width={200} />
//                 <Tooltip />
//                 <Bar dataKey="value" fill="#9c27b0" />
//               </BarChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* News */}
//       {currentCompany && (
//         <div className="card" style={{ marginBottom: 24 }}>
//           <div className="news-header">
//             <div>
//               <h3>Latest news on {currentCompany}</h3>
//               <p className="muted">Stay on top of recent developments.</p>
//             </div>
//             {newsLoading && <span className="muted">Fetching news…</span>}
//           </div>

//           {newsError && <div className="alert alert-warning" style={{ marginTop: 12 }}>{newsError}</div>}

//           {!newsLoading && !newsError && news.length === 0 && <p className="muted" style={{ marginTop: 12 }}>No recent news articles available.</p>}

//           {news.length > 0 && (
//             <div className="news-grid">
//               {news.map((article, idx) => (
//                 <article key={article.url || idx} className="news-card">
//                   {article.image ? (
//                     <div className="news-img" style={{ backgroundImage: `url(${article.image})` }} />
//                   ) : (
//                     <div className="news-img news-img--placeholder">No image</div>
//                   )}
//                   <div className="news-body">
//                     <h4 className="news-title">{article.title}</h4>
//                     <p className="news-desc">{article.description || "No description available."}</p>
//                     {article.url && <a className="news-btn" href={article.url} target="_blank" rel="noopener noreferrer">Read More →</a>}
//                   </div>
//                 </article>
//               ))}
//             </div>
//           )}
//         </div>
//       )}

//       {/* Raw fallback */}
//       {(!groupedKpiChart.length && !revenueSeries.length && !netProfitSeries.length && !assetPie.length && !liabilityPie.length && !ratioList.length) && (
//         <div className="card">
//           <h3>Analysis Data Available</h3>
//           <p className="muted">No charts could be drawn — dataset structure may not match expected format or values are missing.</p>
//           <details>
//             <summary>View raw analysis JSON</summary>
//             <pre className="result-json">{JSON.stringify(analysisData, null, 2)}</pre>
//           </details>
//         </div>
//       )}
//     </div>
//   );
// }


// DashboardPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { api, API_BASE_URL } from "../utils/api";
import { transformAnalysisData, formatLargeNumber } from "../utils/dataTransform";
import LineChartComponent from "../components/charts/LineChartComponent";
import PieChartComponent from "../components/charts/PieChartComponent";

const COMPANY_STORAGE_KEY = "latestCompanyName";

export default function DashboardPage() {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [files, setFiles] = useState([]);
  const [news, setNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsError, setNewsError] = useState(null);
  const [currentCompany, setCurrentCompany] = useState(
    () => localStorage.getItem(COMPANY_STORAGE_KEY) || ""
  );

  // helpers
  const safeNumber = (v) => typeof v === "number" && !Number.isNaN(v) && Number.isFinite(v);

  const formatKpiLabel = (key) => key.replace(/_/g, " ").toUpperCase();

  // Try to read periods object from 'kpi_periods' produced by parser. Accept two shapes:
  // Shape A: { "2025": v, "2024": v, "2023": v }
  // Shape B: { latest: v, prev1: v, prev2: v }
  // Return normalized { 2025: valOrNull, 2024: valOrNull, 2023: valOrNull }
  const normalizePeriods = (periodObj) => {
    if (!periodObj || typeof periodObj !== "object") return { 2025: null, 2024: null, 2023: null };

    // If keys are numeric years
    if ("2025" in periodObj || "2024" in periodObj || "2023" in periodObj) {
      return {
        2025: safeNumber(periodObj[2025]) ? periodObj[2025] : (safeNumber(periodObj["2025"]) ? periodObj["2025"] : null),
        2024: safeNumber(periodObj[2024]) ? periodObj[2024] : (safeNumber(periodObj["2024"]) ? periodObj["2024"] : null),
        2023: safeNumber(periodObj[2023]) ? periodObj[2023] : (safeNumber(periodObj["2023"]) ? periodObj["2023"] : null),
      };
    }

    // If shape is latest/prev1/prev2
    if ("latest" in periodObj || "prev1" in periodObj || "prev2" in periodObj) {
      return {
        2025: safeNumber(periodObj.latest) ? periodObj.latest : null,
        2024: safeNumber(periodObj.prev1) ? periodObj.prev1 : null,
        2023: safeNumber(periodObj.prev2) ? periodObj.prev2 : null,
      };
    }

    // Otherwise try find any numeric values in object and pick last three (best effort)
    const numericEntries = Object.entries(periodObj).filter(([k, v]) => safeNumber(v));
    if (numericEntries.length === 0) return { 2025: null, 2024: null, 2023: null };
    // choose last 3 numeric entries
    const last3 = numericEntries.slice(-3).map(([, v]) => v);
    const pad = (arr) => {
      const out = [null, null, null];
      for (let i = 0; i < arr.length; ++i) {
        out[out.length - arr.length + i] = arr[i];
      }
      return out;
    };
    const arranged = pad(last3);
    // arranged order (older..newest) -> convert to 2023,2024,2025
    return {
      2023: arranged[0],
      2024: arranged[1],
      2025: arranged[2],
    };
  };

  // Extract periods for a KPI key. We prefer analysisData.kpis[`${key}_periods`] if present.
  // If not present, we attempt to find a multi-year row in balance_sheet/pnl/cash_flow (analysisData.* rows)
  // As a last resort, fallback to scalar latest value placed at 2025 only.
  const getKpiPeriods = (key, searchConfig = {}) => {
    // searchConfig: { section: 'balance_sheet'|'pnl'|'cash_flow', keywords: [] }
    if (!analysisData) return { 2025: null, 2024: null, 2023: null };

    const kpisObj = analysisData.kpis || analysisData.important_kpis || {};
    // direct periods from parser
    const periodField = kpisObj[`${key}_periods`];
    if (periodField) {
      return normalizePeriods(periodField);
    }

    // some older flows might put important_kpis as flat fields where value is an object (we handled in parser logic),
    // but also check analysisData.balance_sheet/pnl rows
    const tryRows = (rows = [], keywords = []) => {
      if (!Array.isArray(rows)) return null;
      const lowKeywords = keywords.map((k) => k.toLowerCase());
      for (const row of rows) {
        const lbl = (row.label || "").toLowerCase();
        if (!lbl) continue;
        if (lowKeywords.some((kw) => lbl.includes(kw))) {
          if (row.values) {
            // row.values might have col_2..col_5 pattern etc — try to map using same logic as earlier
            const vals = row.values || {};
            // attempt to build {2025,2024,2023} from row.values:
            // if has col_5 => col_3->2025, col_4->2024, col_5->2023
            const keysLower = Object.keys(vals).map((k) => k.toLowerCase());
            if (keysLower.includes("col_5")) {
              return {
                2025: safeNumber(vals["col_3"]) ? vals["col_3"] : null,
                2024: safeNumber(vals["col_4"]) ? vals["col_4"] : null,
                2023: safeNumber(vals["col_5"]) ? vals["col_5"] : null,
              };
            }
            if (keysLower.includes("col_4")) {
              return {
                2025: safeNumber(vals["col_2"]) ? vals["col_2"] : null,
                2024: safeNumber(vals["col_3"]) ? vals["col_3"] : null,
                2023: safeNumber(vals["col_4"]) ? vals["col_4"] : null,
              };
            }
            // fallback: last 3 present keys
            const presentKeys = Object.keys(vals);
            const numericVals = presentKeys.filter((k) => safeNumber(vals[k]));
            if (numericVals.length >= 3) {
              const last3 = numericVals.slice(-3);
              return {
                2025: safeNumber(vals[last3[2]]) ? vals[last3[2]] : null,
                2024: safeNumber(vals[last3[1]]) ? vals[last3[1]] : null,
                2023: safeNumber(vals[last3[0]]) ? vals[last3[0]] : null,
              };
            }
          }
        }
      }
      return null;
    };

    // if a searchConfig provided, try that section
    if (searchConfig && searchConfig.section && searchConfig.keywords) {
      const rows = analysisData[searchConfig.section] || [];
      const r = tryRows(rows, searchConfig.keywords);
      if (r) return r;
    }

    // generic fallback searches
    const bsRows = analysisData.balance_sheet || [];
    const pnlRows = analysisData.pnl_rows || analysisData.pnl || [];
    const cfRows = analysisData.cash_flow || [];

    // heuristics per key
    if (key === "total_assets") {
      const r = tryRows(bsRows, ["total assets", "totalassets", "total assets and liabilities", "totalassetsandliabilities"]);
      if (r) return r;
    } else if (key === "total_equity") {
      const r = tryRows(bsRows, ["total equity", "equity attributable", "shareholders funds", "shareholdersfunds"]);
      if (r) return r;
    } else if (key === "total_liabilities") {
      const r = tryRows(bsRows, ["total liabilities", "total liabilities and equity", "total liabilities and equity"]);
      if (r) return r;
    } else if (key === "revenue") {
      const r = tryRows(Array.isArray(pnlRows) ? pnlRows : [], ["total income", "total revenue", "revenue", "sales"]);
      if (r) return r;
    } else if (key === "net_profit") {
      const r = tryRows(Array.isArray(pnlRows) ? pnlRows : [], ["profit for the year", "profit for the period", "profit after tax", "net profit"]);
      if (r) return r;
    } else if (key === "net_cash_flow") {
      const r = tryRows(cfRows, ["net cash", "net cash flow", "net (decrease)/increase in cash", "net cash from operating"]);
      if (r) return r;
    }

    // final fallback: scalar placed into 2025 only
    const scalar = kpisObj && (kpisObj[key] || (analysisData.kpis && analysisData.kpis[key]));
    if (safeNumber(scalar)) {
      return { 2025: scalar, 2024: null, 2023: null };
    }

    return { 2025: null, 2024: null, 2023: null };
  };

  // // ===== load files & analysis =====
  // useEffect(() => {
  //   loadFiles();
  // }, []);

  // const loadFiles = async () => {
  //   try {
  //     const fileList = await api.getFiles();
  //     setFiles(fileList);
  //     const idFromUrl = searchParams.get("fileId");
  //     setSelectedFileId(idFromUrl || (fileList[0]?.id || null));
  //   } catch (err) {
  //     setError("Failed to load files.");
  //     setLoading(false);
  //   }
  // };

  // useEffect(() => {
  //   if (selectedFileId) loadAnalysisData(selectedFileId);
  // }, [selectedFileId]);

  // const loadAnalysisData = async (fileId) => {
  //   setLoading(true);
  //   try {
  //     const raw = await api.analyzeFile(fileId);
  //     const parsed = transformAnalysisData(raw);
  //     setAnalysisData(parsed);
  //     if (parsed?.company_name) {
  //       setCurrentCompany(parsed.company_name);
  //       localStorage.setItem(COMPANY_STORAGE_KEY, parsed.company_name);
  //     }
  //   } catch (err) {
  //     setError("Failed to load analysis.");
  //     setAnalysisData(null);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // // fetch news
  // useEffect(() => {
  //   const name = currentCompany?.trim();
  //   if (!name) return;
  //   let cancelled = false;
  //   const getNews = async () => {
  //     setNewsLoading(true);
  //     try {
  //       const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(name)}`);
  //       const data = await res.json();
  //       if (!cancelled) setNews(Array.isArray(data) ? data : data.articles || []);
  //     } catch {
  //       if (!cancelled) setNewsError("Unable to fetch news.");
  //     } finally {
  //       if (!cancelled) setNewsLoading(false);
  //     }
  //   };
  //   getNews();
  //   return () => (cancelled = true);
  // }, [currentCompany]);

  // ===== load files & analysis =====
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const fileList = await api.getFiles();
      setFiles(fileList);
      const idFromUrl = searchParams.get("fileId");
      setSelectedFileId(idFromUrl || (fileList[0]?.id || null));
    } catch (err) {
      setError("Failed to load files.");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedFileId) loadAnalysisData(selectedFileId);
  }, [selectedFileId]);

  // ---------- new loadAnalysisData with sessionStorage caching ----------
  const loadAnalysisData = async (fileId) => {
    const cacheKey = `dashboard_${fileId}`;                    // session key
    const cached = sessionStorage.getItem(cacheKey);

    // If cached -> use it instantly and DO NOT fetch
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        setAnalysisData(parsed);
        setLoading(false);
        // update company state as well (so news can use it)
        if (parsed?.company_name) {
          setCurrentCompany(parsed.company_name);
          localStorage.setItem(COMPANY_STORAGE_KEY, parsed.company_name);
        }
        return; // no fetch
      } catch (e) {
        // if cache parse fails, fall through to fetch
        console.warn("Failed to parse cached dashboard:", e);
      }
    }

    // not cached -> fetch (first time)
    setLoading(true);
    try {
      const raw = await api.analyzeFile(fileId);
      const parsed = transformAnalysisData(raw);

      setAnalysisData(parsed);
      sessionStorage.setItem(cacheKey, JSON.stringify(parsed)); // save to session

      if (parsed?.company_name) {
        setCurrentCompany(parsed.company_name);
        localStorage.setItem(COMPANY_STORAGE_KEY, parsed.company_name);
      }
    } catch (err) {
      setError("Failed to load analysis.");
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  // fetch news (cached in sessionStorage per company)
  useEffect(() => {
    const name = currentCompany?.trim();
    if (!name) return;

    const cacheKey = `news_${name}`;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        // optional TTL - only used if you want time based invalidation
        // parsed.ts is epoch ms when cached
        // We'll accept cached if present (since upload clears caches)
        setNews(parsed.articles || []);
        setNewsLoading(false);
        return;
      } catch (e) {
        // bad cache -> fallthrough to fetch
        console.warn("news cache parse failed", e);
      }
    }

    let cancelled = false;
    const getNews = async () => {
      setNewsLoading(true);
      setNewsError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/news/${encodeURIComponent(name)}`);
        const data = await res.json();
        const articles = Array.isArray(data) ? data : data.articles || [];
        if (!cancelled) {
          setNews(articles);
          sessionStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), articles }));
        }
      } catch (err) {
        if (!cancelled) setNewsError("Unable to fetch news.");
      } finally {
        if (!cancelled) setNewsLoading(false);
      }
    };
    getNews();
    return () => { cancelled = true; };
  }, [currentCompany]);



  // ===== build KPI cards =====
  const KPI_KEYS = [
    { key: "total_assets", label: "Total Assets" },
    { key: "total_equity", label: "Total Equity" },
    { key: "total_liabilities", label: "Total Liabilities" },
    { key: "revenue", label: "Revenue" },
    { key: "net_profit", label: "Net Profit" },
    { key: "net_cash_flow", label: "Net Cash Flow" },
  ];

  // Each KPI chart data: produce [{ period: '2023', value }, { period: '2024', value }, { period: '2025', value }]
  const kpiCharts = useMemo(() => {
    if (!analysisData) return {};
    const out = {};
    for (const item of KPI_KEYS) {
      const periods = getKpiPeriods(item.key);
      // convert to array, sorted ascending by year (2023..2025) but charts prefer category order later.
      const arr = [
        { period: "2023", value: safeNumber(periods[2023]) ? periods[2023] : null },
        { period: "2024", value: safeNumber(periods[2024]) ? periods[2024] : null },
        { period: "2025", value: safeNumber(periods[2025]) ? periods[2025] : null },
      ].filter((d) => d.value !== null); // remove nulls so chart doesn't render empty bars
      out[item.key] = { label: item.label, series: arr, rawPeriods: periods };
    }
    return out;
  }, [analysisData]);

  // Ratios list (latest)
  const ratioList = useMemo(() => {
    const ratios = (analysisData?.kpis && analysisData.kpis.ratios) || (analysisData?.important_kpis && analysisData.important_kpis.ratios) || {};
    return Object.entries(ratios)
      .filter(([_, v]) => safeNumber(v))
      .map(([k, v]) => ({ key: k, label: k.replace(/_/g, " ").toUpperCase(), value: v }));
  }, [analysisData]);

  // pies (use latest periods if available else fallback to scalar)
  const assetPie = useMemo(() => {
    if (!analysisData?.balance_sheet) return [];
    const rows = analysisData.balance_sheet.filter((r) => r.section === "assets");
    return rows.map((r) => {
      if (r.values) {
        // prefer kpi_period-style values if exist preferring 2025
        const p = (() => {
          // try parser-produced period fields on row (if any)
          const keys = Object.keys(r.values || {}).map((k) => k.toLowerCase());
          if (keys.includes("col_5")) {
            return r.values["col_3"];
          }
          if (keys.includes("col_4")) {
            return r.values["col_2"];
          }
          // fallback last numeric
          const numericKeys = Object.keys(r.values).filter((k) => safeNumber(r.values[k]));
          if (numericKeys.length) return r.values[numericKeys[numericKeys.length - 1]];
          return null;
        })();
        if (safeNumber(p)) return { name: r.label, value: p };
      }
      if (safeNumber(r.value)) return { name: r.label, value: r.value };
      return null;
    }).filter(Boolean).slice(0, 6);
  }, [analysisData]);

  const liabilityPie = useMemo(() => {
    if (!analysisData?.balance_sheet) return [];
    const rows = analysisData.balance_sheet.filter((r) => r.section === "liabilities");
    return rows.map((r) => {
      if (r.values) {
        const keys = Object.keys(r.values || {}).map((k) => k.toLowerCase());
        if (keys.includes("col_5")) {
          if (safeNumber(r.values["col_3"])) return { name: r.label, value: r.values["col_3"] };
        } else if (keys.includes("col_4")) {
          if (safeNumber(r.values["col_2"])) return { name: r.label, value: r.values["col_2"] };
        } else {
          const numericKeys = Object.keys(r.values).filter((k) => safeNumber(r.values[k]));
          if (numericKeys.length) return { name: r.label, value: r.values[numericKeys[numericKeys.length - 1]] };
        }
      }
      if (safeNumber(r.value)) return { name: r.label, value: r.value };
      return null;
    }).filter(Boolean).slice(0, 6);
  }, [analysisData]);

  // === Render helpers for single KPI chart (updated with multi-color bars) ===
  const KpiChart = ({ kpiKey }) => {
    const dataObj = kpiCharts[kpiKey];
    if (!dataObj) return null;

    const fullPeriods = dataObj.rawPeriods || { 2025: null, 2024: null, 2023: null };

    // Build single-row grouped bar data
    const row = {
      name: dataObj.label,
      y2023: safeNumber(fullPeriods[2023]) ? fullPeriods[2023] : null,
      y2024: safeNumber(fullPeriods[2024]) ? fullPeriods[2024] : null,
      y2025: safeNumber(fullPeriods[2025]) ? fullPeriods[2025] : null,
    };

    if (!row.y2023 && !row.y2024 && !row.y2025) return null;

    const values = [row.y2023, row.y2024, row.y2025].filter(v => safeNumber(v));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = Math.max(Math.abs(max - min) * 0.12, Math.abs(max) * 0.05, 1);
    const domain = [Math.floor(min - pad), Math.ceil(max + pad)];

    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <h4 style={{ marginBottom: 8 }}>{dataObj.label} — Last 3 Periods</h4>
        <div style={{ width: "100%", height: 240 }}>
          <ResponsiveContainer>
            <BarChart data={[row]} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={domain} tickFormatter={(v) => formatLargeNumber(v)} />
              <Tooltip formatter={(v) => formatLargeNumber(v)} />
              <Legend />
              <Bar dataKey="y2023" name="2023" fill="#f97316" />
              <Bar dataKey="y2024" name="2024" fill="#4caf50" />
              <Bar dataKey="y2025" name="2025" fill="#1976d2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };


  // ====== RENDER STATES ======
  if (loading && !analysisData) return <div className="page">Loading…</div>;
  if (error && !analysisData) return <div className="page">{error}</div>;
  if (!analysisData) return <div className="page">No analysis data available.</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Insights Dashboard</h2>
        <p className="muted">Key financial metrics and trends</p>

        {files.length > 0 && (
          <select
            className="file-selector"
            value={selectedFileId || ""}
            onChange={(e) => setSelectedFileId(e.target.value)}
            style={{ marginTop: 12 }}
          >
            {files.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* KPI Cards (latest scalar values) */}
      {analysisData?.kpis && (
        <div style={{ marginBottom: 24 }}>
          <h3>Important KPIs (Latest- Data in ₹ Millions)</h3>
          <div className="kpi-cards-grid">
            {KPI_KEYS.map(({ key, label }) => {
              const scalar = (analysisData.kpis && analysisData.kpis[key]) || (analysisData.important_kpis && analysisData.important_kpis[key]);
              if (!safeNumber(scalar)) return null;
              return (
                <div key={key} className="kpi-card">
                  <div className="kpi-card-label">{label.toUpperCase()}</div>
                  <div className="kpi-card-value">{formatLargeNumber(scalar)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Ratios (latest) */}
      {ratioList.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3>Important Ratios</h3>
          <div className="kpi-cards-grid">
            {ratioList.map((r) => (
              <div key={r.key} className="kpi-card">
                <div className="kpi-card-label">{r.label}</div>
                <div className="kpi-card-value">{Number(r.value).toFixed(3)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Individual KPI charts (one per KPI) */}

      <h3 style={{ marginTop: 20, marginBottom: 12 }}>
        Important KPIs — Last 3 Periods (y-axis: Data in ₹ Millions)
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
          gap: "20px",
        }}
      >
        <KpiChart kpiKey="total_assets" />
        <KpiChart kpiKey="total_equity" />
        <KpiChart kpiKey="total_liabilities" />
        <KpiChart kpiKey="revenue" />
        <KpiChart kpiKey="net_profit" />
        <KpiChart kpiKey="net_cash_flow" />
      </div>

      {/* Revenue & Net Profit trend line charts (if desired) — uses periods as well */}
      {/* Convert periods to arrays for line component */}
      {(() => {
        const revenuePeriods = getKpiPeriods("revenue");
        const revenueData = [
          { period: "2023", value: safeNumber(revenuePeriods[2023]) ? revenuePeriods[2023] : null },
          { period: "2024", value: safeNumber(revenuePeriods[2024]) ? revenuePeriods[2024] : null },
          { period: "2025", value: safeNumber(revenuePeriods[2025]) ? revenuePeriods[2025] : null },
        ].filter((d) => d.value !== null);

        const profitPeriods = getKpiPeriods("net_profit");
        const profitData = [
          { period: "2023", value: safeNumber(profitPeriods[2023]) ? profitPeriods[2023] : null },
          { period: "2024", value: safeNumber(profitPeriods[2024]) ? profitPeriods[2024] : null },
          { period: "2025", value: safeNumber(profitPeriods[2025]) ? profitPeriods[2025] : null },
        ].filter((d) => d.value !== null);

        return (
          <>
            {revenueData.length > 0 && (
              <LineChartComponent
                title="Revenue Trend (last 3 years)"
                color="#1976d2"
                data={revenueData.map((d) => ({ period: d.period, value: d.value }))}
                dataKey="value"
              />
            )}
            {profitData.length > 0 && (
              <LineChartComponent
                title="Net Profit Trend (last 3 years)"
                color="#008000"
                data={profitData.map((d) => ({ period: d.period, value: d.value }))}
                dataKey="value"
              />
            )}
          </>
        );
      })()}

      {/* Asset / Liability pies */}
      {assetPie.length > 0 && <PieChartComponent title="Asset Breakdown (latest)" data={assetPie} />}
      {liabilityPie.length > 0 && <PieChartComponent title="Liability Breakdown (latest)" data={liabilityPie} />}

      {/* News */}
      {currentCompany && (
        <div className="card" style={{ marginTop: 18 }}>
          <h3>Latest news on {currentCompany}</h3>
          {newsError && <div className="alert alert-warning">{newsError}</div>}
          {newsLoading && <div className="muted">Fetching news…</div>}
          {!newsLoading && news.length === 0 && <div className="muted">No recent news available.</div>}
          {news.length > 0 && (
            <div className="news-grid" style={{ marginTop: 12 }}>
              {news.map((n, idx) => (
                <article key={n.url || idx} className="news-card">
                  <div
                    className="news-img"
                    style={{ backgroundImage: `url(${n.image || ""})` }}
                  />
                  <div className="news-body">
                    <h4>{n.title}</h4>
                    <p>{n.description}</p>
                    {n.url && <a href={n.url} target="_blank" rel="noreferrer">Read More →</a>}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Raw fallback for debugging */}
      {(!Object.keys(kpiCharts).length && !assetPie.length && !liabilityPie.length && !ratioList.length) && (
        <div className="card" style={{ marginTop: 18 }}>
          <h3>Analysis Data Available</h3>
          <p className="muted">No charts could be drawn — dataset structure may not match expected format or values are missing.</p>
          <details>
            <summary>View raw analysis JSON</summary>
            <pre className="result-json">{JSON.stringify(analysisData, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}