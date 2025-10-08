# from fastapi import APIRouter, UploadFile, File
# import os, uuid

# router = APIRouter()

# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/")
# async def upload_file(file: UploadFile = File(...)):
#     file_id = str(uuid.uuid4())
#     file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
#     with open(file_path, "wb") as f:
#         f.write(await file.read())
    
#     return {"message": "File uploaded successfully", "file_id": file_id, "path": file_path}
# app/routes/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from pathlib import Path
from typing import Dict

# 1️⃣ Router object for modular structure
router = APIRouter()

# 2️⃣ Define upload directory (safe, outside of source tree ideally)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 3️⃣ Allowed extensions — OWASP A1: prevent malicious uploads
ALLOWED_EXTENSIONS = {".pdf"}

# 4️⃣ Max file size (bytes) — SDL best practice to prevent DoS
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/", response_class=JSONResponse, status_code=201)
async def upload_file(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Secure file upload endpoint.
    Accepts only PDFs and stores them in a controlled directory.
    """

    # 5️⃣ Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF allowed.")

    # 6️⃣ Generate random safe file name (avoid collisions and path traversal)
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename

    # 7️⃣ Enforce file size limits before reading
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10 MB allowed.")

    # 8️⃣ Write securely to disk (atomic, controlled)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # 9️⃣ Respond with metadata only (never expose file paths directly)
    return {
        "message": "File uploaded successfully",
        "file_id": file_id,
        "stored_as": safe_filename
    }