#!/usr/bin/env python3
"""
GitHub Persona Analyzer
Analyzes contributor patterns from GitHub PRs stored in Milvus
"""

import json
from collections import defaultdict, Counter
from datetime import datetime
from pymilvus import connections, Collection, utility, FieldSchema, CollectionSchema, DataType
from sentence_transformers import SentenceTransformer
from textblob import TextBlob
import re


class GitHubPersonaAnalyzer:
    """Analyze GitHub contributor patterns and build personas"""

    def __init__(self, collection_name='github_prs', milvus_host='localhost', milvus_port='19530'):
        self.collection_name = collection_name
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = None

    def connect(self):
        """Connect to Milvus"""
        try:
            connections.connect(alias="default", host=self.milvus_host, port=self.milvus_port)
            return True
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            return False

    def load_embedding_model(self):
        """Load embedding model for persona embeddings"""
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model

    def get_all_prs(self):
        """Fetch all PRs from Milvus collection"""
        if not self.connect():
            return []

        if not utility.has_collection(self.collection_name):
            print(f"Collection {self.collection_name} does not exist")
            return []

        collection = Collection(name=self.collection_name)
        collection.load()

        # Query all PRs
        results = collection.query(
            expr="source_type == 'github_pr'",
            output_fields=["source_id", "title", "content", "metadata", "url"]
        )

        collection.release()
        return results

    def extract_user_activities(self, prs):
        """Extract all activities per user from PRs"""
        user_data = defaultdict(lambda: {
            'prs_authored': [],
            'prs_reviewed': [],
            'approvals_given': [],
            'changes_requested': [],
            'comments_only': [],
            'prs_merged': [],
            'all_comments': [],
            'review_comments': [],
            'issue_comments': [],
            'review_times': [],
            'merge_times': []
        })

        for pr in prs:
            try:
                metadata = json.loads(pr.get('metadata', '{}'))
                content = pr.get('content', '')

                # Extract PR author (use name, not login)
                author = metadata.get('author', 'unknown')  # Already stores name from web_interface
                pr_number = metadata.get('number', 0)
                pr_url = pr.get('url', '')
                created_at = metadata.get('created_at', '')
                merged_at = metadata.get('merged_at', '')
                merged_by = metadata.get('merged_by', None)  # Already stores name from web_interface

                # Track PR authorship
                user_data[author]['prs_authored'].append({
                    'pr_number': pr_number,
                    'title': pr.get('title', ''),
                    'url': pr_url,
                    'created_at': created_at,
                    'merged': metadata.get('merged', False),
                    'merged_by': merged_by
                })

                # Extract reviewers and their actions from content
                # Parse reviews section
                reviews_match = re.search(r'--- REVIEWS \((\d+): (\d+) approved, (\d+) changes requested\) ---', content)
                if reviews_match:
                    total_reviews = int(reviews_match.group(1))
                    approvals_count = int(reviews_match.group(2))
                    changes_req_count = int(reviews_match.group(3))

                # Parse individual reviews
                review_pattern = r'\d+\. (APPROVED|CHANGES_REQUESTED|COMMENTED) by (\w+): (.+?)(?=\n\d+\.|---|\Z)'
                for match in re.finditer(review_pattern, content, re.DOTALL):
                    state = match.group(1)
                    reviewer = match.group(2)
                    review_body = match.group(3).strip()

                    user_data[reviewer]['prs_reviewed'].append({
                        'pr_number': pr_number,
                        'pr_author': author,
                        'state': state,
                        'url': pr_url
                    })

                    if state == 'APPROVED':
                        user_data[reviewer]['approvals_given'].append({
                            'pr_number': pr_number,
                            'pr_author': author,
                            'url': pr_url
                        })
                    elif state == 'CHANGES_REQUESTED':
                        user_data[reviewer]['changes_requested'].append({
                            'pr_number': pr_number,
                            'pr_author': author,
                            'url': pr_url
                        })
                    elif state == 'COMMENTED':
                        user_data[reviewer]['comments_only'].append({
                            'pr_number': pr_number,
                            'pr_author': author,
                            'url': pr_url
                        })

                    # Store review comment
                    if review_body and review_body != '(no comment)':
                        user_data[reviewer]['all_comments'].append({
                            'type': 'review',
                            'pr_number': pr_number,
                            'text': review_body,
                            'state': state
                        })

                # Parse discussion comments
                comment_pattern = r'\d+\. (\w+): (.+?)(?=\n\d+\.|---|\Z)'
                discussion_section = re.search(r'--- DISCUSSION COMMENTS.*?---', content, re.DOTALL)
                if discussion_section:
                    for match in re.finditer(comment_pattern, discussion_section.group(0), re.DOTALL):
                        commenter = match.group(1)
                        comment_text = match.group(2).strip()

                        user_data[commenter]['issue_comments'].append({
                            'pr_number': pr_number,
                            'text': comment_text
                        })
                        user_data[commenter]['all_comments'].append({
                            'type': 'discussion',
                            'pr_number': pr_number,
                            'text': comment_text
                        })

                # Parse code review comments
                code_comment_pattern = r'\d+\. (\w+) on .+?: (.+?)(?=\n\d+\.|---|\Z)'
                code_section = re.search(r'--- CODE REVIEW COMMENTS.*?---', content, re.DOTALL)
                if code_section:
                    for match in re.finditer(code_comment_pattern, code_section.group(0), re.DOTALL):
                        commenter = match.group(1)
                        comment_text = match.group(2).strip()

                        user_data[commenter]['review_comments'].append({
                            'pr_number': pr_number,
                            'text': comment_text
                        })
                        user_data[commenter]['all_comments'].append({
                            'type': 'code_review',
                            'pr_number': pr_number,
                            'text': comment_text
                        })

                # Track who merged the PR
                if merged_by:
                    user_data[merged_by]['prs_merged'].append({
                        'pr_number': pr_number,
                        'pr_author': author,
                        'url': pr_url,
                        'merged_at': merged_at,
                        'self_merge': merged_by == author
                    })

                    # Calculate merge time if available
                    if created_at and merged_at:
                        try:
                            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            merged = datetime.fromisoformat(merged_at.replace('Z', '+00:00'))
                            hours_to_merge = (merged - created).total_seconds() / 3600
                            user_data[merged_by]['merge_times'].append(hours_to_merge)
                        except:
                            pass

            except Exception as e:
                print(f"Error processing PR: {e}")
                continue

        return dict(user_data)

    def analyze_comment_patterns(self, comments):
        """Analyze commenting patterns and extract insights"""
        if not comments:
            return {
                'common_phrases': [],
                'tone': 'neutral',
                'avg_length': 0,
                'sentiment_score': 0,
                'topics': {}
            }

        # Combine all comment text
        all_text = ' '.join([c['text'] for c in comments if c.get('text')])

        # Calculate average comment length
        avg_length = sum(len(c['text']) for c in comments if c.get('text')) / len(comments)

        # Extract common phrases (2-3 words)
        words = re.findall(r'\b\w+\b', all_text.lower())
        phrases = []
        for i in range(len(words) - 1):
            phrases.append(f"{words[i]} {words[i+1]}")

        phrase_counter = Counter(phrases)
        common_phrases = [
            {'phrase': phrase, 'count': count}
            for phrase, count in phrase_counter.most_common(10)
        ]

        # Sentiment analysis
        try:
            blob = TextBlob(all_text)
            sentiment_score = blob.sentiment.polarity  # -1 to 1

            if sentiment_score > 0.2:
                tone = 'positive'
            elif sentiment_score < -0.2:
                tone = 'critical'
            else:
                tone = 'neutral'
        except:
            sentiment_score = 0
            tone = 'neutral'

        # Topic detection (simple keyword matching)
        topics = {
            'code_style': sum(1 for c in comments if any(word in c['text'].lower() for word in ['style', 'format', 'lint', 'convention'])),
            'logic_bugs': sum(1 for c in comments if any(word in c['text'].lower() for word in ['bug', 'error', 'issue', 'wrong', 'fix'])),
            'performance': sum(1 for c in comments if any(word in c['text'].lower() for word in ['performance', 'slow', 'optimize', 'efficient', 'speed'])),
            'security': sum(1 for c in comments if any(word in c['text'].lower() for word in ['security', 'vulnerable', 'auth', 'permission', 'safe'])),
            'documentation': sum(1 for c in comments if any(word in c['text'].lower() for word in ['doc', 'comment', 'readme', 'documentation']))
        }

        return {
            'common_phrases': common_phrases,
            'tone': tone,
            'avg_length': int(avg_length),
            'sentiment_score': round(sentiment_score, 2),
            'topics': topics
        }

    def build_persona(self, username, user_activities):
        """Build comprehensive persona for a user"""
        activities = user_activities.get(username, {})

        # Calculate statistics
        prs_authored_count = len(activities['prs_authored'])
        prs_reviewed_count = len(activities['prs_reviewed'])
        approvals_count = len(activities['approvals_given'])
        changes_req_count = len(activities['changes_requested'])
        comments_only_count = len(activities['comments_only'])
        prs_merged_count = len(activities['prs_merged'])

        # Calculate merge statistics
        self_merges = [m for m in activities['prs_merged'] if m.get('self_merge', False)]
        other_merges = [m for m in activities['prs_merged'] if not m.get('self_merge', False)]

        merge_rate = prs_merged_count / prs_reviewed_count if prs_reviewed_count > 0 else 0
        self_merge_rate = len(self_merges) / prs_authored_count if prs_authored_count > 0 else 0
        approval_rate = approvals_count / prs_reviewed_count if prs_reviewed_count > 0 else 0

        # Calculate average times
        avg_merge_time = sum(activities['merge_times']) / len(activities['merge_times']) if activities['merge_times'] else 0

        # Determine role based on activity
        if prs_merged_count > 10 and merge_rate > 0.3:
            role = 'maintainer'
        elif prs_reviewed_count > prs_authored_count and prs_reviewed_count > 5:
            role = 'reviewer'
        elif prs_authored_count > 5:
            role = 'contributor'
        else:
            role = 'participant'

        # Analyze comment patterns
        comment_patterns = self.analyze_comment_patterns(activities['all_comments'])

        # Determine review style
        if prs_reviewed_count == 0:
            review_style = 'none'
        elif len(activities['all_comments']) / prs_reviewed_count > 3:
            review_style = 'thorough'
        elif approval_rate > 0.8:
            review_style = 'quick_approver'
        elif changes_req_count / prs_reviewed_count > 0.5:
            review_style = 'strict'
        else:
            review_style = 'balanced'

        # Build statistics
        statistics = {
            'prs_authored': prs_authored_count,
            'prs_reviewed': prs_reviewed_count,
            'approvals_given': approvals_count,
            'changes_requested': changes_req_count,
            'comments_only': comments_only_count,
            'prs_merged': prs_merged_count,
            'prs_merged_own': len(self_merges),
            'prs_merged_others': len(other_merges),
            'merge_rate': round(merge_rate, 2),
            'self_merge_rate': round(self_merge_rate, 2),
            'approval_rate': round(approval_rate, 2),
            'avg_time_to_merge_hours': round(avg_merge_time, 1),
            'total_comments': len(activities['all_comments']),
            'avg_comments_per_review': round(len(activities['all_comments']) / prs_reviewed_count, 1) if prs_reviewed_count > 0 else 0
        }

        # Build patterns
        patterns = {
            'common_phrases': comment_patterns['common_phrases'],
            'comment_types': comment_patterns['topics'],
            'review_style': review_style,
            'tone': comment_patterns['tone'],
            'avg_comment_length': comment_patterns['avg_length'],
            'sentiment_score': comment_patterns['sentiment_score']
        }

        # Build relationships (who they work with)
        frequently_reviews = Counter()
        for review in activities['prs_reviewed']:
            frequently_reviews[review['pr_author']] += 1

        frequently_reviewed_by = Counter()
        # This would need to be calculated by checking who reviewed their PRs

        relationships = {
            'frequently_reviews': [
                {'username': user, 'count': count}
                for user, count in frequently_reviews.most_common(10)
            ],
            'frequently_reviewed_by': []  # Would need reverse lookup
        }

        # Generate persona description for embedding
        persona_description = (
            f"{username} is a {role} who has authored {prs_authored_count} PRs and reviewed {prs_reviewed_count} PRs. "
            f"They have an approval rate of {approval_rate:.0%} and have merged {prs_merged_count} PRs. "
            f"Their review style is {review_style} with a {comment_patterns['tone']} tone. "
            f"They often comment on {', '.join(k for k, v in comment_patterns['topics'].items() if v > 0)}."
        )

        return {
            'username': username,
            'display_name': username,  # Could be enhanced with actual name
            'role': role,
            'statistics': statistics,
            'patterns': patterns,
            'relationships': relationships,
            'persona_description': persona_description
        }

    def ensure_persona_collection(self):
        """Ensure github_personas collection exists"""
        if not self.connect():
            return None

        collection_name = 'github_personas'

        if utility.has_collection(collection_name):
            return Collection(name=collection_name)

        # Create collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="username", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="display_name", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="role", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="statistics", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="patterns", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="relationships", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="persona_description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="last_updated", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(fields=fields, description="GitHub contributor personas")
        collection = Collection(name=collection_name, schema=schema)

        # Create index
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        return collection

    def store_persona(self, persona):
        """Store persona in Milvus"""
        collection = self.ensure_persona_collection()
        if collection is None:
            return False

        model = self.load_embedding_model()

        # Generate embedding from persona description
        embedding = model.encode([persona['persona_description']])[0].tolist()

        # Prepare data
        data = [
            [persona['username']],
            [persona['display_name']],
            [persona['role']],
            [json.dumps(persona['statistics'])],
            [json.dumps(persona['patterns'])],
            [json.dumps(persona['relationships'])],
            [persona['persona_description']],
            [datetime.now().isoformat()],
            [embedding]
        ]

        # Delete existing persona for this user
        try:
            collection.delete(f"username == '{persona['username']}'")
        except:
            pass

        # Insert new persona
        collection.insert(data)
        collection.flush()

        return True

    def build_all_personas(self):
        """Build personas for all users in PR collection"""
        print("[Persona Analyzer] Fetching all PRs...")
        prs = self.get_all_prs()

        if not prs:
            return {'success': False, 'message': 'No PRs found', 'personas': []}

        print(f"[Persona Analyzer] Analyzing {len(prs)} PRs...")
        user_activities = self.extract_user_activities(prs)

        print(f"[Persona Analyzer] Found {len(user_activities)} unique contributors")

        personas = []
        for username in user_activities.keys():
            if username == 'unknown':
                continue

            print(f"[Persona Analyzer] Building persona for {username}...")
            persona = self.build_persona(username, user_activities)

            # Store in Milvus
            if self.store_persona(persona):
                personas.append({
                    'username': username,
                    'role': persona['role'],
                    'statistics': persona['statistics']
                })
                print(f"[Persona Analyzer] ✓ Stored persona for {username}")
            else:
                print(f"[Persona Analyzer] ✗ Failed to store persona for {username}")

        return {
            'success': True,
            'message': f'Built {len(personas)} personas from {len(prs)} PRs',
            'personas': personas
        }

    def get_persona(self, username):
        """Get persona data for specific user"""
        if not self.connect():
            return None

        collection_name = 'github_personas'
        if not utility.has_collection(collection_name):
            return None

        collection = Collection(name=collection_name)
        collection.load()

        results = collection.query(
            expr=f"username == '{username}'",
            output_fields=["username", "display_name", "role", "statistics", "patterns",
                          "relationships", "persona_description", "last_updated"]
        )

        collection.release()

        if results:
            result = results[0]
            return {
                'username': result['username'],
                'display_name': result['display_name'],
                'role': result['role'],
                'statistics': json.loads(result['statistics']),
                'patterns': json.loads(result['patterns']),
                'relationships': json.loads(result['relationships']),
                'persona_description': result['persona_description'],
                'last_updated': result['last_updated']
            }

        return None

    def get_all_personas(self):
        """Get all personas with summary stats"""
        if not self.connect():
            return []

        collection_name = 'github_personas'
        if not utility.has_collection(collection_name):
            return []

        collection = Collection(name=collection_name)
        collection.load()

        results = collection.query(
            expr="username != ''",
            output_fields=["username", "display_name", "role", "statistics", "last_updated"],
            limit=1000
        )

        collection.release()

        personas = []
        for result in results:
            stats = json.loads(result['statistics'])
            personas.append({
                'username': result['username'],
                'display_name': result['display_name'],
                'role': result['role'],
                'statistics': stats,
                'last_updated': result['last_updated']
            })

        return personas
