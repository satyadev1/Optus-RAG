# Jira Issue Retrieval Guide - Using Jira Python Package

## Overview

Complete guide to retrieving all issues from Jira using the official Jira Python package with progress tracking and Milvus integration.

---

## 📦 Files Created

1. **`fetch_all_jira_issues.py`** - Main retrieval script with comprehensive features
2. **`jira_examples.py`** - 13 common use case examples
3. **`test_jira_connection.py`** - Connection verification script

---

## 🚀 Quick Start

### 1. Test Connection

```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
source venv/bin/activate
python3 test_jira_connection.py
```

**Expected Output:**
```
✅ Connected successfully!
Total: 83 projects
Fetched 5 recent issues
```

### 2. List All Projects

```bash
python3 -c "
from fetch_all_jira_issues import JiraIssueRetriever
retriever = JiraIssueRetriever()
retriever.get_all_projects()
"
```

### 3. Fetch All Issues from a Project

```bash
python3 -c "
from fetch_all_jira_issues import JiraIssueRetriever
retriever = JiraIssueRetriever()
issues = retriever.fetch_all_issues(projects=['NEXUS'])
print(f'Fetched {len(issues)} issues')
"
```

---

## 📚 Usage Examples

### Example 1: Fetch All Issues from Specific Projects

```python
from fetch_all_jira_issues import JiraIssueRetriever

# Initialize
retriever = JiraIssueRetriever()

# Fetch from multiple projects
issues = retriever.fetch_all_issues(
    projects=['NEXUS', 'IQ', 'CLM'],
    progress_file="jira_multi_project_progress.json"
)

# Get statistics
stats = retriever.get_issue_statistics(issues)
retriever.print_statistics(stats)

# Save to JSON
retriever.save_to_json(issues, 'all_issues.json')
```

### Example 2: Fetch Recently Updated Issues

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

# Last 7 days
issues = retriever.fetch_all_issues(
    jql_query='updated >= -7d ORDER BY updated DESC',
    max_results=100,
    progress_file="recent_issues_progress.json"
)

print(f"Fetched {len(issues)} recent issues")
```

### Example 3: Fetch Issues by Status

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

# All open issues
issues = retriever.fetch_all_issues(
    jql_query='status = "Open" ORDER BY created DESC',
    progress_file="open_issues_progress.json"
)

# All in-progress issues
issues = retriever.fetch_all_issues(
    jql_query='status = "In Progress" ORDER BY created DESC',
    progress_file="inprogress_issues_progress.json"
)
```

### Example 4: Fetch Your Assigned Issues

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='assignee = currentUser() ORDER BY updated DESC',
    progress_file="my_issues_progress.json"
)
```

### Example 5: Fetch High Priority Issues

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='priority in (Highest, High) AND resolution = Unresolved',
    progress_file="high_priority_progress.json"
)
```

### Example 6: Fetch Issues in Date Range

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='created >= "2026-01-01" AND created <= "2026-02-18"',
    progress_file="daterange_progress.json"
)
```

### Example 7: Fetch Issues with Specific Label

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='labels = "security" ORDER BY created DESC',
    progress_file="security_issues_progress.json"
)
```

### Example 8: Fetch Specific Issue Keys

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

issue_keys = ['NEXUS-50206', 'NEXUS-50393', 'NEXUS-48549']
issues = retriever.fetch_all_issues(
    jql_query=f'key in ({", ".join(issue_keys)})',
    progress_file="specific_issues_progress.json"
)
```

### Example 9: Export to CSV

```python
from fetch_all_jira_issues import JiraIssueRetriever
import csv

retriever = JiraIssueRetriever()

# Fetch issues
issues = retriever.fetch_all_issues(projects=['NEXUS'])

# Export to CSV
with open('issues.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Key', 'Summary', 'Status', 'Assignee', 'Created'])

    for issue in issues:
        writer.writerow([
            issue.key,
            issue.fields.summary,
            issue.fields.status.name,
            issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
            str(issue.fields.created)
        ])

print("Exported to issues.csv")
```

### Example 10: Get Project Statistics

```python
from fetch_all_jira_issues import JiraIssueRetriever

retriever = JiraIssueRetriever()

# Get all projects
projects = retriever.get_all_projects()

# Get issue count for each
for project in projects[:10]:
    count = retriever.get_project_issue_count(project.key)
    print(f"{project.key}: {count:,} issues")
