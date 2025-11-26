@echo off
echo.
echo 🚀 Setting up SQLite Database for Financial Insight Engine
echo ==========================================================
echo.

REM Check if we're in the backend directory
if not exist "main.py" (
    echo ❌ Error: Please run this script from the backend directory
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install sqlalchemy
echo.

REM Run database test
echo 🧪 Testing database setup...
python test_database.py
echo.

REM Check if migration is needed
if exist "uploaded_files\file_metadata.json" (
    echo 📁 Found existing file_metadata.json
    echo 🔄 Running migration...
    python migrate_to_sqlite.py
    echo.
) else (
    echo ℹ️  No existing data to migrate
    echo.
)

echo ✅ Database setup complete!
echo.
echo Next steps:
echo   1. Start the server: uvicorn main:app --reload
echo   2. Test the API at: http://localhost:8000/docs
echo.
pause
