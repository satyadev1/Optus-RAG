# Token Usage Tracking & Audit System

## Overview

Comprehensive token usage tracking system for Claude API calls with detailed audit trails, cost analysis, and performance metrics.

---

## Features

### 1. ✅ Automatic Token Tracking
Every Claude API call is automatically tracked with:
- **Input tokens**: Tokens sent (context + question)
- **Output tokens**: Tokens received (answer)
- **Total tokens**: Sum of input + output
- **Cost calculation**: Automatic cost computation based on model pricing
- **Response time**: Milliseconds taken for each request
- **Documents retrieved**: Number of documents from Milvus
- **Question & collection**: What was asked and where it searched
- **Success status**: Whether the request succeeded or failed

### 2. ✅ Cost Breakdown
- **Claude Sonnet 4.5**: $3 per million input tokens, $15 per million output tokens
- **Claude Opus**: $15 per million input tokens, $75 per million output tokens
- **Claude Haiku**: $0.25 per million input tokens, $1.25 per million output tokens

### 3. ✅ Comprehensive Dashboard
New **Token Usage** tab showing:
- **Key Metrics Cards**:
  - Total cost
  - Total tokens (input + output)
  - Average response time
  - Total documents retrieved

- **Recent Queries Table**: Last 50 queries with full details
- **Model Breakdown**: Usage and cost by AI model
- **Collection Breakdown**: Usage by data source (Jira, GitHub, etc.)
- **Daily Cost Trend**: Track spending over time

### 4. ✅ Export Capabilities
- **CSV Export**: Download complete audit trail
- **Filter by period**: Today, Week, Month, All Time
- **Audit compliance**: Full audit trail for cost tracking

---

## Files Created/Modified

### New Files

1. **token_tracker.py**
   - SQLite database for persistent storage
   - `TokenTracker` class with comprehensive tracking
   - Cost calculation for all Claude models
   - Statistics and reporting functions
   - CSV export functionality

2. **frontend/src/components/TokenUsageTab.js**
   - Beautiful dashboard UI
   - Real-time statistics
   - Multiple views (Recent, Breakdown, Trends)
   - Export button
   - Period filtering (Today/Week/Month/All)

### Modified Files

1. **claude_rag.py**
   - Added `time` and `token_tracker` imports
   - Modified `ask_claude()` to capture token usage from API response
   - Modified `query_with_context()` to track usage in database
   - Returns `token_usage` in response

2. **web_interface.py**
   - Added `send_file` import
   - New endpoint: `GET /token_usage/stats` - Get usage statistics
   - New endpoint: `GET /token_usage/cost_breakdown` - Get daily costs
   - New endpoint: `GET /token_usage/export` - Export to CSV

3. **frontend/src/App.js**
   - Added `TokenUsageTab` import
   - Added `FiDollarSign` icon import
   - Added new tab: "Token Usage" with 💰 icon
   - Added TabPanel with TokenUsageTab component

---

## Database Schema

### Table: `token_usage`

```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model TEXT NOT NULL,
    question TEXT NOT NULL,
    collection TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    documents_retrieved INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    user_id TEXT DEFAULT 'default',
    session_id TEXT,
    success BOOLEAN DEFAULT 1
)
```

---

## API Endpoints

### GET /token_usage/stats
Get comprehensive usage statistics

**Query Parameters:**
- `period`: `today`, `week`, `month`, `all` (default: `all`)
- `limit`: Number of recent queries to return (default: 100)

**Response:**
```json
{
  "success": true,
  "stats": {
    "period": "all",
    "summary": {
      "total_requests": 150,
      "total_input_tokens": 450000,
      "total_output_tokens": 85000,
      "total_tokens": 535000,
      "total_cost": 2.625,
      "total_documents": 1050,
      "avg_response_time": 2340,
      "successful_requests": 148,
      "failed_requests": 2
    },
    "recent_queries": [...],
    "model_breakdown": [...],
    "collection_breakdown": [...]
  }
}
```

### GET /token_usage/cost_breakdown
Get daily cost breakdown

**Query Parameters:**
- `period`: `week`, `month` (default: `month`)

**Response:**
```json
{
  "success": true,
  "breakdown": [
    {
      "date": "2024-02-17",
      "requests": 25,
      "tokens": 45000,
      "cost": 0.285
    }
  ]
}
```

### GET /token_usage/export
Export usage data to CSV

**Query Parameters:**
- `period`: `today`, `week`, `month`, `all` (default: `all`)

**Response:**
CSV file download with all tracked data

---

## Usage Examples

### Backend Tracking (Automatic)

Every time Claude is called:
```python
# In claude_rag.py - ask_claude() method
message = self.client.messages.create(...)

# Extract usage
input_tokens = message.usage.input_tokens
output_tokens = message.usage.output_tokens

# Store for tracking
self._last_usage = {
    'input_tokens': input_tokens,
    'output_tokens': output_tokens,
    'total_tokens': input_tokens + output_tokens,
    'response_time_ms': response_time_ms
}
```

```python
# In query_with_context() - automatic tracking
tracker = get_tracker()
tracker.track_usage(
    model='claude-sonnet-4-5',
    question=question,
    collection=collection_name,
    input_tokens=usage_info['input_tokens'],
    output_tokens=usage_info['output_tokens'],
    documents_retrieved=len(documents),
    response_time_ms=usage_info['response_time_ms']
)
```

### Frontend Dashboard

