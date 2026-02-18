# Text Indexing - Direct Content Indexing Guide

## Overview

The **Index Text** feature allows you to directly add any text content to Milvus for AI retrieval. This is perfect for quick notes, documentation snippets, meeting summaries, code examples, or any text you want AI to access without creating files.

---

## 🎯 What It Does

### Instant Indexing
- Add text content directly through a web form
- No need to create files or upload documents
- Content is immediately searchable via semantic search
- AI (Claude and Ollama) can retrieve and reference it

### Smart Storage
- Generates semantic embeddings automatically
- Organizes content by collections
- Tags for categorization
- Full metadata tracking (word count, character count, timestamps)

---

## 📝 How to Use

### Step-by-Step

1. **Open Web Interface**
   ```
   http://localhost:3000
   ```

2. **Go to "Index Text" Tab**
   - It's the 4th tab (after Claude AI, Ollama AI, Search)

3. **Fill in the Form**

   **Title** (Required)
   - Give your content a descriptive name
   - Examples:
     - "Meeting Notes - Q1 Planning 2024"
     - "API Authentication Documentation"
     - "Deployment Procedure"
     - "Troubleshooting Guide - 502 Errors"

   **Content** (Required)
   - Enter or paste your text
   - Can be any length (shows word/character count)
   - Examples:
     - Meeting notes and decisions
     - Code snippets with explanations
     - Procedures and instructions
     - Summaries and key points
     - Reference documentation

   **Collection Name** (Optional, default: "custom_notes")
   - Organize your content into collections
   - Examples:
     - `meeting_notes` - All meeting summaries
     - `procedures` - SOPs and how-tos
     - `knowledge_base` - General information
     - `troubleshooting` - Problem solutions
     - `api_docs` - API documentation

   **Tags** (Optional)
   - Add keywords for better organization
   - Press Enter or click "Add Tag" to add
   - Examples: security, API, frontend, urgent, production

4. **Click "📥 Index Text Content"**
   - Content is indexed immediately
   - Success message shows statistics
   - Form clears for next entry

5. **Query Your Content**
   - Go to "Claude AI" or "Ollama AI" tabs
   - Select your collection (e.g., "custom_notes")
   - Ask questions about your indexed content
   - AI will retrieve and reference your text

---

## 💡 Use Cases

### 1. Meeting Notes
**Title:** "Engineering Standup - 2024-02-11"
**Content:**
```
Key Decisions:
- Migrate authentication service to microservices by Q2
- Hire 2 backend engineers (Python/FastAPI experience)
- Switch from REST to GraphQL for new endpoints

Action Items:
- John: Create architecture proposal by Friday
- Sarah: Draft job descriptions
- Team: Review GraphQL migration plan

Blockers:
- Waiting on security audit results
- Database migration tool needs testing
```
**Tags:** meeting, engineering, decisions

### 2. API Documentation
**Title:** "User Authentication API"
**Content:**
```
Endpoint: POST /api/v1/auth/login
Request Body: { "email": "string", "password": "string" }
Response: { "token": "jwt_token", "expires_in": 3600 }

Authentication:
- Include token in header: Authorization: Bearer {token}
- Token expires in 1 hour
- Refresh endpoint: POST /api/v1/auth/refresh

Error Codes:
- 401: Invalid credentials
- 429: Rate limit exceeded (10 requests/minute)
```
**Tags:** API, authentication, documentation

### 3. Troubleshooting Guide
**Title:** "Fix for 502 Bad Gateway Errors"
**Content:**
```
Symptom: Users getting 502 errors on production

Root Cause: Backend service timeout (30s default too short)

Solution:
1. SSH to production: ssh deploy@prod-server
2. Edit nginx config: sudo nano /etc/nginx/nginx.conf
3. Increase timeout: proxy_read_timeout 120s;
4. Restart nginx: sudo systemctl restart nginx
5. Check logs: tail -f /var/log/nginx/error.log

Verification:
- Test endpoint: curl -I https://api.example.com/health
- Should return 200 OK in < 5 seconds

Prevention:
- Monitor backend response times
- Set alerts for responses > 10s
- Review timeout settings monthly
```
**Tags:** troubleshooting, nginx, production, 502

