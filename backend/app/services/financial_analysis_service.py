# compute key financial ratios and simple insights from parsed financial JSON.
# this is intentionally simple: robust analytics (seasonality, co-variates) can be added later.

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def compute_kpis(parsed: Dict[str, Any]) -> Dict[str, Any]:
    # i/p: parsed_data from parser_service.parse_financial_document
    # o/p: dictionary of ratios and short commentary
    result: Dict[str, Any] = {}
    try:
        bs_items = parsed.get("sections", {}).get("balance_sheet", [])
        pnl = parsed.get("sections", {}).get("pnl", {})
        cf = parsed.get("sections", {}).get("cash_flow", {})

        # extract a handful of common items by fuzzy keys
        total_assets = _find_single_value(bs_items, ["TOTAL ASSETS"])
        total_equity = _find_single_value(bs_items, ["TOTAL EQUITY"])
        total_liabilities = _find_single_value(bs_items, ["TOTAL LIABILITIES"])

        revenue = _extract_numeric(pnl, ["REVENUE", "TOTAL INCOME"])
        net_profit = _extract_numeric(pnl, ["PROFIT", "NET PROFIT", "PROFIT FOR THE PERIOD"])

        # ratios
        if revenue and net_profit:
            try:
                result["net_profit_margin_pct"] = round((net_profit / revenue) * 100, 2)
            except Exception:
                pass
        if total_equity and total_liabilities:
            try:
                result["debt_to_equity"] = round((total_liabilities / total_equity), 2)
            except Exception:
                pass
        if total_assets and total_equity:
            try:
                result["equity_to_assets_pct"] = round((total_equity / total_assets) * 100, 2)
            except Exception:
                pass
        if total_assets and revenue:
            try:
                result["asset_turnover_ratio"] = round((revenue / total_assets), 2)
            except Exception:
                pass
        if total_equity and net_profit:
            try:
                result["return_on_equity_pct"] = round((net_profit / total_equity) * 100, 2)
            except Exception:
                pass

        # cash-related
        operating_cf = _extract_numeric(cf, ["NET CASH GENERATED", "OPERATING", "CASH GENERATED FROM OPERATIONS"])
        capex = _extract_numeric(cf, ["Purchase", "CAPEX"])
        if operating_cf is not None and capex is not None:
            try:
                result["free_cash_flow"] = round(operating_cf - capex, 2)
            except Exception:
                pass

        # include raw values where available to help debugging
        if revenue is not None:
            result["revenue"] = revenue
        if net_profit is not None:
            result["net_profit"] = net_profit
        if total_assets is not None:
            result["total_assets"] = total_assets
        if total_equity is not None:
            result["total_equity"] = total_equity
        if total_liabilities is not None:
            result["total_liabilities"] = total_liabilities

        if revenue and net_profit and net_profit > 5 * revenue:
        # Likely OCR misread — try scale correction
            if revenue < 1000:
                # If revenue seems unrealistically small, scale it up
                revenue = revenue * 1000
            elif net_profit > 1e6:
                # If profit is absurdly large, rescale
                net_profit = net_profit / 100
        # basic narrative
        result["summary"] = _generate_summary(result)

    except Exception as e:
        logger.exception("compute_kpis failed: %s", e)
        result["error"] = str(e)
    return result


def _find_single_value(items: list, key_snippets: list) -> Optional[float]:
    for it in items:
        for key in key_snippets:
            if it.get("item") and key in it["item"].upper():
                return it.get("current_period")
    return None


def _extract_numeric(section: dict, key_snippets: list) -> Optional[float]:
    if not section:
        return None
    # section may be dict (pnl) or list (bs)
    if isinstance(section, dict):
        for k, v in section.items():
            for key in key_snippets:
                if key in k.upper():
                    if isinstance(v, dict):
                        return v.get("value")
                    return v
    # if section is list (some cashflow rows parsed as list)
    if isinstance(section, list):
        for it in section:
            if it.get("item"):
                for key in key_snippets:
                    if key in it["item"].upper():
                        return it.get("current_period")
    return None


def _generate_summary(metrics: dict) -> str:
    if not metrics:
        return "Insufficient parsed metrics for summary."
    parts = []
    if metrics.get("net_profit_margin_pct") is not None:
        parts.append(f"Net profit margin ~ {metrics['net_profit_margin_pct']}%")
    if metrics.get("debt_to_equity") is not None:
        parts.append(f"Debt-to-equity ratio ~ {metrics['debt_to_equity']}")
    if metrics.get("equity_to_assets_pct") is not None:
        parts.append(f"Equity-to-assets ratio ~ {metrics['equity_to_assets_pct']}%")
    if metrics.get("free_cash_flow") is not None:
        parts.append(f"Free cash flow ≈ ₹{metrics['free_cash_flow']} crore")
    if metrics.get("return_on_equity_pct") is not None:
        parts.append(f"Return on equity ~ {metrics['return_on_equity_pct']}%")
    if metrics.get("asset_turnover_ratio") is not None:
        parts.append(f"Asset turnover ratio ~ {metrics['asset_turnover_ratio']}")
    if not parts:
        # if at least revenue/net_profit present, mention them
        if metrics.get("revenue") is not None and metrics.get("net_profit") is not None:
            parts.append(f"Revenue: ₹{metrics['revenue']}, Net profit: ₹{metrics['net_profit']}")
    return "; ".join(parts) or "Insufficient parsed data."

