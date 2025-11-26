#!/bin/bash

echo "🚀 Setting up SQLite Database for Financial Insight Engine"
echo "=========================================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install sqlalchemy
echo ""

# Run database test
echo "🧪 Testing database setup..."
python test_database.py
echo ""

# Check if migration is needed
if [ -f "uploaded_files/file_metadata.json" ]; then
    echo "📁 Found existing file_metadata.json"
    echo "🔄 Running migration..."
    python migrate_to_sqlite.py
    echo ""
else
    echo "ℹ️  No existing data to migrate"
    echo ""
fi

echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start the server: uvicorn main:app --reload"
echo "  2. Test the API at: http://localhost:8000/docs"
echo ""