### 4. Code Snippets
**Title:** "Python Rate Limiter Decorator"
**Content:**
```python
from functools import wraps
from time import time, sleep

def ratelimit(max_calls=10, period=60):
    """
    Rate limiting decorator
    Usage: @ratelimit(max_calls=10, period=60)
    """
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                sleep(sleep_time)

            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage:
@ratelimit(max_calls=5, period=60)
def expensive_api_call(data):
    return requests.post(API_URL, json=data)
```
**Tags:** python, code, rate-limiting, decorator

### 5. Deployment Procedure
**Title:** "Production Deployment Checklist"
**Content:**
```
Pre-Deployment:
□ All tests passing (unit, integration, E2E)
□ Code review approved by 2+ engineers
□ Security scan completed (no critical issues)
□ Database migrations tested on staging
□ Rollback plan documented

Deployment Steps:
1. Create release branch: git checkout -b release/v1.2.3
2. Update version in package.json
3. Generate changelog: npm run changelog
4. Create PR to main branch
5. Wait for CI/CD pipeline (approx 15 minutes)
6. Get approval from tech lead
7. Merge to main
8. Tag release: git tag v1.2.3 && git push --tags
9. Monitor deployment pipeline
10. Verify health checks pass

Post-Deployment:
□ Smoke test critical paths
□ Check error rates in monitoring dashboard
□ Verify no spike in 5xx errors
□ Monitor performance metrics for 30 minutes
□ Notify team in #releases channel

Rollback (if needed):
1. Revert merge commit
2. Deploy previous version
3. Run database rollback script
4. Notify incident channel
```
**Tags:** deployment, procedures, checklist, production

---

## 🔍 Querying Indexed Text

### Via Claude AI

1. Go to **"Claude AI"** tab
2. **Data Sources**: Select your collection (e.g., "custom_notes")
3. **Ask Questions**:
   - "What were the key decisions from the Q1 planning meeting?"
   - "How do I fix 502 errors according to our troubleshooting guide?"
   - "What's the rate limiter code snippet we documented?"
   - "Summarize all meeting notes from this week"

### Via Ollama AI

1. Go to **"Ollama AI"** tab
2. **Search Collection**: Select your collection
3. **Ask Questions**: Same as Claude AI
4. Works completely offline

### Via Semantic Search

1. Go to **"Search"** tab
2. **Collection**: Select your collection
3. **Search Query**: Enter keywords or questions
4. **Results**: See most relevant indexed texts with similarity scores

---

## 📊 Features & Benefits

### Real-Time Indexing
- **Instant**: Content available immediately after indexing
- **No Delays**: No batch processing or waiting
- **Live Updates**: Add content anytime, query immediately

### Semantic Search
- **Smart Matching**: Finds content by meaning, not just keywords
- **Context-Aware**: Understands intent and context
- **Ranked Results**: Most relevant content appears first

### Organization
- **Collections**: Group related content together
- **Tags**: Add multiple categories to each entry
- **Metadata**: Automatic tracking of word count, timestamps

### AI Integration
- **Claude AI**: Advanced reasoning over your content
- **Ollama AI**: Offline access and analysis
- **RAG**: Retrieval Augmented Generation for accurate answers

### Flexibility
- **Any Text**: Notes, code, docs, procedures, anything
- **Any Length**: From short snippets to long documents
- **Any Format**: Plain text, markdown, code blocks

---

## 📈 Statistics Displayed

After indexing, you'll see:
- **Title**: Your chosen title
- **Collection**: Where it's stored
- **Word Count**: Number of words
- **Character Count**: Number of characters
- **Tags**: Applied tags
- **Text ID**: Unique identifier (for debugging)

---

## 🎨 Best Practices

### 1. Use Descriptive Titles
❌ Bad: "Notes"
✅ Good: "Sprint Planning Meeting - Team Alpha - 2024-02-11"

