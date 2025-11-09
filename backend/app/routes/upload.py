from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any
from app.services.ocr_service import extract_text

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png"}


@router.post("/", response_class=JSONResponse, status_code=201)
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Secure file upload endpoint.
    Accepts files and stores them in a controlled directory.
    Performs OCR extraction using extract_text.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    try:
        extracted_data = extract_text(str(file_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {repr(e)}"
        )

    cleaned = extracted_data.get("cleaned_text", "")
    message = "File uploaded successfully"
    if not cleaned.strip():
        message = "File uploaded successfully but extraction failed."

    return {
        "message": message,
        "file_id": file_id,
        "stored_as": safe_filename,
        "raw_text": extracted_data.get("raw_text", "")[:10000],
        "cleaned_text": extracted_data.get("cleaned_text", "")[:10000],
        "tables": extracted_data.get("tables", [])
    }


# from fastapi import APIRouter, UploadFile, File, HTTPException, status
# from fastapi.responses import JSONResponse
# import os
# import uuid
# import shutil
# from pathlib import Path
# from typing import Dict, Any
# from app.services.ocr_service import extract_text

# router=APIRouter() #router object

# UPLOAD_DIR=Path("uploads") #creates a directory uploads where all the uploaded files are stored
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ALLOWED_EXTENSIONS={".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png"}

# #MAX_FILE_SIZE=20*1024*1024 #20 MB

# @router.post("/", response_class=JSONResponse, status_code=201)
# async def upload_file(file: UploadFile=File(...)) -> Dict[str, Any]:
#     """
#     Secure file upload endpoint.
#     Accepts files and stores them in a controlled directory.
#     Performs OCR extraction using extract_text.
#     """

#     file_ext=Path(file.filename).suffix.lower()
#     if file_ext not in ALLOWED_EXTENSIONS:
#         raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

#     #generate random file name to avoid collisions
#     file_id=str(uuid.uuid4()) #using uuid4 to avoid collisions and prevent path traversal attacks as we should never use fil.filenames directly to store files
#     safe_filename=f"{file_id}{file_ext}"
#     file_path=UPLOAD_DIR / safe_filename

#     #contents=await file.read()

#     #write to disk/ save the uploaded file
#     try:
#         with open(file_path, "wb") as f:
#             shutil.copyfileobj(file.file, f)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
#     try:
#         extracted_data=extract_text(str(file_path))
#     except HTTPException as e:
#         #forward handled HTTP errors (like unsupported format)
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Text extraction failed: {repr(e)}" #{type(e).__name__}"
#         )
#     cleaned=extracted_data.get("cleaned_text", "")
#     message="File uploaded successfully"
#     if not cleaned.strip():
#         message="File uploaded successfully but extraction failed."
#     #respond with metadata
#     return {
#         "message": message,
#         "file_id": file_id,
#         "stored_as": safe_filename,
#         "raw_text": extracted_data.get("raw_text", "")[:10000],
#         "cleaned_text": extracted_data.get("cleaned_text", "")[:10000],
#         "tables": extracted_data.get("tables", [])
#     }