"""
Parser service that converts cleaned_text + tables into structured financial JSON.

✅ Features:
- Robust section detection (handles merged OCR text like 'profitandloss', 'cashflow', etc.)
- Extracts key financial data (Balance Sheet, P&L, Cash Flow, Equity)
- Fallback pattern-based extraction when tables fail
- Clean normalization and data validation
- Adheres to OWASP safe coding principles
"""

import re
import logging
from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.services.preprocessing_service import parse_number, detect_document_scale

logger = logging.getLogger(__name__)

# Core numeric token regex
_NUM_TOKEN_RE = r'\(?[0-9][0-9,\.()]*\)?'


# -------------------------------------------------------------------------
# SECTION SPLITTER — detects sections reliably even with OCR distortions
# -------------------------------------------------------------------------
def _split_into_sections(text: str) -> Dict[str, str]:
    """
    Splits financial document into sections based on key phrases,
    regardless of OCR spacing or case.
    This uses regex patterns that allow optional non-alphanumeric characters
    between letters so merged headings (profitandloss, profit and loss, PROF IT & LOSS) are detected.
    """
    if not text:
        return {}

    section_terms = {
        "balance_sheet": ["balance sheet", "statement of financial position", "balancesheet", "financialposition"],
        "pnl": ["profit and loss", "statement of profit and loss", "statement of profit", "profitandloss", "statementofprofitandloss", "operations"],
        "cash_flow": ["cash flow", "statement of cash flows", "cashflow", "statementofcashflows"],
        "changes_in_equity": ["changes in equity", "statement of changes in equity", "changesinequity"],
    }

    positions: Dict[str, int] = {}

    # For each term build a tolerant regex that allows non-alphanumeric between characters
    def tolerant_pattern(term: str) -> str:
        # split into words and join with a flexible separator
        words = re.split(r'\s+', term.strip())
        parts = []
        for w in words:
            # allow optional non-alnum between characters in a word
            chars = [re.escape(c) + r'[^a-z0-9]*' for c in w.lower()]
            parts.append(''.join(chars))
        # allow any whitespace/non-word between words
        return r'\b' + r'[^a-z0-9]*'.join(parts) + r'\b'

    lower_text = text  # keep original (we'll search with regex)
    for name, terms in section_terms.items():
        for term in terms:
            pat = tolerant_pattern(term)
            m = re.search(pat, lower_text, flags=re.IGNORECASE)
            if m:
                positions[name] = m.start()
                break

    if not positions:
        # fallback: whole text as balance_sheet block
        return {"balance_sheet": text}

    # sort detected positions and slice original text into blocks
    sorted_items = sorted(positions.items(), key=lambda x: x[1])
    sections: Dict[str, str] = {}
    for i, (sec_name, start_idx) in enumerate(sorted_items):
        end_idx = sorted_items[i + 1][1] if i + 1 < len(sorted_items) else len(text)
        block = text[start_idx:end_idx].strip()
        # only include reasonably sized blocks
        if len(block) > 50:
            sections[sec_name] = block
    return sections


