# 🚀 Quick Start Guide - Enhanced AI System

**Last Updated**: February 18, 2026
**Status**: ✅ All Features Operational

---

## ⚡ Quick Commands

### Check Server Status
```bash
curl http://localhost:5001/health
```

### Ask a Question (Multi-Collection Search)
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is NEXUS-48549 about?",
    "collection": "all",
    "top_k": 5
  }'
```

### Upload a CSV File
```bash
curl -X POST http://localhost:5001/upload_file \
  -F "file=@/path/to/your/file.csv" \
  -F "collection=jira_tickets"
```

### Restart Server
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
./restart_server.sh
```

### Run Tests
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
source venv/bin/activate
python3 test_multi_collection_rag.py
```

---

## 🎯 Key Features

### 1. Multi-Collection AI Search ⭐
**What it does**: Searches across ALL your data sources at once
- JIRA tickets (3,816)
- Codebase analysis (23,439)
- GitHub PRs (1,451)
- Developer personas (297)
- Custom notes (129)
- And more...

**Total**: 29,153 searchable documents

**Example**:
```bash
# This searches EVERYTHING
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"Your question","collection":"all"}'
```

### 2. Large File Upload
**What it does**: Upload CSV files up to 100MB with automatic chunking

**Example**:
```bash
curl -X POST http://localhost:5001/upload_file \
  -F "file=@large_data.csv" \
  -F "collection=jira_tickets"
```

### 3. Response Time Tracking
**What it does**: Every API call returns how long it took

**Example Response**:
```json
{
  "success": true,
  "answer": "Your answer...",
  "response_time_seconds": 54.7,
  "timestamp": "2026-02-18T16:32:33"
}
```

### 4. Health Monitoring
**What it does**: Check if server and Milvus are running

**Example**:
```bash
curl http://localhost:5001/health
```

---

## 📊 What You Get from Multi-Collection Search

When you ask: **"What are the firewall issues in NEXUS?"**

The AI searches:
1. **JIRA tickets** → Finds tickets about firewall
2. **Codebase** → Finds code related to firewall
3. **GitHub PRs** → Finds PR discussions about firewall
4. **Developer personas** → Finds who worked on firewall
5. **Custom notes** → Finds any notes about firewall

Then it **synthesizes everything** into one comprehensive answer!

---

## 🎨 Frontend Integration Example

```javascript
// Multi-collection search with response time
async function askQuestion(question) {
  const response = await fetch('/ask_claude', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      question: question,
      collection: 'all',  // Search everything!
      top_k: 5
    })
  });

  const data = await response.json();

  // Display answer
  document.getElementById('answer').innerText = data.answer;

  // Display response time
  document.getElementById('time').innerText =
    `Responded in ${data.response_time_seconds} seconds`;

  // Display sources
  const collections = new Set(
    data.sources.map(s => s.collection)
  );
  document.getElementById('sources').innerText =
    `Sources: ${data.sources.length} documents from ${collections.size} collections`;
}
```

---

## 🔧 Troubleshooting

### Server not responding?
```bash
# Restart the server
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
./restart_server.sh
```

### Want to see what's happening?
```bash
# Check logs
tail -f backend.log
```

### Upload failing?
- Max file size: 100MB
- Automatically chunked into 1000-row segments
- Check that file is valid CSV format

### Query taking too long?
- Multi-collection search takes ~50-60 seconds
- This is normal - searching 29K+ documents
- Reduce `top_k` parameter for faster results

---

## 📚 Documentation

Detailed docs in the same directory:

1. **IMPLEMENTATION_COMPLETE_SUMMARY.md** - Overview of all features
2. **MULTI_COLLECTION_RAG_COMPLETE.md** - Deep dive into multi-collection search
3. **UPLOAD_STATUS_SUMMARY.md** - CSV upload details
4. **CHUNKING_AND_TIMING_IMPLEMENTATION.md** - Technical implementation

---

## 🎯 Example Queries to Try

### 1. Find a specific JIRA ticket
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"What is NEXUS-48549 about?","collection":"all"}'
```

### 2. Technical issue analysis
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the firewall configuration issues?","collection":"all"}'
```

### 3. Code search
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me authentication-related code","collection":"all"}'
```

### 4. Developer info
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"Who works on authentication features?","collection":"all"}'
```

### 5. PR analysis
```bash
curl -X POST http://localhost:5001/ask_claude \
  -H "Content-Type: application/json" \
  -d '{"question":"Show recent PRs about Docker","collection":"all"}'
```

---

## ✅ Current Status

**Server**: Running (PID: 57413) ✅
**Milvus**: Connected (8 collections) ✅
**Searchable Collections**: 7 active ✅
**Total Documents**: 29,153 ✅
**All Features**: Operational ✅

---

## 🎉 Ready to Use!

Your AI system is **production-ready** with:
- ✅ Comprehensive multi-collection search
- ✅ Large file upload support
- ✅ Performance tracking
- ✅ Health monitoring

Start asking questions and enjoy the comprehensive, multi-source AI analysis!

**Need help?** Check the detailed documentation files in this directory.
