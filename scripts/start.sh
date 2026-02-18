#!/bin/bash
# Start RAG System (Milvus + Backend + Frontend)

echo "========================================"
echo "Starting RAG System"
echo "========================================"
echo ""

# Start Milvus
echo "1. Starting Milvus vector database..."
docker-compose up -d
sleep 5
echo "   ✓ Milvus started"
echo ""

# Start Backend
echo "2. Starting Flask backend..."
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
python3 web_interface.py &
BACKEND_PID=$!
echo "   ✓ Backend started (PID: $BACKEND_PID)"
echo ""

# Start Frontend
echo "3. Starting React frontend..."
cd frontend
npm install --silent 2>/dev/null
npm start &
FRONTEND_PID=$!
echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "========================================"
echo "RAG System is running!"
echo "========================================"
echo ""
echo "Services:"
echo "  - Milvus:   http://localhost:19530"
echo "  - Backend:  http://localhost:5000"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

wait
