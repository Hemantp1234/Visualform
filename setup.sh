#!/bin/bash

# VisualForm Setup Script
# This script sets up the development environment for VisualForm

echo "🚀 VisualForm Setup"
echo "==================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python3 -c "
from app import app, db
from models import init_db
with app.app_context():
    init_db(app)
    print('✅ Database initialized successfully!')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate venv:  source venv/bin/activate"
echo "  2. Run Flask app:  python3 app.py"
echo "  3. Open browser:   http://localhost:5000"
echo ""
echo "First time? Register at /register with any username/password"
echo "Then configure AWS credentials from the dashboard"
