# Confidence Score System

## Overview

Comprehensive confidence scoring system that evaluates the reliability of AI responses based on source quality, quantity, diversity, and relevance.

---

## Confidence Score Calculation

### Algorithm

The confidence score is calculated using **4 weighted factors**:

```python
Total Confidence = (Source Quality × 40%) +
                   (Source Quantity × 20%) +
                   (Source Diversity × 20%) +
                   (High-Quality Sources × 20%)
```

---

### Factor 1: Source Quality (40% weight)

**Calculation:**
```python
avg_score = sum(source.score for source in sources) / len(sources)
source_quality = avg_score × 0.4
```

**Meaning:**
- Average relevance score of all sources
- Higher relevance = higher confidence
- Most important factor (40% weight)

**Example:**
- Sources: [0.95, 0.87, 0.73, 0.68, 0.61]
- Average: 0.768
- Contribution: 0.768 × 0.4 = **0.307** (30.7%)

---

### Factor 2: Source Quantity (20% weight)

**Calculation:**
```python
quantity_factor = min(num_documents / 10.0, 1.0) × 0.2
```

**Meaning:**
- More sources = higher confidence
- Normalized: 1 source = 0%, 10+ sources = 100%
- Linear scaling between 1-10

**Example:**
- 7 documents found
- Contribution: (7/10) × 0.2 = **0.14** (14%)

---

### Factor 3: Source Diversity (20% weight)

**Calculation:**
```python
unique_sources = len(set(source.collection for source in sources))
diversity_factor = min(unique_sources / 3.0, 1.0) × 0.2
```

**Meaning:**
- Multiple source types = higher confidence
- Normalized: 1 type = 0%, 3+ types = 100%
- Validates information across different data sources

**Example:**
- Collections: [jira_tickets, github_prs, documents]
- Unique: 3
- Contribution: (3/3) × 0.2 = **0.2** (20%)

---

### Factor 4: High-Quality Sources (20% weight)

**Calculation:**
```python
high_quality_count = sum(1 for s in sources if s.score > 0.8)
high_quality_factor = min(high_quality_count / 3.0, 1.0) × 0.2
```

**Meaning:**
- Presence of excellent matches (score > 80%)
- Normalized: 0 excellent = 0%, 3+ excellent = 100%
- Ensures some sources are very relevant

**Example:**
- High-quality sources (>0.8): 2
- Contribution: (2/3) × 0.2 = **0.133** (13.3%)

---

## Confidence Levels

### Scoring Thresholds

| Score Range | Level | Badge Color | Meaning |
|-------------|-------|-------------|---------|
| 0.80 - 1.00 | Very High | 🟢 Green | Excellent data, highly reliable |
| 0.65 - 0.79 | High | 🔵 Blue | Good data, reliable |
| 0.50 - 0.64 | Medium | 🟡 Yellow | Adequate data, fairly reliable |
| 0.30 - 0.49 | Low | 🟠 Orange | Limited data, less reliable |
| 0.00 - 0.29 | Very Low | 🔴 Red | Insufficient data, unreliable |

---

## Example Calculations

### Example 1: High Confidence Response

**Query:** "How to configure Firewall Docker?"

**Sources Retrieved:**
```
Collection        Score
────────────────────────
jira_tickets      0.95
github_prs        0.92
documents         0.88
jira_tickets      0.85
github_prs        0.82
documents         0.78
jira_tickets      0.75
```

**Calculation:**
```
Factor 1: Source Quality
  Avg score: (0.95+0.92+0.88+0.85+0.82+0.78+0.75) / 7 = 0.85
  Contribution: 0.85 × 0.4 = 0.34

Factor 2: Source Quantity
  Documents: 7
  Contribution: (7/10) × 0.2 = 0.14

Factor 3: Source Diversity
  Unique collections: 3 (jira, github, docs)
  Contribution: (3/3) × 0.2 = 0.2

Factor 4: High-Quality Sources
  Sources > 0.8: 5
  Contribution: (5/3) × 0.2 = 0.2 (capped at 0.2)

Total Confidence: 0.34 + 0.14 + 0.2 + 0.2 = 0.88
Level: Very High
```

**Result:** 🟢 **Very High (88%)**

