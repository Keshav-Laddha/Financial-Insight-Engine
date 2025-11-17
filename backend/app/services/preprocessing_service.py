import re
from typing import Optional, Tuple

UNIT_SCALES = {
    "crore": 1e7,
    "cr": 1e7,
    "cr.": 1e7,
    "lakh": 1e5,
    "lac": 1e5,
    "lacs": 1e5,
    "thousand": 1e3,
    "million": 1e6,
    "mn": 1e6,
    "billion": 1e9,
    "bn": 1e9,
}

def detect_scale_from_text(text: str) -> float:
    """
    Detect scale keyword in text (crore, lakh, million, etc.) and return corresponding multiplier.
    Defaults to crore.
    """
    if not text:
        return UNIT_SCALES["crore"]
    lowered = text.lower()
    if "crore" in lowered or "` crore" in lowered or "₹ crore" in lowered:
        return UNIT_SCALES["crore"]
    if "lakh" in lowered or " lac " in lowered or "lacs" in lowered:
        return UNIT_SCALES["lakh"]
    if "million" in lowered or "mn" in lowered:
        return UNIT_SCALES["million"]
    if "billion" in lowered or "bn" in lowered:
        return UNIT_SCALES["billion"]
    return UNIT_SCALES["crore"]

def _strip_brackets_and_signs(s: str) -> Tuple[str, bool]:
    """
    Remove parentheses or leading minus, and return cleaned string and negative flag.
    """
    negative = False
    s = s.strip()
    if not s:
        return "", False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    return s, negative

def parse_number_string_to_crore(raw: Optional[str]) -> Optional[float]:
    """
    Convert raw numeric string to float in report's scale units (crore/lakh).
    Returns None if it cannot parse.
    """
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    # known non-numeric markers
    if s in ("-", "—", "–", "nil", "na", "n/a", "*", ""):
        return None
    # remove trailing non-numeric characters
    s = re.sub(r"[^\d\(\)\.\,\-]+$", "", s)
    s, negative = _strip_brackets_and_signs(s)
    s = s.replace(",", "").replace("₹", "").replace("`", "").strip()
    s = s.replace("O", "0").replace("l", "1") #this line
    if s.count(".") > 1:
        parts = s.split(".")
        s = parts[0] + "." + "".join(parts[1:])
    s = re.sub(r"[a-zA-Z]+$", "", s).strip()
    if not re.search(r"\d", s): #this line
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if negative else val

def scale_crore_to_rupees(value_crore: Optional[float], scale: float) -> Optional[int]:
    """
    Convert value in crores/lakhs to absolute rupees (int).
    """
    if value_crore is None:
        return None
    try:
        return int(round(value_crore * scale))
    except Exception:
        return None

def find_first_number_in_line(line: str) -> Optional[float]:
    """
    Find first numeric token in line and parse it (in scale units).
    """
    if not line:
        return None
    matches = re.findall(r"[+\-]?\(?[0-9][0-9\.,]*\)?", line)
    for token in matches:
        num = parse_number_string_to_crore(token)
        if num is not None:
            return num
    return None



# """
# Responsibilities:
# - Unicode normalization
# - Collapse spaced letters & digits
# - Remove headers/footers & boilerplate
# - Normalize dates, currencies and numeric tokens
# - Provide safe numeric parsing with scale inference (crore detection)
# """

# import re
# import unicodedata
# import logging
# from typing import Optional, Tuple

# logger = logging.getLogger(__name__)


# def normalize_ocr_text(text: str) -> str:
#     """
#     Fix common OCR issues in financial PDFs:
#     - Remove random extra spaces between characters
#     - Merge split words like 'PROF IT' → 'PROFIT'
#     - Normalize uppercase patterns
#     """
#     # remove multiple spaces and fix broken words
#     text = re.sub(r'\s+', ' ', text)
#     # merge all-caps broken words (e.g., "PROF IT" -> "PROFIT")
#     text = re.sub(r'([A-Z])\s+([A-Z])', r'\1\2', text)
#     # restore 'STATEMENTOF...' style headers
#     text = re.sub(r'STATEMENTOF', 'STATEMENT OF ', text, flags=re.IGNORECASE)
#     text = re.sub(r'CONDENSEDCONSOLIDATED', 'CONDENSED CONSOLIDATED ', text, flags=re.IGNORECASE)
#     text = re.sub(r'PROFITANDLOSS', 'PROFIT AND LOSS', text, flags=re.IGNORECASE)
#     text = re.sub(r'CASHFLOW', 'CASH FLOW', text, flags=re.IGNORECASE)
#     text = re.sub(r'CHANGESINEQUITY', 'CHANGES IN EQUITY', text, flags=re.IGNORECASE)
#     return text.strip()