Users can:
1. **View Summary**:
   - Total cost across all queries
   - Token usage breakdown
   - Average response time
   - Total documents retrieved

2. **Browse Recent Queries**:
   - See all recent questions asked
   - View tokens and cost per query
   - Check response times
   - Verify success/failure status

3. **Analyze by Model**:
   - See which Claude models are used
   - Compare costs between models
   - Track request distribution

4. **Analyze by Collection**:
   - See which data sources are queried
   - Compare usage across Jira, GitHub, Documents
   - Identify most-used collections

5. **Track Cost Trends**:
   - Daily spending over time
   - Identify cost spikes
   - Plan budget accordingly

6. **Export for Audit**:
   - Download complete CSV
   - Filter by time period
   - Share with finance/management

---

## Cost Calculation

### Formula
```
Input Cost = (input_tokens / 1,000,000) × input_price_per_MTok
Output Cost = (output_tokens / 1,000,000) × output_price_per_MTok
Total Cost = Input Cost + Output Cost
```

### Example
**Claude Sonnet 4.5 Query:**
- Input: 5,000 tokens
- Output: 1,200 tokens
- Input cost: (5,000 / 1,000,000) × $3 = $0.015
- Output cost: (1,200 / 1,000,000) × $15 = $0.018
- **Total: $0.033**

---

## Dashboard Views

### 1. Key Metrics (Top Cards)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 💰 Total Cost   │  │ 📊 Total Tokens │  │ ⏱️  Avg Time    │  │ 📁 Documents    │
│   $2.6250       │  │   535,000       │  │   2,340ms       │  │   1,050         │
│   150 requests  │  │   450K in       │  │   148 success   │  │   Avg 7 per Q   │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2. Recent Queries Table
```
Timestamp             Question                    Collection   Tokens   Cost      Time
2024-02-17 10:30:15  How to use ALP?             all          6,200    $0.0330   2,150ms
2024-02-17 10:28:42  Firewall Docker issues      github_prs   5,800    $0.0297   1,980ms
2024-02-17 10:25:11  Nexus configuration help    all          7,100    $0.0381   2,450ms
```

### 3. Model Breakdown
```
🤖 claude-sonnet-4-5
   150 requests • 535,000 tokens • $2.625
   [████████████████████████████] 100%
```

### 4. Collection Breakdown
```
📋 all (All Collections)
   95 requests • 340,000 tokens • $1.785
   [████████████████████░░░░░░░░] 68%

🔀 github_prs
   35 requests • 125,000 tokens • $0.562
   [████████░░░░░░░░░░░░░░░░░░░░] 21%

📋 jira_tickets
   20 requests • 70,000 tokens • $0.278
   [████░░░░░░░░░░░░░░░░░░░░░░░░] 11%
```

### 5. Daily Cost Trend
```
Date          Requests   Tokens    Cost
2024-02-17    25         45,000    $0.285
2024-02-16    32         58,000    $0.348
2024-02-15    18         31,000    $0.195
```

---

## Audit Trail

### What's Tracked
Every API call stores:
- ✅ Exact timestamp
- ✅ Full question text (up to 500 chars)
- ✅ Model used
- ✅ Collection searched
- ✅ Input/Output/Total tokens
- ✅ Calculated cost
- ✅ Documents retrieved from Milvus
- ✅ Response time in milliseconds
- ✅ Success/failure status

### Data Retention
- **Default**: Keep all data indefinitely
- **Cleanup**: Optional `clear_old_data(days=90)` function
- **Export**: CSV export anytime for external archiving

### Compliance
- **Complete audit trail**: Every API call logged
- **Cost tracking**: Detailed breakdown by time, model, collection
- **Performance metrics**: Response times and success rates
- **Exportable**: CSV format for finance/accounting systems

---

## Benefits

### For Users
- 💰 **Cost Awareness**: See exactly how much each query costs
- 📊 **Usage Insights**: Understand which questions use more tokens
- 🚀 **Performance**: Track response times and identify slow queries
- 📈 **Trends**: Monitor usage patterns over time

### For Admins
- 💳 **Budget Control**: Track spending and set alerts
- 📑 **Audit Compliance**: Complete trail for financial reporting
- 🎯 **Optimization**: Identify expensive queries to optimize
- 📊 **Analytics**: Understand user behavior and data source usage

### For Finance
- 💵 **Accurate Billing**: Real costs, not estimates
- 📥 **Export Ready**: CSV format for accounting systems
- 📅 **Historical Data**: Track costs over time
- 🔍 **Detailed Breakdown**: By model, collection, user, time

---

## Status: ✅ Complete

All components implemented:
- ✅ Backend tracking in claude_rag.py
- ✅ SQLite database (token_tracker.py)
- ✅ API endpoints (/token_usage/*)
- ✅ Frontend dashboard (TokenUsageTab.js)
- ✅ Tab integration in App.js
- ✅ Automatic cost calculation
- ✅ CSV export functionality
- ✅ Multiple view modes (Recent, Models, Collections, Trends)
- ✅ Period filtering (Today, Week, Month, All)

## Testing

1. **Start backend**: `python web_interface.py`
2. **Ask Claude a question** in the AI Querying tab
3. **Check Token Usage tab** to see:
   - Updated metrics
   - New query in Recent Queries
   - Cost calculated
   - Response time recorded
4. **Export CSV** to verify audit trail

Every Claude API call is now tracked with complete audit information!
