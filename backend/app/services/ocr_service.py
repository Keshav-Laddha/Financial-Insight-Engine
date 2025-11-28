# import os
# import re
# from typing import Any, Dict, List

# from app.services.preprocessing_service import detect_scale_from_text

# # Try to import optional libraries
# try:
#     import pdfplumber
# except ImportError:
#     pdfplumber = None

# try:
#     from PIL import Image
#     import pytesseract
# except ImportError:
#     pytesseract = None
#     Image = None

# try:
#     import openpyxl
# except ImportError:
#     openpyxl = None

# def _clean_text_basic(text: str) -> str:
#     """
#     Basic text cleaning for OCR output.
#     """
#     if not isinstance(text, str):
#         return ""
#     lines = [ln.rstrip() for ln in text.splitlines()]
#     cleaned = "\n".join(lines)
#     cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
#     return cleaned.strip()

# def extract_text_and_tables(file_path: str) -> Dict[str, Any]:
#     """
#     Extract text and tables from a financial document.
#     Supports PDFs, images, Excel, and plain text.
#     """
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"File not found: {file_path}")
#     ext = os.path.splitext(file_path)[1].lower()
#     raw_text = ""
#     tables: List[List[List[str]]] = []

#     if ext == ".pdf":
#         if not pdfplumber:
#             raise RuntimeError("pdfplumber is not installed.")
#         with pdfplumber.open(file_path) as pdf:
#             for page in pdf.pages:
#                 try:
#                     page_text = page.extract_text() or ""
#                 except Exception:
#                     page_text = ""
#                 raw_text += page_text + "\n\n"
#                 # Extract tables from PDF page
#                 try:
#                     extracted_tables = page.extract_tables()
#                 except Exception:
#                     extracted_tables = []
#                 for table in extracted_tables:
#                     norm_table = []
#                     for row in table:
#                         norm_row = ["" if cell is None else str(cell).strip() for cell in row]
#                         norm_table.append(norm_row)
#                     if any(any(cell for cell in r) for r in norm_table):
#                         tables.append(norm_table)
#         # Fallback OCR if no text was found (scanned PDF)
#         if not raw_text.strip():
#             if not (pytesseract and Image):
#                 raise RuntimeError("No text found in PDF and OCR fallback not available.")
#             from pdf2image import convert_from_path
#             images = convert_from_path(file_path, dpi=300)
#             for image in images:
#                 text = pytesseract.image_to_string(image)
#                 raw_text += text + "\n\n"

#     elif ext in [".jpg", ".jpeg", ".png"]:
#         if not (pytesseract and Image):
#             raise RuntimeError("Pillow/pytesseract is not installed.")
#         image = Image.open(file_path)
#         raw_text = pytesseract.image_to_string(image)

#     elif ext in [".xlsx", ".xls"]:
#         if not openpyxl:
#             raise RuntimeError("openpyxl is not installed.")
#         wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
#         sheet = wb.active
#         table: List[List[str]] = []
#         raw_lines: List[str] = []
#         for row in sheet.iter_rows(values_only=True):
#             row_vals = []
#             any_val = False
#             for cell in row:
#                 if cell is None:
#                     row_vals.append("")
#                 else:
#                     row_vals.append(str(cell))
#                     any_val = True
#             if any_val:
#                 table.append(row_vals)
#                 raw_lines.append(" ".join(str(cell) for cell in row if cell is not None))
#         raw_text = "\n".join(raw_lines)
#         if table:
#             tables.append(table)
#     else:
#         # Try reading as plain text
#         try:
#             with open(file_path, "r", encoding="utf-8") as f:
#                 raw_text = f.read()
#         except Exception:
#             raise RuntimeError(f"Unsupported file format: {ext}")

#     cleaned = _clean_text_basic(raw_text)
#     scale = detect_scale_from_text(cleaned)
#     return {"raw_text": raw_text, "cleaned_text": cleaned, "tables": tables, "scale_detected": scale}


"""
Robust OCR service.

Responsibilities:
- Load PDF (uses pdfplumber by default)
- Find TOC-like candidates (first pages)
- Map logical -> physical pages using heading search
- Extract page text and structured tables (via pdfplumber.extract_tables)
- Emit detailed logs and structured errors

If your project uses a different OCR pipeline (Tesseract boxes, custom detector),
adapt extract_tables / extract_pages_text to return the same structures:
- pages_text: Dict[int, str]  (page number -> extracted text)
- tables: List[Dict[str, Any]] where each dict is { "page": int, "table": List[List] }

Requires: pdfplumber
"""
import logging
import re
from typing import List, Dict, Any, Optional
import pdfplumber

logger = logging.getLogger("app.services.ocr_service")


class OcrServiceError(Exception):
    pass


