#!/bin/bash
# Start Flask Backend Only

cd "$(dirname "$0")/.."

echo "========================================"
echo "Starting Backend Server"
echo "========================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Check Milvus
echo "Checking Milvus connection..."
if ! curl -s http://localhost:19530 > /dev/null 2>&1; then
    echo "⚠️  Milvus not running. Start with: docker-compose up -d"
fi

# Start backend
echo ""
echo "Starting backend on http://localhost:5000"
echo "========================================"
python3 web_interface.py
