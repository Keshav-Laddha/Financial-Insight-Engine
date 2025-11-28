# app/services/mda_extractor.py

import pdfplumber

PAGE_OFFSET = 2   # RHPs usually start page numbering after 2 pages

# full text between start_page and end_page
def extract_mda_text(pdf_path: str, start_page: int, end_page: int) -> str:
    extracted = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        start_i = max(start_page - 1 + PAGE_OFFSET, 0)
        end_i = min(end_page - 1 + PAGE_OFFSET, total_pages - 1)

        for i in range(start_i, end_i + 1):
            try:
                raw = pdf.pages[i].extract_text() or ""
                clean = "\n".join(line.strip() for line in raw.split("\n"))
                extracted.append(clean)
            except:
                continue

    return "\n\n".join(extracted)