# -------------------------------------------------------------------------
# CORE PARSER LOGIC
# -------------------------------------------------------------------------
def parse_financial_document(cleaned_text: str, tables: List[List]) -> Dict[str, Any]:
    if not cleaned_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty cleaned_text")

    scale, unit_label = detect_document_scale(cleaned_text)
    sections = _split_into_sections(cleaned_text)

    if not any([sections.get("balance_sheet"), sections.get("pnl")]):
        # Detect company name early for proper metadata
        meta_info = _extract_meta(cleaned_text, unit_label="units")
        return {
            "meta": meta_info,
            "scale": 1.0,
            "sections": {},
            "tables": tables or [],
            "kpis": {
                "summary": "No financial statements detected — likely a narrative, CSR, or management discussion section."
            }
        }
    
    parsed = {
        "meta": _extract_meta(cleaned_text, unit_label),
        "scale": scale,
        "sections": {},
        "tables": tables or [],
    }

    # Structured section parsing
    parsed["sections"]["balance_sheet"] = _extract_table_like_section(sections.get("balance_sheet", ""), scale)
    parsed["sections"]["pnl"] = _extract_simple_kv(sections.get("pnl", ""), scale)
    parsed["sections"]["cash_flow"] = _extract_simple_kv(sections.get("cash_flow", ""), scale)
    parsed["sections"]["changes_in_equity"] = _extract_simple_kv(sections.get("changes_in_equity", ""), scale)

    # If P&L not detected, try a document-wide P&L extraction (fallback)
    if not parsed["sections"]["pnl"]:
        pnl_fb = _extract_pnl_from_text(cleaned_text, scale)
        # merge fallback keys
        if pnl_fb:
            parsed["sections"]["pnl"].update(pnl_fb)

    # Fallback extraction for missing or incomplete balance sheet
    if not parsed["sections"]["balance_sheet"]:
        fallback = _extract_from_text(cleaned_text)
        for sec in ["balance_sheet", "pnl", "cash_flow"]:
            parsed["sections"][sec] = parsed["sections"].get(sec) or fallback.get(sec, {})

    # Validate basic balance (may raise)
    try:
        _validate_basic_balance(parsed)
    except Exception as e:
        # record validation warning instead of failing endpoint
        parsed["validation_warning"] = str(e)

    return parsed


# -------------------------------------------------------------------------
# SECTION HELPERS
# -------------------------------------------------------------------------

def _detect_period_hint(text: str) -> str:
    """
    Detect reporting period like 'As at June 30, 2024' → 'Q1 FY25'
    """
    match = re.search(r'(June|September|December|March)\s+\d{1,2},?\s*(20\d{2})', text)
    if not match:
        return None

    month = match.group(1).lower()
    year = int(match.group(2))
    fy = f"FY{(year + 1) % 100}" if month in ["march"] else f"FY{year % 100 + 1}"

    quarter = {
        "june": "Q1",
        "september": "Q2",
        "december": "Q3",
        "march": "Q4"
    }.get(month, "")
    return f"{quarter} {fy}"

def _extract_meta(text: str, unit_label: str = "units") -> Dict[str, Any]:
    company = None

    # 1️⃣ Find all possible "<Company> Limited"/"Ltd." occurrences
    candidates = re.findall(
        r'\b([A-Z][A-Za-z&\.\s]+?(?:LIMITED|LTD\.))\b',
        text,
        flags=re.IGNORECASE
    )

    # 2️⃣ Filter out known false positives (exchange names, regulators, etc.)
    blacklist = re.compile(r'\b(BSE|NSE|Exchange|Societe|Luxembourg|SEBI|Board|Phiroze|Stock)\b', re.IGNORECASE)
    filtered_candidates = [c.strip() for c in candidates if not blacklist.search(c)]

    # 3️⃣ If multiple matches, choose the most frequent or longest (often the real company)
    if filtered_candidates:
        company = max(filtered_candidates, key=len)

    # 4️⃣ If still not found, look for “For <Company> Limited” or “Regd. Office - <Company>”
    if not company:
        fallback = re.search(
            r'(?:For\s+)?([A-Z][A-Za-z\s&\.]+)\s+(?:Ltd\.?|LIMITED)',
            text,
            flags=re.IGNORECASE
        )
        if fallback:
            company = fallback.group(1).strip() + " Limited"

    if not company:
        reg_match = re.search(r'([A-Z][A-Za-z&\.\s]+)\s*(?=Regd\. Office)', text, flags=re.IGNORECASE)
        if reg_match:
            company = reg_match.group(1).strip()

    # 5️⃣ Extract period if present
    period = None
    period_match = re.search(
        r"(?:as at|as on|quarter ended|half year ended|year ended)\s+([A-Za-z0-9 ,\-]+[0-9]{4})",
        text,
        flags=re.IGNORECASE
    )
    if period_match:
        period = period_match.group(1).strip()

    # 6️⃣ Return safely structured metadata
    meta = {"company": company or "Unknown", "unit": unit_label}
    if period:
        meta["period_hint"] = _detect_period_hint(text)

    return meta


