# app/routes/analysis.py
import os
import tempfile
import logging
from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.ocr_service import OcrService, OcrServiceError
from app.services.parser_service import ParserService

router = APIRouter()
logger = logging.getLogger("app.routes.analysis")

# Shared absolute uploads directory (same logic as upload.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "uploads"))
os.makedirs(STORAGE_DIR, exist_ok=True)


# POST /analyze  -> upload + analyze immediately
@router.post("/", tags=["Analysis"])
async def analyze_pdf(
    file: UploadFile = File(...),
    prefer_label_column: bool = Query(True)
) -> Any:
    """
    Upload a PDF and analyze immediately. Returns same JSON as GET /analyze/{file_id}.
    """
    # Save to temp file and analyze
    suffix = ".pdf" if (file.filename or "").lower().endswith(".pdf") else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp.name
    try:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()
        logger.info("Temporary uploaded file saved: %s", tmp_path)

        response = _run_analysis(tmp_path, prefer_label_column)
        return response

    except Exception:
        logger.exception("Failed during POST /analyze")
        raise HTTPException(status_code=500, detail="internal_error")

    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.debug("Removed temporary file: %s", tmp_path)
        except Exception:
            logger.debug("Temp file cleanup failed (ignored).")


# GET /analyze/{file_id} -> analyze previously uploaded file
@router.get("/{file_id}", tags=["Analysis"])
def analyze_stored(
    file_id: str,
    prefer_label_column: bool = Query(True)
) -> Any:
    """
    Analyze a previously uploaded file by file_id (returned from /upload).
    """
    file_path = os.path.join(STORAGE_DIR, file_id)
    if not os.path.exists(file_path):
        logger.warning("Requested file not found: %s", file_path)
        raise HTTPException(status_code=404, detail="file_not_found")

    logger.info("Analyzing stored file: %s", file_path)
    try:
        return _run_analysis(file_path, prefer_label_column)
    except Exception:
        logger.exception("Failed during GET /analyze/{file_id}")
        raise HTTPException(status_code=500, detail="internal_error")


# Debug helper: list stored uploads (secure enough for local dev)
@router.get("/debug/uploads", tags=["Debug"])
def debug_list_uploads():
    try:
        files = sorted(os.listdir(STORAGE_DIR))
        return {"storage_dir": STORAGE_DIR, "files": files}
    except Exception:
        logger.exception("Failed to list uploads directory")
        raise HTTPException(status_code=500, detail="could_not_list_uploads")

def extract_important_kpis(parsed):
    bs = parsed.get("balance_sheet", [])
    pnl = parsed.get("pnl", [])
    cf = parsed.get("cash_flow", [])

    def find(label_keywords, section):
        for row in section:
            lbl = (row.get("label") or "").lower()
            if any(k in lbl for k in label_keywords):
                vals = row.get("values", {})
                nums = [v for v in vals.values() if isinstance(v, (int, float))]
                return nums[0] if nums else None
        return None

    return {
        "total_assets": find(["total assets", "assets", "t otal assets"], bs),
        "total_equity": find(["equity", "shareholder", "total equity", "total equities"], bs),
        "total_liabilities": find(["liabilities", "total liabilities"], bs),
        "revenue": find(["revenue", "income", "total revenue", "t otal revenue"], pnl),
        "net_profit": find(["profit", "loss"], pnl),
        "operating_cash_flow": find(["operating"], cf),
        "net_cash_flow": find(["net cash"], cf),
    }

# Shared pipeline
def _run_analysis(pdf_path: str, prefer_label_column: bool):
    """
    Runs OCR -> table extraction -> parser and returns JSONResponse.
    """
    ocr = None
    try:
        ocr = OcrService(pdf_path)
        ocr.open()

        toc_candidates = ocr._find_toc()
        logical_start = 99
        if toc_candidates and toc_candidates[0].get("captured"):
            try:
                logical_start = int(toc_candidates[0]["captured"])
            except Exception:
                logger.debug("Could not parse TOC captured page; using default 99")

        mapped = ocr.map_logical_to_physical(logical_start)
        pages_text = ocr.extract_pages_text(mapped["physical_start"], mapped["physical_end"])
        tables = ocr.extract_tables(mapped["physical_start"], mapped["physical_end"])

        parser = ParserService(prefer_first_column_labels=prefer_label_column)
        result = parser.parse(tables, pages_text)

        logger.info(
            "Parsed sections: balance_sheet=%d, pnl=%d, cash_flow=%d, flags=%d",
            len(result.get("balance_sheet", [])),
            len(result.get("pnl", [])),
            len(result.get("cash_flow", [])),
            len(result.get("flags", [])),
        )

        kpis = parser._compute_important_kpis(result)
        result["important_kpis"] = kpis


        return JSONResponse(content=result)

    except OcrServiceError as e:
        logger.exception("OCR service failure")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception:
        logger.exception("Unhandled exception in analysis pipeline")
        raise HTTPException(status_code=500, detail="analysis_failed")

    finally:
        if ocr:
            try:
                ocr.close()
            except Exception:
                logger.debug("Failed to close OCR service (ignored).")