class OcrService:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._pdf: Optional[pdfplumber.PDF] = None

    def open(self):
        try:
            self._pdf = pdfplumber.open(self.pdf_path)
            logger.info(f"PDF loaded: {len(self._pdf.pages)} pages")
        except Exception as e:
            logger.exception("Failed to open PDF file")
            raise OcrServiceError("pdf_open_failed") from e

    def close(self):
        if self._pdf:
            try:
                self._pdf.close()
            except Exception:
                logger.debug("Error closing PDF, ignoring")

    def _find_toc(self, probe_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Scan the first `probe_pages` pages for candidate TOC lines.
        Example TOC line: 'SUMMARY OF FINANCIAL INFORMATION ...................................... 99'
        Returns list of dicts with 'line', 'page_index', 'captured' (page number if found).
        """
        TOC_PATTERNS = [
            r"summary of financial information",
            r"summary financial information",
            r"summary of restated financial information",
            r"summary restated financial information",
            r"summary of consolidated financial information",
            r"summary consolidated financial information",
            r"restated consolidated financial information",
            r"summary of restated consolidated financial information",
            r"summary restated consolidated financial information",
        ]

        toc = []
        try:
            for i in range(min(probe_pages, len(self._pdf.pages))):
                text = (self._pdf.pages[i].extract_text() or "")
                for line in text.splitlines():
                    # if re.search(r"summary of financial information", line, re.I):
                    if any(re.search(p, line, re.I) for p in TOC_PATTERNS):
                        m = re.search(r"(\d{1,4})\s*$", line)
                        toc.append({"line": line.strip(), "page_index": i, "captured": m.group(1) if m else None})
            logger.debug(f"TOC candidates: {len(toc)}")
        except Exception:
            logger.exception("Error while searching TOC pages")
        return toc



    def map_logical_to_physical(self, logical_start: int, toc_page_index: Optional[int] = None) -> Dict[str, int]:

        HEADING_KEYWORDS = [
            "summary of financial information",
            "summary financial information",
            "summary of restated financial information",
            "summary restated financial information",
            "summary of consolidated financial information",
            "summary consolidated financial information",
            "summary of restated consolidated financial information",
            "summary restated consolidated financial information",
            "summary of assets and liabilities",
            "summary balance sheet",
            "summary of profit and loss",
            "summary of cash flows",
            "summary restated balance sheet",
            "summary restated statement of profit and loss",
            "summary restated statement of cash flows",
        ]

        def contains_heading(text: str) -> bool:
            t = (text or "").lower()
            return any(k in t for k in HEADING_KEYWORDS)

        if self._pdf is None:
            raise OcrServiceError("pdf_not_open")

        total_pages = len(self._pdf.pages)

        mapped = {
            "logical_start": int(logical_start),
            "toc_page": int(toc_page_index) if toc_page_index is not None else 0,
            "mapped_physical_start": max(1, int(logical_start)),
            "physical_start": max(1, int(logical_start)),
            "physical_end": min(total_pages, int(logical_start) + 11),
        }

        # define BEFORE loop (FIX)
        start_idx = max(0, mapped["mapped_physical_start"] - 1)
        end_idx = min(total_pages, start_idx + 40)

        found_page = None

        for p in range(start_idx, end_idx):
            try:
                text = self._pdf.pages[p].extract_text() or ""
                if contains_heading(text):
                    found_page = p + 1
                    break
            except Exception:
                logger.exception(f"Error extracting text from page {p+1}")

        if found_page:
            mapped["physical_start"] = found_page
            mapped["physical_end"] = min(total_pages, found_page + 11)
            logger.info(
                f"Found summary heading at physical page {found_page} "
                f"(delta={found_page - mapped['mapped_physical_start']})"
            )
        else:
            logger.warning("Could not find heading text; using fallback range.")

        return mapped


    def extract_pages_text(self, start: int, end: int) -> Dict[int, str]:
        """
        Extract text for pages in [start, end] inclusive.
        Returns dict: page_number -> text
        """
        if self._pdf is None:
            raise OcrServiceError("pdf_not_open")
        out: Dict[int, str] = {}
        total = len(self._pdf.pages)
        s = max(1, start)
        e = min(total, end)
        for p in range(s - 1, e):
            try:
                text = self._pdf.pages[p].extract_text() or ""
                out[p + 1] = text
                logger.debug(f"Positional fallback extracted {len(text.splitlines())} rows on page {p+1}")
            except Exception:
                logger.exception(f"Failed to extract text from page {p+1}")
                out[p + 1] = ""
        return out

    def extract_tables(self, start: int, end: int) -> List[Dict[str, Any]]:
        """
        Use pdfplumber's extract_tables to obtain structured tables where available.
        Returns list of dicts: { "page": int, "table": List[List] }
        """
        if self._pdf is None:
            raise OcrServiceError("pdf_not_open")
        tables: List[Dict[str, Any]] = []
        total = len(self._pdf.pages)
        s = max(1, start)
        e = min(total, end)
        for p in range(s - 1, e):
            try:
                page = self._pdf.pages[p]
                raw_tables = page.extract_tables() or []
                if raw_tables:
                    for t in raw_tables:
                        tables.append({"page": p + 1, "table": t})
                else:
                    logger.debug(f"No structured tables on page {p+1}")
            except Exception:
                logger.exception(f"Error extracting tables from page {p+1}")
        logger.info(f"Extraction results: tables={len(tables)}, summary_range={{'physical_start':{start}, 'physical_end':{end}}}")
        return tables