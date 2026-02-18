# How Milvus Stores and Retrieves Code Embeddings

## Overview

Milvus is a **vector database** optimized for storing and searching high-dimensional vectors (embeddings). Think of it as a specialized database for AI similarity search.

---

## Part 1: Storing Code Embeddings

### Step-by-Step Storage Process

```
┌─────────────────────────────────────────────────────────────────┐
│  1. READ CODE FILE                                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  SecurityCrowdIngesterTest.java                        │    │
│  │  ────────────────────────────────────────              │    │
│  │  public class SecurityCrowdIngesterTest {              │    │
│  │      @Test                                             │    │
│  │      public void testIngest() {                        │    │
│  │          // test code...                               │    │
│  │      }                                                  │    │
│  │  }                                                      │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. EXTRACT METADATA (Parse AST)                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  • Language: Java                                      │    │
│  │  • Classes: ["SecurityCrowdIngesterTest"]              │    │
│  │  • Functions: ["testIngest", "setUp", "tearDown"]      │    │
│  │  • Imports: ["org.junit", "java.util"]                 │    │
│  │  • Lines of code: 245                                  │    │
│  │  • Has tests: true                                     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. CREATE EMBEDDING TEXT (Semantic Context)                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  File: SecurityCrowdIngesterTest.java                  │    │
│  │  Language: Java                                        │    │
│  │  Classes: SecurityCrowdIngesterTest                    │    │
│  │  Functions: testIngest, setUp, tearDown                │    │
│  │  Content: public class SecurityCrowdIngesterTest...    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. GENERATE EMBEDDING (SentenceTransformer)                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Model: all-MiniLM-L6-v2 (384 dimensions)             │    │
│  │                                                         │    │
│  │  Text → Neural Network → Vector (384 floats)          │    │
│  │                                                         │    │
│  │  [0.234, -0.567, 0.891, ..., 0.123, -0.456]          │    │
│  │   └──────────── 384 numbers ────────────┘            │    │
│  │                                                         │    │
│  │  • Each dimension captures semantic meaning            │    │
│  │  • Similar code = similar vector                       │    │
│  │  • Enables "meaning-based" search                      │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. STORE IN MILVUS (Insert to Collection)                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Collection: codebase_analysis                         │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │ SCALAR FIELDS (42 fields total)              │     │    │
│  │  ├──────────────────────────────────────────────┤     │    │
│  │  │ id: 123456789                                │     │    │
│  │  │ file_hash: "ec9564dad4a2..."                 │     │    │
│  │  │ file_path: "src/test/.../Test.java"          │     │    │
│  │  │ file_name: "SecurityCrowdIngesterTest.java"  │     │    │
│  │  │ language: "java"                             │     │    │
│  │  │ classes: ["SecurityCrowdIngesterTest"]       │     │    │
│  │  │ functions: ["testIngest", "setUp"]           │     │    │
│  │  │ lines_of_code: 245                           │     │    │
│  │  │ has_tests: true                              │     │    │
│  │  │ repo_name: "nexus-internal"                  │     │    │
│  │  │ content: "public class Security..."          │     │    │
│  │  │ ... (32 more fields)                         │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │ VECTOR FIELD (The Magic!)                    │     │    │
│  │  ├──────────────────────────────────────────────┤     │    │
│  │  │ embedding: [0.234, -0.567, 0.891, ... ]     │     │    │
│  │  │            └─── 384 dimensions ───┘         │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: How Milvus Organizes Data Internally

### Data Structure

```
┌───────────────────────────────────────────────────────────────────┐
│  MILVUS COLLECTION: codebase_analysis                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  SEGMENTS (Data Partitions)                              │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │    │
│  │  │  Segment 1     │  │  Segment 2     │  │  Segment N │ │    │
│  │  │  (1-100 files) │  │  (101-200)     │  │  ...       │ │    │
│  │  │                │  │                │  │            │ │    │
│  │  │  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────┐ │ │    │
│  │  │  │ Scalars  │  │  │  │ Scalars  │  │  │  │ ...  │ │ │    │
│  │  │  │ (metadata)│  │  │  │ (metadata)│  │  │  │      │ │ │    │
│  │  │  └──────────┘  │  │  └──────────┘  │  │  └──────┘ │ │    │
│  │  │  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────┐ │ │    │
│  │  │  │ Vectors  │  │  │  │ Vectors  │  │  │  │ ...  │ │ │    │
│  │  │  │ (embeddings)│  │  │(embeddings)│  │  │      │ │ │    │
│  │  │  └──────────┘  │  │  └──────────┘  │  │  └──────┘ │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────┘ │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  INDEXES (For Fast Search)                               │    │
│  │  ┌────────────────────────────────────────────────────┐  │    │
│  │  │  HNSW Index (Hierarchical Navigable Small World)   │  │    │
│  │  │                                                     │  │    │
│  │  │  • Graph-based index structure                     │  │    │
│  │  │  • O(log N) search complexity                      │  │    │
│  │  │  • Balances speed vs accuracy                      │  │    │
│  │  │                                                     │  │    │
│  │  │  Vector Space (384D):                              │  │    │
│  │  │       ┌────────────────────────┐                   │  │    │
│  │  │       │    •  •     •          │  Each dot = a file│  │    │
│  │  │       │  •    •   •    •       │  Close dots =     │  │    │
│  │  │       │    •    •     •  •     │  similar code     │  │    │
│  │  │       │  •  •     •     •      │                   │  │    │
│  │  │       │     •  •    •    •     │                   │  │    │
│  │  │       └────────────────────────┘                   │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

