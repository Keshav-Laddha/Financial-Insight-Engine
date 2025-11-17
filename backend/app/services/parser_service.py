# # parser_service.py
# """
# Robust parser improvements:
# - normalize_number: resilient OCR numeric normalizer
# - table postprocessing: prefer bottom totals, consolidated detection
# - KPI computation using authoritative totals
# - generic: works across company reports
# """

# import re
# import math
# from decimal import Decimal, InvalidOperation
# from typing import Optional, List, Dict, Any, Tuple

# # ---- numeric normalizer ---------------------------------------------------
# def normalize_number(raw: Optional[str]) -> Optional[float]:
#     """
#     Turn an OCR/raw numeric-like string into a float value (crores or rupees as given).
#     Returns None if it cannot be reliably parsed.

#     Handles:
#      - parentheses for negatives: "(123.45)" -> -123.45
#      - repeated/misplaced dots like "1,31.4.80" -> 1314.80
#      - common OCR confusions: l/I -> 1, O/o -> 0 (when safe)
#      - thousands separators, stray chars, currency symbols
#     """
#     if raw is None:
#         return None
#     s = str(raw).strip()
#     if s == '':
#         return None

#     # Quick reject if obviously not numeric and not containing digits
#     if not re.search(r'\d', s):
#         return None

#     # detect negative via parentheses or leading '-'
#     neg = False
#     if s.startswith('(') and s.endswith(')'):
#         neg = True
#         s = s[1:-1].strip()

#     # fix common unicode dashes
#     s = s.replace('\u2013', '-').replace('\u2014', '-').replace('\u2212', '-')

#     # remove currency symbols and other common leading noise
#     s = re.sub(r'[₹$£€]', '', s)

#     # Replace comma thousands separators (we remove commas and then handle dots)
#     # but keep them first for inspection. Remove spaces.
#     s = s.replace(' ', '')

#     # OCR fixes: 'O' or 'o' between digits likely 0; 'l'/'I' between digits likely 1
#     s = re.sub(r'(?<=\d)[Oo](?=\d)', '0', s)
#     s = re.sub(r'(?<=\d)[lI](?=\d)', '1', s)
#     s = re.sub(r'(?<=\d)[lI](?=\D)', '1', s)
#     s = re.sub(r'(?<=\D)[lI](?=\d)', '1', s)

#     # Remove commas (thousands separators) - OCR sometimes places them correctly or incorrectly
#     s = s.replace(',', '')

#     # Collapse multiple dots into a sane format:
#     # If more than 1 dot, convert by removing all dots and then placing last dot as decimal point
#     if s.count('.') > 1:
#         s_no_dot = s.replace('.', '')
#         if len(s_no_dot) > 2:
#             s = s_no_dot[:-2] + '.' + s_no_dot[-2:]
#         else:
#             s = s_no_dot

#     # Keep only digits, a single dot, and an optional leading minus
#     s = s.strip()
#     leading_minus = ''
#     if s.startswith('-'):
#         leading_minus = '-'
#         s = s[1:].lstrip()
#     s = re.sub(r'[^0-9.]', '', s)
#     if s.count('.') > 1:
#         parts = s.split('.')
#         s = parts[0] + '.' + ''.join(parts[1:])
#     s = leading_minus + s

#     if s in ['', '.', '-', '-.']:
#         return None

#     try:
#         val = Decimal(s)
#     except InvalidOperation:
#         return None

#     val_f = float(val)
#     if neg:
#         val_f = -val_f

#     # sanity clamp: if value is absurdly large ( > 10 million crores ), reject
#     if math.isfinite(val_f) and abs(val_f) > 1e7:
#         return None

#     return val_f

# # ---- table utilities ------------------------------------------------------
# def pick_numeric_from_cellblock(cell_raw: str) -> Optional[float]:
#     """
#     If a cell's raw text contains multiple numeric lines, prefer the last meaningful numeric
#     (typical for totals placed at end). Returns normalized float or None.
#     """
#     if not cell_raw:
#         return None
#     lines = [ln.strip() for ln in cell_raw.splitlines() if ln.strip()]
#     # prefer last line that contains digits
#     for ln in reversed(lines):
#         if re.search(r'\d', ln):
#             n = normalize_number(ln)
#             if n is not None:
#                 return n
#     # fallback: try to extract any numeric token in whole cell
#     tokens = re.findall(r'[\d\.,\(\)-]+', cell_raw)
#     for tok in reversed(tokens):
#         n = normalize_number(tok)
#         if n is not None:
#             return n
#     return None

# def find_table_total_candidate(tables: List[Dict[str, Any]], label_patterns: List[str]) -> Optional[Tuple[float, str]]:
#     """
#     Search parsed tables for rows/cells that match any label pattern (e.g., 'total assets', 'total equity').
#     Returns (value, matched_label) or None.
#     """
#     label_patterns_lower = [p.lower() for p in label_patterns]
#     # scan tables and rows
#     for table in tables:
#         header = ' '.join(table.get('header', [])).lower() if table.get('header') else ''
#         for row in table.get('rows', []):
#             # each row is dict column->cell
#             for col_key, cell in row.items():
#                 cell_raw = ''
#                 if isinstance(cell, dict):
#                     cell_raw = cell.get('raw', '') or ''
#                 else:
#                     cell_raw = str(cell)
#                 low = cell_raw.lower()
#                 for pat in label_patterns_lower:
#                     if pat in low or low.startswith(pat):
#                         # candidate found; pick numeric
#                         val = pick_numeric_from_cellblock(cell_raw)
#                         if val is not None:
#                             return (val, pat)
#     return None

