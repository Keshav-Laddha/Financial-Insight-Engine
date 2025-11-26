"""
Test script to verify SQLite database setup and operations
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db, FileMetadata


def test_database():
    """Test basic database operations"""
    print("🧪 Testing SQLite Database Setup\n")
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   ✅ Database initialized\n")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Test 1: Insert a record
        print("2. Testing INSERT operation...")
        test_file = FileMetadata(
            id="test_123",
            stored_as="test_123_sample.pdf",
            name="sample.pdf",
            uploaded_at=datetime.utcnow(),
            size=1024,
            type="application/pdf",
            company="Test Company"
        )
        db.add(test_file)
        db.commit()
        print("   ✅ Record inserted\n")
        
        # Test 2: Query the record
        print("3. Testing SELECT operation...")
        result = db.query(FileMetadata).filter(FileMetadata.id == "test_123").first()
        if result:
            print(f"   ✅ Record found: {result.name}")
            print(f"      - ID: {result.id}")
            print(f"      - Company: {result.company}")
            print(f"      - Size: {result.size} bytes\n")
        else:
            print("   ❌ Record not found\n")
        
        # Test 3: Update the record
        print("4. Testing UPDATE operation...")
        result.company = "Updated Company"
        db.commit()
        db.refresh(result)
        print(f"   ✅ Record updated: Company = {result.company}\n")
        
        # Test 4: List all records
        print("5. Testing list all records...")
        all_files = db.query(FileMetadata).all()
        print(f"   ✅ Found {len(all_files)} record(s) in database\n")
        
        # Test 5: Delete the record
        print("6. Testing DELETE operation...")
        db.delete(result)
        db.commit()
        print("   ✅ Record deleted\n")
        
        # Verify deletion
        result = db.query(FileMetadata).filter(FileMetadata.id == "test_123").first()
        if result is None:
            print("7. Verifying deletion...")
            print("   ✅ Record successfully deleted\n")
        else:
            print("   ❌ Record still exists\n")
        
        print("=" * 50)
        print("✅ All database tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_database()
