"""
Migration script to transfer data from file_metadata.json to SQLite database
Run this once to migrate existing data.
"""
import os
import json
from datetime import datetime
from app.database import SessionLocal, init_db, FileMetadata

def migrate_json_to_sqlite():
    """
    Read existing file_metadata.json and insert records into SQLite database.
    """
    # Initialize database
    init_db()
    
    # Path to JSON file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    JSON_FILE = os.path.join(BASE_DIR, "uploaded_files", "file_metadata.json")
    
    if not os.path.exists(JSON_FILE):
        print(f"No JSON file found at {JSON_FILE}")
        print("Nothing to migrate.")
        return
    
    # Read JSON data
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not data:
        print("JSON file is empty. Nothing to migrate.")
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        migrated_count = 0
        skipped_count = 0
        
        for entry in data:
            # Check if entry already exists
            existing = db.query(FileMetadata).filter(FileMetadata.id == entry.get("id")).first()
            
            if existing:
                print(f"Skipping duplicate: {entry.get('name')}")
                skipped_count += 1
                continue
            
            # Parse uploadedAt timestamp
            uploaded_at = entry.get("uploadedAt")
            if uploaded_at:
                try:
                    uploaded_at = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                except:
                    uploaded_at = datetime.utcnow()
            else:
                uploaded_at = datetime.utcnow()
            
            # Create new database entry
            new_file = FileMetadata(
                id=entry.get("id"),
                stored_as=entry.get("stored_as"),
                name=entry.get("name"),
                uploaded_at=uploaded_at,
                size=entry.get("size", 0),
                type=entry.get("type", "application/pdf"),
                company=entry.get("company")
            )
            
            db.add(new_file)
            migrated_count += 1
            print(f"Migrated: {entry.get('name')}")
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"   Migrated: {migrated_count} files")
        print(f"   Skipped: {skipped_count} files (already in database)")
        
        # Optionally backup the JSON file
        backup_path = JSON_FILE + ".backup"
        if migrated_count > 0:
            import shutil
            shutil.copy2(JSON_FILE, backup_path)
            print(f"   Backup created: {backup_path}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting migration from JSON to SQLite...")
    migrate_json_to_sqlite()
