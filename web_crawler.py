#!/usr/bin/env python3
"""
Web Crawler - Recursively crawl any website and store in Milvus
"""

import os
import time
import hashlib
from urllib.parse import urljoin, urlparse
from collections import deque
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

load_dotenv()


class WebCrawler:
    def __init__(self, max_pages=100, max_depth=5, delay=1.0):
        """
        Initialize web crawler

        Args:
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth from start URL
            delay: Delay between requests in seconds (respect rate limits)
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.visited_urls = set()
        self.to_visit = deque()
        self.pages_crawled = 0

        # Milvus connection
        self.milvus_host = "localhost"
        self.milvus_port = "19530"
        self.embedding_model = None

        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def load_embedding_model(self):
        """Load sentence transformer for embeddings"""
        if self.embedding_model is None:
            print("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model

    def connect_milvus(self):
        """Connect to Milvus"""
        try:
            connections.connect(alias="default", host=self.milvus_host, port=self.milvus_port)
            return True
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            return False

    def normalize_url(self, url):
        """Normalize URL by removing fragments and trailing slashes"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = parsed._replace(fragment='').geturl()
        # Remove trailing slash for consistency
        if normalized.endswith('/') and normalized != parsed.scheme + '://' + parsed.netloc + '/':
            normalized = normalized[:-1]
        return normalized

    def is_valid_url(self, url, base_domain):
        """
        Check if URL should be crawled

        Args:
            url: URL to check
            base_domain: Base domain to restrict crawling to

        Returns:
            bool: True if URL should be crawled
        """
        parsed = urlparse(url)

        # Must be same domain
        if parsed.netloc != base_domain:
            return False

        # Skip certain file types
        skip_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.zip', '.tar', '.gz', '.mp4', '.mp3', '.avi', '.mov',
            '.css', '.js', '.json', '.xml', '.rss'
        ]
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip common non-content paths
        skip_paths = ['/api/', '/auth/', '/login/', '/logout/', '/admin/', '/private/']
        if any(skip in parsed.path.lower() for skip in skip_paths):
            return False

        return True

    def extract_content(self, soup, url):
        """
        Extract clean text content from HTML

        Args:
            soup: BeautifulSoup object
            url: URL of the page

        Returns:
            dict with title and content
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer',
                            'iframe', 'noscript', 'meta', 'link']):
            element.decompose()

        # Get title
        title = soup.title.string if soup.title else url
        title = title.strip() if title else url

        # Try to find main content area
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.main']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.body if soup.body else soup

        # Extract text
        text = main_content.get_text(separator=' ', strip=True)

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Get meta description if available
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''

        return {
            'title': title,
            'content': text[:50000],  # Limit to 50k chars
            'description': description,
            'url': url
        }

    def extract_links(self, soup, base_url):
        """
        Extract all links from page

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            list of absolute URLs
        """
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(absolute_url)
            links.append(normalized_url)
        return links

    def fetch_page(self, url):
        """
        Fetch a page and return BeautifulSoup object

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            print(f"[Crawler] Fetching: {url}")
            response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Check if it's HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                print(f"[Crawler] Skipping non-HTML content: {content_type}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            return soup

        except requests.exceptions.RequestException as e:
            print(f"[Crawler] Error fetching {url}: {e}")
            return None

    def store_page(self, page_data, collection_name='website_crawl'):
        """
        Store page in Milvus

        Args:
            page_data: dict with page information
            collection_name: Milvus collection name

        Returns:
            bool: Success status
        """
        if not self.connect_milvus():
            return False

        try:
            # Create collection if it doesn't exist
            if not utility.has_collection(collection_name):
                print(f"[Milvus] Creating collection: {collection_name}")
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=500),
                    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1000),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=60000),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2000),
                    FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=2000),
                    FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
                ]
                schema = CollectionSchema(fields, description="Web crawl data")
                collection = Collection(name=collection_name, schema=schema)

                # Create index
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
                print(f"[Milvus] Created collection and index")

            collection = Collection(name=collection_name)

            # Generate embedding
            model = self.load_embedding_model()
            text_to_embed = f"{page_data['title']} {page_data['content'][:5000]}"
            embedding = model.encode([text_to_embed])[0].tolist()

            # Prepare data
            url_hash = hashlib.md5(page_data['url'].encode()).hexdigest()

            import json
            from datetime import datetime

            metadata = json.dumps({
                'description': page_data.get('description', ''),
                'domain': urlparse(page_data['url']).netloc,
                'path': urlparse(page_data['url']).path
            })

            data = [
                ['webpage'],
                [url_hash],
                [page_data['title']],
                [page_data['content']],
                [metadata],
                [page_data['url']],
                [datetime.now().isoformat()],
                [embedding]
            ]

            # Insert
            collection.insert(data)
            collection.flush()

            return True

        except Exception as e:
            print(f"[Milvus] Error storing page: {e}")
            return False

    def crawl(self, start_url, collection_name='website_crawl'):
        """
        Crawl website starting from given URL

        Args:
            start_url: Starting URL
            collection_name: Milvus collection name

        Returns:
            dict with crawl statistics
        """
        print(f"\n{'='*70}")
        print(f"WEB CRAWLER - Starting from {start_url}")
        print(f"Max pages: {self.max_pages} | Max depth: {self.max_depth} | Delay: {self.delay}s")
        print(f"{'='*70}\n")

        # Normalize start URL
        start_url = self.normalize_url(start_url)
        base_domain = urlparse(start_url).netloc

        # Initialize queue with start URL at depth 0
        self.to_visit.append((start_url, 0))

        pages_stored = 0
        pages_failed = 0
        start_time = time.time()

        while self.to_visit and self.pages_crawled < self.max_pages:
            # Get next URL and its depth
            current_url, depth = self.to_visit.popleft()

            # Skip if already visited
            if current_url in self.visited_urls:
                continue

            # Skip if too deep
            if depth > self.max_depth:
                continue

            # Mark as visited
            self.visited_urls.add(current_url)
            self.pages_crawled += 1

            print(f"\n[{self.pages_crawled}/{self.max_pages}] Depth {depth}: {current_url}")

            # Fetch page
            soup = self.fetch_page(current_url)

            if soup:
                # Extract content
                page_data = self.extract_content(soup, current_url)

                print(f"[Crawler] Extracted: {page_data['title'][:80]} ({len(page_data['content'])} chars)")

                # Store in Milvus
                if self.store_page(page_data, collection_name):
                    pages_stored += 1
                    print(f"[Milvus] ✓ Stored in collection '{collection_name}'")
                else:
                    pages_failed += 1
                    print(f"[Milvus] ✗ Failed to store")

                # Extract and queue links (only if not at max depth)
                if depth < self.max_depth:
                    links = self.extract_links(soup, current_url)
                    new_links = 0
                    for link in links:
                        if (link not in self.visited_urls and
                            self.is_valid_url(link, base_domain) and
                            (link, depth + 1) not in self.to_visit):
                            self.to_visit.append((link, depth + 1))
                            new_links += 1

                    print(f"[Crawler] Found {new_links} new links to crawl")
            else:
                pages_failed += 1

            # Rate limiting
            time.sleep(self.delay)

        elapsed_time = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"CRAWL COMPLETED")
        print(f"{'='*70}")
        print(f"Pages crawled: {self.pages_crawled}")
        print(f"Pages stored: {pages_stored}")
        print(f"Pages failed: {pages_failed}")
        print(f"Time elapsed: {elapsed_time:.1f}s")
        print(f"Collection: {collection_name}")
        print(f"{'='*70}\n")

        return {
            'success': True,
            'pages_crawled': self.pages_crawled,
            'pages_stored': pages_stored,
            'pages_failed': pages_failed,
            'elapsed_time': elapsed_time,
            'collection': collection_name,
            'start_url': start_url
        }


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python web_crawler.py <start_url> [collection_name] [max_pages] [max_depth]")
        print("\nExample:")
        print("  python web_crawler.py https://docs.example.com/ example_docs 50 3")
        sys.exit(1)

    start_url = sys.argv[1]
    collection_name = sys.argv[2] if len(sys.argv) > 2 else 'website_crawl'
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    max_depth = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    crawler = WebCrawler(max_pages=max_pages, max_depth=max_depth, delay=1.0)
    result = crawler.crawl(start_url, collection_name=collection_name)

    if result['success']:
        print(f"\n✓ Successfully crawled {result['pages_stored']} pages from {result['start_url']}")
        print(f"  Stored in collection: {result['collection']}")
    else:
        print(f"\n✗ Crawl failed or incomplete")


if __name__ == "__main__":
    main()
