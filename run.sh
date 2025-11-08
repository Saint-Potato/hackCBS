#!/bin/bash

echo "🚀 Starting DB RAG Analytics Backend Server..."
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing/upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your API keys."
    echo "   See .env.example for the required variables."
fi

# Display system info
echo ""
echo "🔍 System Information:"
echo "   Python version: $(python --version)"
echo "   FastAPI: $(pip show fastapi | grep Version | cut -d' ' -f2)"
echo "   Working directory: $(pwd)"
echo ""

# Start the server
echo "🌟 Starting FastAPI server..."
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🌐 Health Check: http://localhost:8000/api/health"
echo "🔄 Auto-reload enabled for development"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Use uvicorn directly with the import string for proper reload
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log