# # ---- consolidated vs standalone detection --------------------------------
# def detect_section_type(text: str) -> str:
#     """
#     Detect keywords in the nearby text to infer whether a table is 'consolidated' or 'standalone'
#     Returns either "consolidated", "standalone", or "unknown"
#     """
#     txt = (text or '').lower()
#     if 'consolidated' in txt:
#         return 'consolidated'
#     if 'standalone' in txt or 'stand alone' in txt:
#         return 'standalone'
#     return 'unknown'

# # ---- KPI computation ------------------------------------------------------
# def compute_kpis_from_parsed(parsed: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Generic KPI computation that tries to find authoritative totals:
#      - prefer consolidated balance sheet totals when available
#      - fall back to standalone if consolidated not found
#      - sanity-check assets ≈ equity + liabilities
#     """
#     out = {}
#     # 1) try parsed_data.sections.balance_sheet for canonical entries
#     bd = parsed.get('parsed_data', {}).get('sections', {}).get('balance_sheet', [])
#     total_assets = None
#     total_equity = None
#     total_liabilities = None

#     if isinstance(bd, list) and bd:
#         for item in bd:
#             if not isinstance(item, dict):
#                 continue
#             key = item.get('item', '').lower()
#             val = item.get('current_period')
#             if val is None:
#                 # maybe it's 'value_crore' style
#                 val = item.get('value_crore') or item.get('value')
#             if key and val is not None:
#                 if 'assets' in key and 'total' in key:
#                     total_assets = float(val)
#                 if 'equity' in key and 'total' in key:
#                     total_equity = float(val)
#                 if 'liabilities' in key and 'total' in key:
#                     total_liabilities = float(val)

#     # 2) fallback: search tables_parsed heuristically
#     tables = parsed.get('parsed_data', {}).get('tables_parsed', []) or parsed.get('tables_parsed', [])
#     if (not total_assets) and tables:
#         cand = find_table_total_candidate(tables, ['total assets', 'total_assets', 'total assets (', 'total assets\n'])
#         if cand:
#             total_assets = cand[0]
#     if (not total_equity) and tables:
#         cand = find_table_total_candidate(tables, ['total equity', 'total_equity', 'total equity\n', 'total shareholders'])
#         if cand:
#             total_equity = cand[0]
#     if (not total_liabilities) and tables:
#         cand = find_table_total_candidate(tables, ['total liabilities', 'total_liabilities', 'total liabilities\n'])
#         if cand:
#             total_liabilities = cand[0]

#     # 3) if still missing, try scanning entire raw_text for lines of "Total assets" and extract numeric
#     raw_text = parsed.get('parsed_data', {}).get('raw_text') or parsed.get('raw_text') or parsed.get('text', '')
#     if raw_text and (not total_assets or not total_equity or not total_liabilities):
#         for line in raw_text.splitlines():
#             low = line.lower()
#             if not total_assets and 'total assets' in low:
#                 n = pick_numeric_from_cellblock(line)
#                 if n is not None:
#                     total_assets = total_assets or n
#             if not total_equity and ('total equity' in low or 'total equity and liabilities' in low):
#                 n = pick_numeric_from_cellblock(line)
#                 if n is not None:
#                     total_equity = total_equity or n
#             if not total_liabilities and 'total liabilities' in low:
#                 n = pick_numeric_from_cellblock(line)
#                 if n is not None:
#                     total_liabilities = total_liabilities or n

#     # 4) final sanity attempt: if assets missing but we have equity+liabilities, compute assets
#     if not total_assets and total_equity is not None and total_liabilities is not None:
#         total_assets = total_equity + total_liabilities

#     # 5) final sanity check: assets ≈ equity + liabilities; if mismatch, try to choose the consistent triple from table candidates
#     def is_consistent(a, e, l, tol=0.005):
#         if a is None or e is None or l is None:
#             return False
#         return abs(a - (e + l)) / max(1, a) <= tol

#     if not is_consistent(total_assets, total_equity, total_liabilities):
#         # try to choose best triple from tables: gather candidates and pick one with smallest error
#         candidates = []
#         # scan tables for numeric columns that look like totals (bottom-most numbers)
#         if tables:
#             # for each table, attempt to find numeric totals for assets/equity/liabilities
#             for table in tables:
#                 a = find_table_total_candidate([table], ['total assets', 'total_assets'])
#                 e = find_table_total_candidate([table], ['total equity', 'total_equity'])
#                 l = find_table_total_candidate([table], ['total liabilities', 'total_liabilities'])
#                 if a and e and l:
#                     candidates.append((a[0], e[0], l[0]))
#         # pick candidate with smallest mismatch
#         best = None
#         best_err = None
#         for (a,e,l) in candidates:
#             err = abs(a - (e + l)) / max(1, a)
#             if best is None or err < best_err:
#                 best = (a,e,l)
#                 best_err = err
#         if best and best_err is not None and best_err < 0.05:  # accept if within 5%
#             total_assets, total_equity, total_liabilities = best

#     # 6) compute KPIs if we have at least assets and equity
#     kpis = {}
#     # convert to rupees: we assume the values are in crores if that's the scale from parsed data.
#     # We do NOT implicitly multiply here; consumer of this function should know units.
#     if total_assets is not None:
#         kpis['total_assets'] = float(total_assets)
#     if total_equity is not None:
#         kpis['total_equity'] = float(total_equity)
#     if total_liabilities is not None:
#         kpis['total_liabilities'] = float(total_liabilities)

#     if total_equity and total_liabilities is not None:
#         try:
#             debt_to_equity = total_liabilities / total_equity if total_equity != 0 else None
#             if debt_to_equity is not None:
#                 kpis['debt_to_equity'] = round(debt_to_equity, 4)
#         except Exception:
#             pass

