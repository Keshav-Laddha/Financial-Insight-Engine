// Data transformation utility to convert backend format to visualization format

/**
 * Transforms backend analysis data to the format expected by visualizations
 * 
 * Backend format:
 * {
 *   "balance_sheet": [{ "item": "...", "current_period": 123 }],
 *   "pnl": { "net_profit": { "value_crore": 123, "value_rupees": 12300000000 } },
 *   "cash_flow": { "operating_cf": { "value_crore": 123, "value_rupees": 12300000000 } },
 *   "kpis": { "net_profit": 123, ... },
 *   "trends": {}
 * }
 * 
 * Expected format:
 * {
 *   "balance_sheet": [{ "name": "...", "value": 123 }],
 *   "pnl": { "net_profit": 123, ... },
 *   "cash_flow": { "operating": 123, ... },
 *   "kpis": { "net_profit": 123, ... },
 *   "trends": { "revenue_trend": { "2021": 400, ... } }
 * }
 */
export const transformAnalysisData = (rawData) => {
  if (!rawData || typeof rawData !== "object") {
    return null;
  }

  const transformed = {
    balance_sheet: [],
    pnl: {},
    cash_flow: {},
    kpis: {},
    trends: {},
  };

  // Transform balance_sheet
  if (Array.isArray(rawData.balance_sheet)) {
    transformed.balance_sheet = rawData.balance_sheet.map((item) => ({
      name: item.item || item.name || "Unknown",
      value: item.current_period || item.value || 0,
      label: item.item || item.name || "Unknown",
    }));
  }

  // Transform P&L
  if (rawData.pnl && typeof rawData.pnl === "object") {
    Object.entries(rawData.pnl).forEach(([key, value]) => {
      if (value && typeof value === "object") {
        // Handle nested structure like { "value_crore": 123, "value_rupees": 12300000000 }
        transformed.pnl[key] = value.value_rupees || value.value_crore * 10000000 || 0;
      } else {
        transformed.pnl[key] = value;
      }
    });
  }

  // Transform Cash Flow
  if (rawData.cash_flow && typeof rawData.cash_flow === "object") {
    Object.entries(rawData.cash_flow).forEach(([key, value]) => {
      // Convert keys like "operating_cf" to "operating"
      const cleanKey = key.replace(/_cf$/, "").replace(/_/g, " ");
      if (value && typeof value === "object") {
        transformed.cash_flow[cleanKey] = value.value_rupees || value.value_crore * 10000000 || 0;
      } else {
        transformed.cash_flow[cleanKey] = value;
      }
    });
  }

  // Transform KPIs (already in good format, but ensure all values are numbers)
  if (rawData.kpis && typeof rawData.kpis === "object") {
    Object.entries(rawData.kpis).forEach(([key, value]) => {
      // Skip summary strings
      if (typeof value === "string") {
        return;
      }
      transformed.kpis[key] = typeof value === "number" ? value : 0;
    });
  }

  // Transform Trends
  // If trends is empty, try to create trends from balance_sheet or other data
  if (rawData.trends && typeof rawData.trends === "object") {
    if (Object.keys(rawData.trends).length > 0) {
      transformed.trends = rawData.trends;
    } else {
      // Create a simple trend from balance sheet items if available
      const trendData = {};
      if (Array.isArray(rawData.balance_sheet) && rawData.balance_sheet.length > 0) {
        rawData.balance_sheet.forEach((item, index) => {
          const period = `Period ${index + 1}`;
          trendData[period] = item.current_period || item.value || 0;
        });
      }
      if (Object.keys(trendData).length > 0) {
        transformed.trends.revenue_trend = trendData;
      }
    }
  }

  const companyName =
    (typeof rawData.company_name === "string" && rawData.company_name) ||
    (typeof rawData.company === "string" && rawData.company) ||
    "";
  transformed.company_name = companyName ? companyName.toUpperCase() : "";

  return transformed;
};

/**
 * Prepares trend data for charts
 */
export const prepareTrendDataForChart = (trends) => {
  if (!trends || typeof trends !== "object") return [];

  const data = [];

  // Try revenue_trend first
  if (trends.revenue_trend && typeof trends.revenue_trend === "object") {
    Object.entries(trends.revenue_trend).forEach(([period, value]) => {
      if (value !== null && value !== undefined) {
        data.push({
          period: period,
          revenue: Number(value) || 0,
        });
      }
    });
  }

  // Try other trend keys
  Object.entries(trends).forEach(([key, value]) => {
    if (key !== "revenue_trend" && typeof value === "object" && value !== null) {
      Object.entries(value).forEach(([period, val]) => {
        if (val !== null && val !== undefined) {
          data.push({
            period: period,
            [key]: Number(val) || 0,
          });
        }
      });
    }
  });

  return data;
};

/**
 * Prepares KPI data for bar chart
 */
export const prepareKPIDataForChart = (kpis) => {
  if (!kpis || typeof kpis !== "object") return [];

  return Object.entries(kpis)
    .filter(([_, value]) => {
      // Filter out non-numeric values and summary strings
      return typeof value === "number" && !isNaN(value);
    })
    .map(([name, value]) => ({
      name: name.replace(/_/g, " ").toUpperCase(),
      value: Number(value) || 0,
    }));
};

/**
 * Formats large numbers for display
 */
export const formatLargeNumber = (num) => {
  if (typeof num !== "number") return "N/A";
  
  if (num >= 1e12) {
    return (num / 1e12).toFixed(2) + "T";
  } else if (num >= 1e9) {
    return (num / 1e9).toFixed(2) + "B";
  } else if (num >= 1e6) {
    return (num / 1e6).toFixed(2) + "M";
  } else if (num >= 1e3) {
    return (num / 1e3).toFixed(2) + "K";
  }
  return num.toLocaleString("en-US");
};