def _extract_table_like_section(section_text: str, scale: float) -> List[Dict[str, Any]]:
    items = []
    if not section_text:
        return items

    raw_lines = re.split(r'[\n\r]+', section_text)
    candidate_frags = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # break overly long lines using common punctuation heuristics
        if len(line) > 500:
            frags = re.split(r'[;\.\:\-]{1,}\s+', line)
            candidate_frags.extend([f.strip() for f in frags if len(f.strip()) > 5])
            continue
        candidate_frags.append(line)

    for line in candidate_frags:
        # find numeric tokens anywhere
        if re.search(r'(DIN|Partner|Director|Chartered Accountants|Mumbai|LLP|CFO|Secretary)', line, re.IGNORECASE):
            continue
        nums = re.findall(r'\(?[0-9][0-9,\.()]*\)?', line)
        if not nums:
            continue

        # prefer numeric tokens at end of fragment
        tail_match = re.search(r'(' + _NUM_TOKEN_RE + r'(?:\s+' + _NUM_TOKEN_RE + r')?)\s*$', line)
        if tail_match:
            vals = re.findall(r'\(?[0-9\.,]+\)?', tail_match.group(1))
            name = line[:tail_match.start()].strip()
        else:
            vals = nums[:2]
            name = re.sub(r'\(?[0-9][0-9,\.()]*\)?', '', line).strip()

        name = _normalize_item_name(name)

        # handle glued comma-grouped numbers inside a single token
        if len(vals) == 1:
            glued = vals[0]
            m_glued = re.search(
                r'([0-9]{1,3}(?:,[0-9]{2,3})+)([0-9]{1,3}(?:,[0-9]{2,3})+)$',
                glued
            )
            if m_glued:
                vals = [m_glued.group(1), m_glued.group(2)]

        curr = parse_number(vals[0]) if len(vals) >= 1 else None
        prev = parse_number(vals[1]) if len(vals) >= 2 else None

        if curr is not None:
            curr *= scale
        if prev is not None:
            prev *= scale

        # filter noisy note headings etc.
        if name.lower().startswith(("note", "annexure")):
            continue
        # skip tiny numeric tokens with no real label
        if curr is not None and abs(curr) < 100 and len(name.split()) < 3:
            continue

        items.append({
            "item": name,
            "current_period": curr,
            "previous_period": prev,
            "confidence": "high" if curr is not None else "low"
        })

    return items


def _extract_simple_kv(section_text: str, scale: float) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not section_text:
        return out
    lines = re.split(r'[\n\r]+', section_text)
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # pattern: text <num> [<num>] at end of line
        m = re.search(r'(.{3,200}?)\s+(' + _NUM_TOKEN_RE + r')(?:\s+(' + _NUM_TOKEN_RE + r'))?\s*$', line)
        if not m:
            continue
        key = _normalize_item_name(m.group(1))
        val1 = parse_number(m.group(2))
        val2 = parse_number(m.group(3)) if m.group(3) else None
        if val1 is not None:
            val1 *= scale
        if val2 is not None:
            val2 *= scale
        out[key] = {"value": val1, "previous": val2}
    return out


# -------------------------------------------------------------------------
# FALLBACK TEXT EXTRACTION (when structured parsing fails)
# -------------------------------------------------------------------------
def _extract_from_text(raw_text: str) -> dict:
    text = raw_text.upper().replace(",", "")
    text = re.sub(r'\s+', ' ', text)

    patterns = {
        "TOTAL ASSETS": r"TOTAL\s*ASSETS.*?([0-9\)\(][0-9\.,\(\)-]*)",
        "TOTAL EQUITY": r"TOTAL\s*EQUITY.*?([0-9\)\(][0-9\.,\(\)-]*)",
        "TOTAL LIABILITIES": r"TOTAL\s*(?:LIABILITIES|CURRENT\s*LIABILITIES).*?([0-9\)\(][0-9\.,\(\)-]*)",
        "REVENUE": r"(?:REVENUE|TOTAL\s+INCOME|REVENUE\s+FROM\s+OPERATIONS).*?([0-9\)\(][0-9\.,\(\)-]*)",
        "PROFIT FOR THE PERIOD": r"PROFIT\s*FOR\s*THE\s*PERIOD.*?([0-9\)\(][0-9\.,\(\)-]*)",
    }

    extracted = {"balance_sheet": [], "pnl": {}, "cash_flow": {}}

    for label, pattern in patterns.items():
        m = re.search(pattern, text, flags=re.IGNORECASE | re.S)
        if not m:
            continue
        try:
            num = float(m.group(1).replace(",", "").replace("(", "").replace(")", ""))
        except Exception:
            continue

        if "ASSET" in label or "EQUITY" in label or "LIABIL" in label:
            extracted["balance_sheet"].append({"item": label, "current_period": num, "confidence": "high"})
        elif "REV" in label:
            extracted["pnl"]["Revenue"] = {"value": num}
        elif "PROFIT" in label:
            extracted["pnl"]["Profit for the Period"] = {"value": num}

    return extracted


