# Web Crawler - Complete Site Analysis Guide

## Overview

The Web Crawler is a powerful tool that recursively crawls entire websites and stores all pages in Milvus for AI analysis. It works with **any website** - documentation sites, blogs, knowledge bases, or any web content you want to analyze.

---

## 🚀 Features

### Comprehensive Crawling
- **Recursive Navigation**: Follows all internal links automatically
- **Domain Restriction**: Only crawls pages from the same domain
- **Depth Control**: Configurable maximum depth to control how deep to crawl
- **Page Limit**: Set maximum number of pages to prevent runaway crawls
- **Smart Filtering**: Automatically skips non-content files (images, PDFs, CSS, JS, etc.)

### Content Extraction
- **Clean Text**: Removes navigation, headers, footers, scripts, and styling
- **Title Extraction**: Captures page titles and meta descriptions
- **Main Content Focus**: Prioritizes main content areas (article, main tags)
- **Deduplication**: URL normalization prevents duplicate pages

### Rate Limiting & Respect
- **Configurable Delay**: 1-second delay between requests (configurable)
- **User Agent**: Identifies as a legitimate browser
- **Timeout Handling**: Graceful handling of slow or unresponsive pages
- **Error Recovery**: Continues crawling even if some pages fail

### Storage & Search
- **Milvus Integration**: Stores all pages with semantic embeddings
- **Vector Search**: Pages are immediately searchable via AI
- **Organized Collections**: Group crawls by collection name
- **Rich Metadata**: Stores domain, path, description for filtering

---

## 📖 How to Use

### Via Web Interface (Recommended)

1. **Open the Web Interface**
   ```
   http://localhost:3000
   ```

2. **Go to "Crawl Website" Tab**
   - It's the last tab in the navigation

3. **Configure the Crawl**
   - **Website URL**: Enter the starting URL (e.g., `https://help.sonatype.com/`)
   - **Collection Name**: Name for organizing crawled pages (e.g., `sonatype_docs`)
   - **Max Pages**: Maximum pages to crawl (default: 50, range: 1-1000)
   - **Max Depth**: How many links deep to follow (default: 3, range: 1-10)

4. **Start Crawling**
   - Click "🚀 Start Crawling"
   - Wait for completion (1-2 seconds per page)
   - View statistics when done

5. **Query the Crawled Content**
   - Go to "Claude AI" or "Ollama AI" tabs
   - Select your collection name
   - Ask questions about the crawled content

### Via Command Line

```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
source venv/bin/activate

# Basic usage
python web_crawler.py https://help.sonatype.com/ sonatype_docs

# With custom limits
python web_crawler.py https://docs.python.org/ python_docs 100 4
```

**Command Format:**
```bash
python web_crawler.py <start_url> [collection_name] [max_pages] [max_depth]
```

**Examples:**
```bash
# Crawl Sonatype documentation
python web_crawler.py https://help.sonatype.com/ sonatype_docs 50 3

# Crawl Python docs
python web_crawler.py https://docs.python.org/3/ python_docs 100 4

# Crawl a blog
python web_crawler.py https://example.com/blog/ blog_posts 200 5
```

---

## ⚙️ Configuration Options

### Max Pages
- **Default**: 50
- **Range**: 1-1000
- **Purpose**: Limits total number of pages crawled
- **Recommendation**:
  - Small sites (< 50 pages): 50-100
  - Medium sites (50-200 pages): 100-300
  - Large sites (200+ pages): 300-1000

### Max Depth
- **Default**: 3
- **Range**: 1-10
- **Purpose**: Limits how many clicks away from start URL to crawl
- **Explanation**:
  - Depth 1: Only pages directly linked from start URL
  - Depth 2: Pages linked from depth-1 pages
  - Depth 3: Pages linked from depth-2 pages (recommended)
  - Higher depths: More comprehensive but slower

### Delay Between Requests
- **Default**: 1.0 seconds
- **Purpose**: Rate limiting to respect server resources
- **Editable**: Modify `delay` parameter in code if needed

### Collection Name
- **Default**: `website_crawl`
- **Purpose**: Organize crawled sites in separate collections
- **Recommendation**: Use descriptive names like:
  - `sonatype_docs`
  - `company_kb`
  - `product_manual`
  - `blog_archive`

---

## 🎯 Use Cases

### 1. Documentation Sites
**Example**: https://help.sonatype.com/