#     if total_assets and total_equity:
#         try:
#             eq_pct = (total_equity / total_assets) * 100 if total_assets != 0 else None
#             if eq_pct is not None:
#                 kpis['equity_to_assets_pct'] = round(eq_pct, 2)
#         except Exception:
#             pass

#     # revenue extraction (try parsed_data -> pnl -> revenue -> value_crore)
#     revenue = None
#     pnl = parsed.get('parsed_data', {}).get('sections', {}).get('pnl', {})
#     if isinstance(pnl, dict):
#         r = pnl.get('revenue') or pnl.get('total_revenue') or {}
#         if isinstance(r, dict):
#             revenue = r.get('value_crore') or r.get('value') or r.get('numeric_crore') or None
#     # fallback search raw_text for "Total revenue" lines
#     if not revenue and raw_text:
#         for line in raw_text.splitlines():
#             if 'total revenue' in line.lower() or 'total revenue from operations' in line.lower():
#                 v = pick_numeric_from_cellblock(line)
#                 if v is not None:
#                     revenue = v
#                     break

#     if revenue is not None:
#         kpis['revenue'] = float(revenue)

#     # asset turnover = revenue / assets
#     if revenue is not None and total_assets is not None and total_assets != 0:
#         kpis['asset_turnover_ratio'] = round(float(revenue) / float(total_assets), 4)

#     # add a simple summary
#     summ_parts = []
#     if 'debt_to_equity' in kpis:
#         summ_parts.append(f"Debt-to-Equity: {kpis['debt_to_equity']}")
#     if 'asset_turnover_ratio' in kpis:
#         summ_parts.append(f"Asset Turnover: {kpis['asset_turnover_ratio']}")
#     if 'equity_to_assets_pct' in kpis:
#         summ_parts.append(f"Equity/Assets: {kpis['equity_to_assets_pct']}%")
#     if summ_parts:
#         kpis['summary'] = '; '.join(summ_parts)

#     return kpis

# # ---- top-level helper ----------------------------------------------------
# def postprocess_parsed_document(parsed_doc: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Given an initial raw parsed document (from OCR + table extraction),
#     apply normalization & KPI computation and attach corrected fields.
#     """
#     # normalize numeric tokens inside tables_parsed cells
#     tables = parsed_doc.get('parsed_data', {}).get('tables_parsed', []) or parsed_doc.get('tables_parsed', [])
#     if tables:
#         for table in tables:
#             rows = table.get('rows', [])
#             for r_idx, row in enumerate(rows):
#                 for col, cell in list(row.items()):
#                     if isinstance(cell, dict):
#                         raw = cell.get('raw')
#                         norm = pick_numeric_from_cellblock(raw)
#                         if norm is not None:
#                             # store numeric normalized value explicitly
#                             cell['numeric_crore'] = norm
#                             cell['numeric_rupees'] = int(round(norm * 10000000))
#                             row[col] = cell
#                     else:
#                         # keep as-is
#                         pass
#     # compute kpis
#     kpis = compute_kpis_from_parsed(parsed_doc)
#     # attach kpis under parsed_data.kpis
#     parsed_doc.setdefault('parsed_data', {})
#     parsed_doc['parsed_data'].setdefault('kpis', {})
#     # move/overwrite with computed kpis
#     parsed_doc['parsed_data']['kpis'].update(kpis)
#     return parsed_doc


import re
from typing import List, Dict, Any, Optional
from app.services.preprocessing_service import parse_number_string_to_crore, scale_crore_to_rupees
from app.services.preprocessing_service import find_first_number_in_line

