# app/services/toc_service.py

import pdfplumber
import re


# Extract TOC text from first 20 pages
def extract_toc_text(pdf_path: str) -> str:
    toc_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for i in range(min(20, len(pdf.pages))):
            try:
                text = pdf.pages[i].extract_text() or ""
                if text.strip():
                    toc_text.append(text)
            except:
                continue

    return "\n".join(toc_text)


# Detect MDA start & end page from TOC text
def detect_mda_page_range(toc_text: str):
    text = toc_text.lower().replace("’", "'")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    keywords = [
        "management's discussion and analysis of financial condition and result of operations",
        "management's discussion and analysis",
        "management discussion and analysis",
        "discussion and analysis of financial condition",
        "analysis of financial condition",
        "financial condition and result of operations",
        "management discussion",
        "md&a",
        "mda",
    ]

    mda_start_page = None
    mda_line_index = None

    # --- FIND START PAGE ---
    for i, line in enumerate(lines):
        if not any(k in line for k in keywords):
            continue

        # same-line page number
        match_same = re.search(r"(\d{1,4})\s*$", line)
        if match_same:
            mda_start_page = int(match_same.group(1))
            mda_line_index = i
            break

        # next-line page number
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            match_next = re.search(r"(\d{1,4})\s*$", next_line)
            if match_next:
                mda_start_page = int(match_next.group(1))
                mda_line_index = i + 1
                break

    if not mda_start_page:
        return None, None

    # --- FIND END PAGE ---
    mda_end_page = None
    for j in range(mda_line_index + 1, len(lines)):
        match = re.search(r"(\d{1,4})\s*$", lines[j])
        if match:
            mda_end_page = int(match.group(1))
            break

    if not mda_end_page:
        mda_end_page = mda_start_page + 20

    return mda_start_page, mda_end_page