from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from pathlib import Path
from typing import Dict
from app.services.ocr_service import extract_text

router=APIRouter() #router object

UPLOAD_DIR=Path("uploads") #creates a directory uploads where all the uploaded files are stored
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS={".pdf"}

MAX_FILE_SIZE=20*1024*1024 #20 MB

@router.post("/", response_class=JSONResponse, status_code=201)
async def upload_file(file: UploadFile=File(...)) -> Dict[str, str]:
    """
    Secure file upload endpoint.
    Accepts only PDFs and stores them in a controlled directory.
    """

    file_ext=Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF allowed.")

    #generate random file name to avoid collisions
    file_id=str(uuid.uuid4()) #using uuid4 to avoid collisions and prevent path traversal attacks as we should never use fil.filenames directly to store files
    safe_filename=f"{file_id}{file_ext}"
    file_path=UPLOAD_DIR / safe_filename

    contents=await file.read()
    if len(contents)>MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 20 MB allowed.")
    
    #write to disk
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    try:
        extracted_text = extract_text(str(file_path))
    except HTTPException as e:
        #forward handled HTTP errors (like unsupported format)
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {type(e).__name__}"
        )
    
    #respond with metadata
    return {
        "message": "File uploaded successfully",
        "file_id": file_id,
        "stored_as": safe_filename,
        "extracted_text": extracted_text[:10000]  # cap to prevent oversized responses
    }