def parse_financial_document(cleaned_text: str, tables: List[List[List[str]]], scale: float) -> Dict[str, Any]:
    """
    Parse cleaned text and extracted tables to extract financial sections.
    """
    balance_sheet: List[Dict[str, Any]] = []
    pnl: Dict[str, Dict[str, Any]] = {}
    cash_flow: Dict[str, Dict[str, Any]] = {}

    # Helper functions
    def add_bs_item(name: str, current: Optional[int], previous: Optional[int] = None):
        item = {"item": name}
        if current is not None:
            item["current_period"] = current
        if previous is not None:
            item["previous_period"] = previous
        balance_sheet.append(item)

    def set_section_value(section: Dict[str, Any], key: str, val_crore: Optional[float], prev_crore: Optional[float] = None):
        rupees = scale_crore_to_rupees(val_crore, scale) if val_crore is not None else None
        prev_rupees = scale_crore_to_rupees(prev_crore, scale) if prev_crore is not None else None
        section[key] = {"value_crore": val_crore, "value_rupees": rupees}
        if prev_rupees is not None:
            section[key]["previous_value_rupees"] = prev_rupees

    # Parse lines from text
    lines = [ln for ln in cleaned_text.splitlines() if ln.strip()]
    for line in lines:
        low = line.lower()
        # Balance Sheet lines
        if "total assets" in low and "current assets" not in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                balance_sheet.append({"item": "Total Assets", "current_period": rupees})
        if "total equity" in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                balance_sheet.append({"item": "Total Equity", "current_period": rupees})
        if "total liabilities" in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                balance_sheet.append({"item": "Total Liabilities", "current_period": rupees})
        if "current assets" in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                balance_sheet.append({"item": "Current Assets", "current_period": rupees})
        if "current liabilities" in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                balance_sheet.append({"item": "Current Liabilities", "current_period": rupees})
        # P&L lines
        if ("total income" in low or "total revenue" in low or "revenue from operations" in low) and "profit" not in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                pnl["revenue"] = {"value_crore": val, "value_rupees": rupees}
        if ("net profit" in low or "profit after tax" in low or "profit for the year" in low or "profit for the period" in low):
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                pnl["net_profit"] = {"value_crore": val, "value_rupees": rupees}
        # Cash Flow lines
        if "net cash from operating" in low or "net cash generated from operating" in low or "cash generated from operations" in low:
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                cash_flow["operating_cf"] = {"value_crore": val, "value_rupees": rupees}
        if ("purchase of fixed" in low or "payment for property" in low or "capital expenditure" in low or "capex" in low):
            val = find_first_number_in_line(line)
            if val is not None:
                rupees = scale_crore_to_rupees(val, scale)
                cash_flow["capex"] = {"value_crore": val, "value_rupees": rupees}

    # Parse tables for multi-period data (if any)
    for table in tables:
        if len(table) < 2:
            continue
        header = table[0]
        # Identify numeric columns by year in header
        numeric_cols = [i for i, cell in enumerate(header) if isinstance(cell, str) and re.search(r"\d{4}", cell)]
        if len(numeric_cols) >= 2:
            cur_idx, prev_idx = numeric_cols[0], numeric_cols[1]
        else:
            # fallback: assume first column is labels, next two are numbers
            if len(header) >= 3 and header[1] and header[2] and all(re.match(r"^[\d,\.\-]+$", str(x).replace(',', '')) for x in header[1:3]):
                cur_idx, prev_idx = 1, 2
            else:
                continue
        for row in table[1:]:
            if not row or len(row) <= max(cur_idx, prev_idx):
                continue
            label = str(row[0]).strip()
            label_norm = label.lower()
            cur_val = parse_number_string_to_crore(str(row[cur_idx])) if row[cur_idx] not in (None, "") else None
            prev_val = parse_number_string_to_crore(str(row[prev_idx])) if row[prev_idx] not in (None, "") else None
            cur_rupees = scale_crore_to_rupees(cur_val, scale) if cur_val is not None else None
            prev_rupees = scale_crore_to_rupees(prev_val, scale) if prev_val is not None else None
            # Balance Sheet items
            if "total assets" in label_norm:
                balance_sheet = [item for item in balance_sheet if item.get("item") != "Total Assets"]
                add_bs_item("Total Assets", cur_rupees, prev_rupees)
            elif "total equity" in label_norm or "shareholders funds" in label_norm or "equity and liabilities" in label_norm:
                balance_sheet = [item for item in balance_sheet if item.get("item") != "Total Equity"]
                add_bs_item("Total Equity", cur_rupees, prev_rupees)
            elif "total liabilities" in label_norm:
                balance_sheet = [item for item in balance_sheet if item.get("item") != "Total Liabilities"]
                add_bs_item("Total Liabilities", cur_rupees, prev_rupees)
            elif "current assets" in label_norm:
                balance_sheet = [item for item in balance_sheet if item.get("item") != "Current Assets"]
                add_bs_item("Current Assets", cur_rupees, prev_rupees)
            elif "current liabilities" in label_norm:
                balance_sheet = [item for item in balance_sheet if item.get("item") != "Current Liabilities"]
                add_bs_item("Current Liabilities", cur_rupees, prev_rupees)
            # P&L items
            elif "total income" in label_norm or "total revenue" in label_norm or "revenue from operations" in label_norm or "sales" in label_norm:
                set_section_value(pnl, "revenue", cur_val, prev_val)
            elif ("net profit" in label_norm or "profit after tax" in label_norm or "profit for the year" in label_norm) and "gross profit" not in label_norm:
                set_section_value(pnl, "net_profit", cur_val, prev_val)
            # Cash Flow items
            elif "net cash from operating" in label_norm or "net cash generated from operating" in label_norm:
                set_section_value(cash_flow, "operating_cf", cur_val, prev_val)
            elif "capital expenditure" in label_norm or "purchase of fixed assets" in label_norm or "capex" in label_norm:
                set_section_value(cash_flow, "capex", cur_val, prev_val)

    # Remove duplicate balance sheet items, keeping last entries
    unique = {}
    for item in balance_sheet:
        unique[item["item"]] = item
    balance_sheet = list(unique.values())

    return {"sections": {"balance_sheet": balance_sheet, "pnl": pnl, "cash_flow": cash_flow}, "scale": scale, "raw_text": cleaned_text}



# """
# parser_service.py

# Responsibilities:
# - Accept cleaned_text (string) and tables (list of extracted tables)
# - Parse common financial statements pieces:
#     * Balance sheet totals (total assets, total equity, total liabilities)
#     * Income statement totals (revenue / total income, net profit / profit for period, profit attributable)
#     * Cash flow items (operating cash flow, capex)
#     * Basic items: cash & cash equivalents, current assets, current liabilities
# - Use fuzzy matching for label variants (several synonyms)
# - Return parsed_data with numeric values BOTH as 'crore' and 'rupees' (scaled)
# - Provide sections dict and tables_parsed
# """

# import re
# from typing import Dict, Any, List, Tuple, Optional
# from app.services.preprocessing_service import (
#     detect_scale_from_text,
#     parse_number_string_to_crore,
#     scale_crore_to_rupees,
#     find_first_number_in_line,
# )