Crawl entire documentation to enable AI to answer questions about your product:
```
Question: "How do I configure Maven proxy in Nexus Repository?"
AI finds answer from crawled help.sonatype.com pages
```

### 2. Knowledge Bases
**Example**: Internal company wiki, Confluence

Import entire knowledge base for AI-powered search:
```
Question: "What's our security incident response procedure?"
AI searches crawled internal wiki
```

### 3. Blogs & Articles
**Example**: Company blog, technical articles

Archive and search blog content:
```
Question: "What did we write about Kubernetes last year?"
AI searches crawled blog posts
```

### 4. Product Manuals
**Example**: User guides, API documentation

Make manuals searchable and interactive:
```
Question: "How do I authenticate with the API?"
AI references crawled API documentation
```

### 5. Competitor Analysis
**Example**: Competitor documentation, pricing pages

Analyze competitor content (ethically and legally):
```
Question: "What features does Competitor X highlight?"
AI analyzes crawled competitor site
```

---

## 📊 Crawl Statistics

After crawling, you'll see:

- **Pages Crawled**: Total number of pages visited
- **Pages Stored**: Successfully stored in Milvus
- **Failed**: Pages that couldn't be fetched or processed
- **Elapsed Time**: Total crawl duration
- **Collection**: Where pages are stored
- **Start URL**: Original starting point

**Example Output:**
```
✓ Crawl Completed Successfully

Pages Crawled: 47
Pages Stored: 45
Failed: 2
Time: 52.3s

Collection: sonatype_docs
Source: https://help.sonatype.com/
```

---

## 🔍 Querying Crawled Content

### Via Claude AI Tab

1. Go to "Claude AI" tab
2. Select your collection or "All Collections"
3. Ask questions:
   - "What does the documentation say about Docker installation?"
   - "Summarize the security best practices from the help site"
   - "How do I configure LDAP authentication?"

### Via Ollama AI Tab

1. Go to "Ollama AI" tab
2. Select your collection
3. Choose model (e.g., deepseek-r1:8b)
4. Ask questions about crawled content

### Via Search Tab

1. Go to "Search" tab
2. Select your collection
3. Enter search query
4. View relevant pages with similarity scores

---

## 🛡️ Best Practices

### 1. Start with Small Limits
- Test with 10-20 pages first
- Increase limits once you verify it works

### 2. Use Descriptive Collection Names
- `sonatype_docs` not `docs`
- `company_blog_2024` not `blog`
- Makes it easier to manage multiple crawls

### 3. Respect Rate Limits
- Don't set delay below 1 second
- Don't crawl the same site repeatedly in short time
- Check robots.txt if unsure

### 4. Choose Appropriate Depth
- Depth 2-3 for most documentation sites
- Depth 4-5 for large, complex sites
- Higher depths = exponentially more pages

### 5. Monitor Crawl Progress
- Watch for high failure rates
- Stop if it takes too long
- Adjust limits based on site structure

### 6. Clean Up Old Crawls
- Delete outdated collections
- Re-crawl periodically for updated content
- Keep collection names organized

---

## 🚫 What Gets Skipped

The crawler automatically skips:

### File Types
- Images: .jpg, .jpeg, .png, .gif, .svg, .ico
- Documents: .pdf (but can be uploaded separately)
- Archives: .zip, .tar, .gz
- Media: .mp4, .mp3, .avi, .mov
- Code: .css, .js, .json, .xml

### Path Patterns
- API endpoints: `/api/*`
- Authentication: `/auth/*`, `/login/*`, `/logout/*`
- Admin panels: `/admin/*`, `/private/*`

### External Links
- Only pages from the same domain are crawled
- External links are not followed

---

## 🐛 Troubleshooting

### "Error crawling website"
- **Check URL**: Must be valid and accessible
- **Check connectivity**: Can you access the site in browser?
- **Check Milvus**: Is it running? (`docker ps`)

### "Failed to store pages"
- **Check Milvus**: Run `docker ps` to verify containers are healthy
- **Check disk space**: Milvus needs space to store vectors
- **Check logs**: Look at `web_server.log` for details

### "Too many failures"
- **Site blocking**: Site may block automated access
- **Rate limiting**: Reduce number of pages or increase delay
- **Site structure**: Some sites don't work well with crawlers

### "Crawl taking too long"
- **Reduce max pages**: Lower the limit
- **Reduce max depth**: Less depth = fewer pages
- **Check site size**: Large sites take time (1-2s per page)