# def clean_text(raw_text: str) -> str:
#     # returns cleaned text (string)
#     if not isinstance(raw_text, str):
#         raise TypeError("clean_text expects a string")

#     text = unicodedata.normalize("NFKC", raw_text)  # normalize unicode
#     replacements = {
#         "“": '"', "”": '"', "‘": "'", "’": "'",
#         "–": "-", "—": "-", "−": "-", "•": "-",
#         "₹.": "₹", "Rs.": "₹", "Rs": "₹", "INR": "₹",
#         "\x0c": " ",  # form-feed
#     }
#     for old, new in replacements.items():
#         text = text.replace(old, new)

#     text = re.sub(r"[\x00-\x1F\x7F]", "", text)  # remove control chars
#     text = text.replace("\u00A0", " ")

#     # remove common boilerplate artifacts
#     text = _remove_boilerplate(text)

#     # Normalize OCR-style broken words and digits
#     text = collapse_spaced_letters(text)
#     text = collapse_spaced_digits(text)

#     # Restore reasonable spacing between words and numbers
#     text = restore_spaces_between_words_and_numbers(text)

#     # Add space between repeated comma-groups to help splitting (heuristic)
#     text = re.sub(
#         r'(\d{1,3}(?:,\d{2,3})+)(?=(\d{1,3}(?:,\d{2,3})+))',
#         r'\1 ',
#         text
#     )

#     # normalize percent spacing (10 % -> 10%)
#     text = re.sub(r"(\d)\s+%", r"\1%", text)
#     text = re.sub(r"\b(Rs|RS|INR)\.?\b", "₹", text, flags=re.IGNORECASE)
#     text = re.sub(r"₹\s+", "₹", text)

#     # quick OCR misread fixes
#     text = re.sub(r"(?<=\b)[0O](?=[A-Za-z])", "O", text)  # 0/O confusion
#     text = re.sub(r"(?<=[A-Za-z])[1I](?=[a-z])", "l", text)  # 1/l confusion
#     text = re.sub(r"(?<=\b)5(?=[A-Za-z])", "S", text)  # 5/S confusion

#     # normalize common date patterns to YYYY-MM-DD where possible
#     text = re.sub(
#         r"(\b\d{1,2})[/-](\d{1,2})[/-](\d{2,4}\b)",
#         lambda m: f"{m.group(3).zfill(4)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}",
#         text,
#     )

#     # remove repeated headers/footers at page boundaries
#     text = remove_repeated_headers_footers(text)

#     # Normalize whitespace within each surviving line but keep line breaks
#     lines = text.splitlines()
#     normalized_lines = []
#     for ln in lines:
#         ln = ln.strip()
#         if not ln:
#             continue
#         ln = re.sub(r'[ \t]+', ' ', ln)
#         normalized_lines.append(ln)
#     text = "\n".join(normalized_lines).strip()

#     # Apply OCR header normalizer as a last step
#     text = normalize_ocr_text(text)

#     # safe fallback
#     if not text.strip():
#         logger.warning("clean_text returned empty; using raw_text fallback")
#         text = raw_text.strip()

#     return text


# def _remove_boilerplate(text: str) -> str:
#     patterns = [
#         r"Export to Sheets",
#         r"Generated by .*",
#         r"Page\s*\d+(\s*of\s*\d+)?",
#         r"As per our report of even date attached",
#     ]
#     for pat in patterns:
#         text = re.sub(pat, " ", text, flags=re.IGNORECASE)
#     return text


# def collapse_spaced_letters(text: str) -> str:
#     # collapse sequences of single letters separated by spaces (target groups of >=3)
#     return re.sub(r'\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b',
#                   lambda m: m.group(0).replace(' ', ''), text)


# def collapse_spaced_digits(text: str) -> str:
#     # collapse stray spaces inside numeric clusters (conservative heuristics)
#     text = re.sub(r'(?<!\d)(?:\d\s+){2,}\d(?!\d)', lambda m: re.sub(r'\s+', '', m.group(0)), text)
#     # cases like "1 49,748" -> "149,748"
#     text = re.sub(r'(?<!\d)(\d)\s+(\d{1,3}(?:,\d{2,3})+)', r'\1\2', text)
#     return text