def _extract_pnl_from_text(text: str, scale: float) -> Dict[str, Any]:
    """
    Document-wide P&L fallback: search for revenue/total income and profit numbers anywhere.
    This helps when a 'P&L' heading wasn't recognized but numbers exist in the file.
    """
    out: Dict[str, Any] = {}
    if not text:
        return out
    # Search for common revenue labels then numeric tokens after them
    patterns = [
        (r"(?:TOTAL\s+INCOME|TOTAL\s+REVENUE|REVENUE\s+FROM\s+OPERATIONS|REVENUE)\s*[:\-]?\s*([0-9\(\)\.,]+)", "Revenue"),
        (r"(?:PROFIT\s+FOR\s+THE\s+PERIOD|NET\s+PROFIT|PROFIT\s+AFTER\s+TAX|PAT)\s*[:\-]?\s*([0-9\(\)\.,]+)", "Profit for the Period"),
        (r"(?:PROFIT\s+BEFORE\s+TAX|PBT)\s*[:\-]?\s*([0-9\(\)\.,]+)", "Profit Before Tax")
    ]
    # allow case-insensitive searches
    for pat, label in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            raw_num = m.group(1)
            num = parse_number(raw_num)
            if num is not None:
                out[label] = {"value": num * scale}
    return out


# -------------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------------
def _normalize_item_name(name: str) -> str:
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.strip(':;,.')
    if len(name) > 120:
        cut = re.search(r'(.{80,120}?)[:;\.\-\,\n]', name)
        name = cut.group(1).strip() if cut else name[:120].rsplit(' ', 1)[0]
    name = re.sub(r'^[\W\d]+', '', name)
    name = re.sub(r'[\W\d]+$', '', name)
    return name


def _validate_basic_balance(parsed: Dict[str, Any]) -> None:
    bs = parsed.get("sections", {}).get("balance_sheet", [])
    def find_item(key_substr):
        for it in bs:
            if it.get("item") and key_substr in it["item"].upper():
                return it
        return None

    total_assets = find_item("TOTAL ASSETS")
    total_eq = find_item("TOTAL EQUITY")
    total_liab = find_item("TOTAL LIABILITIES")
    if total_assets and (total_eq or total_liab):
        assets = total_assets.get("current_period")
        rhs = (total_eq.get("current_period", 0) if total_eq else 0) + (total_liab.get("current_period", 0) if total_liab else 0)
        if assets is not None and abs(assets - rhs) > max(1.0, 0.001 * abs(assets)):
            raise ValueError(f"Balance mismatch: Assets={assets} vs Eq+Liab={rhs}")





# """
# Parser service that converts cleaned_text + tables into structured financial JSON.
# - Detects sections (Balance Sheet, P&L, Cash Flows, Equity, Notes)
# - Extracts line items heuristically from lines: "Name ... number [number]"
# - Converts numbers using preprocessing_service.parse_number
# - Adds per-item confidence where parsing was fuzzy
# """

# import re
# import logging
# from typing import Dict, Any, List, Tuple
# from fastapi import HTTPException, status

# from app.services.preprocessing_service import parse_number, detect_document_scale

# logger=logging.getLogger(__name__)

