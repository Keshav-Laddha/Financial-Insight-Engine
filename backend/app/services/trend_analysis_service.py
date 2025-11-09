# aggregate parsed financial JSONs for a company across periods and compute trends.
# expect input: list of parsed_data dicts returned by parser_service.parse_financial_document
# returns a timeseries-like structure and YoY/QoQ growth where possible.

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def aggregate_periods(parsed_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    parsed_list: list of parsed_data objects (each with meta.period_hint and sections)
    Returns:
      {
        'timeseries': {period_label: {kpis...}},
        'comparisons': {...}
      }
    """
    result = {"timeseries": {}, "comparisons": {}}
    for p in parsed_list:
        meta = p.get("meta", {})
        period = meta.get("period_hint") or meta.get("company") or f"period_{len(result['timeseries'])+1}"
        # compute a small set of KPIs using financial_analysis_service
        try:
            from app.services.financial_analysis_service import compute_kpis
            kpis = compute_kpis(p)
        except Exception as e:
            logger.exception("compute_kpis in aggregate failed: %s", e)
            kpis = {"error": str(e)}
        result["timeseries"][period] = {"meta": meta, "kpis": kpis}

    # compute pairwise comparisons (eg latest vs previous)
    periods = sorted(result["timeseries"].keys())
    if len(periods) >= 2:
        latest = periods[-1]
        prev = periods[-2]
        latest_kpis = result["timeseries"][latest]["kpis"]
        prev_kpis = result["timeseries"][prev]["kpis"]
        comparisons = {}
        for k in latest_kpis:
            if isinstance(latest_kpis.get(k), (int, float)) and isinstance(prev_kpis.get(k), (int, float)):
                try:
                    growth = round(((latest_kpis[k] - prev_kpis[k]) / abs(prev_kpis[k])) * 100, 2) if prev_kpis[k] != 0 else None
                except Exception:
                    growth = None
                comparisons[k] = {"latest": latest_kpis[k], "previous": prev_kpis[k], "growth_pct": growth}
        result["comparisons"] = {"periods": [prev, latest], "metrics": comparisons}
    return result

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