# def restore_spaces_between_words_and_numbers(text: str) -> str:
#     # restores missing spaces between letters and digits while being conservative
#     text = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", text)
#     text = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
#     return text


# def remove_repeated_headers_footers(text: str) -> str:
#     """
#     Remove repeated short lines (likely header/footer) across pages.
#     """
#     lines = [ln.strip() for ln in re.split(r'[\r\n]+', text) if ln.strip()]
#     if not lines:
#         return text

#     from collections import Counter
#     cnt = Counter(lines)
#     repeated = {ln for ln, c in cnt.items() if c > 1 and len(ln) < 80}
#     if not repeated:
#         return text
#     filtered = [ln for ln in lines if ln not in repeated]
#     return "\n".join(filtered)


# def parse_number(value: Optional[str]) -> Optional[float]:
#     """
#     Safely parse numeric tokens into float.
#     Handles:
#     - Parentheses -> negative
#     - Indian/Western comma grouping
#     - Currency symbol ₹
#     Returns None on failure.
#     """
#     if value is None:
#         return None
#     s = str(value).strip()

#     if s.lower() in {"", "na", "n/a", "-"}:
#         return None

#     s = s.replace("₹", "").replace("Rs", "").replace("INR", "")
#     # parentheses -> negative
#     if s.startswith("(") and s.endswith(")"):
#         s = "-" + s[1:-1]

#     # remove any non-digit except dot and minus
#     s = re.sub(r"[^\d\.\-,()]", "", s)

#     # invalid if many parentheses/minuses
#     if s.count('(') > 1 or s.count(')') > 1 or s.count('-') > 1:
#         return None

#     # remove parentheses
#     s = s.replace('(', '').replace(')', '')

#     # guard against huge glued digits
#     s_no_commas = s.replace(',', '')
#     if len(re.sub(r'[^\d]', '', s_no_commas)) > 12:
#         return None

#     s = s_no_commas
#     if s in {"", "-", "."}:
#         return None
#     try:
#         return float(s)
#     except Exception:
#         return None


# def detect_document_scale(text: str) -> Tuple[float, str]:
#     """
#     Detect document scale/units.
#     Returns (scale_multiplier, unit_label).
#     We keep numbers in document units (crore -> 1.0).
#     """
#     lower = text.lower()
#     if "crore" in lower or "₹ crore" in lower or "(₹ crore)" in lower:
#         return 1.0, "crore"
#     if "lakh" in lower or "lac" in lower:
#         return 0.01, "lakh"
#     if "million" in lower:
#         return 0.1, "million"
#     if "billion" in lower:
#         return 100.0, "billion"
#     return 1.0, "units"




# # """
# # Responsibilities:
# # - Unicode normalization
# # - Collapse spaced letters & digits
# # - Remove headers/footers & boilerplate
# # - Normalize dates, currencies and numeric tokens
# # - Provide safe numeric parsing with scale inference (crore detection)
# # """
# # import re
# # import unicodedata
# # import logging
# # from typing import Optional, Tuple

# # logger=logging.getLogger(__name__)


# # def normalize_ocr_text(text: str) -> str:
# #     """
# #     Fix common OCR issues in financial PDFs:
# #     - Remove random extra spaces between characters
# #     - Merge split words like 'PROF IT' → 'PROFIT'
# #     - Normalize uppercase patterns
# #     """
# #     # remove multiple spaces and fix broken words
# #     text = re.sub(r'\s+', ' ', text)
# #     # merge all-caps broken words (e.g., "PROF IT" -> "PROFIT")
# #     text = re.sub(r'([A-Z])\s+([A-Z])', r'\1\2', text)
# #     # restore 'STATEMENTOF...' style headers
# #     text = re.sub(r'STATEMENTOF', 'STATEMENT OF ', text)
# #     text = re.sub(r'CONDENSEDCONSOLIDATED', 'CONDENSED CONSOLIDATED ', text)
# #     text = re.sub(r'INTERIM', 'INTERIM ', text)
# #     return text

# # def clean_text(raw_text: str)->str:
# #     #returns cleaned text (string)
# #     if not isinstance(raw_text, str):
# #         raise TypeError("clean_text expects a string")
    