# #section header regex map
# SECTION_PATTERNS={
#     # "balance_sheet": r"(BALANCE\s*SHEET|STATEMENT\s+OF\s+FINANCIAL\s+POSITION|CONDENSED\s+CONSOLIDATED\s+INTERIM\s+BALANCE\s+SHEET)",
#     # "pnl": r"(PROFIT\s+AND\s+LOSS|STATEMENT\s+OF\s+PROFIT|STATEMENT\s+OF\s+OPERATIONS|CONDENSED\s+CONSOLIDATED\s+INTERIM\s+STATEMENT\s+OF)",
#     # "cash_flow": r"(CASH\s+FLOW|STATEMENT\s+OF\s+CASH\s+FLOWS)",
#     # "changes_in_equity": r"(STATEMENT\s+OF\s+CHANGES\s+IN\s+EQUITY|CHANGES\s+IN\s+EQUITY)",
#     # "notes": r"(NOTES\s+TO\s+ACCOUNTS|NOTES\s+FORMING\s+PART)",
#     "balance_sheet": r"(BALANCE\s*[\-_]*SHEET|STATEMENT\s*OF\s*FINANCIAL\s*POSITION)",
#     "pnl": r"(PROFIT\s*AND\s*LOSS|STATEMENT\s*OF\s*PROFIT\s*AND\s*LOSS|STATEMENTOFPROFITANDLOSS|OPERATIONS)",
#     "cash_flow": r"(CASH\s*FLOW|STATEMENT\s*OF\s*CASH\s*FLOWS|STATEMENTOFCASHFLOWS)",
# }

# #number-like token regex: optionally parentheses, digits and commas and decimals
# _NUM_TOKEN_RE=r'\(?\d{1,3}(?:[,\d{2,3}]*\d)?(?:\.\d+)?\)?'


# def _extract_from_text(raw_text: str)->dict:
#     #detects key financial matrix
#     text=raw_text.upper().replace(",", "")
    
#     #add spacing between letters and digits (helps match patterns)
#     text=re.sub(r"([A-Z])([0-9])", r"\1 \2", text)
#     text=re.sub(r"([0-9])([A-Z])", r"\1 \2", text)

#     patterns = {
#         "TOTAL ASSETS": r"TOTAL\s*ASSETS.*?([0-9\)\(][0-9\.,\(\)-]*)\s+([0-9\)\(][0-9\.,\(\)-]*)",
#         "TOTAL EQUITY": r"TOTAL\s*EQUITY.*?([0-9\)\(][0-9\.,\(\)-]*)\s+([0-9\)\(][0-9\.,\(\)-]*)",
#         "TOTAL LIABILITIES": r"TOTAL\s*(?:LIABILITIES|CURRENT\s*LIABILITIES).*?([0-9\)\(][0-9\.,\(\)-]*)\s+([0-9\)\(][0-9\.,\(\)-]*)",
#         "REVENUE": r"(?:REVENUE|TOTAL\s+INCOME|REVENUE\s+FROM\s+OPERATIONS).*?([0-9\)\(][0-9\.,\(\)-]*)",
#         "PROFIT FOR THE PERIOD": r"PROFIT\s*FOR\s*THE\s*PERIOD.*?([0-9\)\(][0-9\.,\(\)-]*)",
#         "changes_in_equity": r"(STATEMENT\s*OF\s*CHANGES\s*IN\s*EQUITY|CHANGES\s*IN\s*EQUITY)"
#     }

#     extracted={"balance_sheet": [], "pnl": {}, "cash_flow": {}}

#     for label, pattern in patterns.items():
#         m=re.search(pattern, text, flags=re.IGNORECASE | re.S)
#         if m:
#             nums=[float(x) for x in m.groups() if x]
#             if "ASSETS" in label or "EQUITY" in label or "LIABILITIES" in label:
#                 extracted["balance_sheet"].append({
#                     "item": label,
#                     "current_period": nums[0] if len(nums) > 0 else None,
#                     "previous_period": nums[1] if len(nums) > 1 else None
#                 })
#             elif "REVENUE" in label:
#                 extracted["pnl"]["Revenue"]={"value": nums[0]}
#             elif "PROFIT" in label:
#                 extracted["pnl"]["Profit for the Period"]={"value": nums[0]}
#     return extracted