# # fuzzy label variants for key items
# LABEL_PATTERNS = {
#     "total_assets": [
#         r"total assets\b",
#         r"assets\s+total\b",
#         r"total\s+asset\s+and\s+liabilities\b",
#         r"total\s+assets\s+and\s+liabilities\b",
#     ],
#     "total_equity": [r"total equity\b", r"total shareholders' equity\b", r"total shareholders equity\b"],
#     "total_liabilities": [r"total liabilities\b"],
#     "revenue": [r"total income\b", r"total revenue\b", r"revenue from operations\b", r"total revenue from operations\b"],
#     "net_profit": [r"profit for the period\b", r"profit for the period attributable\b", r"profit for the period.*\b", r"profit after tax\b", r"net profit\b", r"profit for the year\b"],
#     "profit_attrib": [r"profit attributable to shareholders of the company\b", r"profit attributable to shareholders\b"],
#     "cash_and_cash_equivalents": [r"cash and cash equivalents\b", r"cash & cash equivalents\b", r"cash and cash equivalents \(.*\)\b"],
#     "current_assets": [r"total current assets\b", r"current assets\b"],
#     "current_liabilities": [r"total current liabilities\b", r"current liabilities\b"],
#     "operating_cf": [r"net cash generated from operating activities\b", r"net cash generated from operating activities\b", r"net cash inflow from operating activities\b"],
#     "capex": [r"purchase of property, plant and equipment\b", r"payment for purchase of property, plant and equipment\b", r"payment for purchase of property plant and equipment\b"],
#     "eps": [r"earnings per share\b", r"basic earnings per share\b", r"eps\b"],
# }

# # normalize regex
# LABEL_PATTERNS = {k: [re.compile(pat, re.IGNORECASE) for pat in pats] for k, pats in LABEL_PATTERNS.items()}


# def _match_label_in_text(text: str, patterns: List[re.Pattern]) -> Optional[Tuple[str, int]]:
#     """
#     Search the text for a line that contains any of the compiled patterns.
#     Returns (line, index) of the first match or None.
#     """
#     lines = text.splitlines()
#     for i, ln in enumerate(lines):
#         for pat in patterns:
#             if pat.search(ln):
#                 return ln, i
#     return None


# def _search_nearby_number(lines: List[str], idx: int, window: int = 3) -> Optional[float]:
#     """
#     Once we find a label at lines[idx], look in the same line and +/- window lines for the first numeric token.
#     Return numeric value (as shown in report unit, e.g., '149748') or None.
#     """
#     # check same line first
#     for offset in range(0, window + 1):
#         for sign in (1, -1):
#             line_index = idx + sign * offset if offset != 0 else idx
#             if line_index < 0 or line_index >= len(lines):
#                 continue
#             num = find_first_number_in_line(lines[line_index])
#             if num is not None:
#                 return num
#     return None


# def _extract_from_tables(tables: List[List[List[str]]], header_tokens: List[str]) -> Optional[float]:
#     """
#     Try to find a value in tables heuristically.
#     tables is a list of tables; each table is list of rows; each row is list of cell text strings.
#     header_tokens: list of lowercased substrings to match the label.
#     """
#     if not tables:
#         return None
#     for table in tables:
#         for row in table:
#             # join row cells to a string
#             row_join = " ".join(cell for cell in row if cell)
#             lower = row_join.lower()
#             for tok in header_tokens:
#                 if tok in lower:
#                     # attempt to find numeric cells to the right of the label
#                     # prefer last numeric cell in row
#                     for cell in reversed(row):
#                         if not cell:
#                             continue
#                         val = parse_number_string_to_crore(cell)
#                         if val is not None:
#                             return val
#                     # fallback: any numeric in the row
#                     for cell in row:
#                         v = parse_number_string_to_crore(cell)
#                         if v is not None:
#                             return v
#     return None


# def _try_patterns_in_text(cleaned_text: str, key: str) -> Optional[float]:
#     patterns = LABEL_PATTERNS.get(key, [])
#     match = _match_label_in_text(cleaned_text, patterns)
#     if match:
#         line, idx = match
#         # search near the label for numbers
#         lines = cleaned_text.splitlines()
#         num = _search_nearby_number(lines, idx, window=4)
#         if num is not None:
#             return num
#     return None


# def parse_financial_document(cleaned_text: str, tables: List[List[List[str]]]) -> Dict[str, Any]:
#     """
#     Main parsing entrypoint used by routes.
#     cleaned_text: full cleaned text string returned from OCR flow
#     tables: list of tables (each table a list of row lists)
#     Returns parsed_data dict with:
#       - sections: {balance_sheet: [...], pnl: {...}, cash_flow: {...}}
#       - tables_parsed: list...
#       - scale: detected scale (float)
#       - raw_text: original cleaned_text (for auditing, truncated by caller)
#     """
#     # detect scale
#     scale = detect_scale_from_text(cleaned_text)

#     result = {
#         "sections": {
#             "balance_sheet": [],
#             "pnl": {},
#             "cash_flow": {},
#         },
#         "tables_parsed": [],
#         "scale": scale,
#         "raw_text": cleaned_text,
#     }

#     # helper to set values both as crore and rupees
#     def set_value(section: Dict, name: str, val_crore: Optional[float], source: str = "text"):
#         rupees = scale_crore_to_rupees(val_crore, scale) if val_crore is not None else None
#         section[name] = {"value_crore": val_crore, "value_rupees": rupees, "source": source}

#     # 1) Try common keys from text (label matching)
#     keys = [
#         ("total_assets", "balance_sheet"),
#         ("total_equity", "balance_sheet"),
#         ("total_liabilities", "balance_sheet"),
#         ("current_assets", "balance_sheet"),
#         ("current_liabilities", "balance_sheet"),
#         ("revenue", "pnl"),
#         ("net_profit", "pnl"),
#         ("profit_attrib", "pnl"),
#         ("cash_and_cash_equivalents", "balance_sheet"),
#         ("operating_cf", "cash_flow"),
#         ("capex", "cash_flow"),
#     ]

