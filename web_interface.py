#!/usr/bin/env python3
"""
Optus Data Management Web Interface
Upload files, fetch Jira tickets, and GitHub PRs
"""

import os
import json
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from requests.auth import HTTPBasicAuth
import PyPDF2
import hashlib
from ollama_rag import OllamaRAG
from claude_rag import ClaudeRAG
from web_crawler import WebCrawler
from github_analyzer import GitHubPersonaAnalyzer
from persona_report import PersonaReportGenerator
from bs4 import BeautifulSoup
import re
from image_vectorizer import ImageVectorizer
from codebase_analyzer import CodebaseAnalyzer
from codebase_analyzer_with_progress import CodebaseAnalyzerWithProgress
from codebase_analyzer_smart import SmartCodebaseAnalyzer

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
app.secret_key = 'milvus-secret-key-2026'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size (increased for chunked uploads)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'md', 'json', 'csv', 'log', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Global variables
embedding_model = None
image_vectorizer = None
milvus_connected = False

# Optus configuration
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_ticket_id(query):
    """
    Extract JIRA ticket ID from various query formats:
    - Direct ID: PROJ-12345
    - URL: https://your-instance.atlassian.net/browse/PROJ-12345
    - In sentence: "give me details about PROJ-12345"
    """
    # Pattern for JIRA ticket ID (PROJECT-NUMBER)
    pattern = r'([A-Z]+-\d+)'

    match = re.search(pattern, query)
    if match:
        return match.group(1)

    return None


def load_model():
    """Load embedding models"""
    global embedding_model, image_vectorizer
    if embedding_model is None:
        print("Loading text embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Text model loaded")

    if image_vectorizer is None:
        print("Loading image vectorizer (CLIP)...")
        try:
            image_vectorizer = ImageVectorizer()
            print("✓ Image vectorizer loaded")
        except Exception as e:
            print(f"⚠ Could not load image vectorizer: {e}")
            image_vectorizer = None

    return embedding_model


def connect_milvus():
    """Connect to Optus"""
    global milvus_connected
    if not milvus_connected:
        try:
            connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
            milvus_connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to Optus: {e}")
            return False
    return True


def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def read_file_content(filepath, filename):
    """Read content from uploaded file"""
    ext = filename.rsplit('.', 1)[1].lower()

    try:
        if ext == 'pdf':
            return extract_text_from_pdf(filepath)
        elif ext in ['txt', 'md', 'log', 'csv']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        else:
            return "Unsupported file type"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def ensure_action_logs_collection():
    """Ensure action_logs collection exists"""
    collection_name = "action_logs"

    if not connect_milvus():
        return None

    if utility.has_collection(collection_name):
        return Collection(name=collection_name)

    # Create action logs collection (Optus requires at least one vector field)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="action_type", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="endpoint", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="parameters", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=20),
        FieldSchema(name="duration_ms", dtype=DataType.INT64),
        FieldSchema(name="result_summary", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="error_message", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=2)  # Dummy vector field (required by Optus)
    ]

    schema = CollectionSchema(fields, description="Action logs for tracking all operations")
    collection = Collection(name=collection_name, schema=schema)

    # Create index on vector field
    index_params = {
        "index_type": "FLAT",
        "metric_type": "L2",
        "params": {}
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    print(f"[Action Logs] Created collection: {collection_name}")
    return collection


def log_action(action_type, endpoint, parameters, status, duration_ms, result_summary="", error_message="", source="api", metadata=None):
    """Log an action to the action_logs collection"""
    try:
        collection = ensure_action_logs_collection()
        if collection is None:
            print("[Action Logs] Failed to get collection")
            return

        timestamp = datetime.now().isoformat()

        # Prepare data (including dummy vector for Optus requirement)
        data = [
            [timestamp],
            [action_type],
            [endpoint],
            [json.dumps(parameters)[:2000]],
            [status],
            [int(duration_ms)],
            [result_summary[:1000]],
            [error_message[:1000]],
            [source],
            [json.dumps(metadata or {})[:2000]],
            [[0.0, 0.0]]  # Dummy vector (required by Optus)
        ]

        # Insert
        collection.insert(data)
        collection.flush()

        print(f"[Action Logs] Logged: {action_type} - {status} ({duration_ms}ms)")

    except Exception as e:
        print(f"[Action Logs] Error logging action: {e}")


def ensure_collection(collection_name, dim=384):
    """Ensure collection exists, create if not"""
    if not connect_milvus():
        return None

    if utility.has_collection(collection_name):
        return Collection(name=collection_name)

    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
        FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]

    schema = CollectionSchema(fields=fields, description=f"{collection_name} collection")
    collection = Collection(name=collection_name, schema=schema)

    # Create index
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    return collection


def ensure_pr_tracker_collection():
    """Ensure PR tracker collection exists"""
    if not connect_milvus():
        return None

    collection_name = 'github_pr_tracker'

    if utility.has_collection(collection_name):
        return Collection(name=collection_name)

    # Create simple tracking collection without embeddings
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="repository", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="pr_number", dtype=DataType.INT64),
        FieldSchema(name="pr_title", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=50),  # success, failed
        FieldSchema(name="error_message", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="fetched_at", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="collection_name", dtype=DataType.VARCHAR, max_length=100),
    ]

    schema = CollectionSchema(fields=fields, description="GitHub PR fetch tracking")
    collection = Collection(name=collection_name, schema=schema)

    return collection


def track_pr_fetch(repository, pr_number, pr_title, status, error_message="", collection_name="github_prs"):
    """Track a PR fetch attempt"""
    try:
        collection = ensure_pr_tracker_collection()
        if collection is None:
            return False

        data = [
            [repository],
            [pr_number],
            [pr_title[:1000]],
            [status],
            [error_message[:1000]],
            [datetime.now().isoformat()],
            [collection_name]
        ]

        collection.insert(data)
        collection.flush()
        return True
    except Exception as e:
        print(f"[PR Tracker] Error tracking PR: {e}")
        return False


def get_tracked_prs(repository=None):
    """Get list of tracked PRs"""
    try:
        if not connect_milvus():
            return []

        collection_name = 'github_pr_tracker'
        if not utility.has_collection(collection_name):
            return []

        collection = Collection(name=collection_name)
        collection.load()

        # Query PRs
        if repository:
            expr = f"repository == '{repository}'"
        else:
            expr = "repository != ''"

        results = collection.query(
            expr=expr,
            output_fields=["repository", "pr_number", "pr_title", "status", "error_message", "fetched_at", "collection_name"],
            limit=10000
        )

        collection.release()
        return results
    except Exception as e:
        print(f"[PR Tracker] Error getting tracked PRs: {e}")
        return []


def is_pr_already_fetched(repository, pr_number):
    """Check if a PR has already been successfully fetched"""
    try:
        tracked_prs = get_tracked_prs(repository)
        for pr in tracked_prs:
            if pr['pr_number'] == pr_number and pr['status'] == 'success':
                return True
        return False
    except:
        return False


def store_document(collection_name, source_type, source_id, title, content, metadata, url=""):
    """Store document in Milvus"""
    try:
        model = load_model()
        collection = ensure_collection(collection_name)

        if collection is None:
            return False, "Failed to connect to Milvus"

        # Generate embedding
        text_for_embedding = f"{title} {content[:5000]}"
        embedding = model.encode([text_for_embedding])[0].tolist()

        # Prepare data with proper truncation
        metadata_json = json.dumps(metadata)
        if len(metadata_json) > 4900:
            metadata_json = metadata_json[:4900]

        data = [
            [source_type],
            [source_id],
            [title[:1000]],
            [content[:10000]],
            [metadata_json],
            [url[:500]],
            [datetime.now().isoformat()],
            [embedding]
        ]

        # Insert
        collection.insert(data)
        collection.flush()

        return True, "Document stored successfully"
    except Exception as e:
        return False, f"Error storing document: {str(e)}"


def store_document_with_vector(collection_name, source_type, source_id, title, content, vector, metadata, url=""):
    """Store document with pre-computed vector (e.g., from images)"""
    try:
        collection = ensure_collection(collection_name)

        if collection is None:
            return False, "Failed to connect to Milvus"

        # Convert numpy vector to list if needed
        if hasattr(vector, 'tolist'):
            embedding = vector.tolist()
        else:
            embedding = list(vector)

        # Pad or truncate vector to match collection dimension (384 for all-MiniLM-L6-v2)
        # CLIP outputs 512-dim, need to handle this
        target_dim = 384
        if len(embedding) > target_dim:
            # Simple truncation (or could use PCA/projection)
            embedding = embedding[:target_dim]
        elif len(embedding) < target_dim:
            # Pad with zeros
            embedding = embedding + [0.0] * (target_dim - len(embedding))

        # Prepare data with proper truncation
        metadata_json = json.dumps(metadata)
        if len(metadata_json) > 4900:
            metadata_json = metadata_json[:4900]

        data = [
            [source_type],
            [source_id],
            [title[:1000]],
            [content[:10000]],
            [metadata_json],
            [url[:500]],
            [datetime.now().isoformat()],
            [embedding]
        ]

        # Insert
        collection.insert(data)
        collection.flush()

        return True, f"Image stored successfully with {len(vector)}-dim vector (adapted to {target_dim}-dim)"
    except Exception as e:
        return False, f"Error storing image: {str(e)}"


def fetch_jira_tickets(jira_keys):
    """Fetch Jira tickets by keys with ALL available data"""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        return None, "Jira credentials not configured"

    auth = HTTPBasicAuth(jira_email, jira_token)
    headers = {"Accept": "application/json"}

    tickets = []
    errors = []
    for key in jira_keys:
        try:
            # Fetch with ALL fields and expanded data (changelog, comments, attachments, etc.)
            url = f"{jira_url}/rest/api/3/issue/{key.strip()}"
            params = {
                'fields': 'summary,description,status,priority,issuetype,assignee,reporter,creator,created,updated,labels,components,attachment,project,parent,fixVersions,duedate,resolution,resolutiondate',
                'expand': 'changelog,renderedFields,names,schema,transitions,operations,editmeta,versionedRepresentations'
            }
            print(f"[Jira] Fetching {key} from {url}")
            response = requests.get(url, auth=auth, headers=headers, params=params)
            response.raise_for_status()
            ticket_data = response.json()

            # Also fetch comments separately for better formatting
            comments_url = f"{jira_url}/rest/api/3/issue/{key.strip()}/comment"
            comments_response = requests.get(comments_url, auth=auth, headers=headers)
            if comments_response.status_code == 200:
                ticket_data['all_comments'] = comments_response.json()

            # Fetch watchers
            try:
                watchers_url = f"{jira_url}/rest/api/3/issue/{key.strip()}/watchers"
                watchers_response = requests.get(watchers_url, auth=auth, headers=headers)
                if watchers_response.status_code == 200:
                    ticket_data['all_watchers'] = watchers_response.json()
            except:
                pass  # Watchers may not be accessible

            tickets.append(ticket_data)
            fields = ticket_data.get('fields', {})
            rendered_fields = ticket_data.get('renderedFields', {})
            names = ticket_data.get('names', {})
            print(f"[Jira] ✓ Fetched {key} with full details (fields: {len(fields)})")
            print(f"[Jira] DEBUG - Available field keys: {list(fields.keys())}")
            print(f"[Jira] DEBUG - Rendered fields keys: {list(rendered_fields.keys())}")

            # Debug: Print actual content of rendered fields
            for field_name in ['summary', 'description', 'status', 'priority']:
                if field_name in rendered_fields:
                    val = rendered_fields.get(field_name)
                    print(f"[Jira] DEBUG - renderedFields['{field_name}'] = {str(val)[:200] if val else 'None'}")

            # Save raw ticket data for inspection
            import json
            debug_file = f"jira_ticket_debug_{key}.json"
            with open(debug_file, 'w') as f:
                json.dump(ticket_data, f, indent=2, default=str)
            print(f"[Jira] DEBUG - Full ticket data saved to {debug_file}")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code} for {key}: {e.response.text[:200]}"
            print(f"[Jira] ✗ {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error fetching {key}: {str(e)}"
            print(f"[Jira] ✗ {error_msg}")
            errors.append(error_msg)

    if not tickets and errors:
        return None, f"Failed to fetch any tickets. Errors: {'; '.join(errors)}"

    return tickets, None


def fetch_confluence_page(page_url):
    """Fetch Confluence page with all available details"""
    jira_url = os.getenv("JIRA_URL")  # e.g., https://your-instance.atlassian.net
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        return None, "Confluence credentials not configured (uses Jira credentials)"

    # Parse Confluence URL to extract page ID
    # Format: https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/PAGEID/Page+Title
    try:
        # Extract page ID from URL
        match = re.search(r'/pages/(\d+)', page_url)
        if not match:
            return None, "Invalid Confluence page URL format. Expected format: .../pages/PAGEID/..."

        page_id = match.group(1)
        print(f"[Confluence] Extracted page ID: {page_id}")
    except:
        return None, "Failed to parse Confluence page URL"

    auth = HTTPBasicAuth(jira_email, jira_token)
    headers = {"Accept": "application/json"}

    try:
        # Confluence base URL (derive from JIRA_URL)
        confluence_base = jira_url.replace('/jira', '')  # Handle different URL formats
        if not '/wiki' in confluence_base:
            confluence_base = f"{confluence_base}/wiki"

        # Fetch page content with expansions
        url = f"{confluence_base}/rest/api/content/{page_id}"
        params = {
            'expand': 'body.storage,body.view,version,space,history,ancestors,children,descendants.page'
        }

        print(f"[Confluence] Fetching page {page_id} from {url}...")
        response = requests.get(url, auth=auth, headers=headers, params=params)
        response.raise_for_status()
        page_data = response.json()

        print(f"[Confluence] ✓ Fetched page: {page_data.get('title', 'Unknown')}")
        print(f"[Confluence]   - Space: {page_data.get('space', {}).get('name', 'Unknown')}")
        print(f"[Confluence]   - Version: {page_data.get('version', {}).get('number', 'Unknown')}")

        return page_data, None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None, f"Confluence page not found (ID: {page_id}). Check URL and permissions."
        elif e.response.status_code == 401:
            return None, "Authentication failed. Check Jira credentials in .env file."
        else:
            return None, f"HTTP Error {e.response.status_code}: {str(e)}"
    except Exception as e:
        print(f"[Confluence] Error: {e}")
        return None, f"Error fetching Confluence page: {str(e)}"


def fetch_github_pr(pr_url):
    """Fetch GitHub PR data with ALL available details"""
    github_token = os.getenv("GITHUB_TOKEN")

    # Parse PR URL: https://github.com/owner/repo/pull/number
    try:
        parts = pr_url.strip().split('/')
        owner = parts[3]
        repo = parts[4]
        pr_number = parts[6]
    except:
        return None, "Invalid GitHub PR URL format"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}" if github_token else ""
    }

    try:
        base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

        # Fetch PR data
        print(f"[GitHub] Fetching PR #{pr_number} from {owner}/{repo}...")
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        pr_data = response.json()

        # Fetch PR files with changes
        print(f"[GitHub] Fetching file changes...")
        files_url = f"{base_url}/files"
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        pr_data['files'] = files_response.json()

        # Fetch all issue comments (general PR comments)
        print(f"[GitHub] Fetching issue comments...")
        issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}"
        comments_url = f"{issue_url}/comments"
        comments_response = requests.get(comments_url, headers=headers)
        if comments_response.status_code == 200:
            pr_data['issue_comments'] = comments_response.json()

        # Fetch all review comments (inline code comments)
        print(f"[GitHub] Fetching review comments...")
        review_comments_url = f"{base_url}/comments"
        review_comments_response = requests.get(review_comments_url, headers=headers)
        if review_comments_response.status_code == 200:
            pr_data['review_comments'] = review_comments_response.json()

        # Fetch all reviews (approvals, changes requested, etc.)
        print(f"[GitHub] Fetching reviews...")
        reviews_url = f"{base_url}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        if reviews_response.status_code == 200:
            pr_data['reviews'] = reviews_response.json()

        # Fetch all commits in the PR
        print(f"[GitHub] Fetching commits...")
        commits_url = f"{base_url}/commits"
        commits_response = requests.get(commits_url, headers=headers)
        if commits_response.status_code == 200:
            pr_data['commits'] = commits_response.json()

        # Fetch timeline/events
        print(f"[GitHub] Fetching timeline...")
        timeline_headers = headers.copy()
        timeline_headers["Accept"] = "application/vnd.github.mockingbird-preview+json"
        timeline_url = f"{issue_url}/timeline"
        timeline_response = requests.get(timeline_url, headers=timeline_headers)
        if timeline_response.status_code == 200:
            pr_data['timeline'] = timeline_response.json()

        # Fetch linked issues (if any)
        print(f"[GitHub] Fetching issue details...")
        issue_response = requests.get(issue_url, headers=headers)
        if issue_response.status_code == 200:
            issue_data = issue_response.json()
            pr_data['labels'] = issue_data.get('labels', [])
            pr_data['assignees'] = issue_data.get('assignees', [])
            pr_data['reactions'] = issue_data.get('reactions', {})

        print(f"[GitHub] ✓ Fetched PR #{pr_number} with complete details")
        print(f"[GitHub]   - Files: {len(pr_data.get('files', []))}")
        print(f"[GitHub]   - Issue Comments: {len(pr_data.get('issue_comments', []))}")
        print(f"[GitHub]   - Review Comments: {len(pr_data.get('review_comments', []))}")
        print(f"[GitHub]   - Reviews: {len(pr_data.get('reviews', []))}")
        print(f"[GitHub]   - Commits: {len(pr_data.get('commits', []))}")

        return pr_data, None
    except Exception as e:
        print(f"[GitHub] Error: {e}")
        return None, f"Error fetching GitHub PR: {str(e)}"


