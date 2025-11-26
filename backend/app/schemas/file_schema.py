"""
Pydantic schemas for file metadata
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileMetadataCreate(BaseModel):
    id: str
    stored_as: str
    name: str
    uploadedAt: Optional[str] = None
    size: int
    type: str
    company: Optional[str] = None


class FileMetadataSchema(BaseModel):
    id: str
    stored_as: str
    name: str
    uploaded_at: datetime
    size: int
    type: str
    company: Optional[str] = None

    class Config:
        from_attributes = True
