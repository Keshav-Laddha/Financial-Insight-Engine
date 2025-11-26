"""
Database configuration and models for SQLite
"""
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "file_storage.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# File metadata model
class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(String, primary_key=True, index=True)
    stored_as = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    size = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    company = Column(String, nullable=True)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
