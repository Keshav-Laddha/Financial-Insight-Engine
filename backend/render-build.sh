#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python -c "from app.database import init_db; init_db()"

echo "Build complete!"
