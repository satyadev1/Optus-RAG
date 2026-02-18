# Milvus Data Management & AI Interface

Complete offline AI-powered data management system with Milvus vector database, Ollama reasoning, and web interface.

## Features

✅ **Offline Milvus Vector Database** - No internet required
✅ **File Upload** - Support for TXT, PDF, MD, JSON, CSV, LOG files
✅ **Jira Integration** - Fetch and store Jira tickets by ID
✅ **GitHub Integration** - Import GitHub PRs with file changes
✅ **Semantic Search** - Find relevant documents using AI embeddings
✅ **Ollama AI Q&A** - Offline AI reasoning with RAG (Retrieval Augmented Generation)

## Architecture

```
┌─────────────────┐
│  Web Interface  │  (Flask on port 5000)
│   (Browser UI)  │
└────────┬────────┘
         │
    ┌────┴────────────────┬──────────────┐
    │                     │              │
┌───▼────┐         ┌──────▼──────┐  ┌───▼────┐
│ Milvus │         │   Ollama    │  │  APIs  │
│  DB    │◄────────┤ AI Reasoning│  │ (Jira, │
│(19530) │         │  (11434)    │  │GitHub) │
└────────┘         └─────────────┘  └────────┘
```

## Prerequisites

1. **Docker & Docker Compose** - For Milvus
2. **Python 3.8+** - For web interface
3. **Ollama** (Optional but recommended) - For AI reasoning

## Quick Start

### 1. Start Milvus Database

```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"

# Start Milvus (offline mode)
./milvus.sh start

# Check status
./milvus.sh status
```

**Milvus will be available at:** `localhost:19530`

### 2. Install Python Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --index-url https://pypi.org/simple -r requirements.txt
```

### 3. Install & Start Ollama (For AI Features)

```bash
# Install Ollama
# Visit: https://ollama.ai

# Start Ollama server
ollama serve

# Pull recommended model (in another terminal)
ollama pull deepseek-r1:8b  # Best reasoning model
# OR
ollama pull llama3.2         # Faster, lighter model
```

**Ollama will be available at:** `http://localhost:11434`

### 4. Load Initial Jira Data

```bash
# Activate virtual environment if not already
source venv/bin/activate

# Store your existing Jira tickets in Milvus
python jira_to_milvus.py
```

### 5. Start Web Interface

```bash
# Activate virtual environment
source venv/bin/activate

# Start web server
python web_interface.py
```

**Web interface will be available at:** `http://localhost:5000`

## Usage Guide

### 📤 Upload Files

1. Go to **Upload File** tab
2. Select file (TXT, PDF, MD, JSON, CSV, LOG)
3. Choose collection name (default: "documents")
4. Click "Upload & Store"

Files are automatically:
- Converted to text
- Embedded using AI
- Stored in Milvus for semantic search

### 🎫 Fetch Jira Tickets

1. Go to **Jira Tickets** tab
2. Enter ticket keys (e.g., "NEXUS-50206, NEXUS-50393")
3. Choose collection name (default: "jira_tickets")
4. Click "Fetch & Store"

### 🐙 Import GitHub PRs

1. Go to **GitHub PRs** tab
2. Enter PR URL (e.g., "https://github.com/owner/repo/pull/123")
3. Choose collection name (default: "github_prs")
4. Click "Fetch & Store"

### 🔍 Semantic Search

1. Go to **Search** tab
2. Enter your search query
3. Select collection to search
4. Choose number of results
5. Click "Search with AI"

Example queries:
- "firewall docker quarantine issues"
- "feature flags and authorization"
- "security vulnerabilities"

### 🤖 Ollama AI Q&A (Offline Reasoning)

**Most Powerful Feature!**

1. Go to **Ollama AI** tab
2. Check Ollama status (should show green)
3. Ask any question in natural language
4. Select data source (Jira, GitHub, Documents)
5. Choose AI model
6. Click "Ask Ollama AI"

**Example Questions:**
- "What Docker firewall issues are currently in development?"
- "Summarize all feature flag related work"
- "What security issues have been fixed recently?"
- "Explain the GitHub PR changes for authentication"

**How it works:**
1. Your question is converted to an embedding
2. Relevant documents are retrieved from Milvus (RAG)
3. Context + question sent to Ollama
4. Ollama reasons about the data and provides answer
5. You get answer + source documents

## Recommended Ollama Models

### Best for Reasoning & Complex Questions:
```bash
ollama pull deepseek-r1:8b    # 8B parameters, excellent reasoning
ollama pull deepseek-r1:14b   # 14B parameters, better but slower
```

### Balanced Performance:
```bash
ollama pull llama3.2          # Fast, good quality
ollama pull qwen2.5           # Great for technical content
```