# def parse_financial_document(cleaned_text: str, tables: List[List]) -> Dict[str, Any]:
#     if not cleaned_text:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty cleaned_text")

#     scale, unit_label=detect_document_scale(cleaned_text)

#     sections= _split_into_sections(cleaned_text)

#     parsed={
#         "meta": _extract_meta(cleaned_text, unit_label=unit_label),
#         "scale": scale,
#         "sections": {},
#         "tables": tables or [],
#     }

#     # #parse balance sheet if present
#     # if "balance_sheet" in sections:
#     #     parsed["sections"]["balance_sheet"]= _extract_table_like_section(sections["balance_sheet"], scale)
#     # else:
#     #     parsed["sections"]["balance_sheet"]= []

#     # #parse P&L
#     # if "pnl" in sections:
#     #     parsed["sections"]["pnl"]= _extract_simple_kv(sections["pnl"], scale)
#     # else:
#     #     parsed["sections"]["pnl"]= {}

#     # #parse cash flow
#     # if "cash_flow" in sections:
#     #     parsed["sections"]["cash_flow"]= _extract_simple_kv(sections["cash_flow"], scale)
#     # else:
#     #     parsed["sections"]["cash_flow"]={}

#     # #attach tables raw -> try to map tables to sections by proximity heuristics
#     # parsed["tables_parsed"]= _parse_tables(tables, scale)

#     # #basic validation
#     # try:
#     #     _validate_basic_balance(parsed)
#     # except Exception as e:
#     #     parsed["validation_warning"]=str(e)

#     # #fallback extraction: if structured parsing failed or produced too few items
#     # if not parsed["sections"].get("balance_sheet") or len(parsed["sections"]["balance_sheet"]) < 3:
#     #     try:
#     #         fallback= _extract_from_text(cleaned_text)
#     #         for sec in ["balance_sheet", "pnl", "cash_flow"]:
#     #             if not parsed["sections"].get(sec) or not parsed["sections"][sec]:
#     #                 parsed["sections"][sec]=fallback.get(sec, {} if sec != "balance_sheet" else [])
#     #     except Exception as e:
#     #         logger.warning(f"Fallback text extraction failed: {e}")

#     # return parsed

#     parsed["sections"]["balance_sheet"] = _extract_table_like_section(
#         sections.get("balance_sheet", ""), scale)
#     parsed["sections"]["pnl"] = _extract_simple_kv(sections.get("pnl", ""), scale)
#     parsed["sections"]["cash_flow"] = _extract_simple_kv(sections.get("cash_flow", ""), scale)
#     if "changes_in_equity" in sections:
#         parsed["sections"]["changes_in_equity"] = _extract_simple_kv(sections["changes_in_equity"], scale)
#     else:
#         parsed["sections"]["changes_in_equity"] = {}

#     if not parsed["sections"]["balance_sheet"]:
#         fallback = _extract_from_text(cleaned_text)
#         for sec in ["balance_sheet", "pnl", "cash_flow"]:
#             parsed["sections"][sec] = parsed["sections"].get(sec) or fallback.get(sec, {})

#     try:
#         _validate_basic_balance(parsed)
#     except Exception as e:
#         parsed["validation_warning"] = str(e)

#     return parsed


# def _split_into_sections(text: str) -> Dict[str, str]:
#     matches = [(n, m.start()) for n, p in SECTION_PATTERNS.items()
#                for m in re.finditer(p, text, flags=re.IGNORECASE)]
#     matches.sort(key=lambda x: x[1])
#     if not matches:
#         return {"balance_sheet": text}

#     sections = {}
#     for i, (name, start) in enumerate(matches):
#         end = matches[i + 1][1] if i + 1 < len(matches) else len(text)
#         block = text[start:end].strip()
#         if len(block) > 200:
#             sections[name] = block
#     return sections


# def _extract_meta(text: str, unit_label: str="units") -> Dict[str, Any]:
#     company=None
#     m=re.search(r"^([A-Z][A-Z\s\.\-&]{3,}LIMITED)", text, flags=re.MULTILINE)
#     if m:
#         company=m.group(1).strip()
#     #attempt to find "As at" dates in header lines
#     # period_matches=re.findall(r"(?:As at|As on)\s*([A-Za-z0-9 ,\-]+[0-9]{4})", text, flags=re.IGNORECASE)
#     # period=period_matches[0].strip() if period_matches else None
#     # return {"company": company or "Unknown", "period_hint": period, "unit": unit_label}
#     return {"company": company or "Unknown", "unit": unit_label}