#     # iterate keys and use heuristics
#     for k, section_name in keys:
#         val = _try_patterns_in_text(cleaned_text, k)
#         if val is None:
#             # try from tables with simple tokens (take first word of pattern)
#             token_guesses = [pat.pattern.split(r"\b")[0].strip().strip("\\") for pat in LABEL_PATTERNS.get(k, [])]
#             # also use direct friendly tokens
#             friendly = {
#                 "total_assets": ["total assets", "total assets  ", "total"],
#                 "total_equity": ["total equity", "total shareholders"],
#                 "total_liabilities": ["total liabilities"],
#                 "revenue": ["total income", "revenue from operations", "total revenue"],
#                 "net_profit": ["profit for the period", "profit for the year", "net profit", "profit after tax"],
#                 "profit_attrib": ["profit attributable to shareholders", "attributable to shareholders"],
#                 "cash_and_cash_equivalents": ["cash and cash equivalents", "cash & cash equivalents"],
#                 "current_assets": ["total current assets", "current assets"],
#                 "current_liabilities": ["total current liabilities", "current liabilities"],
#                 "operating_cf": ["net cash generated from operating activities", "net cash generated from operating"],
#                 "capex": ["payment for purchase of property, plant and equipment", "purchase of property plant and equipment"],
#             }.get(k, [])
#             token_list = token_guesses + friendly
#             val = _extract_from_tables(tables, token_list)
#             if val is None:
#                 # final attempt: generic search in whole text for the first numeric near a line with label words
#                 for token in token_list:
#                     if not token:
#                         continue
#                     idx = cleaned_text.lower().find(token)
#                     if idx != -1:
#                         # take a slice and find first number in that slice
#                         snippet = cleaned_text[max(0, idx - 200): idx + 200]
#                         val_snip = find_first_number_in_line(snippet)
#                         if val_snip is not None:
#                             val = val_snip
#                             break

#         set_value(result["sections"][section_name], k, val, source=("text" if val is not None else "none"))

#     # 2) Parse tables and return a normalized simple structure in tables_parsed
#     for table in tables:
#         if not table:
#             continue
#         # header normalization: make header tokens lowercase, underscore separated
#         header_row = table[0] if table and len(table) > 0 else []
#         header_norm = []
#         for h in header_row:
#             if not isinstance(h, str):
#                 header_norm.append("")
#                 continue
#             h2 = re.sub(r"[^0-9a-zA-Z]+", "_", h.strip().lower()).strip("_")
#             header_norm.append(h2)
#         rows_parsed = []
#         for row in table[1:]:
#             cellmap = {}
#             for i, cell in enumerate(row):
#                 key = header_norm[i] if i < len(header_norm) else f"c{i}"
#                 # parse numeric if possible
#                 num = parse_number_string_to_crore(cell) if isinstance(cell, str) else None
#                 cellmap[key] = {"raw": cell, "numeric_crore": num, "numeric_rupees": scale_crore_to_rupees(num, scale) if num is not None else None}
#             rows_parsed.append(cellmap)
#         result["tables_parsed"].append({"header": header_norm, "rows": rows_parsed})

#     # 3) Provide small validation & warnings
#     # If totals are wildly inconsistent (e.g., total_assets missing but current_assets present), warn later in calling code.
#     # Add a simple sanity check: if total_assets exists and equity+liabilities missing, attempt to compute liabilities
#     ta = result["sections"]["balance_sheet"].get("total_assets", {}).get("value_crore")
#     te = result["sections"]["balance_sheet"].get("total_equity", {}).get("value_crore")
#     cl = result["sections"]["balance_sheet"].get("current_liabilities", {}).get("value_crore")
#     ca = result["sections"]["balance_sheet"].get("current_assets", {}).get("value_crore")
#     # compute total_liabilities if missing
#     if ta is not None and te is not None and result["sections"]["balance_sheet"].get("total_liabilities", {}).get("value_crore") in (None,):
#         computed_liab = ta - te
#         set_value(result["sections"]["balance_sheet"], "total_liabilities", computed_liab, source="computed")
#         result.setdefault("_notes", []).append("total_liabilities computed as total_assets - total_equity")
#     # populate simple parsed_data top-level for backward compatibility
#     parsed_data = {
#         "sections": result["sections"],
#         "tables_parsed": result["tables_parsed"],
#         "scale": result["scale"],
#         "raw_text": result["raw_text"],
#     }
#     return parsed_data


# # """
# # Parser service that converts cleaned_text + tables into structured financial JSON.

# # ✅ Features:
# # - Robust section detection (handles merged OCR text like 'profitandloss', 'cashflow', etc.)
# # - Extracts key financial data (Balance Sheet, P&L, Cash Flow, Equity)
# # - Fallback pattern-based extraction when tables fail
# # - Clean normalization and data validation
# # - Adheres to OWASP safe coding principles
# # """

# # import re
# # import logging
# # from typing import Dict, Any, List
# # from fastapi import HTTPException, status
# # from app.services.preprocessing_service import parse_number, detect_document_scale

# # logger = logging.getLogger(__name__)

# # # Core numeric token regex
# # _NUM_TOKEN_RE = r'\(?[0-9][0-9,\.()]*\)?'


# # # -------------------------------------------------------------------------
# # # SECTION SPLITTER — detects sections reliably even with OCR distortions
# # # -------------------------------------------------------------------------
# # def _split_into_sections(text: str) -> Dict[str, str]:
# #     """
# #     Splits financial document into sections based on key phrases,
# #     regardless of OCR spacing or case.
# #     This uses regex patterns that allow optional non-alphanumeric characters
# #     between letters so merged headings (profitandloss, profit and loss, PROF IT & LOSS) are detected.
# #     """
# #     if not text:
# #         return {}