### Lightweight:
```bash
ollama pull phi3              # Very fast, smaller model
```

## Management Scripts

### Milvus Control

```bash
./milvus.sh start    # Start Milvus
./milvus.sh stop     # Stop Milvus
./milvus.sh restart  # Restart Milvus
./milvus.sh status   # Check status
./milvus.sh logs     # View logs
./milvus.sh reset    # Delete all data and reset
```

### Jira Integration

```bash
# Fetch your Jira user details and tickets
python jira_client.py

# Store tickets in Milvus
python jira_to_milvus.py
```

### Ollama RAG (Command Line)

```bash
# Test Ollama RAG from command line
python ollama_rag.py
```

## Configuration

### Jira Credentials
Edit `.env` file:
```env
JIRA_URL=https://sonatype.atlassian.net
JIRA_EMAIL=your.email@sonatype.com
JIRA_API_TOKEN=your_api_token
```

### GitHub Token
Edit `.env` file:
```env
GITHUB_TOKEN=your_github_personal_access_token
```

### Ollama Model
Change default model in `web_interface.py`:
```python
# Line in ollama route
model_name = request.json.get('model', 'deepseek-r1:8b')  # Change default here
```

## Data Collections

Milvus organizes data into collections:

| Collection | Purpose | Source |
|------------|---------|--------|
| `jira_tickets` | Jira issues | jira_client.py or web interface |
| `github_prs` | Pull requests | Web interface |
| `documents` | Uploaded files | Web interface |

You can create custom collections via the web interface.

## Troubleshooting

### Milvus Won't Start
```bash
# Reset everything
./milvus.sh reset

# Check Docker
docker ps
docker logs milvus-standalone
```

### Ollama Not Working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if not available
ollama pull llama3.2
```

### Web Interface Can't Connect to Milvus
- Make sure Milvus is running: `./milvus.sh status`
- Check port 19530 is not blocked
- Verify network: `docker network ls`

### Python Dependencies Issues
```bash
# Use public PyPI instead of local Nexus
pip install --index-url https://pypi.org/simple -r requirements.txt
```

## Security Notes

- ✅ Milvus runs **completely offline** (no internet access)
- ✅ Ollama runs **locally** (no data sent to cloud)
- ✅ All AI reasoning happens **on your machine**
- ⚠️ `.env` file contains credentials (already in .gitignore)
- ⚠️ Never commit Jira tokens or GitHub tokens to git

## Performance Tips

1. **Use smaller models for faster responses:**
   - `llama3.2` or `phi3` for quick answers
   - `deepseek-r1:8b` for complex reasoning

2. **Adjust context documents:**
   - Use `top_k=3` for focused answers
   - Use `top_k=5-7` for comprehensive answers

3. **GPU Acceleration:**
   - Ollama automatically uses GPU if available
   - Check with: `ollama ps`

## Files Overview

```
Sonatype-Personal/
├── docker-compose.yml          # Milvus configuration
├── .env                        # Credentials (not in git)
├── milvus.sh                   # Milvus management script
│
├── jira_client.py              # Fetch Jira tickets
├── jira_to_milvus.py           # Store Jira in Milvus
├── ollama_rag.py               # Ollama RAG engine
├── web_interface.py            # Flask web server
│
├── templates/
│   └── index.html              # Web UI
│
├── requirements.txt            # Python dependencies
├── README.md                   # Milvus documentation
└── README_WEB_INTERFACE.md     # This file
```

## Advanced Usage

### Search via API (curl)

```bash
# Semantic search
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "firewall issues", "collection": "jira_tickets", "top_k": 5}'

# Ask Ollama
curl -X POST http://localhost:5000/ask_ollama \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the firewall issues?", "collection": "jira_tickets", "model": "llama3.2"}'
```

### Python API Usage

```python
from ollama_rag import OllamaRAG

# Initialize
rag = OllamaRAG(model_name="deepseek-r1:8b")

# Ask question with context
result = rag.query_with_context(
    question="What firewall issues exist?",
    collection_name="jira_tickets",
    top_k=3
)

print(result['answer'])
```

## What's Next?

- ✅ Add more file formats (DOCX, XLSX)
- ✅ Implement chat history
- ✅ Add user authentication
- ✅ Export search results
- ✅ Scheduled Jira sync
- ✅ Multi-collection search

## Support

For issues:
1. Check logs: `./milvus.sh logs`
2. Verify Ollama: `ollama ps`
3. Check web server console output

---

**Created:** 2026-02-11
**Milvus Version:** 2.3.3
**Ollama Compatible:** All models
**Status:** ✅ Production Ready (Offline)