# def _extract_table_like_section(section_text: str, scale: float) -> List[Dict[str, Any]]:
#     #extract lines of the form: <item name> <number> <number>
#     #this is a heuristic; we return list of items with numeric values for current and previous period if present.
#     items=[]
#     #split into candidate lines using newlines and semicolon/punctuation
#     raw_lines=re.split(r'[\n\r]+', section_text)
#     candidate_frags=[]
#     for line in raw_lines:
#         line=line.strip()
#         if not line:
#             continue
#         #if a line is extremely long, break by sentence/punctuation heuristics
#         if len(line)>500:
#             frags=re.split(r'[;\.\:\-]{1,}\s+', line)
#             frags=[f.strip() for f in frags if len(f.strip()) > 5]
#             if frags:
#                 candidate_frags.extend(frags)
#                 continue
#         candidate_frags.append(line)

#     for line in candidate_frags:
#         #find numeric tokens anywhere
#         nums=re.findall(r'\(?[0-9][0-9,\.()]*\)?', line)
#         if not nums:
#             continue

#         #prefer numeric tokens at end of fragment
#         tail_match=re.search(r'(' + _NUM_TOKEN_RE + r'(?:\s+' + _NUM_TOKEN_RE + r')?)\s*$', line)
#         if tail_match:
#             tail=tail_match.group(1)
#             vals=re.findall(r'\(?[0-9\.,]+\)?', tail)
#             name=line[:tail_match.start()].strip()
#         else:
#             #fallback: take the first one or two numeric tokens
#             vals=nums[:2]
#             name=re.sub(r'\(?[0-9][0-9,\.()]*\)?', '', line).strip()

#         name=_normalize_item_name(name)

#         # ---- handle glued comma-grouped numbers inside a single token ----
#         # If we have only one numeric string but it contains two adjacent comma-groups
#         # like "32,52631,481" (no space), try to split into two numbers.
#         if len(vals) == 1:
#             glued = vals[0]
#             # attempt to find two comma-group patterns adjacent with no space
#             m_glued = re.search(
#                 r'([0-9]{1,3}(?:,[0-9]{2,3})+)([0-9]{1,3}(?:,[0-9]{2,3})+)$',
#                 glued
#             )
#             if m_glued:
#                 # split into two tokens
#                 vals = [m_glued.group(1), m_glued.group(2)]

#         curr=parse_number(vals[0]) if len(vals)>=1 else None
#         prev=parse_number(vals[1]) if len(vals)>=2 else None

#         if curr is not None:
#             curr=curr*scale
#         if prev is not None:
#             prev=prev*scale

#         confidence="high" if curr is not None else "low"
#         if name.lower().startswith("note") or name.lower().startswith("annexure"):
#             continue
#         if curr is not None and abs(curr) < 100 and len(name.split()) < 3:
#             # Skip short lines like "Note 10(a) 9,232"
#             continue
#         items.append({"item": name, "current_period": curr, "previous_period": prev, "confidence": confidence})

#     return items


# def _extract_simple_kv(section_text: str, scale: float) -> Dict[str, Any]:
#     #extract simple key-value pairs like 'Profit for the period 12,040' heuristically.
#     #returns a dict mapping normalized keys to numeric values.
#     out={}
#     #find lines and try to find a key and a number
#     lines=re.split(r'[\n\r]+', section_text)
#     for raw in lines:
#         line=raw.strip()
#         if not line:
#             continue
#         #pattern: <text> <num>
#         m=re.search(r'(.{3,200}?)\s+(' + _NUM_TOKEN_RE + r')(?:\s+(' + _NUM_TOKEN_RE + r'))?\s*$', line)
#         if not m:
#             continue
#         key=_normalize_item_name(m.group(1))
#         val1=parse_number(m.group(2))
#         val2=parse_number(m.group(3)) if m.group(3) else None
#         if val1 is not None:
#             val1=val1 * scale
#         if val2 is not None:
#             val2=val2 * scale
#         out[key]={"value": val1, "previous": val2}
#     return out