# #     section_terms = {
# #         "balance_sheet": ["balance sheet", "statement of financial position", "balancesheet", "financialposition"],
# #         "pnl": ["profit and loss", "statement of profit and loss", "statement of profit", "profitandloss", "statementofprofitandloss", "operations"],
# #         "cash_flow": ["cash flow", "statement of cash flows", "cashflow", "statementofcashflows"],
# #         "changes_in_equity": ["changes in equity", "statement of changes in equity", "changesinequity"],
# #     }

# #     positions: Dict[str, int] = {}

# #     # For each term build a tolerant regex that allows non-alphanumeric between characters
# #     def tolerant_pattern(term: str) -> str:
# #         # split into words and join with a flexible separator
# #         words = re.split(r'\s+', term.strip())
# #         parts = []
# #         for w in words:
# #             # allow optional non-alnum between characters in a word
# #             chars = [re.escape(c) + r'[^a-z0-9]*' for c in w.lower()]
# #             parts.append(''.join(chars))
# #         # allow any whitespace/non-word between words
# #         return r'\b' + r'[^a-z0-9]*'.join(parts) + r'\b'

# #     lower_text = text  # keep original (we'll search with regex)
# #     for name, terms in section_terms.items():
# #         for term in terms:
# #             pat = tolerant_pattern(term)
# #             m = re.search(pat, lower_text, flags=re.IGNORECASE)
# #             if m:
# #                 positions[name] = m.start()
# #                 break

# #     if not positions:
# #         # fallback: whole text as balance_sheet block
# #         return {"balance_sheet": text}

# #     # sort detected positions and slice original text into blocks
# #     sorted_items = sorted(positions.items(), key=lambda x: x[1])
# #     sections: Dict[str, str] = {}
# #     for i, (sec_name, start_idx) in enumerate(sorted_items):
# #         end_idx = sorted_items[i + 1][1] if i + 1 < len(sorted_items) else len(text)
# #         block = text[start_idx:end_idx].strip()
# #         # only include reasonably sized blocks
# #         if len(block) > 50:
# #             sections[sec_name] = block
# #     return sections


# # # -------------------------------------------------------------------------
# # # CORE PARSER LOGIC
# # # -------------------------------------------------------------------------
# # def parse_financial_document(cleaned_text: str, tables: List[List]) -> Dict[str, Any]:
# #     if not cleaned_text:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty cleaned_text")

# #     scale, unit_label = detect_document_scale(cleaned_text)
# #     sections = _split_into_sections(cleaned_text)

# #     if not any([sections.get("balance_sheet"), sections.get("pnl")]):
# #         # Detect company name early for proper metadata
# #         meta_info = _extract_meta(cleaned_text, unit_label="units")
# #         return {
# #             "meta": meta_info,
# #             "scale": 1.0,
# #             "sections": {},
# #             "tables": tables or [],
# #             "kpis": {
# #                 "summary": "No financial statements detected — likely a narrative, CSR, or management discussion section."
# #             }
# #         }
    
# #     parsed = {
# #         "meta": _extract_meta(cleaned_text, unit_label),
# #         "scale": scale,
# #         "sections": {},
# #         "tables": tables or [],
# #     }

# #     # Structured section parsing
# #     parsed["sections"]["balance_sheet"] = _extract_table_like_section(sections.get("balance_sheet", ""), scale)
# #     parsed["sections"]["pnl"] = _extract_simple_kv(sections.get("pnl", ""), scale)
# #     parsed["sections"]["cash_flow"] = _extract_simple_kv(sections.get("cash_flow", ""), scale)
# #     parsed["sections"]["changes_in_equity"] = _extract_simple_kv(sections.get("changes_in_equity", ""), scale)

# #     # If P&L not detected, try a document-wide P&L extraction (fallback)
# #     if not parsed["sections"]["pnl"]:
# #         pnl_fb = _extract_pnl_from_text(cleaned_text, scale)
# #         # merge fallback keys
# #         if pnl_fb:
# #             parsed["sections"]["pnl"].update(pnl_fb)

# #     # Fallback extraction for missing or incomplete balance sheet
# #     if not parsed["sections"]["balance_sheet"]:
# #         fallback = _extract_from_text(cleaned_text)
# #         for sec in ["balance_sheet", "pnl", "cash_flow"]:
# #             parsed["sections"][sec] = parsed["sections"].get(sec) or fallback.get(sec, {})

# #     # Validate basic balance (may raise)
# #     try:
# #         _validate_basic_balance(parsed)
# #     except Exception as e:
# #         # record validation warning instead of failing endpoint
# #         parsed["validation_warning"] = str(e)

# #     return parsed


# # # -------------------------------------------------------------------------
# # # SECTION HELPERS
# # # -------------------------------------------------------------------------

# # def _detect_period_hint(text: str) -> str:
# #     """
# #     Detect reporting period like 'As at June 30, 2024' → 'Q1 FY25'
# #     """
# #     match = re.search(r'(June|September|December|March)\s+\d{1,2},?\s*(20\d{2})', text)
# #     if not match:
# #         return None

# #     month = match.group(1).lower()
# #     year = int(match.group(2))
# #     fy = f"FY{(year + 1) % 100}" if month in ["march"] else f"FY{year % 100 + 1}"

# #     quarter = {
# #         "june": "Q1",
# #         "september": "Q2",
# #         "december": "Q3",
# #         "march": "Q4"
# #     }.get(month, "")
# #     return f"{quarter} {fy}"

# # def _extract_meta(text: str, unit_label: str = "units") -> Dict[str, Any]:
# #     company = None

# #     # 1️⃣ Find all possible "<Company> Limited"/"Ltd." occurrences
# #     candidates = re.findall(
# #         r'\b([A-Z][A-Za-z&\.\s]+?(?:LIMITED|LTD\.))\b',
# #         text,
# #         flags=re.IGNORECASE
# #     )

