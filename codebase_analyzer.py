#!/usr/bin/env python3
"""
Codebase Analyzer - Extract maximum metadata for AI queries
Analyzes code repositories and stores rich context in Milvus
Includes Git integration for version tracking and latest code retrieval
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import hashlib
import requests
from multiprocessing import Pool, cpu_count, Manager
from functools import partial
import time


class CodebaseAnalyzer:
    def __init__(self, milvus_host="localhost", milvus_port="19530"):
        """Initialize codebase analyzer"""
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = None
        self.collection_name = "codebase_analysis"
        self.audit_collection_name = "codebase_analysis_audit"
        self._embedding_cache = {}  # Cache embeddings for duplicate content
        self._git_info_cache = {}  # Cache Git information

        # File extensions to analyze
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'header',
            '.hpp': 'header',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.rs': 'rust',
            '.scala': 'scala',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
        }

        # Files to ignore
        self.ignore_patterns = [
            '__pycache__', '.git', '.svn', 'node_modules', 'venv', 'env',
            '.idea', '.vscode', 'dist', 'build', 'target', '.DS_Store',
            '*.pyc', '*.pyo', '*.so', '*.dylib', '*.dll', '*.exe',
            '.pytest_cache', '.mypy_cache', '.tox', 'coverage',
        ]

    def load_embedding_model(self):
        """Load sentence transformer for embeddings"""
        if self.embedding_model is None:
            print("[Analyzer] Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model

    def connect_milvus(self):
        """Connect to Milvus"""
        try:
            connections.connect(alias="default", host=self.milvus_host, port=self.milvus_port)
            print("[Analyzer] ✓ Connected to Milvus")
            return True
        except Exception as e:
            print(f"[Analyzer] ❌ Failed to connect to Milvus: {e}")
            return False

    def create_collection(self):
        """Create Milvus collection with rich schema for code analysis"""
        if utility.has_collection(self.collection_name):
            print(f"[Analyzer] Collection '{self.collection_name}' already exists")
            return True

        print(f"[Analyzer] Creating collection '{self.collection_name}'...")

        # Define schema with maximum metadata
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="file_hash", dtype=DataType.VARCHAR, max_length=64),  # Unique file identifier
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),  # Full path
            FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=256),  # File name
            FieldSchema(name="file_extension", dtype=DataType.VARCHAR, max_length=16),  # .py, .js, etc.
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=32),  # python, javascript, etc.
            FieldSchema(name="chunk_index", dtype=DataType.INT64),  # Chunk number for large files
            FieldSchema(name="total_chunks", dtype=DataType.INT64),  # Total chunks for this file

            # Content fields
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8000),  # Code content
            FieldSchema(name="content_summary", dtype=DataType.VARCHAR, max_length=1000),  # Brief summary

            # Code structure metadata
            FieldSchema(name="imports", dtype=DataType.VARCHAR, max_length=2000),  # Imports/dependencies
            FieldSchema(name="classes", dtype=DataType.VARCHAR, max_length=2000),  # Class names
            FieldSchema(name="functions", dtype=DataType.VARCHAR, max_length=2000),  # Function names
            FieldSchema(name="variables", dtype=DataType.VARCHAR, max_length=2000),  # Global variables

            # Documentation
            FieldSchema(name="docstrings", dtype=DataType.VARCHAR, max_length=2000),  # Extracted docs
            FieldSchema(name="comments", dtype=DataType.VARCHAR, max_length=2000),  # Inline comments

            # Code metrics
            FieldSchema(name="lines_of_code", dtype=DataType.INT64),  # Total LOC
            FieldSchema(name="complexity_score", dtype=DataType.INT64),  # Cyclomatic complexity
            FieldSchema(name="has_tests", dtype=DataType.BOOL),  # Contains test code
            FieldSchema(name="has_main", dtype=DataType.BOOL),  # Has main/entry point

            # Context metadata
            FieldSchema(name="directory", dtype=DataType.VARCHAR, max_length=512),  # Parent directory
            FieldSchema(name="module_path", dtype=DataType.VARCHAR, max_length=512),  # Python module path
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1000),  # Custom tags (JSON array)

            # Relationships
            FieldSchema(name="dependencies", dtype=DataType.VARCHAR, max_length=2000),  # File dependencies
            FieldSchema(name="dependents", dtype=DataType.VARCHAR, max_length=2000),  # Files that depend on this

            # Timestamps
            FieldSchema(name="indexed_at", dtype=DataType.VARCHAR, max_length=64),  # When indexed
            FieldSchema(name="file_modified_at", dtype=DataType.VARCHAR, max_length=64),  # Last modified

            # Repository info
            FieldSchema(name="repo_name", dtype=DataType.VARCHAR, max_length=256),  # Repository name
            FieldSchema(name="repo_path", dtype=DataType.VARCHAR, max_length=512),  # Repo root path

            # Git version control info
            FieldSchema(name="git_commit_hash", dtype=DataType.VARCHAR, max_length=64),  # Latest commit hash
            FieldSchema(name="git_commit_message", dtype=DataType.VARCHAR, max_length=500),  # Commit message
            FieldSchema(name="git_commit_author", dtype=DataType.VARCHAR, max_length=128),  # Author name
            FieldSchema(name="git_commit_email", dtype=DataType.VARCHAR, max_length=128),  # Author email
            FieldSchema(name="git_commit_date", dtype=DataType.VARCHAR, max_length=64),  # Commit timestamp
            FieldSchema(name="git_branch", dtype=DataType.VARCHAR, max_length=128),  # Current branch
            FieldSchema(name="git_remote_url", dtype=DataType.VARCHAR, max_length=512),  # Remote origin URL
            FieldSchema(name="github_url", dtype=DataType.VARCHAR, max_length=512),  # GitHub file URL (optional)
            FieldSchema(name="file_commits_count", dtype=DataType.INT64),  # Total commits for this file
            FieldSchema(name="file_contributors", dtype=DataType.VARCHAR, max_length=1000),  # Contributors (JSON)

            # Privacy control
            FieldSchema(name="is_private", dtype=DataType.BOOL),  # Whether this entry is private
            FieldSchema(name="privacy_password_hash", dtype=DataType.VARCHAR, max_length=64),  # Password hash for private access

            # Vector embedding
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Codebase analysis with rich metadata for AI queries"
        )

        collection = Collection(name=self.collection_name, schema=schema)

        # Create index on vector field
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        print(f"[Analyzer] ✓ Collection created with {len(fields)} fields")
        return True

    def create_audit_collection(self):
        """Create Milvus collection for storing analysis audit logs"""
        if utility.has_collection(self.audit_collection_name):
            return True

        print(f"[Analyzer] Creating audit collection '{self.audit_collection_name}'...")

        # Define audit schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="audit_id", dtype=DataType.VARCHAR, max_length=64),  # Unique audit ID
            FieldSchema(name="analysis_timestamp", dtype=DataType.VARCHAR, max_length=64),  # When analysis started
            FieldSchema(name="completion_timestamp", dtype=DataType.VARCHAR, max_length=64),  # When analysis completed

            # Repository information
            FieldSchema(name="repo_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="repo_path", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="github_url", dtype=DataType.VARCHAR, max_length=512),

            # Analysis metrics
            FieldSchema(name="total_files_found", dtype=DataType.INT64),
            FieldSchema(name="files_analyzed", dtype=DataType.INT64),
            FieldSchema(name="files_skipped", dtype=DataType.INT64),
            FieldSchema(name="files_errored", dtype=DataType.INT64),
            FieldSchema(name="total_entries_created", dtype=DataType.INT64),
            FieldSchema(name="total_chunks_created", dtype=DataType.INT64),

            # Performance metrics
            FieldSchema(name="processing_time_seconds", dtype=DataType.DOUBLE),
            FieldSchema(name="files_per_second", dtype=DataType.DOUBLE),
            FieldSchema(name="scan_time_seconds", dtype=DataType.DOUBLE),
            FieldSchema(name="embedding_time_seconds", dtype=DataType.DOUBLE),
            FieldSchema(name="insertion_time_seconds", dtype=DataType.DOUBLE),

            # Configuration
            FieldSchema(name="num_workers", dtype=DataType.INT64),
            FieldSchema(name="pull_latest", dtype=DataType.BOOL),
            FieldSchema(name="is_private", dtype=DataType.BOOL),

            # Git information
            FieldSchema(name="git_branch", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="git_commit_hash", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="git_commit_author", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="git_remote_url", dtype=DataType.VARCHAR, max_length=512),

            # Languages detected
            FieldSchema(name="languages", dtype=DataType.VARCHAR, max_length=1000),  # JSON array

            # System information
            FieldSchema(name="cpu_count", dtype=DataType.INT64),
            FieldSchema(name="host_machine", dtype=DataType.VARCHAR, max_length=128),

            # Status
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=32),  # success, error, partial
            FieldSchema(name="error_message", dtype=DataType.VARCHAR, max_length=1000),

            # Vector for semantic search (summary of analysis)
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Audit logs for codebase analysis runs"
        )

        collection = Collection(name=self.audit_collection_name, schema=schema)

        # Create index on vector field
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        print(f"[Analyzer] ✓ Audit collection created")
        return True

    def store_audit_log(self, audit_data: Dict):
        """Store analysis audit log in Milvus"""
        try:
            self.create_audit_collection()
            collection = Collection(name=self.audit_collection_name)

            # Generate embedding for semantic search of audit logs
            model = self.load_embedding_model()
            audit_summary = f"""