# def _normalize_item_name(name: str) -> str:
#     # basic cleanup: collapse whitespace and remove stray punctuation at ends
#     name = re.sub(r'\s+', ' ', name).strip()
#     name = name.strip(':;,.')
#     # if name is extremely long (e.g., entire paragraph/notes), shorten to first 100-120 chars
#     if len(name) > 120:
#         # prefer to cut at punctuation or whitespace boundary
#         cut = re.search(r'(.{80,120}?)[:;\.\-\,\n]', name)
#         if cut:
#             name = cut.group(1).strip()
#         else:
#             name = name[:120].rsplit(' ', 1)[0]
#     # remove accidental leading/trailing isolated digits/punct
#     name = re.sub(r'^[\W\d]+', '', name)
#     name = re.sub(r'[\W\d]+$', '', name)
#     return name


# def normalize_table_header(header: List[str]) -> List[str]:
#     """
#     Normalize table column headers:
#     - Converts to lowercase
#     - Replaces spaces and special chars with underscores
#     - Removes trailing underscores
#     Example: "Total Assets (₹ crore)" → "total_assets_₹_crore"
#     """
#     return [
#         re.sub(r'_+', '_', re.sub(r'[^a-zA-Z0-9]', '_', h.strip().lower())).strip('_')
#         for h in header
#     ]


# def _parse_tables(tables: List[List], scale: float) -> List[Dict[str, Any]]:
#     #convert pdfplumber 'tables' (list-of-lists) into normalized list-of-dicts.
#     #this function does a light parsing only; heavier table parsing should be done separately.

#     parsed=[]
#     if not tables:
#         return parsed
#     for tbl in tables:
#         #attempt to treat first row as header if all cells are strings
#         if not tbl:
#             continue
#         header=[str(x).strip() for x in tbl[0]]
#         header=normalize_table_header(header)
#         rows=[]
#         for r in tbl[1:]:
#             #map header -> cell
#             row={}
#             for i, h in enumerate(header):
#                 cell=r[i] if i<len(r) else ""
#                 #try numeric parse
#                 num=None
#                 if isinstance(cell, (int, float)):
#                     num=float(cell)*scale
#                 else:
#                     num=parse_number(cell)
#                     if num is not None:
#                         num=num*scale
#                 row[h]={"raw": cell, "numeric": num}
#             rows.append(row)
#         parsed.append({"header": header, "rows": rows})
#     return parsed


# def _validate_basic_balance(parsed: Dict[str, Any]) -> None:
#     #validate that TOTAL ASSETS ≈ TOTAL EQUITY + TOTAL LIABILITIES (heuristic).
#     #if cannot find values, do nothing. If mismatch beyond tolerance, raise ValueError.
#     bs=parsed.get("sections", {}).get("balance_sheet", [])
#     # try to find "TOTAL ASSETS" and "TOTAL EQUITY" or "TOTAL EQUITY AND LIABILITIES"
#     def find_item(key_substr):
#         for it in bs:
#             if it.get("item") and key_substr in it["item"].upper():
#                 return it
#         return None

#     total_assets=find_item("TOTAL ASSETS")
#     total_eq=find_item("TOTAL EQUITY")
#     total_eq_liab=find_item("TOTAL EQUITY AND LIABILITIES") or find_item("TOTAL EQUITY AND LIABILITIES")
#     #prefer eq+liab detection if available
#     if total_assets and (total_eq_liab or total_eq):
#         assets=total_assets.get("current_period")
#         if total_eq_liab:
#             rhs=total_eq_liab.get("current_period")
#         else:
#             #attempt to sum equity + (total liabilities as "Total current liabilities" + "Total non-current liabilities")
#             rhs=None
#         if assets is not None and rhs is not None:
#             if abs(assets-rhs)>max(1.0, 0.001 * assets):
#                 raise ValueError(f"Asset mismatch: Assets={assets} vs Eq+Liab={rhs}")