---

## 📈 Performance Metrics

### Crawl Speed
- **Average**: 1-2 seconds per page
- **Factors**:
  - Page size and complexity
  - Server response time
  - Network latency
  - Delay between requests

### Storage Requirements
- **Per Page**: ~10-50 KB in Milvus
- **50 pages**: ~0.5-2.5 MB
- **500 pages**: ~5-25 MB
- **1000 pages**: ~10-50 MB

### Memory Usage
- **Crawler**: ~200-500 MB RAM
- **Milvus**: ~500 MB - 2 GB RAM
- **Embedding Model**: ~100-200 MB RAM

---

## 🔐 Security & Privacy

### Data Storage
- All crawled content stored locally in Milvus
- No data sent to external services (except original websites)
- Complete offline capability after crawling

### Authentication
- Does not handle login/authentication
- Only crawls publicly accessible pages
- Cannot access password-protected content

### Robots.txt
- Currently does not check robots.txt
- Use responsibly and ethically
- Don't crawl if site explicitly disallows

### Rate Limiting
- Built-in 1-second delay respects servers
- Avoids overwhelming target websites
- Can be increased if needed

---

## 🎓 Advanced Usage

### Custom Delay
Edit `web_crawler.py`:
```python
crawler = WebCrawler(max_pages=100, max_depth=5, delay=2.0)  # 2-second delay
```

### Multiple Collections
Crawl different sections to separate collections:
```bash
# Crawl user guides
python web_crawler.py https://docs.example.com/user-guide/ user_guides 50 3

# Crawl API docs
python web_crawler.py https://docs.example.com/api/ api_docs 100 4

# Crawl tutorials
python web_crawler.py https://docs.example.com/tutorials/ tutorials 75 3
```

### Incremental Crawling
Re-crawl same collection to update content:
```bash
# Initial crawl
python web_crawler.py https://help.sonatype.com/ sonatype_docs 50 3

# Update later (overwrites old pages)
python web_crawler.py https://help.sonatype.com/ sonatype_docs 50 3
```

### Integration with AI
After crawling, use in AI queries:
```python
# Via Claude RAG
rag = ClaudeRAG()
result = rag.query_with_context(
    question="How do I configure the firewall?",
    collection_name="sonatype_docs",
    top_k=5
)
```

---

## 📝 Example Crawl Session

### Step-by-Step Example: Crawling Sonatype Documentation

1. **Open Web Interface**: http://localhost:3000

2. **Navigate to Crawler Tab**: Click "Crawl Website"

3. **Enter Details**:
   - URL: `https://help.sonatype.com/`
   - Collection: `sonatype_docs`
   - Max Pages: `50`
   - Max Depth: `3`

4. **Start Crawl**: Click "🚀 Start Crawling"

5. **Wait for Completion** (~50 seconds for 50 pages)

6. **View Results**:
   ```
   Pages Crawled: 47
   Pages Stored: 45
   Failed: 2
   Time: 52.3s
   ```

7. **Test with AI**:
   - Go to "Claude AI" tab
   - Collection: Select "sonatype_docs"
   - Question: "What are the system requirements for Nexus Repository?"
   - Claude answers using crawled documentation

---

## 🆘 Support

### Check Logs
```bash
# Flask backend logs
tail -f /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal/web_server.log

# React frontend logs
tail -f /Users/komaragiri.satyadev/Desktop/Personal\ Projects/Sonatype-Personal/frontend/react_server.log
```

### Verify Services
```bash
# Check all services
docker ps                    # Milvus
lsof -ti:5000               # Flask
lsof -ti:3000               # React
brew services list | grep ollama  # Ollama
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Crawler not starting | Restart Flask backend |
| No results in AI | Verify collection name matches |
| Slow crawling | Reduce max_pages or increase delay |
| High failure rate | Check if site blocks crawlers |
| Out of memory | Reduce max_pages, restart Milvus |

---

## 📚 Related Features

- **Claude AI**: Query crawled content with advanced reasoning
- **Ollama AI**: Offline analysis of crawled pages
- **Semantic Search**: Find relevant pages by meaning, not keywords
- **Jira Integration**: Combine crawled docs with ticket data
- **GitHub Integration**: Cross-reference PRs with documentation

---

Last Updated: 2026-02-11
Version: 1.0