# #compute key financial ratios and simple insights from parsed financial JSON.
# #this is intentionally simple: robust analytics (seasonality, co-variates) can be added later.

# from typing import Dict, Any, Optional
# import math
# import logging

# logger=logging.getLogger(__name__)


# def compute_kpis(parsed: Dict[str, Any]) -> Dict[str, Any]:
#     #i/p: parsed_data from parser_service.parse_financial_document
#     #o/p: dictionary of ratios and short commentary
#     result={}
#     try:
#         bs_items=parsed.get("sections", {}).get("balance_sheet", [])
#         pnl=parsed.get("sections", {}).get("pnl", {})
#         cf=parsed.get("sections", {}).get("cash_flow", {})

#         #extract a handful of common items by fuzzy keys
#         total_assets= _find_single_value(bs_items, ["TOTAL ASSETS"])
#         total_equity= _find_single_value(bs_items, ["TOTAL EQUITY"])
#         total_liabilities=None
#         #try finding "Total current liabilities" + "Total non-current liabilities" if present
#         total_liabilities= _find_single_value(bs_items, ["TOTAL LIABILITIES"])

#         revenue = _extract_numeric(pnl, ["REVENUE", "TOTAL INCOME"])
#         #profit_before_tax = _extract_numeric_from_pnl(pnl, ["PROFIT BEFORE TAX", "PROFIT BEFORE TAX (LOSS)"])
#         net_profit = _extract_numeric(pnl, ["PROFIT", "NET PROFIT"])

#         #ratios
#         if revenue and net_profit:
#             result["net_profit_margin_pct"]=round((net_profit/revenue)*100, 2)
#         if total_equity and total_liabilities:
#             result["debt_to_equity"]=round((total_liabilities / total_equity), 2)
#         if total_assets and total_equity:
#             result["equity_to_assets_pct"]=round((total_equity / total_assets) * 100, 2)
#         if total_assets and revenue:
#             result["asset_turnover_ratio"] = round((revenue / total_assets), 2)
#         if total_equity and net_profit:
#             result["return_on_equity_pct"] = round((net_profit / total_equity) * 100, 2)

#         #cash-related
#         operating_cf= _extract_numeric(cf, ["NET CASH GENERATED", "OPERATING"])
#         capex= _extract_numeric(cf, ["Purchase", "CAPEX"])
#         if operating_cf is not None and capex is not None:
#             #free cash flow
#             result["free_cash_flow"] = round(operating_cf - capex, 2)

#         #basic narrative
#         result["summary"]= _generate_summary(result)

#     except Exception as e:
#         logger.exception("compute_kpis failed: %s", e)
#         result["error"]=str(e)
#     return result


# def _find_single_value(items: list, key_snippets: list) -> Optional[float]:
#     for it in items:
#         for key in key_snippets:
#             if it.get("item") and key in it["item"].upper():
#                 return it.get("current_period")
#     return None


# def _extract_numeric(section: dict, key_snippets: list) -> Optional[float]:
#     if not section:
#         return None
#     # section may be dict (pnl) or list (bs)
#     if isinstance(section, dict):
#         for k, v in section.items():
#             for key in key_snippets:
#                 if key in k.upper():
#                     if isinstance(v, dict):
#                         return v.get("value")
#                     return v
#     return None


# def _generate_summary(metrics: dict) -> str:
#     if not metrics:
#         return "Insufficient parsed metrics for summary."
#     parts = []
#     if metrics.get("net_profit_margin_pct") is not None:
#         parts.append(f"Net profit margin ~ {metrics['net_profit_margin_pct']}%")
#     if metrics.get("debt_to_equity") is not None:
#         parts.append(f"Debt-to-equity ratio ~ {metrics['debt_to_equity']}")
#     if metrics.get("equity_to_assets_pct") is not None:
#         parts.append(f"Equity-to-assets ratio ~ {metrics['equity_to_assets_pct']}%")
#     if metrics.get("free_cash_flow") is not None:
#         parts.append(f"Free cash flow ≈ ₹{metrics['free_cash_flow']} crore")
#     if metrics.get("return_on_equity_pct") is not None:
#         parts.append(f"Return on equity ~ {metrics['return_on_equity_pct']}%")
#     if metrics.get("asset_turnover_ratio") is not None:
#         parts.append(f"Asset turnover ratio ~ {metrics['asset_turnover_ratio']}")
#     return "; ".join(parts) or "Insufficient parsed data."