# #     # 2️⃣ Filter out known false positives (exchange names, regulators, etc.)
# #     blacklist = re.compile(r'\b(BSE|NSE|Exchange|Societe|Luxembourg|SEBI|Board|Phiroze|Stock)\b', re.IGNORECASE)
# #     filtered_candidates = [c.strip() for c in candidates if not blacklist.search(c)]

# #     # 3️⃣ If multiple matches, choose the most frequent or longest (often the real company)
# #     if filtered_candidates:
# #         company = max(filtered_candidates, key=len)

# #     # 4️⃣ If still not found, look for “For <Company> Limited” or “Regd. Office - <Company>”
# #     if not company:
# #         fallback = re.search(
# #             r'(?:For\s+)?([A-Z][A-Za-z\s&\.]+)\s+(?:Ltd\.?|LIMITED)',
# #             text,
# #             flags=re.IGNORECASE
# #         )
# #         if fallback:
# #             company = fallback.group(1).strip() + " Limited"

# #     if not company:
# #         reg_match = re.search(r'([A-Z][A-Za-z&\.\s]+)\s*(?=Regd\. Office)', text, flags=re.IGNORECASE)
# #         if reg_match:
# #             company = reg_match.group(1).strip()

# #     # 5️⃣ Extract period if present
# #     period = None
# #     period_match = re.search(
# #         r"(?:as at|as on|quarter ended|half year ended|year ended)\s+([A-Za-z0-9 ,\-]+[0-9]{4})",
# #         text,
# #         flags=re.IGNORECASE
# #     )
# #     if period_match:
# #         period = period_match.group(1).strip()

# #     # 6️⃣ Return safely structured metadata
# #     meta = {"company": company or "Unknown", "unit": unit_label}
# #     if period:
# #         meta["period_hint"] = _detect_period_hint(text)

# #     return meta


# # def _extract_table_like_section(section_text: str, scale: float) -> List[Dict[str, Any]]:
# #     items = []
# #     if not section_text:
# #         return items

# #     raw_lines = re.split(r'[\n\r]+', section_text)
# #     candidate_frags = []

# #     for line in raw_lines:
# #         line = line.strip()
# #         if not line:
# #             continue
# #         # break overly long lines using common punctuation heuristics
# #         if len(line) > 500:
# #             frags = re.split(r'[;\.\:\-]{1,}\s+', line)
# #             candidate_frags.extend([f.strip() for f in frags if len(f.strip()) > 5])
# #             continue
# #         candidate_frags.append(line)

# #     for line in candidate_frags:
# #         # find numeric tokens anywhere
# #         if re.search(r'(DIN|Partner|Director|Chartered Accountants|Mumbai|LLP|CFO|Secretary)', line, re.IGNORECASE):
# #             continue
# #         nums = re.findall(r'\(?[0-9][0-9,\.()]*\)?', line)
# #         if not nums:
# #             continue

# #         # prefer numeric tokens at end of fragment
# #         tail_match = re.search(r'(' + _NUM_TOKEN_RE + r'(?:\s+' + _NUM_TOKEN_RE + r')?)\s*$', line)
# #         if tail_match:
# #             vals = re.findall(r'\(?[0-9\.,]+\)?', tail_match.group(1))
# #             name = line[:tail_match.start()].strip()
# #         else:
# #             vals = nums[:2]
# #             name = re.sub(r'\(?[0-9][0-9,\.()]*\)?', '', line).strip()

# #         name = _normalize_item_name(name)

# #         # handle glued comma-grouped numbers inside a single token
# #         if len(vals) == 1:
# #             glued = vals[0]
# #             m_glued = re.search(
# #                 r'([0-9]{1,3}(?:,[0-9]{2,3})+)([0-9]{1,3}(?:,[0-9]{2,3})+)$',
# #                 glued
# #             )
# #             if m_glued:
# #                 vals = [m_glued.group(1), m_glued.group(2)]

# #         curr = parse_number(vals[0]) if len(vals) >= 1 else None
# #         prev = parse_number(vals[1]) if len(vals) >= 2 else None

# #         if curr is not None:
# #             curr *= scale
# #         if prev is not None:
# #             prev *= scale

# #         # filter noisy note headings etc.
# #         if name.lower().startswith(("note", "annexure")):
# #             continue
# #         # skip tiny numeric tokens with no real label
# #         if curr is not None and abs(curr) < 100 and len(name.split()) < 3:
# #             continue

# #         items.append({
# #             "item": name,
# #             "current_period": curr,
# #             "previous_period": prev,
# #             "confidence": "high" if curr is not None else "low"
# #         })

# #     return items


# # def _extract_simple_kv(section_text: str, scale: float) -> Dict[str, Any]:
# #     out: Dict[str, Any] = {}
# #     if not section_text:
# #         return out
# #     lines = re.split(r'[\n\r]+', section_text)
# #     for raw in lines:
# #         line = raw.strip()
# #         if not line:
# #             continue
# #         # pattern: text <num> [<num>] at end of line
# #         m = re.search(r'(.{3,200}?)\s+(' + _NUM_TOKEN_RE + r')(?:\s+(' + _NUM_TOKEN_RE + r'))?\s*$', line)
# #         if not m:
# #             continue
# #         key = _normalize_item_name(m.group(1))
# #         val1 = parse_number(m.group(2))
# #         val2 = parse_number(m.group(3)) if m.group(3) else None
# #         if val1 is not None:
# #             val1 *= scale
# #         if val2 is not None:
# #             val2 *= scale
# #         out[key] = {"value": val1, "previous": val2}
# #     return out