# RAG System - Startup Guide

## Quick Start

### 1. Start Backend Server

Open a terminal and run:

```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
./start_backend.sh
```

Or manually:

```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
source venv/bin/activate
python3 web_interface.py
```

**Backend will run on:** `http://localhost:5001`

### 2. Start Frontend (React)

Open a NEW terminal and run:

```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal/frontend
npm start
```

**Frontend will run on:** `http://localhost:3000`

---

## Troubleshooting

### Error: "Proxy error: Could not proxy request"

**Cause:** Backend server is not running on port 5001

**Solution:**
1. Open a new terminal
2. Run: `./start_backend.sh`
3. Wait for "Running on http://0.0.0.0:5001" message
4. Refresh your browser

### Error: "ModuleNotFoundError: No module named 'flask'"

**Cause:** Dependencies not installed

**Solution:**
```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
source venv/bin/activate
pip install flask flask-cors pymilvus sentence-transformers requests PyPDF2 beautifulsoup4 python-dotenv pillow anthropic
```

### Error: "Failed to connect to Milvus"

**Cause:** Milvus database is not running

**Solution:**
```bash
# Check if Milvus is running
docker ps | grep milvus

# If not running, start it
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
docker-compose up -d
```

### Port 5001 Already in Use

**Solution:**
```bash
# Find process using port 5001
lsof -ti:5001

# Kill the process
kill -9 $(lsof -ti:5001)

# Restart backend
./start_backend.sh
```

---

## Checking if Services are Running

### Check Backend
```bash
curl http://localhost:5001/health
```

Should return: `{"status": "ok"}`

### Check Milvus
```bash
curl http://localhost:19530
```

Should connect without error

### Check Frontend
Open browser to `http://localhost:3000`

---

## Complete Startup Sequence

### Terminal 1: Milvus (if needed)
```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
docker-compose up -d
```

### Terminal 2: Backend
```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal
./start_backend.sh
```

Wait for: `* Running on http://0.0.0.0:5001`

### Terminal 3: Frontend
```bash
cd /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal/frontend
npm start
```

Wait for: `Compiled successfully!`

### Browser
Open: `http://localhost:3000`

---

## Stopping Services

### Stop Backend
Press `Ctrl+C` in backend terminal

Or:
```bash
pkill -f "python.*web_interface.py"
```

### Stop Frontend
Press `Ctrl+C` in frontend terminal

### Stop Milvus
```bash
docker-compose down
```

---

## Development Mode

### Backend with Auto-Reload
```bash
source venv/bin/activate
export FLASK_ENV=development
python3 web_interface.py
```

### Frontend with Hot Reload
```bash
cd frontend
npm start
```
(Already has hot reload by default)

---

## Logs

### Backend Logs
Located in terminal where backend is running

### Frontend Logs
- Terminal: Build logs
- Browser Console (F12): Runtime logs

### Milvus Logs
```bash
docker-compose logs -f milvus-standalone
```

---

## Quick Commands

```bash
# Start everything
./start_backend.sh &           # Terminal 1
cd frontend && npm start &     # Terminal 2

# Check status
curl http://localhost:5001/health     # Backend
curl http://localhost:3000            # Frontend
curl http://localhost:19530           # Milvus

# Stop everything
pkill -f "python.*web_interface"
pkill -f "react-scripts"
docker-compose down
```

---

## Environment Variables

Create `.env` file if needed:

```bash
# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# API Keys (optional)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Server
FLASK_ENV=development
PORT=5001
```

---

Last Updated: 2026-02-17