### Physical Storage

```
┌─────────────────────────────────────────────────────────────────┐
│  MINIO (Object Storage)                                         │
│                                                                  │
│  /milvus/                                                       │
│  ├── segments/                                                  │
│  │   ├── segment_001.bin      ← Binary data (scalars)          │
│  │   ├── segment_002.bin                                       │
│  │   └── ...                                                   │
│  │                                                              │
│  ├── indexes/                                                   │
│  │   ├── index_001.idx        ← HNSW index structure           │
│  │   ├── index_002.idx                                         │
│  │   └── ...                                                   │
│  │                                                              │
│  └── vectors/                                                   │
│      ├── vectors_001.vec      ← 384D embeddings                │
│      ├── vectors_002.vec                                       │
│      └── ...                                                   │
│                                                                  │
│  ETCD (Metadata Store)                                          │
│  ├── collection_metadata                                        │
│  ├── segment_info                                               │
│  └── index_status                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Retrieving Code (Similarity Search)

### Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. USER QUERY                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  "Find authentication tests in Java"                   │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. CONVERT QUERY TO EMBEDDING                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Same model: all-MiniLM-L6-v2                          │    │
│  │                                                         │    │
│  │  "Find authentication tests in Java"                   │    │
│  │  → [0.123, -0.456, 0.789, ..., 0.234]                 │    │
│  │     └──────── Query Vector ────────┘                  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. SEARCH IN VECTOR SPACE (Milvus Search)                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Algorithm: HNSW (Approximate Nearest Neighbor)        │    │
│  │                                                         │    │
│  │  Vector Space:                                         │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │                                               │     │    │
│  │  │      File2 •     • File5                     │     │    │
│  │  │              ╲   ╱                            │     │    │
│  │  │       File1 • ✦ • File4 ← Closest matches   │     │    │
│  │  │              ╱   ╲                            │     │    │
│  │  │      File3 •       • File6                   │     │    │
│  │  │                                               │     │    │
│  │  │      ✦ = Query vector                        │     │    │
│  │  │                                               │     │    │
│  │  │  Distance Metric: Cosine Similarity          │     │    │
│  │  │  • 1.0 = identical                            │     │    │
│  │  │  • 0.0 = unrelated                            │     │    │
│  │  │  • -1.0 = opposite                            │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. RETRIEVE TOP-K RESULTS (with metadata filtering)            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Search parameters:                                    │    │
│  │  • top_k: 5 (return 5 most similar)                   │    │
│  │  • metric: cosine similarity                           │    │
│  │  • filters: language == "java" AND has_tests == true  │    │
│  │                                                         │    │
│  │  Results:                                              │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │ 1. SecurityCrowdIngesterTest.java            │     │    │
│  │  │    Score: 0.95 (95% similar)                 │     │    │
│  │  │    + metadata (path, classes, functions...)  │     │    │
│  │  ├──────────────────────────────────────────────┤     │    │
│  │  │ 2. AuthenticationServiceTest.java            │     │    │
│  │  │    Score: 0.92                               │     │    │
│  │  ├──────────────────────────────────────────────┤     │    │
│  │  │ 3. LoginControllerTest.java                  │     │    │
│  │  │    Score: 0.89                               │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Key Concepts

### 1. Embeddings (Vectors)

**What is an embedding?**
- A list of 384 floating-point numbers
- Each number represents a semantic dimension
- Generated by a neural network (SentenceTransformer)

**Example:**
```python
# Text
"public class AuthTest { }"

