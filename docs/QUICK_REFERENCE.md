# 🚀 Quick Reference - NEXUS Jira Dataset

**Last Updated**: February 18, 2026 at 4:00 PM
**Status**: ✅ Ready for Production

---

## 📊 Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Tickets** | 2,500 |
| **Date Range** | Feb 19, 2024 - Feb 18, 2026 (2 years) |
| **Ticket Range** | NEXUS-41973 to NEXUS-50736 |
| **In Milvus** | 2,500 (100%) ✅ |
| **Success Rate** | 100% (no failures) |
| **File Size** | 96.88 MB |

---

## 🎫 5 Test Tickets for UI

### Quick Copy-Paste List:
```
NEXUS-42793
NEXUS-42016
NEXUS-42034
NEXUS-44150
NEXUS-41973
```

### Details:

**1. NEXUS-42793** - Your Bug (PyPI)
- Summary: Invalid pypi component version breaks PCCS
- Assignee: Satyadev Komaragiri (YOU)
- Priority: Medium | Status: Done | Comments: 6

**2. NEXUS-42016** - Critical Bug (S3)
- Summary: s3 blob store fails to load unless it has s3:GetBucketPolicy permission
- Assignee: Lisa Durant
- Priority: Critical | Status: Done | Comments: 7

**3. NEXUS-42034** - Policy Violation
- Summary: Policy Violation apache-mime4j-core : 0.8.9
- Assignee: Igor Serdyuchenko
- Priority: Major | Status: Done | Comments: 0

**4. NEXUS-44150** - Story (Conan Search)
- Summary: Update Conan Search to support Conan settings and base version
- Assignee: Ivan Contreras
- Priority: Major | Status: Done | Comments: 19 🔥

**5. NEXUS-41973** - Epic (H2 Upgrade)
- Summary: Technical discovery for H2 upgrade
- Assignee: Nicholas Blair
- Priority: Major | Status: Done | Comments: 9

---

## 🔍 Test Query Examples

### For RAG Testing:
```
"Show me ticket NEXUS-42793"
"Find critical bugs in S3 blob store"
"What policy violations were found?"
"Conan search feature implementation"
"H2 database upgrade tickets"
```

### For Semantic Search:
```
"Security vulnerabilities in dependencies"
"Firewall feature tickets"
"Docker quarantine issues"
"Storage and blob store problems"
"Database upgrade technical discovery"
```

---

## 📁 Key Files

### Dataset
`jira_nexus_last_2_years_20260218_155253.json` (96.88 MB)

### Test Data
`ui_test_tickets.json` - 5 tickets for UI testing

### Stats
`jira_nexus_last_2_years_stats_20260218_155253.json`

### Summary
`milvus_last_2_years_summary.json`

---

## 🎯 Quick Stats

- **74.3%** of tickets are Done
- **39.4%** are Stories (features)
- **20.8%** are Bugs
- **47.4%** are Major priority
- **28%** are Unassigned

---

## 🚀 Milvus Query Endpoint

**URL**: `http://localhost:5001/query_jira`

**Example**:
```bash
curl -X POST http://localhost:5001/query_jira \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me NEXUS-42793",
    "collection": "jira_tickets",
    "top_k": 5
  }'
```

---

## ✅ Mission Complete Checklist

- [x] Fetched 2,500 tickets from last 2 years
- [x] Stored 2,500 tickets in Milvus (100%)
- [x] Generated comprehensive statistics
- [x] Created test dataset (5 tickets)
- [x] Documented everything
- [x] Ready for UI testing

---

**Status**: ✅ **ALL SYSTEMS GO** 🚀