### 2. Organize with Collections
```
meeting_notes/       - All meeting summaries
procedures/          - Standard operating procedures
troubleshooting/     - Problem solutions
api_docs/           - API documentation
knowledge_base/     - General reference info
code_snippets/      - Reusable code examples
```

### 3. Add Relevant Tags
- Use consistent tag names
- Include: topic, urgency, team, project
- Examples: `security`, `urgent`, `backend`, `production`

### 4. Include Context
Instead of:
```
"Increase timeout to 120s"
```

Write:
```
"Nginx timeout increased to 120s to fix 502 errors on /api/reports endpoint"
```

### 5. Date Your Content
Include dates in titles or content:
- "Meeting Notes - 2024-02-11"
- "Updated: February 11, 2024"

### 6. Reference Sources
If based on other docs/meetings:
```
"Based on architecture review meeting (see notes in meeting_notes/2024-02-05)"
```

---

## 🔄 Update Workflow

To update existing content:
1. Index new version with updated content
2. Same title will create new entry (not update)
3. Both versions remain searchable
4. Or use unique titles with version numbers

**Example:**
- "API Authentication Guide v1"
- "API Authentication Guide v2"

---

## 🎯 Example Workflow

### Scenario: Post-Meeting Documentation

**After a meeting:**

1. **Open Index Text tab**
2. **Title:** "Engineering Weekly - 2024-02-11"
3. **Content:** (paste meeting notes)
```
Attendees: John, Sarah, Mike, Lisa

Agenda:
1. Sprint progress review
2. Q1 roadmap planning
3. Technical debt discussion

Key Decisions:
- Allocate 20% sprint capacity to tech debt
- Migrate to Kubernetes by end of Q1
- Implement feature flags for all new features

Action Items:
- John: Create K8s migration plan [Due: Feb 18]
- Sarah: Research feature flag libraries [Due: Feb 15]
- Mike: Document current tech debt [Due: Feb 12]

Next Meeting: February 18, 2024
```
4. **Collection:** "meeting_notes"
5. **Tags:** engineering, weekly, decisions, action-items
6. **Click Index**

**Later, query with AI:**
- "What did we decide about technical debt in the last meeting?"
- "Who's responsible for the Kubernetes migration plan?"
- "When is the next engineering meeting?"

AI will find and reference your indexed notes!

---

## 🔐 Security & Privacy

### Local Storage
- All content stored locally in Milvus
- No external services involved
- Complete data privacy

### Access Control
- Content accessible via web interface
- Runs on localhost only (by default)
- No authentication (add if needed)

---

## 🐛 Troubleshooting

### "Error indexing text"
- **Check Milvus**: Ensure containers running
- **Check Backend**: Flask server at http://localhost:5000
- **Check Logs**: See `web_server.log`

### "Content not appearing in search"
- **Wait 1-2 seconds**: Indexing needs brief moment
- **Check Collection**: Use same collection name in search
- **Verify Storage**: Check success message appeared

### "AI not finding my content"
- **Collection Selection**: Select correct collection in AI tab
- **Increase Documents**: Try higher "Documents per Source" (top_k)
- **Rephrase Query**: Try different keywords or questions

---

## 📚 Related Features

- **Upload File**: For PDF, TXT files
- **Crawl Website**: For entire websites
- **Jira Integration**: For ticket data
- **GitHub Integration**: For PR data
- **Claude AI**: For querying indexed content
- **Ollama AI**: For offline querying

---

## 🚀 Quick Start

```bash
# 1. Open web interface
open http://localhost:3000

# 2. Go to "Index Text" tab

# 3. Add your first note:
Title: Test Note
Content: This is a test note to verify the system works.
Collection: test_collection
Tags: test

# 4. Click "Index Text Content"

# 5. Go to Claude AI tab

# 6. Collection: Select "test_collection"

# 7. Ask: "What's in my test note?"

# 8. See AI retrieve your content!
```

---

Last Updated: 2026-02-11
Version: 1.0
