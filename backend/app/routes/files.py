"""
File management routes using SQLite database
Stores only metadata, not physical files
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, FileMetadata
from app.schemas.file_schema import FileMetadataSchema, FileMetadataCreate

router = APIRouter()


@router.get("/", response_model=List[FileMetadataSchema])
async def list_files(db: Session = Depends(get_db)):
    """
    Return list of all uploaded files from database.
    """
    files = db.query(FileMetadata).order_by(FileMetadata.uploaded_at.desc()).all()
    return files


@router.post("/save", status_code=201, response_model=FileMetadataSchema)
async def save_file_metadata(info: FileMetadataCreate, db: Session = Depends(get_db)):
    """
    Save file metadata to database after upload.
    If entry with same id exists, update it.
    """
    if not info.id:
        raise HTTPException(status_code=400, detail="Invalid metadata: id required")

    # Check if file already exists
    existing = db.query(FileMetadata).filter(FileMetadata.id == info.id).first()
    
    if existing:
        # Update existing entry
        existing.stored_as = info.stored_as
        existing.name = info.name
        existing.size = info.size
        existing.type = info.type
        existing.company = info.company
        existing.uploaded_at = datetime.fromisoformat(info.uploadedAt.replace('Z', '+00:00')) if info.uploadedAt else datetime.utcnow()
    else:
        # Create new entry
        new_file = FileMetadata(
            id=info.id,
            stored_as=info.stored_as,
            name=info.name,
            uploaded_at=datetime.fromisoformat(info.uploadedAt.replace('Z', '+00:00')) if info.uploadedAt else datetime.utcnow(),
            size=info.size,
            type=info.type,
            company=info.company
        )
        db.add(new_file)
    
    db.commit()
    db.refresh(existing if existing else new_file)
    
    return existing if existing else new_file


@router.delete("/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """
    Delete file metadata from database.
    """
    file_entry = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    if not file_entry:
        return {"message": "File not found", "deleted": False}
    
    # Delete from database only (no physical files stored)
    db.delete(file_entry)
    db.commit()
    
    return {"message": "Deleted successfully", "deleted": True}


@router.get("/download/{stored_as}")
async def download_file(stored_as: str, db: Session = Depends(get_db)):
    """
    Download endpoint - files are not stored, so this returns metadata only.
    """
    # Verify file exists in database
    file_entry = db.query(FileMetadata).filter(FileMetadata.stored_as == stored_as).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found in database")
    
    # Return metadata since physical file is not stored
    raise HTTPException(status_code=410, detail="File content not stored - only metadata available")


@router.get("/meta/{file_id}", response_model=FileMetadataSchema)
async def get_metadata(file_id: str, db: Session = Depends(get_db)):
    """
    Get metadata for a specific file by ID.
    """
    file_entry = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    if not file_entry:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    return file_entry