---

### Example 2: Medium Confidence Response

**Query:** "What is ALP pricing?"

**Sources Retrieved:**
```
Collection        Score
────────────────────────
github_prs        0.68
github_prs        0.65
documents         0.61
github_prs        0.58
```

**Calculation:**
```
Factor 1: Source Quality
  Avg score: (0.68+0.65+0.61+0.58) / 4 = 0.63
  Contribution: 0.63 × 0.4 = 0.252

Factor 2: Source Quantity
  Documents: 4
  Contribution: (4/10) × 0.2 = 0.08

Factor 3: Source Diversity
  Unique collections: 2 (github, docs)
  Contribution: (2/3) × 0.2 = 0.133

Factor 4: High-Quality Sources
  Sources > 0.8: 0
  Contribution: (0/3) × 0.2 = 0

Total Confidence: 0.252 + 0.08 + 0.133 + 0 = 0.465
Level: Low
```

**Result:** 🟠 **Low (47%)**

---

### Example 3: Very High Confidence Response

**Query:** "Firewall Docker issues in JIRA"

**Sources Retrieved:**
```
Collection        Score
────────────────────────
jira_tickets      0.97
jira_tickets      0.95
github_prs        0.93
documents         0.91
jira_tickets      0.89
github_prs        0.87
documents         0.85
jira_tickets      0.83
github_prs        0.81
documents         0.79
```

**Calculation:**
```
Factor 1: Source Quality
  Avg score: 0.88
  Contribution: 0.88 × 0.4 = 0.352

Factor 2: Source Quantity
  Documents: 10
  Contribution: (10/10) × 0.2 = 0.2

Factor 3: Source Diversity
  Unique collections: 3
  Contribution: (3/3) × 0.2 = 0.2

Factor 4: High-Quality Sources
  Sources > 0.8: 8
  Contribution: (8/3) × 0.2 = 0.2 (capped)

Total Confidence: 0.352 + 0.2 + 0.2 + 0.2 = 0.952
Level: Very High
```

**Result:** 🟢 **Very High (95%)**

---

## Display in Chat Interface

### Badge Display

**Visual:**
```
┌─────────────────────────────────────────┐
│ [claude-sonnet-4-5] [🎯 Very High (88%)]│
│                                          │
│ To configure Firewall Docker...         │
│                                          │
│ Sources: [1] FIREWALL-1234 [95%]...     │
└─────────────────────────────────────────┘
```

**Badge Colors:**
- 🟢 Green (≥80%): Very High
- 🔵 Blue (65-79%): High
- 🟡 Yellow (50-64%): Medium
- 🟠 Orange (30-49%): Low
- 🔴 Red (<30%): Very Low

### Tooltip Details

**Hover over confidence badge to see breakdown:**
```
Quality: 0.85 | Quantity: 7 | Diversity: 3 | High-Quality: 5
```

**Factors Explained:**
- **Quality**: Average relevance score
- **Quantity**: Number of sources found
- **Diversity**: Number of unique collections
- **High-Quality**: Count of sources with score > 80%

---

## Implementation

### Backend (claude_rag.py & ollama_rag.py)

```python
def calculate_confidence(self, sources, num_documents):
    # Calculate 4 factors
    avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
    source_quality = avg_score * 0.4

    quantity_factor = min(num_documents / 10.0, 1.0) * 0.2

    unique_sources = len(set(s.get('collection', '') for s in sources))
    diversity_factor = min(unique_sources / 3.0, 1.0) * 0.2

    high_quality_count = sum(1 for s in sources if s.get('score', 0) > 0.8)
    high_quality_factor = min(high_quality_count / 3.0, 1.0) * 0.2

    # Total
    total_confidence = (source_quality + quantity_factor +
                       diversity_factor + high_quality_factor)

    return {
        'score': round(total_confidence, 3),
        'level': determine_level(total_confidence),
        'factors': {...}
    }
```

### Frontend (ChatInterface.js)