# #     text=unicodedata.normalize("NFKC", raw_text) #normalize unicode (smart quotes, dashes etc)
# #     replacements={
# #         "“": '"', "”": '"', "‘": "'", "’": "'",
# #         "–": "-", "—": "-", "−": "-", "•": "-",
# #         "₹.": "₹", "Rs.": "₹", "Rs": "₹", "INR": "₹",
# #         "\x0c": " ",  #form-feed
# #     }
# #     for old, new in replacements.items():
# #         text=text.replace(old, new)

# #     text=re.sub(r"[\x00-\x1F\x7F]", "", text) #remove invisible/control characters and BOMs
# #     text=text.replace("\u00A0", " ")

# #     #remove common boilerplate artifacts (extendable)
# #     text=_remove_boilerplate(text)

# #     #collapse spaced letters (e.g. "T A T A" -> "TATA") and digits
# #     text=collapse_spaced_letters(text)
# #     text=collapse_spaced_digits(text)

# #     # Fix intra-word and numeric spacing
# #     text=restore_spaces_between_words_and_numbers(text)

# #     text=re.sub(
# #         r'(\d{1,3}(?:,\d{2,3})+)(?=(\d{1,3}(?:,\d{2,3})+))',
# #         r'\1 ',
# #         text
# #     )

# #     #normalize percent spacing (10 % -> 10%)
# #     text=re.sub(r"(\d)\s+%", r"\1%", text)
# #     text=re.sub(r"\b(Rs|RS|INR)\.?\b", "₹", text, flags=re.IGNORECASE) #normalize currency & numbers
# #     text=re.sub(r"₹\s+", "₹", text)

# #     #fix common OCR misreads (context-aware)
# #     #0<->O confusion
# #     text=re.sub(r"(?<=\b)[0O](?=[A-Za-z])", "O", text)
# #     #1<->l confusion
# #     text=re.sub(r"(?<=[A-Za-z])[1I](?=[a-z])", "l", text)
# #     #5<->S confusion
# #     text=re.sub(r"(?<=\b)5(?=[A-Za-z])", "S", text)

# #     #normalize dates to YYYY-MM-DD where reasonably possible
# #     text=re.sub(
# #         r"(\b\d{1,2})[/-](\d{1,2})[/-](\d{2,4}\b)",
# #         lambda m: f"{m.group(3).zfill(4)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}",
# #         text,
# #     )

# #     #remove repeated headers/footers at page boundaries
# #     text=remove_repeated_headers_footers(text)

# #     # Normalize spaces within each line but keep line breaks:
# #     # - This preserves paragraph / table / heading boundaries for parser heuristics.
# #     lines = text.splitlines()
# #     normalized_lines = []
# #     for ln in lines:
# #         ln = ln.strip()
# #         if not ln:
# #             continue
# #         # collapse multiple spaces/tabs inside a line but keep single space separation
# #         ln = re.sub(r'[ \t]+', ' ', ln)
# #         normalized_lines.append(ln)
# #     text = "\n".join(normalized_lines).strip()

# #     #safe fallback
# #     if not text.strip():
# #         logger.warning("clean_text returned empty; using raw_text fallback")
# #         text=raw_text.strip()

# #     return text

# # def _remove_boilerplate(text: str)->str:
# #     patterns=[
# #         r"Export to Sheets",
# #         r"Generated by .*",
# #         r"Page\s*\d+(\s*of\s*\d+)?",
# #         #generic "As per our report of even date attached" often repeats: remove lines
# #         r"As per our report of even date attached",
# #     ]
# #     for pat in patterns:
# #         text=re.sub(pat, " ", text, flags=re.IGNORECASE)
# #     return text

# # def collapse_spaced_letters(text: str)->str:
# #     #collapse sequences of single letters separated by spaces to a single token.
# #     #eg. "T A T A" -> "TATA" but "A B" (two-letter words) might be left alone only if length>=3.
# #     # Target groups of 3+ single letters
# #     return re.sub(r'\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b',
# #                   lambda m: m.group(0).replace(' ', ''), text)