# Becomes vector (384 dimensions)
[0.234, -0.567, 0.891, 0.123, ..., -0.456]
 └─────────────── 384 numbers ──────────────┘

# Similar code has similar vectors
"public class LoginTest { }"  → [0.231, -0.563, 0.887, ...] ← Very close!
"const x = 5;"                → [-0.891, 0.234, -0.123, ...] ← Far away
```

### 2. Similarity Search (Not Exact Match)

**Traditional Database:**
```sql
-- Exact keyword match
SELECT * FROM files WHERE content LIKE '%authentication%'
```
❌ Misses: "login", "auth", "security check"

**Milvus Vector Search:**
```python
# Semantic similarity search
query_vector = embed("authentication")
results = collection.search(query_vector, top_k=5)
```
✅ Finds: "authentication", "login", "auth", "security check", "user validation"

### 3. Why 384 Dimensions?

Think of each dimension as measuring different aspects:

```
Dimension 1:   "Is it a test?"         (0.9 = yes, -0.9 = no)
Dimension 2:   "Is it Java?"           (0.8 = yes)
Dimension 3:   "Is it about auth?"     (0.7 = yes)
Dimension 4:   "Is it a class?"        (0.95 = yes)
Dimension 5:   "Is it frontend?"       (-0.6 = no)
...
Dimension 384: "Is it legacy code?"    (0.1 = maybe)
```

The neural network learns these dimensions automatically from training data.

---

## Part 5: Performance & Scalability

### Current Stats (Your nexus-internal repo)

```
Total Files:     11,474
Analyzed:        4,099 (36%)
In Progress:     7,375 files remaining
Storage Size:    ~500 MB (estimated)

Per File:
├── Scalar data:  ~10 KB (metadata, content)
├── Vector data:  1.5 KB (384 floats × 4 bytes)
└── Index data:   ~500 bytes (HNSW graph)
```

### Search Performance

```
┌─────────────────────────────────────────────────┐
│  Search Speed                                   │
├─────────────────────────────────────────────────┤
│  10 files:        < 1 ms                        │
│  1,000 files:     ~5 ms                         │
│  10,000 files:    ~20 ms                        │
│  100,000 files:   ~50 ms                        │
│  1,000,000 files: ~100 ms                       │
└─────────────────────────────────────────────────┘

Why so fast?
• HNSW index: O(log N) complexity
• In-memory caching
• GPU acceleration (optional)
• Batch processing
```

---

## Part 6: Real Example

### Storing a File

**Input File:** `SecurityCrowdIngesterTest.java`

```java
package com.sonatype.nexus.test;

import org.junit.Test;
import static org.junit.Assert.*;