```

---

## 🔍 JQL Query Reference

### Common JQL Queries

```sql
-- All issues from a project
project = NEXUS

-- Multiple projects
project in (NEXUS, IQ, CLM)

-- Recently updated (last 7 days)
updated >= -7d

-- Date range
created >= "2026-01-01" AND created <= "2026-12-31"

-- By status
status = "Open"
status in ("Open", "In Progress", "Reopened")
resolution = Unresolved

-- By assignee
assignee = currentUser()
assignee = "email@company.com"
assignee is EMPTY  -- Unassigned

-- By priority
priority in (Highest, High)
priority = Blocker

-- By type
type = Bug
type in (Bug, Task, Story)

-- With labels
labels = "security"
labels in ("security", "performance")

-- Complex queries
project = NEXUS AND status = "Open" AND priority = High
project in (NEXUS, IQ) AND assignee = currentUser() AND updated >= -7d
```

---

## 📊 Data Extracted

For each issue, the script extracts:

**Basic Fields:**
- Key, ID, Summary, Description
- Issue Type, Status, Priority, Resolution
- Created, Updated, Resolved dates
- URL

**People:**
- Reporter (name, email)
- Assignee (name, email)
- Creator (name, email)

**Project:**
- Key, Name, ID

**Metadata:**
- Labels
- Components
- Fix Versions
- Affected Versions
- Custom fields (story points, epic link)

**Rich Data:**
- Comments (author, date, body)
- Attachments (filename, size, type)
- Changelog/History (all changes)
- Subtasks
- Issue Links
- Watchers

---

## 📈 Progress Tracking

Progress is saved to JSON and can be monitored in real-time:

```python
# Start fetching with progress tracking
issues = retriever.fetch_all_issues(
    projects=['NEXUS'],
    progress_file="nexus_progress.json"
)
```

**Progress File Format:**
```json
{
  "status": "processing",
  "task_type": "jira",
  "task_name": "Fetching All Jira Issues",
  "total_items": 5000,
  "items_processed": 2500,
  "items_successful": 2500,
  "items_failed": 0,
  "current_item": "NEXUS-12345: Fix authentication...",
  "progress_percent": 50,
  "elapsed_seconds": 120,
  "estimated_remaining_seconds": 120,
  "processing_rate": 20.83
}
```

**Monitor Progress:**
```bash
# Watch progress in real-time
watch -n 2 'cat nexus_progress.json | python3 -m json.tool'

# Or use the viewer
python3 view_progress.py nexus_progress.json
```

---

## 🎯 Use Cases

### Use Case 1: Security Audit

Fetch all security-related issues:

```python
retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='labels = "security" OR summary ~ "security" OR summary ~ "vulnerability"',
    progress_file="security_audit_progress.json"
)

# Analyze by severity
stats = retriever.get_issue_statistics(issues)
retriever.print_statistics(stats)

# Export for review
retriever.save_to_json(issues, 'security_audit.json')
```

### Use Case 2: Sprint Report

Get all issues from current sprint:

```python
retriever = JiraIssueRetriever()

issues = retriever.fetch_all_issues(
    jql_query='sprint = "Sprint 23" AND project = NEXUS',
    progress_file="sprint_report_progress.json"
)

# Get statistics
stats = retriever.get_issue_statistics(issues)
print(f"Sprint 23 Status:")
print(f"  Total: {stats['total_issues']}")
print(f"  Done: {stats['by_status'].get('Done', 0)}")
print(f"  In Progress: {stats['by_status'].get('In Progress', 0)}")
print(f"  Open: {stats['by_status'].get('Open', 0)}")
```

### Use Case 3: Team Workload

Analyze team member workload:

```python
retriever = JiraIssueRetriever()

# Get all open issues
issues = retriever.fetch_all_issues(
    jql_query='project = NEXUS AND resolution = Unresolved',
    progress_file="workload_progress.json"
)

stats = retriever.get_issue_statistics(issues)