# # def collapse_spaced_digits(text: str) -> str:
# #     #collapse stray spaces inside numeric clusters, e.g. "1 49,748" -> "149,748" and "1 2 3 4" -> "1234".
# #     #be conservative to not collapse textual segments.
# #     #collapse long digit groups where digits are single tokens separated by spaces (>=3 tokens)
# #     text=re.sub(r'(?<!\d)(?:\d\s+){2,}\d(?!\d)', lambda m: re.sub(r'\s+', '', m.group(0)), text)
# #     #also collapse cases like "1 49,748" -> "149,748" (single leading digit followed by a comma group)
# #     text=re.sub(r'(?<!\d)(\d)\s+(\d{1,3}(?:,\d{2,3})+)', r'\1\2', text)
# #     return text

# # def restore_spaces_between_words_and_numbers(text: str) -> str:
# #     """Restores missing spaces between letters and digits."""
# #     text=re.sub(r"([A-Za-z])([0-9])", r"\1 \2", text)
# #     text=re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
# #     return text


# # def remove_repeated_headers_footers(text: str) -> str:
# #     """
# #     Attempt to remove repeated header/footer lines across pages by:
# #     - Splitting by newline-like separators in original text
# #     - Counting repeated short lines and removing them
# #     (This is a heuristic)
# #     """
# #     lines=[ln.strip() for ln in re.split(r'[\r\n]+', text) if ln.strip()]
# #     if not lines:
# #         return text
    
# #     #determine candidate repeated lines
# #     from collections import Counter
# #     cnt=Counter(lines)
# #     repeated={ln for ln, c in cnt.items() if c>1 and len(ln)<80}
# #     if not repeated:
# #         return text
# #     filtered=[ln for ln in lines if ln not in repeated]
# #     return "\n".join(filtered)


# # def parse_number(value: Optional[str]) -> Optional[float]:
# #     """
# #     Safely parse numeric tokens into float or int (returns float for compatibility).
# #     Handles:
# #      - Parentheses for negatives: (1,234) -> -1234
# #      - Indian/Western comma grouping: 1,49,748 or 149,748
# #      - Currency symbol ₹
# #      - Strange spacing which should be cleaned already
# #     Returns None on parse failure.
# #     """
# #     if value is None:
# #         return None
# #     s=str(value).strip()

# #     #quick guard
# #     if s in {"", "na", "n/a", "-"}:
# #         return None

# #     #remove currency symbol & weird characters
# #     s=s.replace("₹", "").replace("Rs", "").replace("INR", "")
# #     #parentheses to negative
# #     if s.startswith("(") and s.endswith(")"):
# #         s= "-" + s[1:-1]

# #     #remove any whitespace inside number and non-digit except dot and minus
# #     s = re.sub(r"[^\d\.\-,()]", "", s)

# #     # basic sanity: if it still contains more than one parenthesis group or multiple minus signs it's invalid
# #     if s.count('(') > 1 or s.count(')') > 1 or s.count('-') > 1:
# #         return None

# #     # remove parentheses remaining (we handled sign earlier)
# #     s = s.replace('(', '').replace(')', '')

# #     # if there are multiple comma-separated groups glued without space and with no logical grouping,
# #     # we still try to parse by removing commas. A final guard: if after removing commas result length > 12 digits,
# #     # it's likely concatenation — return None.
# #     s_no_commas = s.replace(',', '')
# #     if len(re.sub(r'[^\d]', '', s_no_commas)) > 12:
# #         # suspiciously large contiguous digits -> likely parsing error
# #         return None

# #     s = s_no_commas

# #     if s in {"", "-", "."}:
# #         return None
# #     try:
# #         return float(s)
# #     except Exception:
# #         return None


# # def detect_document_scale(text: str) -> Tuple[float, str]:
# #     """
# #     Detect units such as '(` crore)' or '(` million)'. Returns (scale, unit_label).
# #     For 'crore' -> scale=1 (we assume numbers already in crores), but you might choose scale=1e7 if you want INR.
# #     We return scale multiplier for the parsed numeric values. For now we use:
# #       - 'crore' -> scale=1 (document numbers are in crore)
# #       - 'million' -> scale=1e-2 if converting to crore (user choice)
# #     Keep it simple: return ('crore', 1.0) if found, otherwise ('units', 1.0)
# #     """
# #     lower=text.lower()
# #     if "crore" in lower:
# #         return 1.0, "crore"
# #     if "lakh" in lower:
# #         #if numbers printed in lakh, converting to crore: 1 lakh = 0.01 crore
# #         return 0.01, "lakh"
# #     return 1.0, "units"