Analysis of {audit_data['repo_name']} at {audit_data['analysis_timestamp']}
Files analyzed: {audit_data['files_analyzed']}
Time taken: {audit_data['processing_time_seconds']:.2f}s
Languages: {audit_data['languages']}
Branch: {audit_data.get('git_branch', 'N/A')}
Status: {audit_data['status']}
            """.strip()

            embedding = model.encode([audit_summary])[0].tolist()
            audit_data['embedding'] = embedding

            collection.insert([audit_data])
            collection.flush()
            print(f"[Audit] ✓ Audit log stored (ID: {audit_data['audit_id']})")
            return True
        except Exception as e:
            print(f"[Audit] ⚠️  Failed to store audit log: {e}")
            return False

    def get_analysis_history(self, repo_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Retrieve analysis history from audit logs"""
        try:
            if not utility.has_collection(self.audit_collection_name):
                return []

            collection = Collection(name=self.audit_collection_name)
            collection.load()

            # Build filter expression
            if repo_name:
                expr = f'repo_name == "{repo_name}"'
            else:
                expr = None

            # Query all fields
            results = collection.query(
                expr=expr if expr else "",
                output_fields=["*"],
                limit=limit
            )

            return results
        except Exception as e:
            print(f"[Audit] Error retrieving history: {e}")
            return []

    def get_analysis_statistics(self) -> Dict:
        """Get overall statistics from audit logs"""
        try:
            if not utility.has_collection(self.audit_collection_name):
                return {'error': 'No audit logs found'}

            collection = Collection(name=self.audit_collection_name)
            collection.load()

            # Get all audit logs
            results = collection.query(
                expr="",
                output_fields=["*"],
                limit=1000
            )

            if not results:
                return {'total_analyses': 0}

            # Calculate statistics
            total_analyses = len(results)
            total_files_analyzed = sum(r.get('files_analyzed', 0) for r in results)
            total_time = sum(r.get('processing_time_seconds', 0) for r in results)
            avg_time = total_time / total_analyses if total_analyses > 0 else 0

            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = sum(1 for r in results if r.get('status') == 'error')

            # Get unique repositories
            unique_repos = set(r.get('repo_name', '') for r in results if r.get('repo_name'))

            # Most analyzed repo
            repo_counts = {}
            for r in results:
                repo = r.get('repo_name', '')
                if repo:
                    repo_counts[repo] = repo_counts.get(repo, 0) + 1

            most_analyzed = max(repo_counts.items(), key=lambda x: x[1]) if repo_counts else ('N/A', 0)

            return {
                'total_analyses': total_analyses,
                'total_files_analyzed': total_files_analyzed,
                'total_time_seconds': total_time,
                'average_time_seconds': avg_time,
                'successful_analyses': successful,
                'failed_analyses': failed,
                'unique_repositories': len(unique_repos),
                'most_analyzed_repo': most_analyzed[0],
                'most_analyzed_count': most_analyzed[1],
                'repositories': list(unique_repos)
            }
        except Exception as e:
            return {'error': str(e)}

    def should_ignore(self, path: str) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str or path_str.endswith(pattern.replace('*', '')):
                return True
        return False

    def is_git_repo(self, directory: Path) -> bool:
        """Check if directory is a git repository"""
        return (directory / '.git').exists()

    def pull_latest_code(self, repo_path: Path) -> Dict:
        """Pull latest code from git remote"""
        if not self.is_git_repo(repo_path):
            return {'success': False, 'message': 'Not a git repository'}

        try:
            print(f"[Git] Pulling latest code from remote...")

            # Check if there's a remote
            result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                return {'success': False, 'message': 'No git remote configured'}

            # Fetch latest changes
            subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Get current branch
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()

            # Pull latest for current branch
            pull_result = subprocess.run(
                ['git', 'pull', 'origin', current_branch],
                cwd=repo_path,
                capture_output=True,
                text=True
            )

            if pull_result.returncode == 0:
                print(f"[Git] ✓ Successfully pulled latest code for branch '{current_branch}'")
                return {'success': True, 'branch': current_branch, 'message': pull_result.stdout}
            else:
                print(f"[Git] ⚠️  Pull completed with warnings: {pull_result.stderr}")
                return {'success': True, 'branch': current_branch, 'message': 'Already up to date'}

        except subprocess.CalledProcessError as e:
            print(f"[Git] ❌ Error pulling code: {e.stderr}")
            return {'success': False, 'message': f'Git pull failed: {e.stderr}'}
        except Exception as e:
            print(f"[Git] ❌ Error: {e}")
            return {'success': False, 'message': str(e)}

    def get_git_info(self, repo_path: Path) -> Dict:
        """Get general git repository information"""
        if not self.is_git_repo(repo_path):
            return {}

        try:
            info = {}

            # Current branch
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['branch'] = branch

            # Latest commit hash
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['commit_hash'] = commit_hash

            # Commit message
            commit_msg = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['commit_message'] = commit_msg[:500]

            # Author info
            author_name = subprocess.run(
                ['git', 'log', '-1', '--pretty=%an'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['commit_author'] = author_name

            author_email = subprocess.run(
                ['git', 'log', '-1', '--pretty=%ae'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['commit_email'] = author_email

            # Commit date
            commit_date = subprocess.run(
                ['git', 'log', '-1', '--pretty=%aI'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            info['commit_date'] = commit_date

            # Remote URL
            remote_url = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True
            ).stdout.strip()
            info['remote_url'] = remote_url

            print(f"[Git] ✓ Repository: {branch} @ {commit_hash[:8]}")
            print(f"[Git]   Latest commit: {commit_msg[:60]}...")
            print(f"[Git]   Author: {author_name} <{author_email}>")

            return info

        except Exception as e:
            print(f"[Git] Warning: Could not get git info: {e}")
            return {}

    def get_file_git_info(self, file_path: Path, repo_path: Path) -> Dict:
        """Get git information for a specific file"""
        if not self.is_git_repo(repo_path):
            return {}

        try:
            rel_path = file_path.relative_to(repo_path)
            info = {}

            # Latest commit for this file
            commit_hash = subprocess.run(
                ['git', 'log', '-1', '--pretty=%H', '--', str(rel_path)],
                cwd=repo_path,
                capture_output=True,
                text=True
            ).stdout.strip()
            info['commit_hash'] = commit_hash

            if commit_hash:
                # Commit message for this file's latest change
                commit_msg = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%B', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                info['commit_message'] = commit_msg[:500]

                # Author of latest change
                author_name = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%an', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                info['commit_author'] = author_name

                author_email = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%ae', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                info['commit_email'] = author_email

                # Commit date
                commit_date = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%aI', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                info['commit_date'] = commit_date

                # Total commits for this file
                commits_count = subprocess.run(
                    ['git', 'rev-list', '--count', 'HEAD', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()
                info['commits_count'] = int(commits_count) if commits_count else 0

                # Contributors to this file (top 5)
                contributors = subprocess.run(
                    ['git', 'log', '--pretty=%an', '--', str(rel_path)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip().split('\n')
                unique_contributors = list(dict.fromkeys([c for c in contributors if c]))[:5]
                info['contributors'] = unique_contributors

            return info

        except Exception as e:
            return {}

    def construct_github_url(self, file_path: Path, repo_path: Path, github_url: Optional[str] = None) -> str:
        """Construct GitHub URL for a file"""
        if not github_url:
            # Try to get from git remote
            try:
                remote_url = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                ).stdout.strip()

                # Convert SSH/HTTPS to GitHub URL format
                if 'github.com' in remote_url:
                    # SSH format: git@github.com:user/repo.git
                    # HTTPS format: https://github.com/user/repo.git
                    github_url = remote_url.replace('git@github.com:', 'https://github.com/')
                    github_url = github_url.replace('.git', '')
            except:
                return ''

        if not github_url or 'github.com' not in github_url:
            return ''

        try:
            # Get current branch
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True
            ).stdout.strip()

            rel_path = file_path.relative_to(repo_path)
            file_url = f"{github_url}/blob/{branch}/{rel_path}"
            return file_url
        except:
            return ''

    def calculate_complexity(self, content: str, language: str) -> int:
        """Calculate approximate cyclomatic complexity"""
        complexity = 1  # Base complexity

        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'and', 'or', '?']
        for keyword in decision_keywords:
            complexity += content.count(keyword)

        return min(complexity, 9999)  # Cap at reasonable max

    def extract_python_metadata(self, content: str, file_path: str) -> Dict:
        """Extract metadata from Python files using AST"""
        metadata = {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
            'docstrings': [],
            'has_main': False,
            'has_tests': False,
        }

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        metadata['imports'].append(node.module)

                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    metadata['classes'].append(node.name)
                    if ast.get_docstring(node):
                        metadata['docstrings'].append(f"{node.name}: {ast.get_docstring(node)[:200]}")
                    # Check for test classes
                    if 'test' in node.name.lower():
                        metadata['has_tests'] = True

                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    metadata['functions'].append(node.name)
                    if ast.get_docstring(node):
                        metadata['docstrings'].append(f"{node.name}: {ast.get_docstring(node)[:200]}")
                    # Check for main
                    if node.name == 'main':
                        metadata['has_main'] = True
                    # Check for test functions
                    if node.name.startswith('test_'):
                        metadata['has_tests'] = True

                # Extract global variables
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            metadata['variables'].append(target.id)

            # Check for if __name__ == "__main__"
            if '__name__' in content and '__main__' in content:
                metadata['has_main'] = True

        except SyntaxError:
            pass  # Ignore syntax errors, file might be incomplete
        except Exception as e:
            print(f"[Analyzer] Warning: Could not parse {file_path}: {e}")

        return metadata

    def extract_javascript_metadata(self, content: str) -> Dict:
        """Extract metadata from JavaScript/TypeScript files"""
        metadata = {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
            'has_tests': False,
        }

        # Extract imports (ES6, CommonJS, TypeScript)
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',
            r'require\([\'"](.+?)[\'"]\)',
            r'import\s+[\'"](.+?)[\'"]',
        ]
        for pattern in import_patterns:
            metadata['imports'].extend(re.findall(pattern, content))

        # Extract classes
        class_pattern = r'class\s+(\w+)'
        metadata['classes'] = re.findall(class_pattern, content)

        # Extract functions (regular, arrow, async)
        function_patterns = [
            r'function\s+(\w+)',
            r'const\s+(\w+)\s*=\s*\(',
            r'const\s+(\w+)\s*=\s*async',
            r'async\s+function\s+(\w+)',
        ]
        for pattern in function_patterns:
            metadata['functions'].extend(re.findall(pattern, content))

        # Check for test files
        if any(test_keyword in content.lower() for test_keyword in ['describe(', 'it(', 'test(', 'expect(']):
            metadata['has_tests'] = True

        return metadata

    def extract_comments(self, content: str, language: str) -> List[str]:
        """Extract comments from code"""
        comments = []

        if language in ['python']:
            # Python comments
            comments = re.findall(r'#\s*(.+)', content)
        elif language in ['javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust']:
            # C-style comments
            comments.extend(re.findall(r'//\s*(.+)', content))
            comments.extend(re.findall(r'/\*\s*(.+?)\s*\*/', content, re.DOTALL))

        return [c.strip()[:200] for c in comments[:20]]  # Limit to 20 comments

    def chunk_content(self, content: str, max_chars: int = 6000) -> List[str]:
        """Split content into chunks for large files - optimized"""
        if len(content) <= max_chars:
            return [content]

        # Limit to max 3 chunks per file for performance
        max_chunks = 3

        # For very large files, use strategic sampling
        if len(content) > max_chars * max_chunks:
            return [
                content[:max_chars],  # Beginning (imports/setup)
                content[-max_chars:]  # End (main/exports)
            ]

        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1
            if current_length + line_length > max_chars and current_chunk:
                chunks.append('\n'.join(current_chunk))
                if len(chunks) >= max_chunks:
                    break
                current_chunk = []
                current_length = 0
            current_chunk.append(line)
            current_length += line_length

        if current_chunk and len(chunks) < max_chunks:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def generate_summary(self, metadata: Dict, language: str) -> str:
        """Generate a brief summary of the code"""
        parts = []

        if metadata.get('classes'):
            parts.append(f"Classes: {', '.join(metadata['classes'][:5])}")
        if metadata.get('functions'):
            parts.append(f"Functions: {', '.join(metadata['functions'][:5])}")
        if metadata.get('imports'):
            parts.append(f"Imports: {', '.join(metadata['imports'][:5])}")

        summary = f"{language.capitalize()} file. " + " | ".join(parts)
        return summary[:1000]

    def analyze_file(self, file_path: Path, repo_name: str, repo_path: str, repo_git_info: Dict, github_url: Optional[str] = None, is_private: bool = False, password_hash: str = "") -> List[Dict]:
        """Analyze a single file and return data for Milvus"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                return []

            # Get file info
            extension = file_path.suffix.lower()
            language = self.supported_extensions.get(extension, 'unknown')

            if language == 'unknown':
                return []

            # Calculate file hash
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()

            # Extract metadata based on language
            if language == 'python':
                metadata = self.extract_python_metadata(content, str(file_path))
            elif language in ['javascript', 'typescript']:
                metadata = self.extract_javascript_metadata(content)
            else:
                metadata = {
                    'imports': [],
                    'classes': [],
                    'functions': [],
                    'variables': [],
                    'has_tests': False,
                    'has_main': False,
                }

            # Extract comments
            comments = self.extract_comments(content, language)

            # Calculate metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            complexity = self.calculate_complexity(content, language)

            # Get Git information for this file
            file_git_info = self.get_file_git_info(file_path, Path(repo_path))

            # Construct GitHub URL
            github_file_url = self.construct_github_url(file_path, Path(repo_path), github_url)

            # Chunk content if needed
            chunks = self.chunk_content(content)

            # Prepare embedding texts for all chunks (for batch processing)
            embedding_texts = []
            for chunk in chunks:
                embedding_text = f"""
File: {file_path.name}
Language: {language}
Directory: {file_path.parent}
Classes: {', '.join(metadata.get('classes', [])[:10])}
Functions: {', '.join(metadata.get('functions', [])[:10])}
Imports: {', '.join(metadata.get('imports', [])[:10])}
Content:
{chunk[:1000]}
                """.strip()
                embedding_texts.append(embedding_text)

            # Generate all embeddings in batch
            embeddings = self._batch_generate_embeddings(embedding_texts)

            # Prepare data for each chunk
            data_entries = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

                # Create entry
                entry = {
                    'file_hash': file_hash,
                    'file_path': str(file_path.relative_to(repo_path)),
                    'file_name': file_path.name,
                    'file_extension': extension,
                    'language': language,
                    'chunk_index': idx,
                    'total_chunks': len(chunks),
                    'content': chunk[:8000],  # Milvus VARCHAR limit
                    'content_summary': self.generate_summary(metadata, language),
                    'imports': json.dumps(metadata.get('imports', [])[:50])[:2000],
                    'classes': json.dumps(metadata.get('classes', [])[:50])[:2000],
                    'functions': json.dumps(metadata.get('functions', [])[:50])[:2000],
                    'variables': json.dumps(metadata.get('variables', [])[:50])[:2000],
                    'docstrings': json.dumps(metadata.get('docstrings', [])[:20])[:2000],
                    'comments': json.dumps(comments[:20])[:2000],
                    'lines_of_code': lines_of_code,
                    'complexity_score': complexity,
                    'has_tests': metadata.get('has_tests', False),
                    'has_main': metadata.get('has_main', False),
                    'directory': str(file_path.parent.relative_to(repo_path)),
                    'module_path': str(file_path.relative_to(repo_path)).replace('/', '.').replace(extension, ''),
                    'tags': json.dumps([language, 'analyzed']),
                    'dependencies': json.dumps(metadata.get('imports', [])[:50])[:2000],
                    'dependents': json.dumps([])[:2000],
                    'indexed_at': datetime.now().isoformat(),
                    'file_modified_at': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'repo_name': repo_name,
                    'repo_path': str(repo_path),
                    # Git version control info
                    'git_commit_hash': file_git_info.get('commit_hash', repo_git_info.get('commit_hash', ''))[:64],
                    'git_commit_message': file_git_info.get('commit_message', repo_git_info.get('commit_message', ''))[:500],
                    'git_commit_author': file_git_info.get('commit_author', repo_git_info.get('commit_author', ''))[:128],
                    'git_commit_email': file_git_info.get('commit_email', repo_git_info.get('commit_email', ''))[:128],
                    'git_commit_date': file_git_info.get('commit_date', repo_git_info.get('commit_date', ''))[:64],
                    'git_branch': repo_git_info.get('branch', '')[:128],
                    'git_remote_url': repo_git_info.get('remote_url', '')[:512],
                    'github_url': github_file_url[:512],
                    'file_commits_count': file_git_info.get('commits_count', 0),
                    'file_contributors': json.dumps(file_git_info.get('contributors', []))[:1000],
                    # Privacy control
                    'is_private': is_private,
                    'privacy_password_hash': password_hash[:64],
                    'embedding': embedding
                }

                data_entries.append(entry)

            return data_entries

        except Exception as e:
            print(f"[Analyzer] Error analyzing {file_path}: {e}")
            return []

    def hash_password(self, password: str) -> str:
        """Hash password for privacy protection"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _process_file_worker(self, args):
        """Worker function for multiprocessing - processes a single file"""
        file_path, repo_name, repo_path, repo_git_info, github_url, is_private, password_hash = args
        try:
            # Skip files larger than 1MB for performance
            file_size = file_path.stat().st_size
            if file_size > 1_000_000:  # 1MB
                return {'success': False, 'error': 'File too large (>1MB)', 'file': str(file_path)}

            entries = self.analyze_file(file_path, repo_name, repo_path, repo_git_info, github_url, is_private, password_hash)
            return {'success': True, 'entries': entries if entries else [], 'file': str(file_path)}
        except Exception as e:
            return {'success': False, 'error': str(e), 'file': str(file_path)}

    def _batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch for better performance"""
        model = self.load_embedding_model()

        # Check cache first
        uncached_texts = []
        uncached_indices = []
        embeddings = [None] * len(texts)

        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._embedding_cache:
                embeddings[i] = self._embedding_cache[text_hash]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Generate embeddings for uncached texts in batch
        if uncached_texts:
            batch_embeddings = model.encode(uncached_texts, batch_size=32, show_progress_bar=False)
            for i, embedding in zip(uncached_indices, batch_embeddings):
                embedding_list = embedding.tolist()
                embeddings[i] = embedding_list
                # Cache it
                text_hash = hashlib.md5(texts[i].encode()).hexdigest()
                self._embedding_cache[text_hash] = embedding_list

        return embeddings

    def analyze_codebase(self, directory: str, repo_name: Optional[str] = None, github_url: Optional[str] = None, pull_latest: bool = True, is_private: bool = False, privacy_password: str = "sdk", num_workers: Optional[int] = None) -> Dict:
        """
        Analyze entire codebase and store in Milvus with multiprocessing

        Args:
            directory: Path to repository
            repo_name: Optional friendly name
            github_url: Optional GitHub repository URL
            pull_latest: Whether to pull latest code from git remote
            is_private: Mark as private (default: False - public)
            privacy_password: Password for private access (default: "sdk", case-insensitive)
            num_workers: Number of parallel workers (default: CPU count)
        """
        # Generate unique audit ID
        audit_id = hashlib.md5(f"{directory}{datetime.now().isoformat()}".encode()).hexdigest()
        analysis_start_time = datetime.now()

        # Initialize timing variables
        scan_time = 0.0
        elapsed_time = 0.0

        try:
            repo_path = Path(directory).resolve()

            if not repo_path.exists():
                return {'success': False, 'error': 'Directory does not exist'}

            if not repo_name:
                repo_name = repo_path.name

            # Hash password for privacy
            password_hash = self.hash_password(privacy_password.lower())  # Case-insensitive

            # Determine number of workers
            if num_workers is None:
                num_workers = max(1, cpu_count() - 1)  # Leave one CPU free

        except Exception as e:
            return {'success': False, 'error': f'Initialization error: {str(e)}'}

        try:
            print(f"\n[Analyzer] {'='*70}")
            print(f"[Analyzer] Analyzing codebase: {repo_name}")
            print(f"[Analyzer] Audit ID: {audit_id[:8]}")
            print(f"[Analyzer] Path: {repo_path}")
            print(f"[Analyzer] Privacy: {'Private' if is_private else 'Public'}")
            print(f"[Analyzer] Workers: {num_workers} parallel processes")
            print(f"[Analyzer] {'='*70}\n")

            # Check if git repo and pull latest code
            if self.is_git_repo(repo_path):
                print(f"[Git] ✓ Git repository detected")

                if pull_latest:
                    pull_result = self.pull_latest_code(repo_path)
                    if not pull_result['success']:
                        print(f"[Git] ⚠️  Could not pull latest code: {pull_result['message']}")
                        print(f"[Git] Continuing with current code...")
            else:
                print(f"[Git] ℹ️  Not a git repository, skipping version control features")

            # Get repository-level Git information
            repo_git_info = self.get_git_info(repo_path)

            # Connect to Milvus
            if not self.connect_milvus():
                return {'success': False, 'error': 'Failed to connect to Milvus'}

            # Create collection
            self.create_collection()

            # Scan directory with optimizations
            all_files = []
            print(f"[Analyzer] Scanning directory...")
            scan_start = time.time()

            for root, dirs, files in os.walk(repo_path):
                # Filter ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore(d)]

                for file in files:
                    file_path = Path(root) / file
                    if not self.should_ignore(str(file_path)) and file_path.suffix in self.supported_extensions:
                        # Skip files larger than 1MB for performance
                        try:
                            if file_path.stat().st_size <= 1_000_000:  # 1MB limit
                                all_files.append(file_path)
                        except:
                            pass  # Skip if can't get file size

            scan_time = time.time() - scan_start
            print(f"[Analyzer] Scan completed in {scan_time:.2f}s")

            total_files = len(all_files)
            print(f"[Analyzer] Found {total_files} files to analyze")

            # Prepare arguments for workers
            worker_args = [
                (file_path, repo_name, repo_path, repo_git_info, github_url, is_private, password_hash)
                for file_path in all_files
            ]

            # Process files in parallel with progress tracking
            print(f"[Analyzer] Starting parallel processing with {num_workers} workers...")
            start_time = time.time()

            all_entries = []
            analyzed_count = 0
            skipped_count = 0
            error_count = 0

            # Use multiprocessing pool
            with Pool(processes=num_workers) as pool:
                # Process in batches for better progress tracking
                batch_size = max(10, total_files // 20)  # At least 10, or 5% of files

                for i in range(0, len(worker_args), batch_size):
                    batch = worker_args[i:i + batch_size]
                    batch_results = pool.map(self._process_file_worker, batch)

                    # Process results
                    for result in batch_results:
                        if result['success']:
                            if result['entries']:
                                all_entries.extend(result['entries'])
                                analyzed_count += 1
                            else:
                                skipped_count += 1
                        else:
                            error_count += 1

                    # Progress update
                    processed = min(i + batch_size, total_files)
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta = (total_files - processed) / rate if rate > 0 else 0

                    print(f"[Analyzer] Progress: {processed}/{total_files} files ({processed*100//total_files}%) | "
                          f"Rate: {rate:.1f} files/sec | ETA: {eta:.1f}s | "
                          f"Analyzed: {analyzed_count} | Skipped: {skipped_count} | Errors: {error_count}")

            elapsed_time = time.time() - start_time
            print(f"\n[Analyzer] ✓ Analysis completed in {elapsed_time:.2f} seconds ({total_files/elapsed_time:.1f} files/sec)")

            # Batch insert into Milvus
            if all_entries:
                print(f"[Analyzer] Inserting {len(all_entries)} entries into Milvus in batches...")
                collection = Collection(name=self.collection_name)

                # Insert in batches of 1000 for better performance
                batch_size = 1000
                for i in range(0, len(all_entries), batch_size):
                    batch = all_entries[i:i + batch_size]
                    collection.insert(batch)
                    print(f"[Analyzer] Inserted batch {i//batch_size + 1}/{(len(all_entries)-1)//batch_size + 1}")

                collection.flush()
                print(f"[Analyzer] ✓ Insertion complete")

                completion_time = datetime.now()
                total_time = (completion_time - analysis_start_time).total_seconds()

                print(f"\n[Analyzer] {'='*70}")
                print(f"[Analyzer] ANALYSIS COMPLETE")
                print(f"[Analyzer] {'='*70}")
                print(f"[Analyzer] Files analyzed: {analyzed_count}")
                print(f"[Analyzer] Files skipped: {skipped_count}")
                print(f"[Analyzer] Errors: {error_count}")
                print(f"[Analyzer] Total entries: {len(all_entries)}")
                print(f"[Analyzer] Repository: {repo_name}")
                print(f"[Analyzer] Processing time: {elapsed_time:.2f}s")
                print(f"[Analyzer] Processing rate: {total_files/elapsed_time:.1f} files/sec")
                print(f"[Analyzer] {'='*70}\n")

                # Store audit log
                import socket
                audit_data = {
                    'audit_id': audit_id,
                    'analysis_timestamp': analysis_start_time.isoformat(),
                    'completion_timestamp': completion_time.isoformat(),
                    'repo_name': repo_name,
                    'repo_path': str(repo_path),
                    'github_url': github_url or '',
                    'total_files_found': total_files,
                    'files_analyzed': analyzed_count,
                    'files_skipped': skipped_count,
                    'files_errored': error_count,
                    'total_entries_created': len(all_entries),
                    'total_chunks_created': len(all_entries),
                    'processing_time_seconds': total_time,
                    'files_per_second': total_files/elapsed_time if elapsed_time > 0 else 0,
                    'scan_time_seconds': scan_time,
                    'embedding_time_seconds': 0.0,
                    'insertion_time_seconds': 0.0,
                    'num_workers': num_workers,
                    'pull_latest': pull_latest,
                    'is_private': is_private,
                    'git_branch': repo_git_info.get('branch', '') if repo_git_info else '',
                    'git_commit_hash': repo_git_info.get('commit_hash', '') if repo_git_info else '',
                    'git_commit_author': repo_git_info.get('commit_author', '') if repo_git_info else '',
                    'git_remote_url': repo_git_info.get('remote_url', '') if repo_git_info else '',
                    'languages': json.dumps(list(set(entry['language'] for entry in all_entries))),
                    'cpu_count': cpu_count(),
                    'host_machine': socket.gethostname(),
                    'status': 'success' if error_count == 0 else 'partial',
                    'error_message': ''
                }

                # Store audit log in background (don't block on failure)
                try:
                    self.store_audit_log(audit_data)
                except Exception as e:
                    print(f"[Audit] ⚠️  Could not store audit log: {e}")

                return {
                    'success': True,
                    'audit_id': audit_id,
                    'repo_name': repo_name,
                    'files_analyzed': analyzed_count,
                    'files_skipped': skipped_count,
                    'errors': error_count,
                    'total_entries': len(all_entries),
                    'processing_time': elapsed_time,
                    'files_per_second': total_files/elapsed_time if elapsed_time > 0 else 0,
                    'analysis_timestamp': analysis_start_time.isoformat(),
                    'completion_timestamp': completion_time.isoformat(),
                    'languages': list(set(entry['language'] for entry in all_entries)),
                    'git_info': {
                        'branch': repo_git_info.get('branch', 'N/A'),
                        'commit_hash': repo_git_info.get('commit_hash', 'N/A')[:8],
                        'commit_message': repo_git_info.get('commit_message', 'N/A')[:100],
                        'commit_author': repo_git_info.get('commit_author', 'N/A'),
                        'remote_url': repo_git_info.get('remote_url', 'N/A')
                    } if repo_git_info else None,
                    'github_url': github_url
                }

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"\n[Analyzer] ❌ ERROR during analysis: {str(e)}")
            print(f"[Analyzer] Traceback:\n{error_msg}")

            # Store error audit log
            completion_time = datetime.now()
            total_time = (completion_time - analysis_start_time).total_seconds()

            try:
                import socket
                error_audit_data = {
                    'audit_id': audit_id,
                    'analysis_timestamp': analysis_start_time.isoformat(),
                    'completion_timestamp': completion_time.isoformat(),
                    'repo_name': repo_name if 'repo_name' in locals() else 'unknown',
                    'repo_path': str(repo_path) if 'repo_path' in locals() else directory,
                    'github_url': github_url or '',
                    'total_files_found': 0,
                    'files_analyzed': 0,
                    'files_skipped': 0,
                    'files_errored': 0,
                    'total_entries_created': 0,
                    'total_chunks_created': 0,
                    'processing_time_seconds': total_time,
                    'files_per_second': 0.0,
                    'scan_time_seconds': scan_time,
                    'embedding_time_seconds': 0.0,
                    'insertion_time_seconds': 0.0,
                    'num_workers': num_workers if 'num_workers' in locals() else 0,
                    'pull_latest': pull_latest,
                    'is_private': is_private,
                    'git_branch': '',
                    'git_commit_hash': '',
                    'git_commit_author': '',
                    'git_remote_url': '',
                    'languages': json.dumps([]),
                    'cpu_count': cpu_count(),
                    'host_machine': socket.gethostname(),
                    'status': 'error',
                    'error_message': str(e)[:900]
                }
                self.store_audit_log(error_audit_data)
            except Exception as audit_err:
                print(f"[Audit] ⚠️  Could not store error audit log: {audit_err}")

            return {
                'success': False,
                'error': str(e),
                'traceback': error_msg,
                'audit_id': audit_id
            }

    def search_code(self, query: str, top_k: int = 10, privacy_password: Optional[str] = None) -> List[Dict]:
        """
        Search codebase with semantic query

        Args:
            query: Search query
            top_k: Number of results
            privacy_password: Password for accessing private documents (case-insensitive)
        """
        if not self.connect_milvus():
            return []

        if not utility.has_collection(self.collection_name):
            print(f"[Analyzer] Collection '{self.collection_name}' does not exist")
            return []

        try:
            # Hash password if provided
            password_hash = self.hash_password(privacy_password.lower()) if privacy_password else None

            # Generate query embedding
            model = self.load_embedding_model()
            query_embedding = model.encode([query]).tolist()

            # Search
            collection = Collection(name=self.collection_name)
            collection.load()

            # Build filter expression for privacy
            if privacy_password:
                # With password: return all (public + private matching password)
                search_filter = f'is_private == false || privacy_password_hash == "{password_hash}"'
            else:
                # No password: only public documents
                search_filter = 'is_private == false'

            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=search_filter,
                output_fields=[
                    "file_path", "file_name", "language", "content", "content_summary",
                    "classes", "functions", "imports", "lines_of_code", "complexity_score",
                    "directory", "repo_name", "has_tests", "has_main", "is_private"
                ]
            )

            # Format results
            documents = []
            for hits in results:
                for hit in hits:
                    documents.append({
                        'file_path': hit.entity.get('file_path', ''),
                        'file_name': hit.entity.get('file_name', ''),
                        'language': hit.entity.get('language', ''),
                        'content': hit.entity.get('content', ''),
                        'summary': hit.entity.get('content_summary', ''),
                        'classes': json.loads(hit.entity.get('classes', '[]')),
                        'functions': json.loads(hit.entity.get('functions', '[]')),
                        'imports': json.loads(hit.entity.get('imports', '[]')),
                        'lines_of_code': hit.entity.get('lines_of_code', 0),
                        'complexity': hit.entity.get('complexity_score', 0),
                        'directory': hit.entity.get('directory', ''),
                        'repo_name': hit.entity.get('repo_name', ''),
                        'has_tests': hit.entity.get('has_tests', False),
                        'has_main': hit.entity.get('has_main', False),
                        'score': round(1 / (1 + hit.distance), 4),
                        'collection': 'codebase_analysis'
                    })

            collection.release()
            return documents

        except Exception as e:
            print(f"[Analyzer] Error searching: {e}")
            return []


def main():
    """Example usage"""
    analyzer = CodebaseAnalyzer()

    # Example: Analyze current project
    result = analyzer.analyze_codebase(
        directory="/path/to/your/project",
        repo_name="Your-Project-Name"
    )

    if result['success']:
        print("\n✓ Analysis complete!")
        print(f"  Files: {result['files_analyzed']}")
        print(f"  Entries: {result['total_entries']}")
        print(f"  Languages: {', '.join(result['languages'])}")

        # Example: Search code
        print("\n" + "="*70)
        print("TESTING CODE SEARCH")
        print("="*70)

        query = "Find all functions that handle API requests"
        print(f"\nQuery: {query}")
        results = analyzer.search_code(query, top_k=5)

        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {result['file_path']} ({result['language']}) [Score: {result['score']}]")
            print(f"   Summary: {result['summary']}")
            print(f"   Functions: {', '.join(result['functions'][:5])}")


if __name__ == "__main__":
    main()
