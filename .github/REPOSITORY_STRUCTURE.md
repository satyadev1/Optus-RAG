# Repository Structure

Clean, organized structure for the RAG System.

## 📁 Directory Layout

```
Optus-RAG/
├── README.md                    # Main documentation
├── API_DOCUMENTATION.md         # API reference
├── PRE_COMMIT_CHECKLIST.md     # Contribution guide
├── docker-compose.yml           # Milvus setup
├── requirements.txt             # Python dependencies
│
├── scripts/                     # Startup scripts
│   ├── start.sh                # Start all services
│   ├── start-backend.sh        # Start Flask only
│   └── start-frontend.sh       # Start React only
│
├── docs/                        # Feature documentation (22 files)
│   ├── README.md               # Docs index
│   ├── HYBRID_SEARCH_IMPLEMENTATION.md
│   ├── JIRA_RETRIEVAL_GUIDE.md
│   └── ...
│
├── frontend/                    # React application
│   ├── public/
│   │   ├── index.html
│   │   └── logo.svg            # Generic RAG logo
│   ├── src/
│   │   ├── App.js
│   │   ├── components/         # React components
│   │   └── index.js
│   └── package.json
│
├── .github/                     # GitHub metadata
│   ├── CLEAN_REPO_SUMMARY.md
│   ├── FINAL_CLEANUP_SUMMARY.md
│   ├── GITHUB_PUBLISH_SUMMARY.md
│   └── SANITIZATION_SUMMARY.md
│
└── Core Python Modules (9 files)
    ├── web_interface.py         # Flask backend server
    ├── claude_rag.py            # Main RAG implementation
    ├── ollama_rag.py            # Ollama integration
    ├── jira_client.py           # Jira API client
    ├── github_analyzer.py       # GitHub analysis
    ├── web_crawler.py           # Website crawler
    ├── image_vectorizer.py      # Image OCR
    ├── codebase_analyzer.py     # Code analysis
    └── token_tracker.py         # Token tracking
```

## 🗂️ File Count

| Category | Count |
|----------|-------|
| Python modules | 9 |
| Shell scripts | 3 |
| Documentation (root) | 3 |
| Documentation (docs/) | 22 |
| Configuration files | 2 |
| **Total (excluding node_modules)** | **39** |

## 🚀 Quick Start

```bash
# Start all services
./scripts/start.sh

# Or start individually
docker-compose up -d              # Milvus
./scripts/start-backend.sh        # Backend
./scripts/start-frontend.sh       # Frontend
```

## 📝 Core Modules

### Backend
- **web_interface.py** - Main Flask server (Port 5000)
- **claude_rag.py** - RAG implementation with Claude AI
- **ollama_rag.py** - Alternative using Ollama

### Data Integrations
- **jira_client.py** - Generic Jira API client
- **github_analyzer.py** - Repository analysis
- **web_crawler.py** - Website indexing

### Utilities
- **image_vectorizer.py** - OCR and image vectorization
- **codebase_analyzer.py** - Code analysis engine
- **token_tracker.py** - API usage tracking

## 🔧 Configuration

- **.env** - Environment variables (not in repo)
- **docker-compose.yml** - Milvus configuration
- **requirements.txt** - Python dependencies
- **frontend/package.json** - Node dependencies

## 📚 Documentation

### Root
- **README.md** - Main project documentation
- **API_DOCUMENTATION.md** - Complete API reference
- **PRE_COMMIT_CHECKLIST.md** - Contributor guide

### docs/
22 detailed feature guides covering:
- Setup and configuration
- Feature implementations
- UI/Frontend guides
- Technical references

### .github/
Project metadata and cleanup records

## 🎯 Design Principles

1. **Clean Root** - Only essential files in root
2. **Organized Scripts** - All scripts in `scripts/`
3. **Comprehensive Docs** - Main docs in root, details in `docs/`
4. **Generic Code** - No company-specific references
5. **Easy Setup** - Simple startup scripts

## 🔒 Excluded Files

Via `.gitignore`:
- `node_modules/`
- `venv/`
- `.env`
- `volumes/`
- `*.log`
- `*.pyc`
- Data files (JSON)

## 📊 Repository Metrics

- **Lines of Code**: ~88,000
- **Git History**: 3 clean commits
- **Size**: ~45MB (without node_modules)
- **Languages**: Python, JavaScript, Shell

## 🎉 Ready For

- ✅ Public sharing
- ✅ Portfolio showcase
- ✅ Open source contributions
- ✅ Educational use
- ✅ Commercial use (with license)
