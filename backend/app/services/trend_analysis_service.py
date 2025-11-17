from typing import Dict, Any

def compute_trends(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute simple trend growth rates for revenue, net profit, and equity.
    """
    trends: Dict[str, Any] = {}
    sections = parsed.get("sections", {})
    bs_items = sections.get("balance_sheet", [])
    pnl = sections.get("pnl", {})

    # Revenue growth
    if "revenue" in pnl:
        current_rev = pnl["revenue"].get("value_rupees")
        prev_rev = pnl["revenue"].get("previous_value_rupees")
        if current_rev is not None and prev_rev is not None and prev_rev != 0:
            try:
                trends["revenue_growth_pct"] = round((current_rev - prev_rev) / prev_rev * 100, 2)
            except Exception:
                trends["revenue_growth_pct"] = None

    # Net profit growth
    if "net_profit" in pnl:
        current_profit = pnl["net_profit"].get("value_rupees")
        prev_profit = pnl["net_profit"].get("previous_value_rupees")
        if current_profit is not None and prev_profit is not None and prev_profit != 0:
            try:
                trends["net_profit_growth_pct"] = round((current_profit - prev_profit) / prev_profit * 100, 2)
            except Exception:
                trends["net_profit_growth_pct"] = None

    # Equity growth (from balance sheet)
    current_equity = None
    prev_equity = None
    for item in bs_items:
        if item.get("item") == "Total Equity":
            current_equity = item.get("current_period")
            prev_equity = item.get("previous_period")
            break
    if current_equity is not None and prev_equity is not None and prev_equity != 0:
        try:
            trends["equity_growth_pct"] = round((current_equity - prev_equity) / prev_equity * 100, 2)
        except Exception:
            trends["equity_growth_pct"] = None

    return trends


# # aggregate parsed financial JSONs for a company across periods and compute trends.
# # expect input: list of parsed_data dicts returned by parser_service.parse_financial_document
# # returns a timeseries-like structure and YoY/QoQ growth where possible.

# from typing import List, Dict, Any
# import logging

# logger = logging.getLogger(__name__)


# def aggregate_periods(parsed_list: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     parsed_list: list of parsed_data objects (each with meta.period_hint and sections)
#     Returns:
#       {
#         'timeseries': {period_label: {kpis...}},
#         'comparisons': {...}
#       }
#     """
#     result = {"timeseries": {}, "comparisons": {}}
#     for p in parsed_list:
#         meta = p.get("meta", {})
#         period = meta.get("period_hint") or meta.get("company") or f"period_{len(result['timeseries'])+1}"
#         # compute a small set of KPIs using financial_analysis_service
#         try:
#             from app.services.financial_analysis_service import compute_kpis
#             kpis = compute_kpis(p)
#         except Exception as e:
#             logger.exception("compute_kpis in aggregate failed: %s", e)
#             kpis = {"error": str(e)}
#         result["timeseries"][period] = {"meta": meta, "kpis": kpis}

#     # compute pairwise comparisons (eg latest vs previous)
#     periods = sorted(result["timeseries"].keys())
#     if len(periods) >= 2:
#         latest = periods[-1]
#         prev = periods[-2]
#         latest_kpis = result["timeseries"][latest]["kpis"]
#         prev_kpis = result["timeseries"][prev]["kpis"]
#         comparisons = {}
#         for k in latest_kpis:
#             if isinstance(latest_kpis.get(k), (int, float)) and isinstance(prev_kpis.get(k), (int, float)):
#                 try:
#                     growth = round(((latest_kpis[k] - prev_kpis[k]) / abs(prev_kpis[k])) * 100, 2) if prev_kpis[k] != 0 else None
#                 except Exception:
#                     growth = None
#                 comparisons[k] = {"latest": latest_kpis[k], "previous": prev_kpis[k], "growth_pct": growth}
#         result["comparisons"] = {"periods": [prev, latest], "metrics": comparisons}
#     return result

# #aggregate parsed financial JSONs for a company across periods and compute trends.
# #expect input: list of parsed_data dicts returned by parser_service.parse_financial_document
# #returns a timeseries-like structure and YoY/QoQ growth where possible.

# from typing import List, Dict, Any
# import logging

# logger=logging.getLogger(__name__)


# def aggregate_periods(parsed_list: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     parsed_list: list of parsed_data objects (each with meta.period_hint and sections)
#     Returns:
#       {
#         'timeseries': {period_label: {kpis...}},
#         'comparisons': {...}
#       }
#     """
#     result={"timeseries": {}, "comparisons": {}}
#     for p in parsed_list:
#         meta=p.get("meta", {})
#         period=meta.get("period_hint") or meta.get("company", "unknown_period")
#         #compute a small set of KPIs using financial_analysis_service
#         try:
#             from app.services.financial_analysis_service import compute_kpis
#             kpis=compute_kpis(p)
#         except Exception as e:
#             logger.exception("compute_kpis in aggregate failed: %s", e)
#             kpis={"error": str(e)}
#         result["timeseries"][period]={"meta": meta, "kpis": kpis}

#     #compute pairwise comparisons (eg latest vs previous)
#     periods=sorted(result["timeseries"].keys())
#     if len(periods)>=2:
#         latest=periods[-1]
#         prev=periods[-2]
#         latest_kpis=result["timeseries"][latest]["kpis"]
#         prev_kpis=result["timeseries"][prev]["kpis"]
#         comparisons={}
#         for k in latest_kpis:
#             if isinstance(latest_kpis.get(k), (int, float)) and isinstance(prev_kpis.get(k), (int, float)):
#                 try:
#                     comparisons[k]={"latest": latest_kpis[k], "previous": prev_kpis[k], "growth_pct": round(((latest_kpis[k]-prev_kpis[k]) / abs(prev_kpis[k]))*100, 2) if prev_kpis[k]!=0 else None}
#                 except Exception:
#                     comparisons[k]={"latest": latest_kpis[k], "previous": prev_kpis[k], "growth_pct": None}
#         result["comparisons"]={"periods": [prev, latest], "metrics": comparisons}
#     return result