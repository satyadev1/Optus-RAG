#!/bin/bash
# Start React Frontend Only

cd "$(dirname "$0")/../frontend"

echo "========================================"
echo "Starting Frontend"
echo "========================================"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start frontend
echo "Starting frontend on http://localhost:3000"
echo "========================================"
npm start
