import os
import re

# Regex to split on spaces, underscores, or hyphens
DELIMITER_PATTERN = re.compile(r"[\s_\-]+")


def extract_company_name(filename: str) -> str:
    """
    Infer a company name from a filename using simple heuristics.

    Steps:
      1. Strip directory information and extension.
      2. Split on whitespace, underscores, or hyphens.
      3. Return the first non-empty token, uppercased.
         - Ignores 32-char hex strings (UUIDs) if present.
      4. Fallback to 'UNKNOWN' when no token is found.
    """

    if not filename:
        return "UNKNOWN"

    base = os.path.splitext(os.path.basename(filename))[0]
    if not base:
        return "UNKNOWN"

    tokens = DELIMITER_PATTERN.split(base)
    for token in tokens:
        cleaned = token.strip()
        if not cleaned:
            continue

        # Skip UUID-like tokens
        if re.fullmatch(r"[0-9a-f]{32}", cleaned.lower()):
            continue

        return cleaned.upper()

    # If every token was empty/uuid, fall back to the original base
    return base.upper()

