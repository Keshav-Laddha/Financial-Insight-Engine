from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.services.ocr_service import extract_text_and_tables
from app.services.parser_service import parse_financial_document
from app.services.financial_analysis_service import compute_kpis
from app.services.trend_analysis_service import compute_trends

router = APIRouter()

UPLOAD_DIR = Path("uploads")

@router.get("/{file_id}")
async def analyze_file_compat(file_id: str):
    """
    Legacy GET route to support frontend using /analyze/{file_id}
    """
    # Reconstruct file path
    file_path = UPLOAD_DIR / file_id

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        extracted = extract_text_and_tables(str(file_path))
        cleaned = extracted.get("cleaned_text", "")
        tables = extracted.get("tables", [])
        scale = extracted.get("scale_detected", 1)

        parsed = parse_financial_document(cleaned, tables, scale)
        kpis = compute_kpis(parsed)
        trends = compute_trends(parsed)

        return {
            "balance_sheet": parsed.get("sections", {}).get("balance_sheet", []),
            "pnl": parsed.get("sections", {}).get("pnl", {}),
            "cash_flow": parsed.get("sections", {}).get("cash_flow", {}),
            "kpis": kpis,
            "trends": trends
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# from fastapi import APIRouter, HTTPException, status
# from pathlib import Path
# from app.services.ocr_service import extract_text_and_tables
# from app.services.parser_service import parse_financial_document
# from app.services.financial_analysis_service import compute_kpis

# router = APIRouter()

# UPLOAD_DIR = Path("uploads")


# @router.get("/{file_id}", tags=["Analysis"])
# async def extract_text_endpoint(file_id: str):
#     """
#     Given a previously uploaded file ID, run extraction -> parsing -> KPI computation.
#     Returns cleaned_text, parsed_data and kpis.
#     """
#     file_path = next(UPLOAD_DIR.glob(f"{file_id}.*"), None)

#     if not file_path or not file_path.exists():
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="File not found."
#         )

#     try:
#         extracted = extract_text_and_tables(str(file_path))
#         cleaned = extracted.get("cleaned_text", "")
#         tables = extracted.get("tables", [])
#         parsed_data = parse_financial_document(cleaned, tables)
#         kpis = compute_kpis(parsed_data)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Processing failed: {repr(e)}")

#     response = {
#         "file_id": file_id,
#         "cleaned_text": cleaned[:10000],
#         "parsed_data": parsed_data,
#         "kpis": kpis
#     }
#     if parsed_data.get("validation_warning"):
#         response["validation_warning"] = parsed_data["validation_warning"]
#     return response