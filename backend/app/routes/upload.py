import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a financial document (PDF, image, Excel, etc.).
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a filename.")
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = {".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".xls", ".txt"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported file type: {ext}")

    # Save file with a unique name to avoid collisions
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")

    return {
        "message": "File uploaded successfully.",
        "file_id": unique_name,
        "file_path": file_path
    }



# from fastapi import APIRouter, UploadFile, File, HTTPException, status
# from fastapi.responses import JSONResponse
# import os
# import uuid
# import shutil
# from pathlib import Path
# from typing import Dict, Any
# from app.services.ocr_service import extract_text_and_tables

# router = APIRouter()

# UPLOAD_DIR = Path("uploads")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png"}


# @router.post("/", response_class=JSONResponse, status_code=201)
# async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
#     """
#     Secure file upload endpoint.
#     Accepts files and stores them in a controlled directory.
#     Performs OCR extraction using extract_text.
#     """
#     file_ext = Path(file.filename).suffix.lower()
#     if file_ext not in ALLOWED_EXTENSIONS:
#         raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

#     file_id = str(uuid.uuid4())
#     safe_filename = f"{file_id}{file_ext}"
#     file_path = UPLOAD_DIR / safe_filename

#     try:
#         with open(file_path, "wb") as f:
#             shutil.copyfileobj(file.file, f)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

#     try:
#         extracted_data = extract_text_and_tables(str(file_path))
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Text extraction failed: {repr(e)}"
#         )

#     cleaned = extracted_data.get("cleaned_text", "")
#     message = "File uploaded successfully"
#     if not cleaned.strip():
#         message = "File uploaded successfully but extraction failed."

#     return {
#         "message": message,
#         "file_id": file_id,
#         "stored_as": safe_filename,
#         "raw_text": extracted_data.get("raw_text", "")[:10000],
#         "cleaned_text": extracted_data.get("cleaned_text", "")[:10000],
#         "tables": extracted_data.get("tables", [])
#     }