# Complete API Documentation
## Milvus Data Management System

All UI functionality is available via REST API for multi-agent and programmatic access.

**Base URL:** `http://localhost:5001`

---

## Table of Contents

1. [Hybrid Search (NEW!)](#hybrid-search-exact--semantic)
2. [File Operations](#file-operations)
3. [Jira Integration](#jira-integration)
4. [GitHub Integration](#github-integration)
5. [Confluence Integration](#confluence-integration)
6. [Repository Analyzer](#repository-analyzer)
7. [Persona Management](#persona-management)
8. [Search & Query](#search--query)
9. [AI Integration (Claude & Ollama)](#ai-integration)
10. [Text Indexing](#text-indexing)
11. [Collection Management](#collection-management)
12. [Claude Code APIs](#claude-code-apis)
13. [Multi-Agent Compatibility](#multi-agent-compatibility)

---

## Hybrid Search (Exact + Semantic)

### 🚀 What's New

The system now uses **intelligent hybrid search** that combines:
- **Exact ID matching** for JIRA tickets (100% accuracy, ~10-20ms)
- **Semantic vector search** for natural language queries (~100-200ms)
- **Priority ordering** that places exact matches at position 1

### How It Works

#### Query Examples:

1. **Exact Match (JIRA Ticket ID):**
   ```
   Query: "NEXUS-50624"
   Result: Position 1, Score 1.0, Match type: exact
   ```

2. **Exact Match (URL):**
   ```
   Query: "https://sonatype.atlassian.net/browse/NEXUS-50624"
   Result: Extracts ID, Position 1, Score 1.0, Match type: exact
   ```

3. **Exact Match (Natural Language):**
   ```
   Query: "give me details about NEXUS-50624"
   Result: Extracts ID, Position 1, Score 1.0, Match type: exact
   ```

4. **Semantic Search (Fallback):**
   ```
   Query: "Webhooks for Firewall Discovery"
   Result: Multiple results with semantic similarity scores (0.6-0.7)
   ```

### Key Benefits

- ✅ **100% accuracy** for direct ticket lookups
- ✅ **10x faster** for exact matches (no vector search needed)
- ✅ **Priority ordering** ensures exact matches appear first
- ✅ **Backward compatible** with semantic search
- ✅ **Flexible queries** - works with IDs, URLs, or natural language

### Response Time Display

All Claude AI responses now include response time:
```
[Answer content...]

---
*Responded in 2.3 seconds*
```

---

## File Operations

### Upload File

**Endpoint:** `POST /upload_file`

**Content-Type:** `multipart/form-data`

Upload and index files in Milvus.

**Parameters:**
- `file` (file): File to upload (PDF, TXT, CSV, JSON, MD, etc.)
- `collection` (string): Target collection name (default: `documents`)

**Response:**
```json
{
  "success": true,
  "message": "Document stored successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/upload_file \
  -F "file=@document.pdf" \
  -F "collection=documents"
```

**Supported formats:**
- PDF, TXT, MD, CSV, JSON, DOCX, XLSX

---

## Jira Integration

### Fetch Jira Tickets

**Endpoint:** `POST /fetch_jira`

Fetch comprehensive Jira ticket data including comments, changelog, attachments.

**Request Body:**
```json
{
  "jira_input": "PROJ-123, PROJ-124, PROJ-125",
  "collection": "jira_tickets"
}
```

**Parameters:**
- `jira_input` (string): Comma or space-separated Jira ticket keys
- `collection` (string): Target collection (default: `jira_tickets`)

**Response:**
```json
{
  "success": true,
  "message": "Stored 3 tickets successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/fetch_jira \
  -H "Content-Type: application/json" \
  -d '{
    "jira_input": "NEXUS-1234 NEXUS-1235",
    "collection": "jira_tickets"
  }'
```

**Data Retrieved:**
- Summary, description, status, priority
- Comments with authors and timestamps
- Changelog/history
- Assignees, reporters, watchers
- Labels, components, versions
- Attachments metadata
- All custom fields

**Configuration Required:**
Set in `.env` file:
```
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token
```

---

## GitHub Integration

### Fetch Single GitHub PR

**Endpoint:** `POST /fetch_github_pr`

Fetch comprehensive data for a single pull request.

**Request Body:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "collection": "github_prs"
}
```

**Parameters:**
- `pr_url` (string): Full GitHub PR URL
- `collection` (string): Target collection (default: `github_prs`)

**Response:**
```json
{
  "success": true,
  "message": "Stored PR #123 with 5 files, 12 commits, 3 reviews..."
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/fetch_github_pr \
  -H "Content-Type: application/json" \
  -d '{
    "pr_url": "https://github.com/sonatype/nexus-public/pull/456",
    "collection": "github_prs"
  }'
```

**Data Retrieved:**
- PR metadata (title, author, state, merged status)
- File changes (additions, deletions, patches)
- All commits with messages and authors
- Reviews (approvals, change requests, comments)
- Issue comments (general discussion)
- Review comments (inline code comments)
- Timeline events
- Labels, assignees, reviewers

### Fetch Repository PRs (Bulk)

**Endpoint:** `POST /fetch_repo_prs`

Fetch all (or specific number of) PRs from a repository with automatic persona analysis.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "pr_limit": "100",
  "state": "all",
  "collection": "github_prs"
}
```

**Parameters:**
- `repo_url` (string): GitHub repository URL
- `pr_limit` (string): Number of PRs to fetch (e.g., "50", "100") or "*" for all
- `state` (string): PR state - "open", "closed", or "all" (default: "all")
- `collection` (string): Target collection (default: `github_prs`)

**Response:**
```json
{
  "success": true,
  "message": "Successfully fetched 100/100 PRs (0 already existed) and built 25 personas",
  "stats": {
    "total_prs": 100,
    "stored_prs": 100,
    "failed_prs": 0,
    "skipped_prs": 0,
    "personas_built": 25,
    "repository": "owner/repo"
  },
  "persona_result": {
    "personas": [...]
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/fetch_repo_prs \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/sonatype/nexus-public",
    "pr_limit": "*",
    "state": "all",
    "collection": "github_prs"
  }'
```

**Features:**
- Automatic pagination for large repositories
- Skips already-fetched PRs (tracked in `github_pr_tracker` collection)
- Auto-triggers persona analysis after fetch completes
- Returns detailed statistics and persona summaries
- Tracks success/failure status for each PR

### Get Analyzed PRs

**Endpoint:** `GET /get_analyzed_prs`

Get list of all PRs that have been analyzed with their status.

**Query Parameters:**
- `repository` (optional): Filter by repository (e.g., "owner/repo")

**Response:**
```json
{
  "success": true,
  "tracked_prs": {
    "successful": [
      {
        "repository": "owner/repo",
        "pr_number": 123,
        "pr_title": "Fix memory leak",
        "status": "success",
        "fetched_at": "2026-02-12T10:30:00",
        "collection_name": "github_prs"
      }
    ],
    "failed": [
      {
        "repository": "owner/repo",
        "pr_number": 124,
        "pr_title": "Add feature X",
        "status": "failed",
        "error_message": "Rate limit exceeded",
        "fetched_at": "2026-02-12T10:35:00"
      }
    ]
  },
  "summary": {
    "total": 2,
    "successful": 1,
    "failed": 1
  }
}
```

**Example:**
```bash
curl "http://localhost:5001/get_analyzed_prs?repository=owner/repo"
```

**Configuration Required:**
Set in `.env` file:
```
GITHUB_TOKEN=your_github_personal_access_token
```

---

## Confluence Integration

### Fetch Confluence Page

**Endpoint:** `POST /fetch_confluence`

Fetch Confluence page with full content and metadata.

**Request Body:**
```json
{
  "page_url": "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title",
  "collection": "confluence_pages"
}
```

**Parameters:**
- `page_url` (string): Full Confluence page URL
- `collection` (string): Target collection (default: `confluence_pages`)

**Response:**
```json
{
  "success": true,
  "message": "Confluence page 'Page Title' stored successfully",
  "stats": {
    "title": "Page Title",
    "space": "SPACE",
    "page_id": "123456",
    "version": 5,
    "content_length": 5432
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/fetch_confluence \
  -H "Content-Type: application/json" \
  -d '{
    "page_url": "https://sonatype.atlassian.net/wiki/spaces/ENG/pages/789/Architecture",
    "collection": "confluence_pages"
  }'
```

**Data Retrieved:**
- Page title and content (HTML converted to plain text)
- Space information
- Version number
- Author and last modifier
- Creation and update timestamps
- Ancestors (parent pages)

**Configuration:**
Uses same credentials as Jira (`.env` file).

---

## Repository Analyzer

### Analyze Repository

**Endpoint:** `POST /fetch_repo_prs`

(Same as bulk PR fetch - includes automatic persona analysis)

See [Fetch Repository PRs](#fetch-repository-prs-bulk) above.

**Additional Features:**
- Automatically analyzes contributor patterns
- Builds personas for all contributors
- Tracks approvals, merges, comments
- Generates collaboration graphs

---

## Persona Management

### Get All Personas

**Endpoint:** `GET /get_all_personas`

Get list of all contributor personas with statistics.

**Query Parameters:**
- `collection` (optional): Filter by collection (default: all persona collections)

**Response:**
```json
{
  "success": true,
  "personas": [
    {
      "username": "alice",
      "display_name": "Alice Johnson",
      "role": "maintainer",
      "statistics": {
        "prs_authored": 45,
        "prs_reviewed": 120,
        "approvals_given": 95,
        "prs_merged": 80,
        "approval_rate": 0.79
      },
      "patterns": {
        "common_phrases": ["looks good", "consider", "what about"],
        "review_style": "thorough"
      },
      "relationships": {
        "frequently_reviews": ["bob", "charlie"]
      }
    }
  ],
  "count": 25
}
```

**Example:**
```bash
curl http://localhost:5001/get_all_personas
```

### Get Specific Persona

**Endpoint:** `GET /get_persona/<username>`

Get detailed persona data for a specific user.

**Response:**
```json
{
  "success": true,
  "persona": {
    "username": "alice",
    "display_name": "Alice Johnson",
    "role": "maintainer",
    "statistics": {...},
    "patterns": {...},
    "relationships": {...}
  }
}
```

**Example:**
```bash
curl http://localhost:5001/get_persona/alice
```

### Export Persona PDF

**Endpoint:** `GET /export_persona_pdf/<username>`

Export detailed persona report as PDF.

**Response:** Binary PDF file

**Example:**
```bash
curl http://localhost:5001/export_persona_pdf/alice \
  --output alice_persona.pdf
```

**PDF Contents:**
- Statistics dashboard
- Approval rate charts
- Common phrases word cloud
- Review topics distribution
- Collaboration network graph
- Sample comments
- Activity timeline

### Export All Personas PDF

**Endpoint:** `GET /export_all_personas_pdf`

Export summary report comparing all personas.

**Response:** Binary PDF file

**Example:**
```bash
curl http://localhost:5001/export_all_personas_pdf \
  --output personas_summary.pdf
```

**PDF Contents:**
- Repository overview
- Contributor statistics table
- Top reviewers comparison
- Approval rates comparison
- Full collaboration network

### Analyze Personas

**Endpoint:** `POST /analyze_personas`

Manually trigger persona analysis for a collection.

**Request Body:**
```json
{
  "collection": "github_prs"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Built 25 personas",
  "personas": [...]
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/analyze_personas \
  -H "Content-Type: application/json" \
  -d '{"collection": "github_prs"}'
```

### Get PR Actions

**Endpoint:** `GET /get_pr_actions/<owner>/<repo>/<pr_number>`

Get detailed timeline of who did what for a specific PR.

**Response:**
```json
{
  "success": true,
  "pr_number": 123,
  "author": "alice",
  "approvers": [
    {"username": "bob", "timestamp": "2026-01-15T10:30:00"},
    {"username": "charlie", "timestamp": "2026-01-15T11:00:00"}
  ],
  "change_requesters": [
    {"username": "dave", "timestamp": "2026-01-14T16:00:00"}
  ],
  "merger": "bob",
  "merged_at": "2026-01-15T14:00:00",
  "timeline": [...]
}
```

**Example:**
```bash
curl http://localhost:5001/get_pr_actions/sonatype/nexus-public/123
```

### Get Approval Statistics

**Endpoint:** `GET /get_approval_stats`

Get approval and merge statistics for all contributors.

**Response:**
```json
{
  "success": true,
  "stats": [
    {
      "username": "alice",
      "approval_count": 95,
      "merge_count": 80,
      "avg_approval_time_hours": 6.2
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5001/get_approval_stats
```

---

## Search & Query

### Hybrid Search (Semantic + Exact Match)

**Endpoint:** `POST /search`

Perform intelligent hybrid search combining **exact ID matching** with **semantic vector search**.

**Request Body:**
```json
{
  "query": "NEXUS-50624",
  "collection": "jira_tickets",
  "top_k": 5
}
```

**Parameters:**
- `query` (string): Search query (supports ticket IDs, URLs, or natural language)
- `collection` (string): Collection to search
- `top_k` (int): Number of results (default: 5)

**Search Behavior:**

1. **Exact Match (for JIRA tickets):**
   - Query: `"NEXUS-50624"` → Returns exact ticket with score 1.0
   - Query: `"https://sonatype.atlassian.net/browse/NEXUS-50624"` → Extracts ID, returns exact match
   - Query: `"give me details about NEXUS-50624"` → Extracts ID, returns exact match
   - **Response time:** ~10-20ms (database query only)
   - **Match type:** `exact`

2. **Semantic Search (fallback):**
   - Query: `"memory leaks and performance issues"` → Vector similarity search
   - **Response time:** ~100-200ms (embedding + vector search)
   - **Match type:** `semantic`

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "title": "NEXUS-50624: Webhooks for Firewall Discovery",
      "content": "Description of the feature...",
      "source_type": "jira",
      "source_id": "NEXUS-50624",
      "url": "https://sonatype.atlassian.net/browse/NEXUS-50624",
      "similarity_score": 1.0,
      "match_type": "exact"
    }
  ],
  "search_method": "exact_match",
  "ticket_id_extracted": "NEXUS-50624"
}
```

**Examples:**

```bash
# Exact match by ticket ID
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "NEXUS-50624",
    "collection": "jira_tickets",
    "top_k": 5
  }'

# Exact match by URL
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "https://sonatype.atlassian.net/browse/NEXUS-50624",
    "collection": "jira_tickets",
    "top_k": 5
  }'

# Semantic search (natural language)
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication and security vulnerabilities",
    "collection": "github_prs",
    "top_k": 10
  }'
```

---

## AI Integration

### Query with Claude AI (RAG with Hybrid Search)

**Endpoint:** `POST /ask_claude`

Ask questions with Claude AI using RAG (Retrieval Augmented Generation) with intelligent hybrid search.

**Request Body:**
```json
{
  "question": "What is NEXUS-50624 about?",
  "collection": "all",
  "top_k": 5
}
```

**Parameters:**
- `question` (string): Question to ask (supports ticket IDs, URLs, or natural language)
- `collection` (string): Collection(s) to search (supports "all" for all collections)
- `top_k` (int): Number of relevant documents to retrieve per collection (default: 3)
- `website_url` (string, optional): URL to scrape and include in context

**How It Works:**

1. **Hybrid Search:** Searches all collections with intelligent exact match + semantic search
2. **Priority Ordering:** Exact matches (score 1.0) are prioritized at position 1
3. **Multi-Collection:** Retrieves context from jira_tickets, github_prs, codebase_analysis, etc.
4. **AI Analysis:** Claude analyzes all retrieved context and generates comprehensive answer
5. **Response Time:** Displayed at the end of answer (e.g., "*Responded in 2.3 seconds*")

**Response:**
```json
{
  "success": true,
  "answer": "NEXUS-50624 is about Webhooks for Firewall Discovery...\n\n---\n*Responded in 2.3 seconds*",
  "sources": [
    {
      "title": "NEXUS-50624: Webhooks for Firewall Discovery",
      "content": "Full ticket description...",
      "url": "https://sonatype.atlassian.net/browse/NEXUS-50624",
      "collection": "jira_tickets",
      "match_type": "exact",
      "score": 1.0
    }
  ],
  "model": "claude-sonnet-4-5",
  "response_time_seconds": 2.3
}
```

**Examples:**

```bash
# Query specific JIRA ticket
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is NEXUS-50624 about?",
    "collection": "all",
    "top_k": 3
  }'

# Query with URL
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{
    "question": "give me details about https://sonatype.atlassian.net/browse/NEXUS-50624",
    "collection": "all",
    "top_k": 5
  }'

# Natural language query
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What security vulnerabilities have been reported?",
    "collection": "all",
    "top_k": 5
  }'

# Query with website scraping
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key features?",
    "collection": "all",
    "website_url": "https://help.sonatype.com",
    "top_k": 3
  }'
```

**Key Features:**
- ✅ **Exact ID matching** for JIRA tickets (100% accuracy)
- ✅ **Priority ordering** (exact matches always first)
- ✅ **Multi-collection search** across all data sources
- ✅ **Response time tracking** (displayed in answer)
- ✅ **Website scraping** integration
- ✅ **Semantic fallback** for natural language queries

**Configuration Required:**
Set in `.env` file:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Query with Ollama

**Endpoint:** `POST /ask_ollama`

Ask questions with Ollama (local LLM) using RAG.

**Request Body:**
```json
{
  "question": "What are the main bugs?",
  "collection": "jira_tickets",
  "model": "llama3.2",
  "top_k": 3
}
```

**Parameters:**
- `question` (string): Question to ask
- `collection` (string): Collection(s) to search (supports "all")
- `model` (string): Ollama model name (default: "llama3.2")
- `top_k` (int): Number of relevant documents (default: 3)

**Response:**
```json
{
  "success": true,
  "answer": "The main bugs reported are...",
  "sources": [...],
  "model": "llama3.2"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/ask_ollama \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Summarize the authentication issues",
    "collection": "github_prs",
    "model": "llama3.2",
    "top_k": 5
  }'
```

### Check Ollama Status

**Endpoint:** `GET /ollama_status`

Check if Ollama is running and get available models.

**Response:**
```json
{
  "success": true,
  "is_running": true,
  "available_models": [
    "llama3.2",
    "mistral",
    "codellama"
  ]
}
```

**Example:**
```bash
curl http://localhost:5001/ollama_status
```

**Requirements:**
- Ollama must be installed and running: `ollama serve`
- Models must be pulled: `ollama pull llama3.2`

---

## Text Indexing

### Index Text

**Endpoint:** `POST /index_text`

Directly index arbitrary text content into Milvus.

**Request Body:**
```json
{
  "title": "Meeting Notes - Architecture Discussion",
  "content": "We discussed the new microservices architecture...",
  "collection": "notes",
  "tags": ["meeting", "architecture", "2024"]
}
```

**Parameters:**
- `title` (string): Title of the text
- `content` (string): Text content to index
- `collection` (string): Target collection (default: `documents`)
- `tags` (array): Optional tags for categorization

**Response:**
```json
{
  "success": true,
  "message": "Successfully indexed 'Meeting Notes' in collection 'notes'...",
  "stats": {
    "title": "Meeting Notes - Architecture Discussion",
    "collection": "notes",
    "word_count": 450,
    "char_count": 2890,
    "tags": ["meeting", "architecture", "2024"],
    "text_id": "a3f9e8c2d1b4a567"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/index_text \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug Analysis Notes",
    "content": "Analyzed the memory leak issue. Root cause: unclosed connections in DatabasePool...",
    "collection": "analysis_notes",
    "tags": ["analysis", "memory-leak", "database"]
  }'
```

---

## Collection Management

### List Collections

**Endpoint:** `GET /collections`

Get list of all Milvus collections.

**Response:**
```json
{
  "success": true,
  "collections": [
    "jira_tickets",
    "github_prs",
    "github_personas",
    "confluence_pages",
    "documents"
  ]
}
```

**Example:**
```bash
curl http://localhost:5001/collections
```

### Get Collection Stats

**Endpoint:** `GET /collection/<collection_name>/stats`

Get statistics for a specific collection.

**Response:**
```json
{
  "success": true,
  "collection": "github_prs",
  "stats": {
    "entity_count": 1250,
    "indexed": true,
    "schema": {...}
  }
}
```

**Example:**
```bash
curl http://localhost:5001/collection/github_prs/stats
```

---

## Claude Code APIs

See [CLAUDE_CODE_API.md](./CLAUDE_CODE_API.md) for detailed documentation of:

- `/api/claude_code/store` - Store single items
- `/api/claude_code/store_bulk` - Store multiple items
- `/api/claude_code/query` - Query stored data

These APIs are designed for programmatic access and multi-agent systems.

---

## Multi-Agent Compatibility

All APIs are designed to work in multi-agent environments:

### 1. Stateless Design
- No session management required
- Each request is independent
- Suitable for distributed systems

### 2. Idempotency
- Safe to retry requests
- Duplicate PR fetches are automatically skipped
- Consistent results for same inputs

### 3. Bulk Operations
- `/fetch_repo_prs` - Fetch multiple PRs
- `/api/claude_code/store_bulk` - Store multiple items
- Efficient for agent batch processing

### 4. Metadata Tracking
- All stored items include:
  - `stored_at` timestamp
  - `source` identifier
  - Custom metadata fields
- Easy to track agent actions

### 5. Flexible Querying
- Semantic search across all data
- Filter by data_type, tags, collections
- Support for complex multi-collection queries

### 6. Error Handling
- Consistent error response format
- Detailed error messages
- Graceful degradation

### Multi-Agent Example Workflow

```python
import requests

base_url = "http://localhost:5001"

class Agent:
    def __init__(self, name):
        self.name = name
        self.base_url = base_url

    def fetch_and_store(self, repo_url):
        """Agent 1: Fetch repository data"""
        response = requests.post(
            f"{self.base_url}/fetch_repo_prs",
            json={
                "repo_url": repo_url,
                "pr_limit": "*",
                "state": "all"
            }
        )
        return response.json()

    def analyze(self, query):
        """Agent 2: Analyze stored data"""
        response = requests.post(
            f"{self.base_url}/ask_claude",
            json={
                "question": query,
                "collection": "all",
                "top_k": 10
            }
        )
        return response.json()

    def store_findings(self, findings):
        """Agent 3: Store analysis results"""
        response = requests.post(
            f"{self.base_url}/api/claude_code/store",
            json={
                "data_type": "analysis",
                "title": f"Analysis by {self.name}",
                "content": findings,
                "source": self.name,
                "tags": ["analysis", "automated"]
            }
        )
        return response.json()

# Multi-agent workflow
fetcher = Agent("DataFetcher")
analyzer = Agent("Analyzer")
reporter = Agent("Reporter")

# Agent 1: Fetch data
result1 = fetcher.fetch_and_store("https://github.com/org/repo")
print(f"Fetched {result1['stats']['stored_prs']} PRs")

# Agent 2: Analyze
result2 = analyzer.analyze("What are the main issues in this repository?")
print(f"Analysis: {result2['answer']}")

# Agent 3: Store findings
result3 = reporter.store_findings(result2['answer'])
print(f"Stored findings: {result3['item_id']}")
```

### Parallel Agent Execution

```python
from concurrent.futures import ThreadPoolExecutor

def agent_task(agent_id, task):
    # Each agent works independently
    response = requests.post(
        f"{base_url}/api/claude_code/store",
        json={
            "data_type": "custom",
            "title": f"Task {task} by Agent {agent_id}",
            "content": f"Agent {agent_id} processed task {task}",
            "source": f"agent_{agent_id}"
        }
    )
    return response.json()

# Run 10 agents in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(agent_task, i, task)
        for i in range(10)
        for task in ["A", "B", "C"]
    ]
    results = [f.result() for f in futures]

print(f"Completed {len(results)} agent tasks")
```

---

## Authentication & Security

**Current Setup:**
- Local development environment
- No authentication required
- Credentials stored in `.env` file

**Production Considerations:**
- Add API key authentication
- Use HTTPS
- Implement rate limiting
- Add request validation
- Secure credential storage

---

## Rate Limits

### External APIs:
- **GitHub:** 5000 requests/hour (authenticated)
- **Jira/Confluence:** Varies by plan
- **Anthropic Claude:** Based on API tier

### Internal:
- No rate limiting on local APIs
- Milvus handles concurrent requests

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "success": false,
  "message": "Detailed error description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (collection/item not found)
- `500` - Server Error (internal error, Milvus connection failure)

---

## Testing

### Health Check
```bash
curl http://localhost:5001/
```

### Test Full Workflow
```bash
# 1. Index some text
curl -X POST http://localhost:5001/index_text \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "This is a test document about authentication"}'

# 2. Search for it
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "collection": "documents", "top_k": 1}'

# 3. Query with AI
curl -X POST http://localhost:5001/ask_ollama \
  -H "Content-Type: application/json" \
  -d '{"question": "What documents mention authentication?", "collection": "documents"}'
```

---

## Python SDK Example

```python
class MilvusAPI:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    def fetch_jira(self, tickets, collection="jira_tickets"):
        return requests.post(f"{self.base_url}/fetch_jira", json={
            "jira_input": tickets,
            "collection": collection
        }).json()

    def fetch_github_pr(self, pr_url, collection="github_prs"):
        return requests.post(f"{self.base_url}/fetch_github_pr", json={
            "pr_url": pr_url,
            "collection": collection
        }).json()

    def fetch_repo(self, repo_url, limit="*", state="all"):
        return requests.post(f"{self.base_url}/fetch_repo_prs", json={
            "repo_url": repo_url,
            "pr_limit": limit,
            "state": state
        }).json()

    def search(self, query, collection, top_k=5):
        return requests.post(f"{self.base_url}/search", json={
            "query": query,
            "collection": collection,
            "top_k": top_k
        }).json()

    def ask_claude(self, question, collection="all", top_k=3):
        return requests.post(f"{self.base_url}/ask_claude", json={
            "question": question,
            "collection": collection,
            "top_k": top_k
        }).json()

    def get_personas(self):
        return requests.get(f"{self.base_url}/get_all_personas").json()

    def export_persona_pdf(self, username, output_path):
        response = requests.get(f"{self.base_url}/export_persona_pdf/{username}")
        with open(output_path, 'wb') as f:
            f.write(response.content)

# Usage
api = MilvusAPI()

# Fetch repository
result = api.fetch_repo("https://github.com/org/repo", limit="100")
print(f"Fetched {result['stats']['stored_prs']} PRs")

# Get personas
personas = api.get_personas()
print(f"Found {personas['count']} contributors")

# Ask question
answer = api.ask_claude("What are the main issues?")
print(f"Answer: {answer['answer']}")
```

---

## Support

For issues or questions:
- Check server logs: `/tmp/backend.log`
- Verify Milvus is running: `docker ps`
- Ensure `.env` credentials are configured
- Test individual endpoints with curl

---

## Server Management

### Start Server
```bash
cd "/path/to/Sonatype-Personal"
source venv/bin/activate
python web_interface.py
```

### Check Status
```bash
curl http://localhost:5001/
lsof -i:5001
```

### View Logs
```bash
tail -f /tmp/backend.log
```

### Start Milvus
```bash
docker-compose up -d
docker ps  # Verify containers are running
```