print("Team Workload:")
for assignee, count in sorted(stats['by_assignee'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {assignee}: {count} issues")
```

### Use Case 4: Bug Tracking

Track all bugs and their status:

```python
retriever = JiraIssueRetriever()

bugs = retriever.fetch_all_issues(
    jql_query='project = NEXUS AND type = Bug',
    progress_file="bugs_progress.json"
)

stats = retriever.get_issue_statistics(bugs)

print("Bug Statistics:")
print(f"  Total Bugs: {stats['total_issues']}")
print(f"  Open: {stats['by_status'].get('Open', 0)}")
print(f"  Resolved: {stats['by_status'].get('Resolved', 0)}")
print(f"  Closed: {stats['by_status'].get('Closed', 0)}")
```

### Use Case 5: Store in Milvus

Fetch and store in Milvus for AI queries:

```python
from fetch_all_jira_issues import JiraIssueRetriever
import requests

retriever = JiraIssueRetriever()

# Fetch issues
issues = retriever.fetch_all_issues(
    projects=['NEXUS'],
    progress_file="milvus_import_progress.json"
)

# Extract data
all_data = []
for issue in issues:
    data = retriever.extract_issue_data(issue)
    all_data.append(data)

# Store in Milvus via API
for data in all_data:
    requests.post('http://localhost:5001/fetch_jira', json={
        'jira_input': data['key'],
        'collection': 'jira_tickets'
    })

print(f"Stored {len(all_data)} issues in Milvus")
```

---

## 🔧 Advanced Options

### Custom Batch Size

```python
# Modify batch size for performance tuning
issues = retriever.fetch_all_issues(
    projects=['NEXUS'],
    max_results=5000  # Limit total results
)
```

### Include/Exclude Fields

```python
# Search with specific fields only
issues = retriever.jira.search_issues(
    'project = NEXUS',
    fields='summary,status,assignee',  # Only these fields
    maxResults=100
)
```

### Expand Options

```python
# Expand specific data
issues = retriever.jira.search_issues(
    'project = NEXUS',
    expand='changelog,renderedFields,operations',
    maxResults=100
)
```

---

## 📊 Performance Tips

### 1. Use Specific Projects

```python
# Faster - specific project
issues = retriever.fetch_all_issues(projects=['NEXUS'])

# Slower - all projects
issues = retriever.fetch_all_issues()
```

### 2. Limit Results for Testing

```python
# Test with small dataset first
issues = retriever.fetch_all_issues(
    projects=['NEXUS'],
    max_results=100  # Only 100 issues
)
```

### 3. Use Filters in JQL

```python
# Faster - filtered query
issues = retriever.fetch_all_issues(
    jql_query='project = NEXUS AND updated >= -30d'
)

# Slower - fetch all then filter in Python
```

### 4. Batch Processing

The script automatically batches requests (100 issues per API call) for optimal performance.

---

## 🐛 Troubleshooting

### Error: "Unbounded JQL queries not allowed"

**Problem:** Jira requires bounded queries (must specify project or date range).

**Solution:** Always include project filter or date range:
```python
# ❌ Bad
jql_query='status = Open'

# ✅ Good
jql_query='project = NEXUS AND status = Open'
```

### Error: "Authentication failed"

**Problem:** Invalid credentials in `.env` file.

**Solution:** Check your `.env` file:
```bash
JIRA_URL=https://sonatype.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_token_here
```

### Error: "Rate limit exceeded"

**Problem:** Too many API requests in short time.

**Solution:** Add delays between batches:
```python
import time
time.sleep(1)  # 1 second delay between batches
```

### Progress File Not Updating

**Problem:** Progress file permissions or path issue.

**Solution:** Use absolute path:
```python
progress_file="/full/path/to/progress.json"
```

---

## 📝 Summary

**Created Scripts:**
1. `fetch_all_jira_issues.py` - Main retrieval with progress tracking
2. `jira_examples.py` - 13 common use cases
3. `test_jira_connection.py` - Connection verification

**Features:**
- ✅ Fetch all issues from Jira with pagination
- ✅ Progress tracking with real-time updates
- ✅ Comprehensive data extraction (comments, attachments, history)
- ✅ Statistics and reporting
- ✅ Export to JSON/CSV
- ✅ Milvus integration ready

**Quick Commands:**
```bash
# Test connection
python3 test_jira_connection.py

# Run examples
python3 jira_examples.py

# Fetch all issues from NEXUS project
python3 -c "
from fetch_all_jira_issues import JiraIssueRetriever
retriever = JiraIssueRetriever()
issues = retriever.fetch_all_issues(projects=['NEXUS'])
retriever.save_to_json(issues, 'nexus_issues.json')
"
```

---

**Ready to retrieve all Jira issues! 🚀**
