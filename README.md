# RAG System with Multi-Source Knowledge Base

A comprehensive Retrieval Augmented Generation (RAG) system that integrates multiple knowledge sources including issue tracking systems (Jira), documentation (Confluence), GitHub repositories, and websites. Built with Milvus vector database, Claude AI, and React frontend.

## Overview

This system provides intelligent question-answering by combining:
- **Vector Search**: Semantic search using Milvus vector database
- **Multi-Source Integration**: Jira issues, Confluence pages, GitHub code, websites
- **AI-Powered Responses**: Claude AI for natural language understanding
- **Web Interface**: React-based UI for easy interaction
- **Hybrid Search**: BM25 + vector similarity for better results

## Features

### Core Capabilities
- **Multi-Collection Search**: Search across different knowledge sources
- **URL Recognition**: Automatically extracts and fetches content from pasted URLs
- **Web Crawling**: Index entire websites for knowledge base
- **GitHub Analysis**: Analyze codebases and repositories
- **Confidence Scoring**: Multi-factor scoring for answer reliability
- **Source Attribution**: Clear citation of information sources

### Data Sources
1. **Issue Tracking** - Index and search Jira/issue tracking data
2. **Documentation** - Confluence/wiki pages with full content
3. **GitHub** - Repository code analysis with file-level search
4. **Websites** - Crawl and index external documentation sites
5. **Images** - OCR and vectorization of images in documents

## Architecture

```
┌─────────────────┐
│  React Frontend │
│  (Port 3000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Flask Backend  │◄────►│ Claude API   │
│  (Port 5000)    │      └──────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Milvus Vector   │◄────►│ Sentence     │
│ Database        │      │ Transformers │
└─────────────────┘      └──────────────┘
```

## Quick Start

### Prerequisites
```bash
# Required software
- Docker & Docker Compose
- Python 3.8+
- Node.js 16+
- 8GB+ RAM recommended
```

### 1. Setup Environment

Create `.env` file with your credentials:
```bash
# Claude API Configuration
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Issue Tracking Configuration (optional)
JIRA_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token_here

# GitHub Configuration (optional)
GITHUB_TOKEN=your_github_token_here
```

### 2. Quick Start (All Services)

```bash
./scripts/start.sh
```

This will start:
- Milvus vector database (port 19530)
- Flask backend (port 5000)
- React frontend (port 3000)

### 3. Manual Start (Individual Services)

**Start Milvus:**
```bash
docker-compose up -d
```

**Start Backend:**
```bash
./scripts/start-backend.sh
```

**Start Frontend:**
```bash
./scripts/start-frontend.sh
```

## Usage Guide

### Web Interface

Access the web interface at `http://localhost:3000`

**Tabs:**
- **Chat**: Ask questions with AI-powered responses
- **Jira**: Upload and index issue tracking data
- **Confluence**: Index documentation pages
- **GitHub**: Analyze repositories and codebases
- **Crawler**: Index external websites

### Asking Questions

Simply type your question in the chat interface:

```
"What is the authentication flow?"
"Show me issues related to performance"
"How does the caching system work?"
```

**URL Support**: Paste URLs directly for instant context:
```
https://your-jira.atlassian.net/browse/ISSUE-123
```

### Indexing Data

#### Issue Tracking Data
1. Go to **Jira** tab
2. Use bulk upload or fetch via API
3. Data is vectorized and stored in Milvus

#### Documentation
1. Go to **Confluence** tab
2. Enter page URLs
3. Content is extracted and indexed

#### GitHub Repositories
1. Go to **GitHub** tab
2. Enter repository URL
3. Code is analyzed and indexed

#### External Websites
1. Go to **Crawler** tab
2. Enter starting URL
3. Set max pages and depth
4. Crawler indexes all reachable pages

## API Endpoints

### Query API
```bash
POST /query
{
  "query": "your question here",
  "collections": ["jira", "confluence", "github", "websites"],
  "limit": 5
}
```

### Upload Jira Data
```bash
POST /upload-jira
Content-Type: multipart/form-data
file: <json_file>
```

### Crawl Website
```bash
POST /crawl-website
{
  "url": "https://example.com",
  "collection_name": "example_docs",
  "max_pages": 100,
  "max_depth": 3
}
```

### GitHub Analysis
```bash
POST /analyze-github
{
  "repo_url": "https://github.com/user/repo",
  "collection_name": "repo_name"
}
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

## Data Collection Scripts

### Fetch Issues from Jira
```bash
python fetch_all_jira_issues.py
```

### Store Issues in Milvus
```bash
python jira_to_milvus.py
```

### Crawl Website
```bash
python web_crawler.py https://docs.example.com my_docs 100 3
```

### Analyze GitHub Repository
```bash
python github_analyzer.py https://github.com/user/repo
```

## Configuration

### Milvus Collections

The system creates separate collections for different data types:
- `jira_tickets` - Issue tracking data
- `confluence_pages` - Documentation pages
- `github_code` - Code repositories
- `websites` - Crawled web content

### Search Configuration

Edit `claude_rag.py` to adjust:
- `top_k`: Number of results per collection (default: 5)
- `score_threshold`: Minimum similarity score (default: 0.3)
- `search_params`: Milvus search parameters

### Embedding Model

Default: `all-MiniLM-L6-v2` (384 dimensions)

To use different model:
```python
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
```

## Project Structure

```
.
├── web_interface.py          # Flask backend server
├── claude_rag.py             # RAG core logic
├── jira_client.py            # Jira API integration
├── github_analyzer.py        # GitHub code analysis
├── web_crawler.py            # Website crawler
├── image_vectorizer.py       # Image OCR & vectorization
├── codebase_analyzer.py      # Code analysis engine
├── frontend/                 # React web interface
│   ├── src/
│   │   ├── components/       # React components
│   │   └── App.js
│   └── package.json
├── docker-compose.yml        # Milvus services
├── requirements.txt          # Python dependencies
└── .env                      # Environment variables
```

## Troubleshooting

### Milvus Connection Issues
```bash
# Check Milvus status
docker-compose ps

# View logs
docker-compose logs milvus-standalone

# Restart services
docker-compose restart
```

### Backend Errors
```bash
# Check Python logs
tail -f backend.log

# Verify environment variables
cat .env
```

### Frontend Issues
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Performance Optimization

- **Batch Processing**: Upload data in chunks for large datasets
- **Index Tuning**: Adjust `nlist` parameter in Milvus collections
- **Caching**: Enable result caching for repeated queries
- **Parallel Processing**: Use multithreaded scripts for data ingestion

## Security Considerations

- Store API keys in `.env` (never commit to git)
- Use `.gitignore` to exclude sensitive files
- Implement rate limiting for production deployments
- Sanitize user inputs before processing
- Use HTTPS in production environments

## Contributing

This is a personal project demonstrating RAG implementation patterns. Feel free to fork and adapt for your needs.

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [Milvus](https://milvus.io/) - Vector database
- [Claude AI](https://anthropic.com/) - Language model
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [React](https://react.dev/) - Frontend framework
- [Flask](https://flask.palletsprojects.com/) - Backend framework