public class SecurityCrowdIngesterTest {
    @Test
    public void testIngest() {
        // Test authentication ingestion
        SecurityCrowdIngester ingester = new SecurityCrowdIngester();
        ingester.ingest("user", "pass");
        assertTrue(ingester.isAuthenticated());
    }
}
```

**Milvus Entry:**

```json
{
  "id": 123456789,
  "file_hash": "ec9564dad4a2...",
  "file_path": "src/test/java/.../SecurityCrowdIngesterTest.java",
  "file_name": "SecurityCrowdIngesterTest.java",
  "file_extension": ".java",
  "language": "java",
  "classes": ["SecurityCrowdIngesterTest"],
  "functions": ["testIngest"],
  "imports": ["org.junit.Test", "org.junit.Assert"],
  "lines_of_code": 12,
  "has_tests": true,
  "has_main": false,
  "repo_name": "nexus-internal",
  "content": "package com.sonatype.nexus.test; ...",
  "embedding": [0.234, -0.567, 0.891, ..., -0.456]
}
```

### Searching

**Query:** "Find tests for authentication"

**Process:**
1. Convert query → vector: `[0.231, -0.563, 0.887, ...]`
2. Search in 384D space
3. Find closest vectors (cosine similarity)
4. Return files with metadata

**Results:**
```
1. SecurityCrowdIngesterTest.java (Score: 0.95)
   ├── Has "authentication" in comments
   ├── Has test methods
   └── Related classes: SecurityCrowdIngester

2. AuthenticationServiceTest.java (Score: 0.92)
   └── Similar semantic meaning

3. LoginControllerTest.java (Score: 0.89)
   └── Related domain (login ≈ authentication)
```

---

## Part 7: Advantages of Milvus for Code Search

### Traditional Search (Keyword)
```
Query: "authentication"
Results: Files containing exact word "authentication"
❌ Misses: "login", "auth", "security", "credentials"
```

### Milvus Vector Search (Semantic)
```
Query: "authentication"
Results: Files with SIMILAR MEANING
✅ Finds: "authentication", "login", "auth", "security",
         "credentials", "user validation", "sign-in"
```

### Additional Benefits

1. **Typo Tolerance**
   - Query: "athentication" (typo)
   - Still finds "authentication" files

2. **Cross-Language**
   - Query: "authentication in Python"
   - Finds Java auth code too (similar concepts)

3. **Code Understanding**
   - Understands: `isLoggedIn()` ≈ `checkAuthentication()`
   - Relates: `User.login()` ≈ `Session.authenticate()`

4. **Contextual Search**
   - Query: "How to validate user input?"
   - Finds: Validation classes, sanitization, input checks

---

## Part 8: Memory & Storage

### In-Memory (RAM)

```
┌────────────────────────────────────────┐
│  MILVUS MEMORY USAGE                   │
├────────────────────────────────────────┤
│  Embedding Model:     ~400 MB          │
│  HNSW Index:          ~200 MB          │
│  Vector Cache:        ~100 MB          │
│  Metadata Cache:      ~50 MB           │
│  ────────────────────────────          │
│  Total:               ~750 MB          │
└────────────────────────────────────────┘
```

### On-Disk (Storage)

```
┌────────────────────────────────────────┐
│  MILVUS DISK USAGE (11,474 files)      │
├────────────────────────────────────────┤
│  Vectors (embeddings):   ~20 MB        │
│  Scalars (metadata):     ~400 MB       │
│  Indexes (HNSW):         ~50 MB        │
│  ────────────────────────────────      │
│  Total:                  ~470 MB       │
└────────────────────────────────────────┘
```

---

## Summary

### How Milvus Works

1. **Store**: Code → Embedding (384D vector) → Milvus
2. **Search**: Query → Embedding → Find similar vectors → Return files
3. **Fast**: HNSW index for O(log N) search
4. **Smart**: Understands meaning, not just keywords

### Key Takeaways

✅ **Semantic Search** - Finds similar code by meaning
✅ **Fast** - Searches millions of files in milliseconds
✅ **Scalable** - Handles large codebases efficiently
✅ **Local** - Everything runs on your machine
✅ **AI-Powered** - Neural network embeddings

### What Makes It Special

Traditional DB: "Find files containing 'auth'"
Milvus: "Find files SIMILAR to authentication logic"

This is why your codebase analyzer is so powerful - it doesn't just index keywords, it understands the MEANING of your code!