##############################################################################
# HEALTH & STATUS ENDPOINTS
##############################################################################

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Milvus connection
        milvus_status = "disconnected"
        collections_count = 0

        if connect_milvus():
            milvus_status = "connected"
            collections = utility.list_collections()
            collections_count = len(collections)

        # Check models loaded
        models_loaded = {
            "text_embedding": embedding_model is not None,
            "image_vectorizer": image_vectorizer is not None
        }

        return jsonify({
            "status": "healthy",
            "service": "optus-ai",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "milvus": {
                "status": milvus_status,
                "host": MILVUS_HOST,
                "port": MILVUS_PORT,
                "collections_count": collections_count
            },
            "models": models_loaded,
            "uptime": "running"
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


##############################################################################
# CODEBASE ANALYSIS ENDPOINTS
##############################################################################

@app.route('/analyze_codebase', methods=['POST'])
def analyze_codebase():
    """
    Analyze a codebase and store in Milvus with progress tracking
    Runs in background thread and returns immediately with progress_file

    Request:
    {
        "directory": "/path/to/repo",
        "repo_name": "optional-name",
        "github_url": "https://github.com/user/repo" (optional),
        "pull_latest": true/false (default: true),
        "is_private": true/false (default: false),
        "privacy_password": "password" (default: "sdk")
    }
    """
    try:
        data = request.json
        directory = data.get('directory')
        repo_name = data.get('repo_name')
        github_url = data.get('github_url')
        pull_latest = data.get('pull_latest', True)
        is_private = data.get('is_private', False)
        privacy_password = data.get('privacy_password', 'sdk')

        if not directory:
            return jsonify({'success': False, 'message': 'Directory path required'})

        if not os.path.exists(directory):
            return jsonify({'success': False, 'message': 'Directory does not exist'})

        print(f"[API] Starting codebase analysis with progress tracking: {directory}")
        if github_url:
            print(f"[API] GitHub URL: {github_url}")
        print(f"[API] Pull latest: {pull_latest}")
        print(f"[API] Privacy: {'Private' if is_private else 'Public'}")

        # Generate unique progress file for this analysis
        progress_file = f"analysis_progress_{hashlib.md5(directory.encode()).hexdigest()[:8]}.json"

        # Define background task
        def run_analysis():
            try:
                analyzer = SmartCodebaseAnalyzer()
                result = analyzer.analyze_codebase_smart(
                    directory=directory,
                    repo_name=repo_name,
                    progress_file=progress_file,
                    skip_duplicates=True
                )
                print(f"[API] ✅ Analysis completed: {result.get('files_analyzed', 0)} files")
            except Exception as e:
                print(f"[API] ❌ Background analysis error: {e}")
                import traceback
                traceback.print_exc()

        # Start analysis in background thread
        import threading
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()

        print(f"[API] Analysis started in background. Progress file: {progress_file}")

        # Return immediately with progress file
        return jsonify({
            'success': True,
            'message': 'Analysis started in background',
            'progress_file': progress_file,
            'status': 'started'
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] ❌ Error starting codebase analysis: {e}")
        print(f"[API] Full traceback:\n{error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error': str(e),
            'traceback': error_trace
        })


@app.route('/analysis_progress', methods=['GET'])
def get_analysis_progress():
    """
    Get current analysis progress
    Query params:
    - progress_file: optional specific progress file (default: analysis_progress.json)
    """
    try:
        progress_file = request.args.get('progress_file', 'analysis_progress.json')

        if not os.path.exists(progress_file):
            return jsonify({'status': 'not_started', 'message': 'No analysis in progress'}), 404

        with open(progress_file, 'r') as f:
            progress_data = json.load(f)

        return jsonify(progress_data)

    except Exception as e:
        print(f"[API] Error reading progress: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/search_codebase', methods=['POST'])
def search_codebase():
    """
    Search codebase with semantic query

    Request:
    {
        "query": "Find authentication code",
        "top_k": 10,
        "privacy_password": "sdk" (optional, for accessing private documents)
    }
    """
    try:
        data = request.json
        query = data.get('query')
        top_k = data.get('top_k', 10)
        privacy_password = data.get('privacy_password')

        if not query:
            return jsonify({'success': False, 'message': 'Query required'})

        print(f"[API] Searching codebase: {query}")
        if privacy_password:
            print(f"[API] Privacy mode: Enabled")

        analyzer = CodebaseAnalyzer()
        results = analyzer.search_code(query, top_k, privacy_password)

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        print(f"[API] Error searching codebase: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/query_code_with_ai', methods=['POST'])
def query_code_with_ai():
    """
    Query codebase using RAG (Retrieval Augmented Generation)

    Request:
    {
        "question": "How does authentication work?",
        "ai_model": "claude" or "ollama",
        "top_k": 10
    }
    """
    try:
        data = request.json
        question = data.get('question')
        ai_model = data.get('ai_model', 'claude')
        top_k = data.get('top_k', 10)

        if not question:
            return jsonify({'success': False, 'message': 'Question required'})

        print(f"[API] Code query with {ai_model}: {question}")

        # Search codebase
        analyzer = CodebaseAnalyzer()
        code_results = analyzer.search_code(question, top_k)

        if not code_results:
            return jsonify({
                'success': True,
                'answer': 'No relevant code found in the analyzed codebase.',
                'sources': [],
                'model': ai_model
            })

        # Build context for AI
        context_docs = []
        for result in code_results:
            context_docs.append({
                'title': f"{result['file_path']} ({result['language']})",
                'content': f"""
File: {result['file_path']}
Language: {result['language']}
Summary: {result['summary']}
Classes: {', '.join(result.get('classes', [])[:5])}
Functions: {', '.join(result.get('functions', [])[:5])}
LOC: {result['lines_of_code']}
Complexity: {result['complexity']}

Code:
{result['content'][:1500]}
                """.strip(),
                'score': result['score'],
                'collection': 'codebase_analysis',
                'source_type': 'code',
                'source_id': result['file_path'],
                'url': f"file://{result['file_path']}"
            })

        # Query AI
        if ai_model == 'claude':
            rag = ClaudeRAG()
            answer = rag.ask_claude(question, context_docs)

            # Get token usage
            usage_info = getattr(rag, '_last_usage', None)
            answer_confidence = usage_info.get('answer_confidence') if usage_info else None

            # Calculate source confidence
            source_confidence = rag.calculate_confidence(code_results, len(code_results))

            # Build dual confidence
            if answer_confidence:
                if answer_confidence >= 0.8:
                    level = 'Very High'
                elif answer_confidence >= 0.65:
                    level = 'High'
                elif answer_confidence >= 0.5:
                    level = 'Medium'
                elif answer_confidence >= 0.3:
                    level = 'Low'
                else:
                    level = 'Very Low'

                confidence = {
                    'score': answer_confidence,
                    'level': level,
                    'answer_confidence': answer_confidence,
                    'source_confidence': source_confidence,
                    'type': 'dual'
                }
            else:
                confidence = source_confidence
                confidence['type'] = 'source_only'

            return jsonify({
                'success': True,
                'answer': answer,
                'sources': context_docs,
                'model': 'claude-sonnet-4-5',
                'confidence_score': confidence,
                'token_usage': usage_info
            })
        else:
            rag = OllamaRAG()
            result = rag.query_with_context(question, collection_name="codebase_analysis", top_k=0)
            # Override with our code results
            result['sources'] = context_docs
            return jsonify({
                'success': True,
                **result
            })

    except Exception as e:
        print(f"[API] Error querying code: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/codebase_stats', methods=['GET'])
def codebase_stats():
    """Get statistics about analyzed codebase"""
    try:
        analyzer = CodebaseAnalyzer()

        if not analyzer.connect_milvus():
            return jsonify({'success': False, 'message': 'Failed to connect to Milvus'})

        if not utility.has_collection('codebase_analysis'):
            return jsonify({
                'success': True,
                'analyzed': False,
                'message': 'No codebase analyzed yet'
            })

        collection = Collection(name='codebase_analysis')
        collection.load()

        # Get total count
        total_entries = collection.num_entities

        collection.release()

        return jsonify({
            'success': True,
            'analyzed': True,
            'total_entries': total_entries,
            'collection': 'codebase_analysis'
        })

    except Exception as e:
        print(f"[API] Error getting stats: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Handle file upload with automatic chunking for large CSV files"""
    import time
    import pandas as pd

    start_time = time.time()  # Track response time

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})

    file = request.files['file']
    collection_name = request.form.get('collection', 'documents')

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        file_ext = filename.rsplit('.', 1)[1].lower()

        # Check if it's an image
        file_ext = filename.rsplit('.', 1)[1].lower()
        is_image = file_ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

        if is_image:
            # Handle image upload with vectorization
            if image_vectorizer is None:
                load_model()  # Load image vectorizer if not loaded

            if image_vectorizer is None:
                return jsonify({'success': False, 'message': 'Image vectorizer not available'})

            # Extract vector from image
            try:
                vector = image_vectorizer.extract_vector(filepath)

                # Use image description as content
                content = f"Image: {filename} (Vector extracted using CLIP)"
                file_hash = hashlib.md5(filename.encode()).hexdigest()

                metadata = {
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'upload_time': datetime.now().isoformat(),
                    'type': 'image',
                    'vector_model': 'CLIP'
                }

                # Store image with its vector
                success, message = store_document_with_vector(
                    collection_name=collection_name,
                    source_type='image',
                    source_id=file_hash,
                    title=filename,
                    content=content,
                    vector=vector,
                    metadata=metadata,
                    url=filepath
                )

                # Clean up
                os.remove(filepath)

                return jsonify({
                    'success': success,
                    'message': message,
                    'vector_dim': len(vector),
                    'file_type': 'image'
                })

            except Exception as e:
                os.remove(filepath)
                return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'})

        elif file_ext == 'csv':
            # Handle CSV files with automatic chunking
            try:
                df = pd.read_csv(filepath)
                total_rows = len(df)

                # Define chunk size (1000 rows per chunk for optimal performance)
                CHUNK_SIZE = 1000
                chunks_processed = 0
                rows_stored = 0

                # Process in chunks
                for i in range(0, total_rows, CHUNK_SIZE):
                    chunk_df = df.iloc[i:i+CHUNK_SIZE]
                    chunk_json = chunk_df.to_json(orient='records')

                    # Create hash for this chunk
                    chunk_hash = hashlib.md5(f"{filename}_{i}".encode()).hexdigest()

                    metadata = {
                        'filename': filename,
                        'chunk_index': chunks_processed + 1,
                        'chunk_start_row': i,
                        'chunk_end_row': min(i + CHUNK_SIZE, total_rows),
                        'total_rows': total_rows,
                        'file_size_mb': file_size_mb,
                        'upload_time': datetime.now().isoformat(),
                        'type': 'csv_chunk'
                    }

                    # Store chunk
                    success, message = store_document(
                        collection_name=collection_name,
                        source_type='csv',
                        source_id=chunk_hash,
                        title=f"{filename} (Chunk {chunks_processed + 1})",
                        content=chunk_json,
                        metadata=metadata,
                        url=filepath
                    )

                    if success:
                        chunks_processed += 1
                        rows_stored += len(chunk_df)

                # Clean up
                os.remove(filepath)

                response_time = time.time() - start_time

                return jsonify({
                    'success': True,
                    'message': f'CSV file processed successfully',
                    'filename': filename,
                    'file_size_mb': round(file_size_mb, 2),
                    'total_rows': total_rows,
                    'chunks_processed': chunks_processed,
                    'rows_stored': rows_stored,
                    'processing_mode': 'chunked' if chunks_processed > 1 else 'single',
                    'response_time_seconds': round(response_time, 3)
                })

            except Exception as e:
                os.remove(filepath)
                response_time = time.time() - start_time
                return jsonify({
                    'success': False,
                    'message': f'Error processing CSV: {str(e)}',
                    'response_time_seconds': round(response_time, 3)
                })

        else:
            # Handle other text-based files
            content = read_file_content(filepath, filename)

            # Store in Milvus
            file_hash = hashlib.md5(content.encode()).hexdigest()
            metadata = {
                'filename': filename,
                'size': os.path.getsize(filepath),
                'upload_time': datetime.now().isoformat()
            }

            success, message = store_document(
                collection_name=collection_name,
                source_type='file',
                source_id=file_hash,
                title=filename,
                content=content,
                metadata=metadata,
                url=filepath
            )

            # Clean up
            os.remove(filepath)

            response_time = time.time() - start_time

            return jsonify({
                'success': success,
                'message': message,
                'response_time_seconds': round(response_time, 3)
            })

    return jsonify({'success': False, 'message': 'Invalid file type'})


@app.route('/fetch_jira', methods=['POST'])
def fetch_jira():
    """Fetch and store Jira tickets"""
    import time
    import hashlib
    import threading
    start_time = time.time()

    jira_input = request.json.get('jira_input', '')
    collection_name = request.json.get('collection', 'jira_tickets')

    # Parse ticket keys from input (handles URLs and plain keys)
    parsed_keys = []
    for item in jira_input.replace(',', ' ').split():
        item = item.strip()
        if not item:
            continue
        # Check if it's a URL and extract the key
        url_match = re.search(r'/browse/([A-Z]+-\d+)', item)
        if url_match:
            parsed_keys.append(url_match.group(1))
        # Check if it's just a ticket key (e.g., NEXUS-12345)
        elif re.match(r'^[A-Z]+-\d+$', item):
            parsed_keys.append(item)
    keys = parsed_keys
    print(f"[Jira] Parsed keys from input '{jira_input}': {keys}")

    if not keys:
        duration_ms = (time.time() - start_time) * 1000
        log_action(
            action_type="fetch_jira",
            endpoint="/fetch_jira",
            parameters={"jira_input": jira_input, "collection": collection_name},
            status="failed",
            duration_ms=duration_ms,
            error_message="No ticket keys provided"
        )
        return jsonify({'success': False, 'message': 'No ticket keys provided'})

    # Create unique progress file
    progress_file = f"jira_progress_{hashlib.md5(jira_input.encode()).hexdigest()[:8]}.json"

    def run_jira_fetch():
        """Background thread for fetching Jira tickets"""
        from universal_progress_tracker import UniversalProgressTracker

        tracker = UniversalProgressTracker(
            progress_file=progress_file,
            task_type="jira",
            task_name="Fetching Jira Tickets"
        )

        try:
            tracker.set_total(len(keys))
            tracker.set_phase('fetching', 'processing')

            tickets, error = fetch_jira_tickets(keys)
            print(f"[Jira] Fetched {len(tickets) if tickets else 0} tickets, error: {error}")

            if error:
                tracker.error(error)
                duration_ms = (time.time() - start_time) * 1000
                log_action(
                    action_type="fetch_jira",
                    endpoint="/fetch_jira",
                    parameters={"jira_input": jira_input, "collection": collection_name, "keys": keys},
                    status="failed",
                    duration_ms=duration_ms,
                    error_message=error
                )
                return

            tracker.set_phase('processing', 'processing')

            # Store each ticket with ALL details
            stored_count = 0
            for ticket in tickets:
                key = ticket.get('key', 'Unknown')
                fields = ticket.get('fields', {})
                rendered_fields = ticket.get('renderedFields', {})
                changelog = ticket.get('changelog', {})

                print(f"[Jira] DEBUG - Processing ticket {key}")
                print(f"[Jira] DEBUG - Fields keys: {list(fields.keys())}")
                print(f"[Jira] DEBUG - Rendered fields keys: {list(rendered_fields.keys())}")

                # Special handling for subtasks - extract from parent if direct fields unavailable
                parent_issue = fields.get('parent', {})
                parent_fields = parent_issue.get('fields', {})

                # Use renderedFields as fallback, or extract from parent for subtasks
                def get_field(field_name, default=''):
                    """Get field from fields, renderedFields, or parent fields"""
                    # Try direct field access first
                    value = fields.get(field_name)
                    if value is not None and value != '':
                        return value

                    # Try rendered fields (may contain HTML)
                    rendered_value = rendered_fields.get(field_name)
                    if rendered_value is not None and rendered_value != '':
                        return rendered_value

                    # For subtasks, check parent fields
                    if parent_fields and field_name in parent_fields:
                        parent_value = parent_fields.get(field_name)
                        if parent_value is not None and parent_value != '':
                            # Add note that this came from parent
                            print(f"[Jira] DEBUG - Using parent's {field_name} for subtask")
                            return parent_value

                    return default

                # Extract summary - if not available, use parent summary with note
                summary = get_field('summary')
                if not summary and parent_issue:
                    parent_summary = parent_fields.get('summary', '')
                    if parent_summary:
                        summary = f"[Subtask of {parent_issue.get('key')}] {parent_summary}"
                        print(f"[Jira] DEBUG - Created summary from parent: {summary[:100]}")
                if not summary:
                    summary = f"{key} (Details restricted)"

                description = get_field('description', '')
                if isinstance(description, dict):
                    description = json.dumps(description)

                # Extract assignee, reporter, creator
                assignee = fields.get('assignee', {})
                reporter = fields.get('reporter', {})
                creator = fields.get('creator', {})

                # Extract changelog/history
                history_items = []
                for history in changelog.get('histories', []):
                    history_items.append({
                        'created': history.get('created'),
                        'author': history.get('author', {}).get('displayName'),
                        'items': history.get('items', [])
                    })

                # Extract comments
                comments = []
                all_comments = ticket.get('all_comments', {})
                for comment in all_comments.get('comments', []):
                    comments.append({
                        'author': comment.get('author', {}).get('displayName'),
                        'created': comment.get('created'),
                        'body': comment.get('body')
                    })

                # Extract attachments
                attachments = []
                for attachment in fields.get('attachment', []):
                    attachments.append({
                        'filename': attachment.get('filename'),
                        'created': attachment.get('created'),
                        'size': attachment.get('size'),
                        'mimeType': attachment.get('mimeType')
                    })

                # Extract watchers
                watchers = []
                all_watchers = ticket.get('all_watchers', {})
                for watcher in all_watchers.get('watchers', []):
                    watchers.append(watcher.get('displayName'))

                # Build comprehensive metadata - use rendered fields for text fields if needed
                def extract_text_from_html(html_text):
                    """Extract plain text from HTML if renderedFields contains HTML"""
                    if not html_text or not isinstance(html_text, str):
                        return html_text
                    from bs4 import BeautifulSoup
                    try:
                        return BeautifulSoup(html_text, 'html.parser').get_text()
                    except:
                        return html_text

                # Extract complex fields with parent fallback
                status_obj = get_field('status', {})
                priority_obj = get_field('priority', {})
                issuetype_obj = get_field('issuetype', {})
                project_obj = get_field('project', {})

                # Add parent info if this is a subtask
                parent_info = {}
                if parent_issue:
                    parent_info = {
                        'parent_key': parent_issue.get('key', ''),
                        'parent_summary': parent_fields.get('summary', ''),
                        'parent_status': parent_fields.get('status', {}).get('name', ''),
                        'parent_type': parent_fields.get('issuetype', {}).get('name', '')
                    }

                metadata = {
                    'status': status_obj.get('name', 'N/A') if isinstance(status_obj, dict) else str(status_obj) if status_obj else 'N/A',
                    'status_category': status_obj.get('statusCategory', {}).get('name', 'N/A') if isinstance(status_obj, dict) else 'N/A',
                    'priority': priority_obj.get('name', 'N/A') if isinstance(priority_obj, dict) else str(priority_obj) if priority_obj else 'N/A',
                    'assignee': assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned',
                    'assignee_email': assignee.get('emailAddress', '') if assignee else '',
                    'reporter': reporter.get('displayName', 'Unknown') if reporter else 'Unknown',
                    'reporter_email': reporter.get('emailAddress', '') if reporter else '',
                    'creator': creator.get('displayName', 'Unknown') if creator else 'Unknown',
                    'issue_type': issuetype_obj.get('name', 'N/A') if isinstance(issuetype_obj, dict) else str(issuetype_obj) if issuetype_obj else 'N/A',
                    'project_key': project_obj.get('key', 'PROJECT') if isinstance(project_obj, dict) else 'PROJECT',
                    'project_name': project_obj.get('name', 'Project') if isinstance(project_obj, dict) else 'Project',
                    'labels': fields.get('labels', []),
                    'components': [c.get('name') for c in fields.get('components', [])] if fields.get('components') else [],
                    'fix_versions': [v.get('name') for v in fields.get('fixVersions', [])] if fields.get('fixVersions') else [],
                    'affected_versions': [v.get('name') for v in fields.get('versions', [])] if fields.get('versions') else [],
                    'created': fields.get('created') or rendered_fields.get('created', ''),
                    'updated': fields.get('updated', ''),
                    'resolved': fields.get('resolutiondate', ''),
                    'due_date': fields.get('duedate', ''),
                    'resolution': fields.get('resolution', {}).get('name', '') if fields.get('resolution') else '',
                    'history_count': len(history_items),
                    'comments_count': len(comments),
                    'attachments_count': len(attachments),
                    'watchers_count': len(watchers),
                    'story_points': fields.get('customfield_10016'),  # Story points (common field)
                    'epic_link': fields.get('customfield_10014'),  # Epic link (common field)
                    **parent_info  # Add parent fields if exists
                }

                print(f"[Jira] DEBUG - Final metadata: status={metadata['status']}, priority={metadata['priority']}, type={metadata['issue_type']}")

                # Build comprehensive content with all details
                content_parts = [
                    f"Summary: {summary}",
                    f"\nDescription: {description}",
                    f"\nStatus: {metadata['status']} ({metadata['status_category']})",
                    f"\nPriority: {metadata['priority']}",
                    f"\nAssignee: {metadata['assignee']}",
                    f"\nReporter: {metadata['reporter']}",
                    f"\nProject: {metadata['project_name']} ({metadata['project_key']})",
                ]

                if metadata['labels']:
                    content_parts.append(f"\nLabels: {', '.join(metadata['labels'])}")

                if metadata['components']:
                    content_parts.append(f"\nComponents: {', '.join(metadata['components'])}")

                # Add comments to content
                if comments:
                    content_parts.append("\n\n--- COMMENTS ---")
                    for i, comment in enumerate(comments[:10], 1):  # Limit to 10 most recent
                        body = comment.get('body', '')
                        if isinstance(body, dict):
                            body = json.dumps(body)
                        content_parts.append(f"\nComment {i} by {comment['author']}: {body[:500]}")

                # Add history/changelog summary
                if history_items:
                    content_parts.append("\n\n--- VERSION HISTORY ---")
                    for i, hist in enumerate(history_items[:10], 1):  # Limit to 10 most recent
                        content_parts.append(f"\n{hist['created']} by {hist['author']}: {json.dumps(hist['items'])[:200]}")

                content = '\n'.join(content_parts)

                success, _ = store_document(
                    collection_name=collection_name,
                    source_type='jira',
                    source_id=key,
                    title=f"{key}: {summary}",
                    content=content,
                    metadata=metadata,
                    url=f"{jira_url}/browse/{key}"
                )

                if success:
                    stored_count += 1
                    summary_text = str(summary)[:50] if summary else "No summary"
                    tracker.increment(current_item=f"{key}: {summary_text}...", successful=True)
                    print(f"[Jira] Stored {key} with {len(comments)} comments, {len(history_items)} history items")
                else:
                    tracker.increment(current_item=f"{key}", successful=False)

            tracker.complete(f'Successfully stored {stored_count}/{len(tickets)} tickets')

            duration_ms = (time.time() - start_time) * 1000
            log_action(
                action_type="fetch_jira",
                endpoint="/fetch_jira",
                parameters={"jira_input": jira_input, "collection": collection_name, "keys": keys},
                status="success",
                duration_ms=duration_ms,
                result_summary=f'Stored {stored_count}/{len(tickets)} tickets',
                metadata={"stored_count": stored_count, "total_tickets": len(tickets)}
            )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            tracker.error(str(e))
            print(f"[Jira] Error: {e}")
            print(f"[Jira] Traceback:\n{error_details}")

    # Start background thread
    thread = threading.Thread(target=run_jira_fetch, daemon=True)
    thread.start()

    # Return immediately with progress file
    return jsonify({
        'success': True,
        'progress_file': progress_file,
        'status': 'started',
        'message': f'Started fetching {len(keys)} Jira tickets'
    })


@app.route('/jira_progress', methods=['GET'])
def get_jira_progress():
    """Get Jira fetch progress"""
    progress_file = request.args.get('progress_file', 'jira_progress.json')
    try:
        with open(progress_file, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({'status': 'not_found', 'message': 'Progress file not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/fetch_confluence', methods=['POST'])
def fetch_confluence():
    """Fetch and store Confluence page"""
    page_url = request.json.get('page_url', '')
    collection_name = request.json.get('collection', 'confluence_pages')

    if not page_url:
        return jsonify({'success': False, 'message': 'No Confluence page URL provided'})

    page_data, error = fetch_confluence_page(page_url)

    if error:
        return jsonify({'success': False, 'message': error})

    # Extract page details
    page_id = page_data.get('id', 'unknown')
    title = page_data.get('title', 'No title')
    page_type = page_data.get('type', 'page')

    # Extract space information
    space = page_data.get('space', {})
    space_key = space.get('key', 'Unknown')
    space_name = space.get('name', 'Unknown')

    # Extract version information
    version_info = page_data.get('version', {})
    version_number = version_info.get('number', 1)
    last_modified_by = version_info.get('by', {}).get('displayName', 'Unknown')
    last_modified = version_info.get('when', '')

    # Extract creation information from history
    history = page_data.get('history', {})
    created_by = history.get('createdBy', {}).get('displayName', 'Unknown')
    created_date = history.get('createdDate', '')

    # Extract body content (HTML)
    body_storage = page_data.get('body', {}).get('storage', {}).get('value', '')
    body_view = page_data.get('body', {}).get('view', {}).get('value', '')

    # Convert HTML to plain text using BeautifulSoup
    soup = BeautifulSoup(body_storage or body_view, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean it up
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    body_text = '\n'.join(chunk for chunk in chunks if chunk)

    # Extract ancestors (parent pages) for breadcrumb
    ancestors = []
    for ancestor in page_data.get('ancestors', []):
        ancestors.append({
            'id': ancestor.get('id'),
            'title': ancestor.get('title')
        })

    # Build comprehensive metadata
    metadata = {
        'page_id': page_id,
        'page_type': page_type,
        'space_key': space_key,
        'space_name': space_name,
        'version': version_number,
        'created_by': created_by,
        'created_date': created_date,
        'last_modified_by': last_modified_by,
        'last_modified': last_modified,
        'ancestors': ancestors,
        'ancestor_titles': [a['title'] for a in ancestors],
        'has_children': len(page_data.get('children', {}).get('page', {}).get('results', [])) > 0,
    }

    # Build comprehensive content
    content_parts = [
        f"Title: {title}",
        f"\nSpace: {space_name} ({space_key})",
        f"\nCreated by: {created_by} on {created_date[:10] if created_date else 'Unknown'}",
        f"\nLast modified by: {last_modified_by} on {last_modified[:10] if last_modified else 'Unknown'}",
        f"\nVersion: {version_number}",
    ]

    # Add breadcrumb (ancestor path)
    if ancestors:
        breadcrumb = ' > '.join([a['title'] for a in ancestors])
        content_parts.append(f"\nBreadcrumb: {breadcrumb} > {title}")

    # Add main content
    content_parts.append(f"\n\n--- CONTENT ---\n{body_text}")

    content = '\n'.join(content_parts)

    # Store in Optus
    success, message = store_document(
        collection_name=collection_name,
        source_type='confluence',
        source_id=f"PAGE#{page_id}",
        title=title,
        content=content,
        metadata=metadata,
        url=page_url
    )

    if success:
        summary = (
            f"Stored Confluence page: {title} (ID: {page_id}) from {space_name} space. "
            f"Version {version_number}, last modified by {last_modified_by}"
        )
        print(f"[Confluence] {summary}")
        return jsonify({
            'success': True,
            'message': summary,
            'page_info': {
                'title': title,
                'page_id': page_id,
                'space': space_name,
                'version': version_number,
                'created_by': created_by,
                'last_modified_by': last_modified_by
            }
        })
    else:
        return jsonify({'success': False, 'message': message})


@app.route('/fetch_github_pr', methods=['POST'])
def fetch_github_pr_route():
    """Fetch and store GitHub PR with ALL details"""
    pr_url = request.json.get('pr_url', '')
    collection_name = request.json.get('collection', 'github_prs')

    if not pr_url:
        return jsonify({'success': False, 'message': 'No PR URL provided'})

    pr_data, error = fetch_github_pr(pr_url)

    if error:
        return jsonify({'success': False, 'message': error})

    # Extract basic info
    title = pr_data.get('title', 'No title')
    body = pr_data.get('body', '') or ''
    pr_number = pr_data.get('number', 0)
    state = pr_data.get('state', 'unknown')
    merged = pr_data.get('merged', False)
    draft = pr_data.get('draft', False)

    # Extract people
    author = pr_data.get('user', {})
    author_name = author.get('name') or author.get('login', 'unknown')  # Prefer real name
    assignees = [a.get('login') for a in pr_data.get('assignees', [])]
    requested_reviewers = [r.get('login') for r in pr_data.get('requested_reviewers', [])]

    # Extract merged_by
    merged_by_user = pr_data.get('merged_by', {})
    merged_by = merged_by_user.get('name') or merged_by_user.get('login') if merged_by_user else None

    # Extract labels
    labels = [label.get('name') for label in pr_data.get('labels', [])]

    # Collect file changes
    files_info = []
    total_additions = 0
    total_deletions = 0
    for file in pr_data.get('files', []):
        additions = file.get('additions', 0)
        deletions = file.get('deletions', 0)
        total_additions += additions
        total_deletions += deletions

        files_info.append({
            'filename': file.get('filename'),
            'status': file.get('status'),
            'additions': additions,
            'deletions': deletions,
            'changes': file.get('changes', 0),
            'patch': file.get('patch', '')[:500]  # First 500 chars of diff
        })

    # Collect issue comments (general PR discussion)
    issue_comments = []
    for comment in pr_data.get('issue_comments', []):
        issue_comments.append({
            'author': comment.get('user', {}).get('login'),
            'created_at': comment.get('created_at'),
            'body': comment.get('body', '')
        })

    # Collect review comments (inline code comments)
    review_comments = []
    for comment in pr_data.get('review_comments', []):
        review_comments.append({
            'author': comment.get('user', {}).get('login'),
            'created_at': comment.get('created_at'),
            'path': comment.get('path'),
            'line': comment.get('line'),
            'body': comment.get('body', '')
        })

    # Collect reviews (approvals, changes requested, etc.)
    reviews = []
    for review in pr_data.get('reviews', []):
        reviewer = review.get('user', {})
        reviewer_name = reviewer.get('name') or reviewer.get('login', 'unknown')  # Prefer real name
        reviews.append({
            'author': reviewer_name,
            'login': reviewer.get('login'),
            'state': review.get('state'),  # APPROVED, CHANGES_REQUESTED, COMMENTED
            'submitted_at': review.get('submitted_at'),
            'body': review.get('body', '')
        })

    # Collect commits
    commits = []
    for commit in pr_data.get('commits', []):
        commits.append({
            'sha': commit.get('sha', '')[:7],
            'author': commit.get('commit', {}).get('author', {}).get('name'),
            'message': commit.get('commit', {}).get('message', ''),
            'date': commit.get('commit', {}).get('author', {}).get('date')
        })

    # Collect timeline events (for key actions)
    timeline_events = []
    for event in pr_data.get('timeline', [])[:20]:  # Limit to 20 most important events
        event_type = event.get('event')
        if event_type in ['merged', 'closed', 'reopened', 'review_requested', 'assigned', 'labeled']:
            timeline_events.append({
                'event': event_type,
                'actor': event.get('actor', {}).get('login') if event.get('actor') else None,
                'created_at': event.get('created_at')
            })

    # Count approvals vs changes requested
    approvals = sum(1 for r in reviews if r['state'] == 'APPROVED')
    changes_requested = sum(1 for r in reviews if r['state'] == 'CHANGES_REQUESTED')

    # Build comprehensive metadata
    metadata = {
        'number': pr_number,
        'state': state,
        'merged': merged,
        'draft': draft,
        'author': author_name,
        'author_login': author.get('login', 'unknown'),
        'merged_by': merged_by,
        'assignees': assignees,
        'requested_reviewers': requested_reviewers,
        'labels': labels,
        'created_at': pr_data.get('created_at', ''),
        'updated_at': pr_data.get('updated_at', ''),
        'merged_at': pr_data.get('merged_at', ''),
        'closed_at': pr_data.get('closed_at', ''),
        'base_branch': pr_data.get('base', {}).get('ref', ''),
        'head_branch': pr_data.get('head', {}).get('ref', ''),
        'mergeable': pr_data.get('mergeable'),
        'mergeable_state': pr_data.get('mergeable_state', ''),
        'files_count': len(files_info),
        'additions': total_additions,
        'deletions': total_deletions,
        'changed_files': pr_data.get('changed_files', 0),
        'commits_count': len(commits),
        'issue_comments_count': len(issue_comments),
        'review_comments_count': len(review_comments),
        'reviews_count': len(reviews),
        'approvals': approvals,
        'changes_requested': changes_requested,
        'reactions': pr_data.get('reactions', {}),
    }

    # Build comprehensive content with all details
    content_parts = [
        f"Title: {title}",
        f"\nState: {state} {'(DRAFT)' if draft else ''} {'[MERGED]' if merged else ''}",
        f"\nAuthor: {author.get('login')}",
        f"\nBase: {metadata['base_branch']} ← Head: {metadata['head_branch']}",
        f"\n\nDescription:\n{body}",
    ]

    if labels:
        content_parts.append(f"\n\nLabels: {', '.join(labels)}")

    if assignees:
        content_parts.append(f"\nAssignees: {', '.join(assignees)}")

    if requested_reviewers:
        content_parts.append(f"\nRequested Reviewers: {', '.join(requested_reviewers)}")

    # Add file changes summary
    content_parts.append(f"\n\n--- FILES CHANGED ({len(files_info)} files) ---")
    content_parts.append(f"Total: +{total_additions} additions, -{total_deletions} deletions")
    for file_info in files_info[:20]:  # Limit to 20 files
        content_parts.append(
            f"\n  {file_info['status']}: {file_info['filename']} "
            f"(+{file_info['additions']}/-{file_info['deletions']})"
        )

    # Add commits
    if commits:
        content_parts.append(f"\n\n--- COMMITS ({len(commits)}) ---")
        for i, commit in enumerate(commits[:15], 1):  # Limit to 15 commits
            content_parts.append(
                f"\n{i}. [{commit['sha']}] {commit['message'].split(chr(10))[0][:100]} "
                f"by {commit['author']}"
            )

    # Add reviews
    if reviews:
        content_parts.append(f"\n\n--- REVIEWS ({len(reviews)}: {approvals} approved, {changes_requested} changes requested) ---")
        for i, review in enumerate(reviews, 1):
            review_body = review['body'][:300] if review['body'] else '(no comment)'
            content_parts.append(
                f"\n{i}. {review['state']} by {review['author']}: {review_body}"
            )

    # Add issue comments (general PR discussion)
    if issue_comments:
        content_parts.append(f"\n\n--- DISCUSSION COMMENTS ({len(issue_comments)}) ---")
        for i, comment in enumerate(issue_comments[:15], 1):  # Limit to 15 comments
            content_parts.append(
                f"\n{i}. {comment['author']}: {comment['body'][:500]}"
            )

    # Add review comments (inline code comments)
    if review_comments:
        content_parts.append(f"\n\n--- CODE REVIEW COMMENTS ({len(review_comments)}) ---")
        for i, comment in enumerate(review_comments[:15], 1):  # Limit to 15 comments
            content_parts.append(
                f"\n{i}. {comment['author']} on {comment['path']}:{comment.get('line', '?')}: "
                f"{comment['body'][:300]}"
            )

    # Add timeline summary
    if timeline_events:
        content_parts.append(f"\n\n--- TIMELINE ({len(timeline_events)} key events) ---")
        for event in timeline_events[:10]:
            actor = event.get('actor') or 'system'
            content_parts.append(f"\n  {event['event']} by {actor}")

    content = '\n'.join(content_parts)

    # Truncate content to fit Optus field limit (10000 chars)
    if len(content) > 9900:
        content = content[:9900] + "\n\n[Content truncated due to length...]"

    success, message = store_document(
        collection_name=collection_name,
        source_type='github_pr',
        source_id=f"PR#{pr_number}",
        title=f"PR #{pr_number}: {title}",
        content=content,
        metadata=metadata,
        url=pr_data.get('html_url', '')
    )

    if success:
        summary = (
            f"Stored PR #{pr_number} with {len(files_info)} files, "
            f"{len(commits)} commits, {len(reviews)} reviews, "
            f"{len(issue_comments)} comments, {len(review_comments)} review comments"
        )
        print(f"[GitHub] {summary}")
        return jsonify({'success': True, 'message': summary})
    else:
        return jsonify({'success': False, 'message': message})


@app.route('/github_rate_limit', methods=['GET'])
def github_rate_limit():
    """Check GitHub API rate limit status"""
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        return jsonify({
            'success': False,
            'message': 'GITHUB_TOKEN not configured in .env file'
        })

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }

    try:
        response = requests.get("https://api.github.com/rate_limit", headers=headers)
        response.raise_for_status()
        data = response.json()

        core = data['resources']['core']
        search = data['resources'].get('search', {})

        # Calculate reset time
        from datetime import datetime
        reset_time = datetime.fromtimestamp(core['reset']).strftime('%Y-%m-%d %H:%M:%S')
        minutes_until_reset = (core['reset'] - datetime.now().timestamp()) / 60

        # Calculate estimated PRs that can be fetched
        remaining_calls = core['remaining']
        estimated_prs = remaining_calls // 8  # ~8 API calls per PR

        return jsonify({
            'success': True,
            'rate_limit': {
                'limit': core['limit'],
                'remaining': core['remaining'],
                'used': core['used'],
                'reset_at': reset_time,
                'minutes_until_reset': round(minutes_until_reset, 1),
                'percentage_used': round((core['used'] / core['limit']) * 100, 1)
            },
            'search': {
                'limit': search.get('limit', 'N/A'),
                'remaining': search.get('remaining', 'N/A')
            },
            'estimates': {
                'prs_can_fetch': estimated_prs,
                'warning': 'Rate limit exceeded' if remaining_calls < 100 else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error checking rate limit: {str(e)}'
        })


@app.route('/fetch_repo_prs', methods=['POST'])
def fetch_repo_prs():
    """Fetch all PRs (or latest 100) from a GitHub repository"""
    import time
    start_time = time.time()

    repo_url = request.json.get('repo_url', '').strip()
    pr_limit = request.json.get('pr_limit', '100').strip()  # '100' or '*' for all
    state = request.json.get('state', 'all')  # open, closed, all
    collection_name = request.json.get('collection', 'github_prs')

    parameters = {"repo_url": repo_url, "pr_limit": pr_limit, "state": state, "collection": collection_name}

    if not repo_url:
        duration_ms = (time.time() - start_time) * 1000
        log_action(
            action_type="fetch_repo_prs",
            endpoint="/fetch_repo_prs",
            parameters=parameters,
            status="failed",
            duration_ms=duration_ms,
            error_message="No repository URL provided"
        )
        return jsonify({'success': False, 'message': 'No repository URL provided'})

    # Parse repo URL: https://github.com/owner/repo
    try:
        parts = repo_url.strip().rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
    except:
        return jsonify({'success': False, 'message': 'Invalid GitHub repository URL format. Expected: https://github.com/owner/repo'})

    github_token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}" if github_token else ""
    }

    # Determine if we fetch all or limited
    fetch_all = (pr_limit == '*')
    max_prs = None if fetch_all else int(pr_limit)

    try:
        print(f"\n[Repo Fetch] Starting to fetch PRs from {owner}/{repo}")
        print(f"[Repo Fetch] Limit: {'ALL' if fetch_all else max_prs} PRs")
        print(f"[Repo Fetch] State filter: {state}")

        # Check rate limit before starting
        if github_token:
            rate_check = requests.get("https://api.github.com/rate_limit", headers=headers)
            if rate_check.status_code == 200:
                rate_data = rate_check.json()
                remaining = rate_data['resources']['core']['remaining']
                limit = rate_data['resources']['core']['limit']
                estimated_prs = remaining // 8

                print(f"[Repo Fetch] GitHub API Rate Limit: {remaining}/{limit} remaining")
                print(f"[Repo Fetch] Estimated PRs can fetch: ~{estimated_prs}")

                if remaining < 100:
                    return jsonify({
                        'success': False,
                        'message': f'GitHub rate limit too low ({remaining} remaining). Need at least 100 calls. Please wait and try again.'
                    })
                elif max_prs and (max_prs * 8) > remaining:
                    return jsonify({
                        'success': False,
                        'message': f'Requested {max_prs} PRs (~{max_prs * 8} API calls) but only {remaining} calls remaining. Try a smaller number or wait for rate limit reset.'
                    })

        # Fetch PR list with pagination
        all_pr_numbers = []
        page = 1
        per_page = 100

        while True:
            list_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            params = {
                'state': state,
                'per_page': per_page,
                'page': page,
                'sort': 'created',
                'direction': 'desc'
            }

            print(f"[Repo Fetch] Fetching page {page}...")
            response = requests.get(list_url, headers=headers, params=params)
            response.raise_for_status()

            prs_page = response.json()

            if not prs_page:
                break

            for pr in prs_page:
                all_pr_numbers.append(pr['number'])

                # Stop if we reached the limit
                if max_prs and len(all_pr_numbers) >= max_prs:
                    break

            if max_prs and len(all_pr_numbers) >= max_prs:
                break

            # Check if there are more pages
            if len(prs_page) < per_page:
                break

            page += 1

        total_prs = len(all_pr_numbers)
        print(f"[Repo Fetch] Found {total_prs} PRs to fetch")

        if total_prs == 0:
            return jsonify({
                'success': True,
                'message': 'No PRs found in repository',
                'stats': {
                    'total_prs': 0,
                    'stored_prs': 0,
                    'failed_prs': 0
                }
            })

        # Parallel PR processing function
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading

        # Thread-safe counters
        stored_count = 0
        failed_count = 0
        skipped_count = 0
        repository_full = f"{owner}/{repo}"
        counter_lock = threading.Lock()

        def process_single_pr(pr_info):
            """Process a single PR (thread-safe)"""
            nonlocal stored_count, failed_count, skipped_count
            i, pr_number = pr_info

            try:
                # Check if PR already fetched
                if is_pr_already_fetched(repository_full, pr_number):
                    print(f"[Repo Fetch] ({i}/{total_prs}) PR #{pr_number} already fetched, skipping...")
                    with counter_lock:
                        skipped_count += 1
                        stored_count += 1
                    return {"status": "skipped", "pr_number": pr_number}

                print(f"[Repo Fetch] ({i}/{total_prs}) Fetching PR #{pr_number}...")

                pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
                pr_data, error = fetch_github_pr(pr_url)

                if error:
                    print(f"[Repo Fetch] ✗ Failed PR #{pr_number}: {error}")
                    track_pr_fetch(repository_full, pr_number, f"PR #{pr_number}", "failed", error, collection_name)
                    with counter_lock:
                        failed_count += 1
                    return {"status": "failed", "pr_number": pr_number, "error": error}

                # Store PR (reuse existing logic from fetch_github_pr_route)
                title = pr_data.get('title', 'No title')
                body = pr_data.get('body', '') or ''
                pr_number_data = pr_data.get('number', 0)
                state_data = pr_data.get('state', 'unknown')
                merged = pr_data.get('merged', False)
                draft = pr_data.get('draft', False)

                # Extract people
                author = pr_data.get('user', {})
                author_name = author.get('name') or author.get('login', 'unknown')
                assignees = [a.get('login') for a in pr_data.get('assignees', [])]
                requested_reviewers = [r.get('login') for r in pr_data.get('requested_reviewers', [])]

                # Extract merged_by
                merged_by_user = pr_data.get('merged_by', {})
                merged_by = merged_by_user.get('name') or merged_by_user.get('login') if merged_by_user else None

                # Extract labels
                labels = [label.get('name') for label in pr_data.get('labels', [])]

                # Collect file changes
                files_info = []
                total_additions = 0
                total_deletions = 0
                for file in pr_data.get('files', []):
                    additions = file.get('additions', 0)
                    deletions = file.get('deletions', 0)
                    total_additions += additions
                    total_deletions += deletions

                    files_info.append({
                        'filename': file.get('filename'),
                        'status': file.get('status'),
                        'additions': additions,
                        'deletions': deletions,
                        'changes': file.get('changes', 0),
                        'patch': file.get('patch', '')[:500]
                    })

                # Collect issue comments
                issue_comments = []
                for comment in pr_data.get('issue_comments', []):
                    commenter = comment.get('user', {})
                    commenter_name = commenter.get('name') or commenter.get('login', 'unknown')
                    issue_comments.append({
                        'author': commenter_name,
                        'created_at': comment.get('created_at'),
                        'body': comment.get('body', '')
                    })

                # Collect review comments
                review_comments = []
                for comment in pr_data.get('review_comments', []):
                    commenter = comment.get('user', {})
                    commenter_name = commenter.get('name') or commenter.get('login', 'unknown')
                    review_comments.append({
                        'author': commenter_name,
                        'created_at': comment.get('created_at'),
                        'path': comment.get('path'),
                        'line': comment.get('line'),
                        'body': comment.get('body', '')
                    })

                # Collect reviews
                reviews = []
                for review in pr_data.get('reviews', []):
                    reviewer = review.get('user', {})
                    reviewer_name = reviewer.get('name') or reviewer.get('login', 'unknown')
                    reviews.append({
                        'author': reviewer_name,
                        'state': review.get('state'),
                        'submitted_at': review.get('submitted_at'),
                        'body': review.get('body', '')
                    })

                # Collect commits
                commits = []
                for commit in pr_data.get('commits', []):
                    commits.append({
                        'sha': commit.get('sha', '')[:7],
                        'author': commit.get('commit', {}).get('author', {}).get('name'),
                        'message': commit.get('commit', {}).get('message', ''),
                        'date': commit.get('commit', {}).get('author', {}).get('date')
                    })

                # Count approvals vs changes requested
                approvals = sum(1 for r in reviews if r['state'] == 'APPROVED')
                changes_requested = sum(1 for r in reviews if r['state'] == 'CHANGES_REQUESTED')

                # Build metadata
                metadata = {
                    'number': pr_number_data,
                    'state': state_data,
                    'merged': merged,
                    'draft': draft,
                    'author': author_name,
                    'author_login': author.get('login', 'unknown'),
                    'merged_by': merged_by,
                    'assignees': assignees,
                    'requested_reviewers': requested_reviewers,
                    'labels': labels,
                    'created_at': pr_data.get('created_at', ''),
                    'updated_at': pr_data.get('updated_at', ''),
                    'merged_at': pr_data.get('merged_at', ''),
                    'closed_at': pr_data.get('closed_at', ''),
                    'base_branch': pr_data.get('base', {}).get('ref', ''),
                    'head_branch': pr_data.get('head', {}).get('ref', ''),
                    'files_count': len(files_info),
                    'additions': total_additions,
                    'deletions': total_deletions,
                    'commits_count': len(commits),
                    'issue_comments_count': len(issue_comments),
                    'review_comments_count': len(review_comments),
                    'reviews_count': len(reviews),
                    'approvals': approvals,
                    'changes_requested': changes_requested,
                }

                # Build content
                content_parts = [
                    f"Title: {title}",
                    f"\nState: {state_data} {'(DRAFT)' if draft else ''} {'[MERGED]' if merged else ''}",
                    f"\nAuthor: {author_name}",
                    f"\nBase: {metadata['base_branch']} ← Head: {metadata['head_branch']}",
                    f"\n\nDescription:\n{body}",
                ]

                if labels:
                    content_parts.append(f"\n\nLabels: {', '.join(labels)}")

                # Add file changes
                content_parts.append(f"\n\n--- FILES CHANGED ({len(files_info)} files) ---")
                content_parts.append(f"Total: +{total_additions} additions, -{total_deletions} deletions")
                for file_info in files_info[:20]:
                    content_parts.append(
                        f"\n  {file_info['status']}: {file_info['filename']} "
                        f"(+{file_info['additions']}/-{file_info['deletions']})"
                    )

                # Add commits
                if commits:
                    content_parts.append(f"\n\n--- COMMITS ({len(commits)}) ---")
                    for idx, commit in enumerate(commits[:15], 1):
                        content_parts.append(
                            f"\n{idx}. [{commit['sha']}] {commit['message'].split(chr(10))[0][:100]} "
                            f"by {commit['author']}"
                        )

                # Add reviews
                if reviews:
                    content_parts.append(f"\n\n--- REVIEWS ({len(reviews)}: {approvals} approved, {changes_requested} changes requested) ---")
                    for idx, review in enumerate(reviews, 1):
                        review_body = review['body'][:300] if review['body'] else '(no comment)'
                        content_parts.append(
                            f"\n{idx}. {review['state']} by {review['author']}: {review_body}"
                        )

                # Add issue comments
                if issue_comments:
                    content_parts.append(f"\n\n--- DISCUSSION COMMENTS ({len(issue_comments)}) ---")
                    for idx, comment in enumerate(issue_comments[:15], 1):
                        content_parts.append(
                            f"\n{idx}. {comment['author']}: {comment['body'][:500]}"
                        )

                # Add review comments
                if review_comments:
                    content_parts.append(f"\n\n--- CODE REVIEW COMMENTS ({len(review_comments)}) ---")
                    for idx, comment in enumerate(review_comments[:15], 1):
                        content_parts.append(
                            f"\n{idx}. {comment['author']} on {comment['path']}:{comment.get('line', '?')}: "
                            f"{comment['body'][:300]}"
                        )

                content = '\n'.join(content_parts)

                # Truncate content to fit Optus field limit (10000 chars)
                if len(content) > 9900:
                    content = content[:9900] + "\n\n[Content truncated due to length...]"

                # Store in Optus
                success, msg = store_document(
                    collection_name=collection_name,
                    source_type='github_pr',
                    source_id=f"PR#{pr_number_data}",
                    title=f"PR #{pr_number_data}: {title}",
                    content=content,
                    metadata=metadata,
                    url=pr_data.get('html_url', '')
                )

                if success:
                    with counter_lock:
                        stored_count += 1
                    print(f"[Repo Fetch] ✓ Stored PR #{pr_number_data}")
                    # Track successful fetch
                    track_pr_fetch(repository_full, pr_number_data, title, "success", "", collection_name)
                    return {"status": "success", "pr_number": pr_number_data}
                else:
                    with counter_lock:
                        failed_count += 1
                    print(f"[Repo Fetch] ✗ Failed to store PR #{pr_number_data}: {msg}")
                    # Track failed storage
                    track_pr_fetch(repository_full, pr_number_data, title, "failed", msg, collection_name)
                    return {"status": "failed", "pr_number": pr_number_data, "error": msg}

            except Exception as e:
                print(f"[Repo Fetch] ✗ Error processing PR #{pr_number}: {e}")
                track_pr_fetch(repository_full, pr_number, f"PR #{pr_number}", "failed", str(e), collection_name)
                with counter_lock:
                    failed_count += 1
                return {"status": "failed", "pr_number": pr_number, "error": str(e)}

        # Execute PR fetching in parallel with ThreadPoolExecutor
        max_workers = 5  # Process 5 PRs concurrently
        print(f"[Repo Fetch] Using {max_workers} parallel workers for fetching PRs")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all PR processing tasks
            pr_tasks = [(i, pr_num) for i, pr_num in enumerate(all_pr_numbers, 1)]
            future_to_pr = {executor.submit(process_single_pr, pr_info): pr_info for pr_info in pr_tasks}

            # Process results as they complete
            for future in as_completed(future_to_pr):
                pr_info = future_to_pr[future]
                try:
                    result = future.result()
                    # Result already logged by process_single_pr
                except Exception as e:
                    print(f"[Repo Fetch] Unexpected error in parallel task for PR {pr_info[1]}: {e}")
                    with counter_lock:
                        failed_count += 1

        print(f"\n[Repo Fetch] Complete! Stored: {stored_count}, Failed: {failed_count}, Skipped: {skipped_count}")

        # Auto-trigger persona analysis
        print(f"[Repo Fetch] Starting persona analysis...")
        analyzer = GitHubPersonaAnalyzer(collection_name=collection_name)
        persona_result = analyzer.build_all_personas()

        duration_ms = (time.time() - start_time) * 1000
        log_action(
            action_type="fetch_repo_prs",
            endpoint="/fetch_repo_prs",
            parameters=parameters,
            status="success",
            duration_ms=duration_ms,
            result_summary=f'Fetched {stored_count}/{total_prs} PRs, built {len(persona_result.get("personas", []))} personas',
            metadata={
                "repository": f"{owner}/{repo}",
                "stored_prs": stored_count,
                "failed_prs": failed_count,
                "skipped_prs": skipped_count,
                "personas_built": len(persona_result.get('personas', []))
            }
        )

        return jsonify({
            'success': True,
            'message': f'Successfully fetched {stored_count}/{total_prs} PRs ({skipped_count} already existed) and built {len(persona_result.get("personas", []))} personas',
            'stats': {
                'total_prs': total_prs,
                'stored_prs': stored_count,
                'failed_prs': failed_count,
                'skipped_prs': skipped_count,
                'personas_built': len(persona_result.get('personas', [])),
                'repository': f"{owner}/{repo}"
            },
            'persona_result': persona_result
        })

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_action(
            action_type="fetch_repo_prs",
            endpoint="/fetch_repo_prs",
            parameters=parameters,
            status="failed",
            duration_ms=duration_ms,
            error_message=str(e)
        )
        print(f"[Repo Fetch] Error: {e}")
        return jsonify({'success': False, 'message': f'Error fetching repository PRs: {str(e)}'})


@app.route('/search', methods=['POST'])
def search():
    """Hybrid search: exact ID match first, then semantic search"""
    query = request.json.get('query', '')
    collection_name = request.json.get('collection', 'jira_tickets')
    top_k = request.json.get('top_k', 5)

    if not query:
        return jsonify({'success': False, 'message': 'No query provided'})

    try:
        if not connect_milvus():
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        if not utility.has_collection(collection_name):
            return jsonify({'success': False, 'message': f'Collection {collection_name} does not exist'})

        collection = Collection(name=collection_name)
        collection.load()

        formatted_results = []
        search_method = 'semantic'

        # Step 1: Extract ticket ID from query (NEXUS-XXXXX or URL)
        ticket_id = extract_ticket_id(query)

        if ticket_id:
            print(f"[Search] Extracted ticket ID: {ticket_id}")
            # Try exact match first
            try:
                exact_results = collection.query(
                    expr=f"source_id == '{ticket_id}'",
                    output_fields=["source_type", "source_id", "title", "content", "metadata", "url", "created_at"],
                    limit=1
                )

                if exact_results:
                    print(f"[Search] Found exact match for {ticket_id}")
                    search_method = 'exact_match'
                    for result in exact_results:
                        formatted_results.append({
                            'source_type': result.get('source_type'),
                            'source_id': result.get('source_id'),
                            'title': result.get('title'),
                            'content': result.get('content'),
                            'metadata': json.loads(result.get('metadata', '{}')),
                            'url': result.get('url'),
                            'created_at': result.get('created_at'),
                            'similarity_score': 1.0,  # Perfect match
                            'match_type': 'exact'
                        })
            except Exception as e:
                print(f"[Search] Exact match failed: {e}")

        # Step 2: If no exact match or no ticket ID, do semantic search
        if not formatted_results:
            print(f"[Search] Using semantic search for: {query}")
            model = load_model()

            # Generate query embedding
            query_embedding = model.encode([query]).tolist()

            # Search
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["source_type", "source_id", "title", "content", "metadata", "url", "created_at"]
            )

            # Format results
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        'source_type': hit.entity.get('source_type'),
                        'source_id': hit.entity.get('source_id'),
                        'title': hit.entity.get('title'),
                        'content': hit.entity.get('content')[:500] + '...',
                        'metadata': json.loads(hit.entity.get('metadata', '{}')),
                        'url': hit.entity.get('url'),
                        'created_at': hit.entity.get('created_at'),
                        'similarity_score': round(1 / (1 + hit.distance), 4),
                        'match_type': 'semantic'
                    })

        collection.release()

        return jsonify({
            'success': True,
            'results': formatted_results,
            'search_method': search_method,
            'ticket_id_extracted': ticket_id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Search error: {str(e)}'})


@app.route('/collections', methods=['GET'])
def get_collections():
    """List all collections"""
    try:
        if not connect_milvus():
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        collections = utility.list_collections()
        collection_info = []

        for coll_name in collections:
            coll = Collection(name=coll_name)
            collection_info.append({
                'name': coll_name,
                'count': coll.num_entities
            })

        return jsonify({'success': True, 'collections': collection_info})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/crawl_website', methods=['POST'])
def crawl_website():
    """Crawl entire website and store all pages in Optus"""
    start_url = request.json.get('start_url', '')
    collection_name = request.json.get('collection', 'website_crawl')
    max_pages = request.json.get('max_pages', 50)
    max_depth = request.json.get('max_depth', 3)

    if not start_url:
        return jsonify({'success': False, 'message': 'No start URL provided'})

    # Validate URL
    from urllib.parse import urlparse
    try:
        parsed = urlparse(start_url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({'success': False, 'message': 'Invalid URL format'})
    except:
        return jsonify({'success': False, 'message': 'Invalid URL'})

    try:
        print(f"\n[Web Interface] Starting crawl of {start_url}")
        print(f"[Web Interface] Max pages: {max_pages}, Max depth: {max_depth}")
        print(f"[Web Interface] Collection: {collection_name}")

        # Create crawler and start
        crawler = WebCrawler(max_pages=max_pages, max_depth=max_depth, delay=1.0)
        result = crawler.crawl(start_url, collection_name=collection_name)

        if result['success']:
            message = (
                f"Successfully crawled {result['pages_stored']} pages from {result['start_url']}. "
                f"Total crawled: {result['pages_crawled']}, Failed: {result['pages_failed']}. "
                f"Time: {result['elapsed_time']:.1f}s"
            )
            return jsonify({
                'success': True,
                'message': message,
                'stats': {
                    'pages_crawled': result['pages_crawled'],
                    'pages_stored': result['pages_stored'],
                    'pages_failed': result['pages_failed'],
                    'elapsed_time': result['elapsed_time'],
                    'collection': result['collection'],
                    'start_url': result['start_url']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Crawl failed'})

    except Exception as e:
        print(f"[Web Interface] Crawl error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/index_text', methods=['POST'])
def index_text():
    """Index custom text content directly into Optus"""
    title = request.json.get('title', '').strip()
    content = request.json.get('content', '').strip()
    collection_name = request.json.get('collection', 'custom_notes')
    tags = request.json.get('tags', [])

    if not title or not content:
        return jsonify({'success': False, 'message': 'Title and content are required'})

    try:
        print(f"\n[Text Index] Indexing text: {title}")
        print(f"[Text Index] Collection: {collection_name}")
        print(f"[Text Index] Content length: {len(content)} characters")
        print(f"[Text Index] Tags: {tags}")

        # Create metadata
        metadata = {
            'tags': tags,
            'word_count': len(content.split()),
            'char_count': len(content),
            'indexed_at': datetime.now().isoformat()
        }

        # Generate unique ID based on title and timestamp
        import time
        text_id = hashlib.md5(f"{title}_{time.time()}".encode()).hexdigest()[:16]

        # Store in Optus
        success, message = store_document(
            collection_name=collection_name,
            source_type='text',
            source_id=text_id,
            title=title,
            content=content,
            metadata=metadata,
            url=f"indexed://{collection_name}/{text_id}"
        )

        if success:
            response_message = (
                f"Successfully indexed '{title}' in collection '{collection_name}'. "
                f"Content: {len(content)} chars, {len(content.split())} words. "
                f"Tags: {', '.join(tags) if tags else 'None'}"
            )
            print(f"[Text Index] ✓ {response_message}")
            return jsonify({
                'success': True,
                'message': response_message,
                'stats': {
                    'title': title,
                    'collection': collection_name,
                    'word_count': len(content.split()),
                    'char_count': len(content),
                    'tags': tags,
                    'text_id': text_id
                }
            })
        else:
            print(f"[Text Index] ✗ Failed: {message}")
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        print(f"[Text Index] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/ask_ollama', methods=['POST'])
def ask_ollama_route():
    """Ask Ollama with RAG (Retrieval Augmented Generation)"""
    question = request.json.get('question', '')
    collection_name = request.json.get('collection', 'jira_tickets')
    model_name = request.json.get('model', 'llama3.2')
    top_k = request.json.get('top_k', 3)

    if not question:
        return jsonify({'success': False, 'message': 'No question provided'})

    try:
        # Initialize Ollama RAG
        rag = OllamaRAG(model_name=model_name)

        # Check if Ollama is running
        is_running, available_models = rag.check_ollama_status()
        if not is_running:
            return jsonify({
                'success': False,
                'message': 'Ollama is not running. Please start Ollama: ollama serve'
            })

        # Query with context (supports "all" for all collections)
        result = rag.query_with_context(question, collection_name, top_k)

        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'model': result['model']
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/claude_code/store', methods=['POST'])
def claude_code_store():
    """
    Unified API for Claude Code to store various types of data in Optus.
    Supports flexible formats and automatic processing.

    Request format:
    {
        "data_type": "issue" | "code_snippet" | "documentation" | "conversation" | "analysis" | "custom",
        "format": "json" | "markdown" | "text" | "structured",
        "title": "Title of the item",
        "content": "Main content (can be string or dict)",
        "metadata": {}, # Optional additional metadata
        "collection": "collection_name", # Optional, defaults based on data_type
        "tags": ["tag1", "tag2"], # Optional tags
        "source": "claude_code", # Optional source identifier
        "url": "" # Optional reference URL
    }
    """
    try:
        # Extract request data
        data_type = request.json.get('data_type', 'custom')
        format_type = request.json.get('format', 'text')
        title = request.json.get('title', 'Untitled')
        content = request.json.get('content', '')
        metadata_input = request.json.get('metadata', {})
        collection_name = request.json.get('collection', None)
        tags = request.json.get('tags', [])
        source = request.json.get('source', 'claude_code')
        url = request.json.get('url', '')

        print(f"[Claude Code API] Received request: type={data_type}, format={format_type}, title={title}")

        # Auto-select collection based on data_type if not specified
        if not collection_name:
            collection_map = {
                'issue': 'issues',
                'bug': 'issues',
                'feature': 'issues',
                'code_snippet': 'code_snippets',
                'documentation': 'documentation',
                'conversation': 'conversations',
                'analysis': 'analysis',
                'custom': 'claude_code_data'
            }
            collection_name = collection_map.get(data_type, 'claude_code_data')

        # Process content based on format
        if format_type == 'json' and isinstance(content, dict):
            # Convert dict to formatted string
            processed_content = json.dumps(content, indent=2)
        elif format_type == 'structured' and isinstance(content, dict):
            # Convert structured data to readable format
            parts = []
            for key, value in content.items():
                if isinstance(value, (list, dict)):
                    parts.append(f"{key}: {json.dumps(value, indent=2)}")
                else:
                    parts.append(f"{key}: {value}")
            processed_content = '\n\n'.join(parts)
        elif format_type == 'markdown':
            # Keep markdown as-is
            processed_content = str(content)
        else:
            # Plain text
            processed_content = str(content)

        # Truncate if too long
        if len(processed_content) > 9900:
            processed_content = processed_content[:9900] + "\n\n[Content truncated...]"

        # Build comprehensive metadata
        metadata = {
            'data_type': data_type,
            'format': format_type,
            'source': source,
            'tags': tags,
            'stored_at': datetime.now().isoformat(),
            'content_length': len(processed_content),
            'original_format': format_type
        }

        # Merge with user-provided metadata
        metadata.update(metadata_input)

        # Generate unique ID
        import time
        item_id = hashlib.md5(f"{title}_{data_type}_{time.time()}".encode()).hexdigest()[:16]

        # Store in Optus
        success, message = store_document(
            collection_name=collection_name,
            source_type=data_type,
            source_id=item_id,
            title=title,
            content=processed_content,
            metadata=metadata,
            url=url or f"claude_code://{collection_name}/{item_id}"
        )

        if success:
            response = {
                'success': True,
                'message': f"Successfully stored {data_type} in collection '{collection_name}'",
                'item_id': item_id,
                'collection': collection_name,
                'stats': {
                    'title': title,
                    'data_type': data_type,
                    'format': format_type,
                    'content_length': len(processed_content),
                    'tags': tags
                }
            }
            print(f"[Claude Code API] ✓ Stored {data_type}: {title}")
            return jsonify(response)
        else:
            print(f"[Claude Code API] ✗ Failed to store: {message}")
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        print(f"[Claude Code API] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/claude_code/store_bulk', methods=['POST'])
def claude_code_store_bulk():
    """
    Store multiple items in a single request.

    Request format:
    {
        "items": [
            {
                "data_type": "issue",
                "title": "Title 1",
                "content": "Content 1",
                ...
            },
            {
                "data_type": "code_snippet",
                "title": "Title 2",
                "content": "Content 2",
                ...
            }
        ],
        "default_collection": "optional_default_collection",
        "default_tags": ["tag1", "tag2"]
    }
    """
    try:
        items = request.json.get('items', [])
        default_collection = request.json.get('default_collection', None)
        default_tags = request.json.get('default_tags', [])

        if not items:
            return jsonify({'success': False, 'message': 'No items provided'})

        print(f"[Claude Code API] Bulk store request: {len(items)} items")

        results = []
        success_count = 0
        failed_count = 0

        for idx, item in enumerate(items, 1):
            try:
                # Merge defaults
                if default_collection and not item.get('collection'):
                    item['collection'] = default_collection
                if default_tags:
                    item['tags'] = list(set(item.get('tags', []) + default_tags))

                # Store item
                data_type = item.get('data_type', 'custom')
                title = item.get('title', f'Item {idx}')
                content = item.get('content', '')
                metadata_input = item.get('metadata', {})
                collection_name = item.get('collection', 'claude_code_data')
                tags = item.get('tags', [])
                format_type = item.get('format', 'text')

                # Process content
                if isinstance(content, dict):
                    processed_content = json.dumps(content, indent=2)
                else:
                    processed_content = str(content)

                # Truncate if needed
                if len(processed_content) > 9900:
                    processed_content = processed_content[:9900] + "\n\n[Content truncated...]"

                # Build metadata
                metadata = {
                    'data_type': data_type,
                    'format': format_type,
                    'source': 'claude_code_bulk',
                    'tags': tags,
                    'stored_at': datetime.now().isoformat(),
                    'bulk_index': idx
                }
                metadata.update(metadata_input)

                # Generate ID
                import time
                item_id = hashlib.md5(f"{title}_{data_type}_{time.time()}_{idx}".encode()).hexdigest()[:16]

                # Store
                success, message = store_document(
                    collection_name=collection_name,
                    source_type=data_type,
                    source_id=item_id,
                    title=title,
                    content=processed_content,
                    metadata=metadata,
                    url=item.get('url', f"claude_code://{collection_name}/{item_id}")
                )

                if success:
                    success_count += 1
                    results.append({
                        'index': idx,
                        'success': True,
                        'item_id': item_id,
                        'title': title
                    })
                    print(f"[Claude Code API] ✓ [{idx}/{len(items)}] Stored: {title}")
                else:
                    failed_count += 1
                    results.append({
                        'index': idx,
                        'success': False,
                        'title': title,
                        'error': message
                    })
                    print(f"[Claude Code API] ✗ [{idx}/{len(items)}] Failed: {title}")

            except Exception as e:
                failed_count += 1
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e)
                })
                print(f"[Claude Code API] ✗ [{idx}/{len(items)}] Error: {e}")

        return jsonify({
            'success': True,
            'message': f"Bulk store complete: {success_count} succeeded, {failed_count} failed",
            'stats': {
                'total': len(items),
                'succeeded': success_count,
                'failed': failed_count
            },
            'results': results
        })

    except Exception as e:
        print(f"[Claude Code API] Bulk store error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/claude_code/query', methods=['POST'])
def claude_code_query():
    """
    Query stored data from Claude Code.

    Request format:
    {
        "query": "search query",
        "collection": "collection_name" or "all",
        "data_type": "optional filter by data_type",
        "tags": ["optional", "tag", "filters"],
        "top_k": 5
    }
    """
    try:
        query = request.json.get('query', '')
        collection_name = request.json.get('collection', 'all')
        data_type_filter = request.json.get('data_type', None)
        tag_filters = request.json.get('tags', [])
        top_k = request.json.get('top_k', 5)

        if not query:
            return jsonify({'success': False, 'message': 'No query provided'})

        print(f"[Claude Code API] Query: {query} in collection: {collection_name}")

        # Perform semantic search
        model = load_model()
        query_embedding = model.encode([query])[0].tolist()

        # Determine collections to search
        if collection_name == 'all':
            collections = get_all_collections()
        else:
            collections = [collection_name]

        all_results = []

        for coll in collections:
            try:
                collection = Collection(coll)
                collection.load()

                # Search
                search_results = collection.search(
                    data=[query_embedding],
                    anns_field="embedding",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                    output_fields=["source_type", "source_id", "title", "content", "metadata", "url"]
                )

                for hits in search_results:
                    for hit in hits:
                        entity = hit.entity
                        metadata = json.loads(entity.get('metadata', '{}'))

                        # Apply filters
                        if data_type_filter and metadata.get('data_type') != data_type_filter:
                            continue

                        if tag_filters:
                            item_tags = metadata.get('tags', [])
                            if not any(tag in item_tags for tag in tag_filters):
                                continue

                        all_results.append({
                            'title': entity.get('title'),
                            'content': entity.get('content', '')[:500],  # Preview
                            'source_type': entity.get('source_type'),
                            'source_id': entity.get('source_id'),
                            'url': entity.get('url'),
                            'metadata': metadata,
                            'similarity_score': round(hit.score, 4),
                            'collection': coll
                        })

                collection.release()

            except Exception as e:
                print(f"[Claude Code API] Error searching {coll}: {e}")

        # Sort by similarity and limit
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        all_results = all_results[:top_k]

        return jsonify({
            'success': True,
            'query': query,
            'results': all_results,
            'count': len(all_results)
        })

    except Exception as e:
        print(f"[Claude Code API] Query error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/action_logs', methods=['GET'])
def get_action_logs():
    """Get action logs with optional filtering"""
    try:
        collection = ensure_action_logs_collection()
        if collection is None:
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        collection.load()

        # Get query parameters
        action_type = request.args.get('action_type')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Query all logs
        query_expr = "id > 0"

        results = collection.query(
            expr=query_expr,
            output_fields=["timestamp", "action_type", "endpoint", "parameters", "status",
                          "duration_ms", "result_summary", "error_message", "source", "metadata"],
            limit=limit
        )

        # Filter in Python (Optus has limited string filtering)
        filtered_results = []
        for result in results:
            # Apply filters
            if action_type and result.get('action_type') != action_type:
                continue
            if status and result.get('status') != status:
                continue
            if start_date and result.get('timestamp') < start_date:
                continue
            if end_date and result.get('timestamp') > end_date:
                continue

            # Parse JSON fields
            try:
                result['parameters'] = json.loads(result.get('parameters', '{}'))
                result['metadata'] = json.loads(result.get('metadata', '{}'))
            except:
                pass

            filtered_results.append(result)

        # Sort by timestamp descending (newest first)
        filtered_results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        collection.release()

        return jsonify({
            'success': True,
            'logs': filtered_results[:limit],
            'count': len(filtered_results)
        })

    except Exception as e:
        print(f"[Action Logs] Error retrieving logs: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/action_logs/stats', methods=['GET'])
def get_action_logs_stats():
    """Get statistics about action logs"""
    try:
        collection = ensure_action_logs_collection()
        if collection is None:
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        collection.load()

        # Query all logs
        results = collection.query(
            expr="id > 0",
            output_fields=["timestamp", "action_type", "endpoint", "status", "duration_ms"],
            limit=10000
        )

        # Calculate statistics
        total_actions = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = sum(1 for r in results if r.get('status') == 'failed')

        # Count by action type
        action_counts = {}
        for r in results:
            action_type = r.get('action_type', 'unknown')
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        # Count by endpoint
        endpoint_counts = {}
        for r in results:
            endpoint = r.get('endpoint', 'unknown')
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

        # Average duration by action type
        duration_by_type = {}
        for r in results:
            action_type = r.get('action_type', 'unknown')
            duration = r.get('duration_ms', 0)
            if action_type not in duration_by_type:
                duration_by_type[action_type] = []
            duration_by_type[action_type].append(duration)

        avg_duration_by_type = {
            k: round(sum(v) / len(v), 2) if v else 0
            for k, v in duration_by_type.items()
        }

        # Recent activity (last hour)
        from datetime import datetime, timedelta
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        recent = sum(1 for r in results if r.get('timestamp', '') > one_hour_ago)

        collection.release()

        return jsonify({
            'success': True,
            'stats': {
                'total_actions': total_actions,
                'successful': successful,
                'failed': failed,
                'success_rate': round((successful / total_actions * 100), 2) if total_actions > 0 else 0,
                'recent_activity_1h': recent,
                'action_counts': action_counts,
                'endpoint_counts': endpoint_counts,
                'avg_duration_ms': avg_duration_by_type,
                'oldest_log': min([r.get('timestamp', '') for r in results]) if results else None,
                'newest_log': max([r.get('timestamp', '') for r in results]) if results else None
            }
        })

    except Exception as e:
        print(f"[Action Logs] Error getting stats: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/ollama_status', methods=['GET'])
def ollama_status():
    """Check Ollama status and available models"""
    try:
        rag = OllamaRAG()
        is_running, models = rag.check_ollama_status()

        return jsonify({
            'success': True,
            'running': is_running,
            'models': models
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'running': False,
            'models': [],
            'message': str(e)
        })


@app.route('/analyze_personas', methods=['POST'])
def analyze_personas():
    """Trigger persona analysis for all users in PRs"""
    collection_name = request.json.get('collection', 'github_prs')

    try:
        print(f"[Persona Analysis] Starting analysis for collection: {collection_name}")
        analyzer = GitHubPersonaAnalyzer(collection_name=collection_name)
        results = analyzer.build_all_personas()

        return jsonify({
            'success': results['success'],
            'message': results['message'],
            'personas': results.get('personas', [])
        })

    except Exception as e:
        print(f"[Persona Analysis] Error: {e}")
        return jsonify({'success': False, 'message': f'Error analyzing personas: {str(e)}'})


@app.route('/get_persona/<username>', methods=['GET'])
def get_persona(username):
    """Get persona data for specific user"""
    try:
        analyzer = GitHubPersonaAnalyzer()
        persona = analyzer.get_persona(username)

        if persona:
            return jsonify({'success': True, 'persona': persona})
        else:
            return jsonify({'success': False, 'message': f'Persona not found for user: {username}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/get_all_personas', methods=['GET'])
def get_all_personas():
    """Get all personas with summary stats"""
    try:
        analyzer = GitHubPersonaAnalyzer()
        personas = analyzer.get_all_personas()

        return jsonify({
            'success': True,
            'personas': personas,
            'count': len(personas)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/merge_duplicate_personas', methods=['POST'])
def merge_duplicate_personas():
    """Merge duplicate persona records by username"""
    try:
        from collections import defaultdict

        if not connect_milvus():
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        collection_name = 'github_personas'

        if not utility.has_collection(collection_name):
            return jsonify({'success': False, 'message': f'Collection {collection_name} does not exist'})

        collection = Collection(name=collection_name)
        collection.load()

        # Get all personas
        results = collection.query(
            expr="id >= 0",
            output_fields=["id", "username", "display_name", "role", "statistics", "patterns", "relationships", "persona_description", "last_updated"]
        )

        if not results:
            return jsonify({'success': False, 'message': 'No personas found'})

        # Group by username to find duplicates
        username_map = defaultdict(list)
        for persona in results:
            username_map[persona['username']].append(persona)

        duplicates = {username: records for username, records in username_map.items() if len(records) > 1}

        if not duplicates:
            return jsonify({
                'success': True,
                'message': 'No duplicates found',
                'total_personas': len(results),
                'unique_usernames': len(username_map),
                'duplicates_merged': 0
            })

        # Merge duplicates
        merged_count = 0
        ids_to_delete = []

        for username, records in duplicates.items():
            # Collect IDs to delete
            for record in records:
                ids_to_delete.append(record['id'])

            # Get latest metadata
            latest_record = max(records, key=lambda r: r['last_updated'])
            display_name = latest_record['display_name']

            # Merge statistics
            merged_stats = {
                "prs_authored": 0,
                "prs_reviewed": 0,
                "approvals_given": 0,
                "changes_requested": 0,
                "comments_only": 0,
                "prs_merged": 0,
                "prs_merged_own": 0,
                "prs_merged_others": 0,
                "total_comments": 0
            }

            for record in records:
                stats = json.loads(record['statistics']) if isinstance(record['statistics'], str) else record['statistics']
                for key in merged_stats.keys():
                    merged_stats[key] += stats.get(key, 0)

            # Calculate rates
            if merged_stats["prs_reviewed"] > 0:
                merged_stats["approval_rate"] = round(merged_stats["approvals_given"] / merged_stats["prs_reviewed"], 2)
                merged_stats["avg_comments_per_review"] = round(merged_stats["total_comments"] / merged_stats["prs_reviewed"], 1)
                merged_stats["merge_rate"] = round(merged_stats["prs_merged"] / merged_stats["prs_reviewed"], 2)
            else:
                merged_stats["approval_rate"] = 0
                merged_stats["avg_comments_per_review"] = 0
                merged_stats["merge_rate"] = 0

            if merged_stats["prs_merged"] > 0:
                merged_stats["self_merge_rate"] = round(merged_stats["prs_merged_own"] / merged_stats["prs_merged"], 2)
            else:
                merged_stats["self_merge_rate"] = 0.0

            # Average time to merge
            total_merge_time = sum(
                (json.loads(r['statistics']) if isinstance(r['statistics'], str) else r['statistics']).get("avg_time_to_merge_hours", 0)
                for r in records
            )
            merged_stats["avg_time_to_merge_hours"] = round(total_merge_time / len(records), 1)

            # Determine role
            if merged_stats["prs_merged"] >= 10 or (merged_stats["prs_reviewed"] >= 20 and merged_stats["prs_authored"] >= 10):
                role = "maintainer"
            elif merged_stats["prs_reviewed"] >= 10 or merged_stats["prs_authored"] >= 5:
                role = "contributor"
            elif merged_stats["prs_reviewed"] > 0 or merged_stats["prs_authored"] > 0:
                role = "reviewer"
            else:
                role = "participant"

            # Get patterns and relationships from latest record
            patterns = latest_record.get('patterns', '{}')
            if isinstance(patterns, str):
                patterns = json.loads(patterns) if patterns else {}

            relationships = latest_record.get('relationships', '{}')
            if isinstance(relationships, str):
                relationships = json.loads(relationships) if relationships else {}

            # Get persona description from latest record
            persona_description = latest_record.get('persona_description', '')

            # Insert merged persona
            merged_data = [
                [username],
                [display_name],
                [role],
                [json.dumps(merged_stats)],
                [json.dumps(patterns)],
                [json.dumps(relationships)],
                [persona_description],
                [datetime.now().isoformat()],
                [[0.0] * 384]  # Dummy embedding (384 dimensions)
            ]

            collection.insert(merged_data)
            merged_count += 1

        # Delete old duplicate records
        for record_id in ids_to_delete:
            collection.delete(f"id == {record_id}")

        collection.flush()
        collection.release()

        # Verify results
        collection.load()
        final_results = collection.query(
            expr="id >= 0",
            output_fields=["username"]
        )
        collection.release()

        final_usernames = [r['username'] for r in final_results]
        unique_final = len(set(final_usernames))

        return jsonify({
            'success': True,
            'message': f'Successfully merged {merged_count} duplicate personas',
            'duplicates_found': len(duplicates),
            'records_deleted': len(ids_to_delete),
            'personas_merged': merged_count,
            'total_personas_before': len(results),
            'total_personas_after': len(final_results),
            'unique_usernames': unique_final,
            'merged_usernames': list(duplicates.keys())
        })

    except Exception as e:
        print(f"[Merge Personas] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/export_persona_pdf/<username>', methods=['GET'])
def export_persona_pdf(username):
    """Export persona analysis as PDF report"""
    try:
        # Get persona data
        analyzer = GitHubPersonaAnalyzer()
        persona = analyzer.get_persona(username)

        if not persona:
            return jsonify({'success': False, 'message': f'Persona not found for user: {username}'})

        # Generate PDF
        generator = PersonaReportGenerator()
        pdf_buffer = generator.generate_persona_report(persona)

        # Return PDF file
        from flask import send_file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'persona_report_{username}_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except Exception as e:
        print(f"[PDF Export] Error: {e}")
        return jsonify({'success': False, 'message': f'Error generating PDF: {str(e)}'})


@app.route('/export_all_personas_pdf', methods=['GET'])
def export_all_personas_pdf():
    """Export summary report for all personas as PDF"""
    try:
        # Get all personas
        analyzer = GitHubPersonaAnalyzer()
        personas = analyzer.get_all_personas()

        if not personas:
            return jsonify({'success': False, 'message': 'No personas found'})

        # Generate PDF
        generator = PersonaReportGenerator()
        pdf_buffer = generator.generate_summary_report(personas)

        # Return PDF file
        from flask import send_file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'personas_summary_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except Exception as e:
        print(f"[PDF Export] Error: {e}")
        return jsonify({'success': False, 'message': f'Error generating PDF: {str(e)}'})


@app.route('/get_pr_actions/<owner>/<repo>/<pr_number>', methods=['GET'])
def get_pr_actions(owner, repo, pr_number):
    """Get detailed 'who did what' for specific PR"""
    try:
        if not connect_milvus():
            return jsonify({'success': False, 'message': 'Failed to connect to Optus'})

        collection_name = request.args.get('collection', 'github_prs')

        if not utility.has_collection(collection_name):
            return jsonify({'success': False, 'message': f'Collection {collection_name} does not exist'})

        collection = Collection(name=collection_name)
        collection.load()

        # Query for this specific PR
        results = collection.query(
            expr=f"source_id == 'PR#{pr_number}'",
            output_fields=["title", "content", "metadata", "url"]
        )

        collection.release()

        if not results:
            return jsonify({'success': False, 'message': f'PR #{pr_number} not found'})

        pr = results[0]
        metadata = json.loads(pr.get('metadata', '{}'))
        content = pr.get('content', '')

        # Extract actions timeline
        actions = []

        # PR creation
        actions.append({
            'action': 'created',
            'actor': metadata.get('author', 'unknown'),
            'timestamp': metadata.get('created_at', ''),
            'details': f"Created PR: {pr.get('title', '')}"
        })

        # Extract reviews from content
        import re
        review_pattern = r'\d+\. (APPROVED|CHANGES_REQUESTED|COMMENTED) by (\w+): (.+?)(?=\n\d+\.|---|\Z)'
        for match in re.finditer(review_pattern, content, re.DOTALL):
            state = match.group(1)
            reviewer = match.group(2)
            actions.append({
                'action': state.lower(),
                'actor': reviewer,
                'timestamp': '',  # Would need to extract from metadata
                'details': f"Review: {state}"
            })

        # PR merged
        if metadata.get('merged'):
            actions.append({
                'action': 'merged',
                'actor': metadata.get('merged_by', 'unknown'),
                'timestamp': metadata.get('merged_at', ''),
                'details': 'Merged PR'
            })

        # Extract approvers and change requesters
        approvers = [a['actor'] for a in actions if a['action'] == 'approved']
        change_requesters = [a['actor'] for a in actions if a['action'] == 'changes_requested']

        return jsonify({
            'success': True,
            'pr': {
                'number': pr_number,
                'title': pr.get('title', ''),
                'url': pr.get('url', ''),
                'author': metadata.get('author', 'unknown'),
                'merged': metadata.get('merged', False),
                'merged_by': metadata.get('merged_by'),
                'state': metadata.get('state', 'unknown')
            },
            'actions_timeline': actions,
            'summary': {
                'author': metadata.get('author', 'unknown'),
                'approvers': list(set(approvers)),
                'change_requesters': list(set(change_requesters)),
                'merger': metadata.get('merged_by')
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/get_analyzed_prs', methods=['GET'])
def get_analyzed_prs():
    """Get list of analyzed PRs with status"""
    try:
        repository = request.args.get('repository', None)
        tracked_prs = get_tracked_prs(repository)

        # Organize by status
        successful = [pr for pr in tracked_prs if pr['status'] == 'success']
        failed = [pr for pr in tracked_prs if pr['status'] == 'failed']

        return jsonify({
            'success': True,
            'tracked_prs': tracked_prs,
            'summary': {
                'total': len(tracked_prs),
                'successful': len(successful),
                'failed': len(failed)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/get_approval_stats', methods=['GET'])
def get_approval_stats():
    """Get approval and merge statistics for all users"""
    try:
        analyzer = GitHubPersonaAnalyzer()
        personas = analyzer.get_all_personas()

        if not personas:
            return jsonify({'success': False, 'message': 'No personas found'})

        # Extract statistics
        approval_stats = []
        merge_stats = []

        for persona in personas:
            stats = persona['statistics']
            approval_stats.append({
                'username': persona['username'],
                'approval_rate': stats.get('approval_rate', 0),
                'approvals_given': stats.get('approvals_given', 0),
                'prs_reviewed': stats.get('prs_reviewed', 0)
            })

            merge_stats.append({
                'username': persona['username'],
                'prs_merged': stats.get('prs_merged', 0),
                'merge_rate': stats.get('merge_rate', 0),
                'self_merge_rate': stats.get('self_merge_rate', 0)
            })

        # Sort by frequency
        approval_stats.sort(key=lambda x: x['approvals_given'], reverse=True)
        merge_stats.sort(key=lambda x: x['prs_merged'], reverse=True)

        return jsonify({
            'success': True,
            'approval_stats': approval_stats[:20],  # Top 20
            'merge_stats': merge_stats[:20],  # Top 20
            'total_contributors': len(personas)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/ask_claude', methods=['POST'])
def ask_claude_route():
    """Ask Claude with RAG + Website Scraping + All Collections + Response Time Tracking"""
    import time

    start_time = time.time()  # Start timing

    question = request.json.get('question', '')
    collection_name = request.json.get('collection', 'all')
    website_url = request.json.get('website_url', '')
    top_k = request.json.get('top_k', 5)

    if not question:
        return jsonify({'success': False, 'message': 'No question provided'})

    try:
        # Initialize Claude RAG
        rag = ClaudeRAG()

        # Query with context (supports website scraping and all collections)
        result = rag.query_with_context(
            question=question,
            collection_name=collection_name,
            website_url=website_url if website_url else None,
            top_k=top_k
        )

        # Calculate response time
        response_time = time.time() - start_time

        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'model': result['model'],
            'website_scraped': result.get('website_scraped'),
            'response_time_seconds': round(response_time, 3),  # Add response time
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        response_time = time.time() - start_time
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'response_time_seconds': round(response_time, 3)
        })


@app.route('/token_usage/stats', methods=['GET'])
def get_token_stats():
    """Get token usage statistics"""
    try:
        from token_tracker import get_tracker
        tracker = get_tracker()

        period = request.args.get('period', 'all')  # today, week, month, all
        limit = int(request.args.get('limit', 100))

        stats = tracker.get_usage_stats(period=period, limit=limit)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/token_usage/cost_breakdown', methods=['GET'])
def get_cost_breakdown():
    """Get daily cost breakdown"""
    try:
        from token_tracker import get_tracker
        tracker = get_tracker()

        period = request.args.get('period', 'month')  # week, month
        breakdown = tracker.get_cost_breakdown(period=period)

        return jsonify({
            'success': True,
            'breakdown': breakdown
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/token_usage/export', methods=['GET'])
def export_token_usage():
    """Export token usage to CSV"""
    try:
        from token_tracker import get_tracker
        tracker = get_tracker()

        period = request.args.get('period', 'all')
        output_path = tracker.export_to_csv(period=period)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'token_usage_{period}.csv',
            mimetype='text/csv'
        )

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API Documentation - Simple HTML page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Optus AI - API Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            h1 { color: #4338ca; }
            .endpoint { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .method { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin-right: 10px; }
            .post { background: #3b82f6; color: white; }
            .get { background: #10b981; color: white; }
            code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
            pre { background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 8px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🤖 Optus AI - API Documentation</h1>
        <p>REST API for AI-powered data management and querying</p>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /ask_claude</h2>
            <p>Query Claude AI with RAG context</p>
            <pre>
{
  "question": "What issues are in development?",
  "collection": "all",
  "top_k": 3,
  "website_url": "https://example.com",
  "context": []
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /ask_ollama</h2>
            <p>Query Ollama AI with RAG context</p>
            <pre>
{
  "question": "Summarize feature flags work",
  "collection": "all",
  "model": "deepseek-r1:8b",
  "top_k": 3
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /search</h2>
            <p>Semantic search across collections</p>
            <pre>
{
  "query": "docker firewall",
  "collection": "jira_tickets",
  "top_k": 5
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /index_text</h2>
            <p>Index custom text into Milvus</p>
            <pre>
{
  "title": "Document Title",
  "content": "Document content here...",
  "source_type": "custom",
  "collection": "documents"
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /upload</h2>
            <p>Upload and index files (PDF, TXT, DOCX, MD)</p>
            <p>Form data: <code>file</code> (required), <code>collection</code> (optional)</p>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /fetch_jira</h2>
            <p>Fetch and index Jira tickets</p>
            <pre>
{
  "jira_input": "PROJ-123, PROJ-456",
  "collection": "jira_tickets"
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /fetch_github</h2>
            <p>Fetch and index GitHub PRs</p>
            <pre>
{
  "repo": "owner/repository",
  "state": "all",
  "max_results": 50
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method post">POST</span> /crawl_website</h2>
            <p>Crawl and index website content</p>
            <pre>
{
  "url": "https://example.com",
  "max_pages": 10
}
            </pre>
        </div>

        <div class="endpoint">
            <h2><span class="method get">GET</span> /ollama_status</h2>
            <p>Check Ollama server status and available models</p>
        </div>

        <p style="text-align: center; color: #6b7280; margin-top: 40px;">
            Optus AI Platform | Port 5001
        </p>
    </body>
    </html>
    """
    return html


@app.route('/save_image', methods=['POST'])
def save_image():
    """Save image with base64 encoding to Milvus"""
    try:
        data = request.json
        image_data = data.get('image_data')  # base64 encoded image
        image_name = data.get('name', f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        description = data.get('description', '')

        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})

        # Load image vectorizer if not loaded
        if image_vectorizer is None:
            load_model()

        if image_vectorizer is None:
            return jsonify({'success': False, 'message': 'Image vectorizer not available'})

        # Decode base64 image
        import base64
        import io
        from PIL import Image

        # Remove data:image prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Save temporarily to extract vector
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_image.png')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(temp_path)

        # Extract vector
        vector = image_vectorizer.extract_vector(temp_path)

        # Create content with base64 data embedded
        content = f"Image: {image_name}\nDescription: {description}\nBase64 Data: {image_data[:100]}..."
        file_hash = hashlib.md5(image_name.encode()).hexdigest()

        metadata = {
            'filename': image_name,
            'size': len(image_bytes),
            'upload_time': datetime.now().isoformat(),
            'type': 'image',
            'vector_model': 'CLIP',
            'description': description,
            'base64_data': image_data,  # Store full base64 data
            'width': image.width,
            'height': image.height
        }

        # Store image with vector in documents collection
        success, message = store_document_with_vector(
            collection_name='documents',
            source_type='screenshot',
            source_id=file_hash,
            title=image_name,
            content=content,
            vector=vector,
            metadata=metadata,
            url=f'data:image/png;base64,{image_data[:50]}...'
        )

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({
            'success': success,
            'message': message,
            'image_id': file_hash,
            'vector_dim': len(vector)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving image: {str(e)}'})


@app.route('/retrieve_image', methods=['POST'])
def retrieve_image():
    """Retrieve image by description or similarity search"""
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 3)

        if not query:
            return jsonify({'success': False, 'message': 'No query provided'})

        # Search in documents collection for images
        collection = Collection('documents')
        collection.load()

        # Generate query vector
        if embedding_model is None:
            load_model()

        query_vector = embedding_model.encode(query).tolist()

        # Search
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr='source_type == "screenshot"',
            output_fields=['title', 'content', 'metadata', 'source_type', 'created_at']
        )

        images = []
        for hits in results:
            for hit in hits:
                entity = hit.entity
                metadata = json.loads(entity.get('metadata')) if isinstance(entity.get('metadata'), str) else entity.get('metadata')

                # Extract base64 data from metadata
                base64_data = metadata.get('base64_data', '')

                images.append({
                    'id': hit.id,
                    'title': entity.get('title'),
                    'description': metadata.get('description', ''),
                    'image_data': f'data:image/png;base64,{base64_data}',
                    'score': hit.distance,
                    'width': metadata.get('width'),
                    'height': metadata.get('height'),
                    'upload_time': metadata.get('upload_time'),
                    'preview': f'data:image/png;base64,{base64_data[:100]}...'
                })

        return jsonify({
            'success': True,
            'images': images,
            'count': len(images)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error retrieving images: {str(e)}'})


@app.route('/codebase_audit/history', methods=['GET'])
def get_codebase_audit_history():
    """Get analysis history from audit logs"""
    try:
        analyzer = CodebaseAnalyzer()
        repo_name = request.args.get('repo_name')
        limit = int(request.args.get('limit', 20))

        history = analyzer.get_analysis_history(repo_name=repo_name, limit=limit)

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/codebase_audit/statistics', methods=['GET'])
def get_codebase_audit_statistics():
    """Get overall statistics from audit logs"""
    try:
        analyzer = CodebaseAnalyzer()
        stats = analyzer.get_analysis_statistics()

        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)

    # Start server
    print("="*70)
    print("MILVUS DATA MANAGEMENT WEB INTERFACE")
    print("="*70)
    print("\nStarting web server at http://localhost:5001")
    print("Make sure Optus is running!")
    print("\n" + "="*70)

    app.run(debug=True, host='0.0.0.0', port=5001)
