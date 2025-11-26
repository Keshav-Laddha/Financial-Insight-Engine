# import os
# from fastapi import APIRouter, HTTPException
# import json

# router = APIRouter()

# METADATA_DIR = "uploaded_files"
# METADATA_FILE = os.path.join(METADATA_DIR, "file_metadata.json")

# # Ensure folder exists
# os.makedirs(METADATA_DIR, exist_ok=True)

# # Ensure file exists
# if not os.path.exists(METADATA_FILE):
#     with open(METADATA_FILE, "w") as f:
#         f.write("[]")     # empty list to store metadata


# @router.get("/")
# def list_files():
#     """
#     Return all uploaded file metadata without reading any PDFs.
#     100% safe and fast.
#     """
#     try:
#         with open(METADATA_FILE, "r") as f:
#             data = json.load(f)
#         return data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to load files: {e}")
    
# @router.get("/view/{file_id}")
# def view_file(file_id: str):
#     filepath = os.path.join(UPLOAD_DIR, file_id)
#     if not os.path.exists(filepath):
#         raise HTTPException(status_code=404, detail="File not found.")

#     return FileResponse(filepath, media_type="application/pdf")

# @router.post("/save")
# def save_file_metadata(info: dict):
#     try:
#         with open(METADATA_FILE, "r") as f:
#             data = json.load(f)

#         data.insert(0, info)

#         with open(METADATA_FILE, "w") as f:
#             json.dump(data, f, indent=2)

#         return {"status": "ok"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to save metadata: {e}")


# app/routes/files.py
import os
import json
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # project_root/app/routes -> go up
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
METADATA_FILE = os.path.join(UPLOAD_DIR, "file_metadata.json")

# Ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _load_metadata() -> List[Dict]:
    """Return list of metadata entries."""
    if not os.path.exists(METADATA_FILE):
        return []
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.loads(f.read() or "[]")
            if isinstance(data, list):
                return data
            # attempt to coerce to list
            return list(data)
    except Exception:
        # if corrupted, try to recover by returning empty list (don't crash)
        return []

def _save_metadata(meta_list: List[Dict]) -> None:
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

def _find_by_id(meta_list: List[Dict], file_id: str):
    for m in meta_list:
        if m.get("id") == file_id or m.get("stored_as") == file_id:
            return m
    return None

@router.get("/", response_model=List[Dict])
async def list_files():
    """
    Return list of file metadata entries saved on server.
    """
    meta = _load_metadata()
    return meta

@router.post("/save", status_code=201)
async def save_file_metadata(info: Dict):
    """
    Save file metadata entry sent from frontend after upload.
    If an entry with same id/stored_as exists, update it.
    """
    if not info or not info.get("id"):
        raise HTTPException(status_code=400, detail="Invalid metadata")

    meta = _load_metadata()
    existing = _find_by_id(meta, info.get("id")) or _find_by_id(meta, info.get("stored_as"))
    if existing:
        # update existing in-place
        existing.update(info)
    else:
        meta.insert(0, info)  # newest first
    _save_metadata(meta)
    return {"message": "Metadata saved", "entry": info}

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete metadata + file if present.
    file_id may be the metadata id or stored_as filename.
    """
    meta = _load_metadata()
    entry = _find_by_id(meta, file_id)
    if not entry:
        return {"message": "File not found", "deleted": False}

    # remove file on disk if stored_as present
    stored_as = entry.get("stored_as")
    if stored_as:
        file_path = os.path.join(UPLOAD_DIR, stored_as)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # log but continue
            print("Warning: failed to remove file on disk:", e)

    # remove metadata entry
    meta = [m for m in meta if not (_find_by_id([m], file_id))]
    _save_metadata(meta)
    return {"message": "Deleted", "deleted": True}

@router.get("/download/{stored_as}")
async def download_file(stored_as: str):
    """
    Serve a stored file by filename (stored_as).
    Make sure the stored_as exists under uploaded_files/
    """
    # sanitize path - disallow paths that go outside
    if os.path.isabs(stored_as) or ".." in stored_as:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(UPLOAD_DIR, stored_as)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # FastAPI/Starlette will stream file
    return FileResponse(path=file_path, filename=stored_as)

# optionally expose endpoint to fetch single metadata entry
@router.get("/meta/{file_id}")
async def get_metadata(file_id: str):
    meta = _load_metadata()
    entry = _find_by_id(meta, file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return entry