```jsx
{msg.confidence && (
  <Tooltip label={`Quality: ${msg.confidence.factors.source_quality}...`}>
    <Badge
      colorScheme={
        msg.confidence.score >= 0.8 ? 'green' :
        msg.confidence.score >= 0.65 ? 'blue' :
        msg.confidence.score >= 0.5 ? 'yellow' :
        msg.confidence.score >= 0.3 ? 'orange' : 'red'
      }
    >
      🎯 {msg.confidence.level} ({(msg.confidence.score * 100).toFixed(0)}%)
    </Badge>
  </Tooltip>
)}
```

---

## Use Cases

### 1. User Decision Making

**Scenario:** User asks "What is the pricing for ALP?"

**Response:**
- Confidence: 🟠 **Low (47%)**
- User sees: Limited data available
- Action: User knows to verify from official docs

### 2. High-Confidence Answers

**Scenario:** User asks "How to fix FIREWALL-1234?"

**Response:**
- Confidence: 🟢 **Very High (95%)**
- User sees: Excellent data, highly reliable
- Action: User can trust the answer with confidence

### 3. Missing Information Detection

**Scenario:** User asks about a new, undocumented feature

**Response:**
- Confidence: 🔴 **Very Low (15%)**
- User sees: Insufficient data
- Action: User understands answer is speculative

---

## Benefits

### For Users
- ✅ **Transparency**: Know how reliable each answer is
- ✅ **Quick assessment**: Glance at badge color
- ✅ **Informed decisions**: Understand when to verify
- ✅ **Trust calibration**: Higher confidence = more trust

### For Admins
- ✅ **Quality monitoring**: Track average confidence scores
- ✅ **Data gaps**: Identify topics with low confidence
- ✅ **Performance metrics**: Measure retrieval quality
- ✅ **System optimization**: Focus on improving low-confidence areas

### For Auditors
- ✅ **Answer quality**: Quantifiable reliability metric
- ✅ **Traceability**: Understand basis for each score
- ✅ **Compliance**: Document answer reliability
- ✅ **Risk assessment**: Flag low-confidence responses

---

## Interpretation Guide

### Very High (≥80%) 🟢
- **Meaning**: Excellent data coverage
- **Trust level**: High
- **Action**: Can rely on answer with confidence
- **Characteristics**: Multiple high-quality sources, diverse collections

### High (65-79%) 🔵
- **Meaning**: Good data coverage
- **Trust level**: Good
- **Action**: Answer is reliable
- **Characteristics**: Good sources, decent quantity

### Medium (50-64%) 🟡
- **Meaning**: Adequate data
- **Trust level**: Fair
- **Action**: Consider verifying critical details
- **Characteristics**: Moderate sources, limited diversity

### Low (30-49%) 🟠
- **Meaning**: Limited data
- **Trust level**: Low
- **Action**: Verify from official sources
- **Characteristics**: Few sources, low relevance

### Very Low (<30%) 🔴
- **Meaning**: Insufficient data
- **Trust level**: Very low
- **Action**: Treat as speculative, verify independently
- **Characteristics**: Very few or no relevant sources

---

## Response Structure

```json
{
  "answer": "...",
  "sources": [...],
  "model": "claude-sonnet-4-5",
  "confidence_score": {
    "score": 0.88,
    "level": "Very High",
    "factors": {
      "source_quality": 0.85,
      "source_quantity": 7,
      "source_diversity": 3,
      "high_quality_sources": 5
    }
  }
}
```

---

## Files Modified

1. **claude_rag.py**
   - Added `calculate_confidence()` method
   - Returns confidence score in response
   - 4-factor weighted calculation

2. **ollama_rag.py**
   - Added `calculate_confidence()` method
   - Same algorithm as Claude
   - Consistent scoring across AI models

3. **ChatInterface.js**
   - Displays confidence badge
   - Color-coded by level
   - Tooltip with factor breakdown
   - Stored in message object

---

## Status: ✅ Complete

All confidence scoring features implemented:
- ✅ 4-factor weighted algorithm
- ✅ Score calculation (0.0 - 1.0)
- ✅ 5-level classification (Very High to Very Low)
- ✅ Color-coded badges (Green to Red)
- ✅ Detailed factor breakdown
- ✅ Tooltip with metrics
- ✅ Applied to both Claude and Ollama
- ✅ Displayed in chat messages
- ✅ Stored in chat history

Users now see **confidence scores** for every AI response, helping them understand answer reliability at a glance!
