#!/usr/bin/env python3
"""
Claude RAG (Retrieval Augmented Generation) Integration
Online AI reasoning with Milvus vector search + Website scraping
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility
import anthropic
import time
from token_tracker import get_tracker

load_dotenv()


class ClaudeRAG:
    def __init__(self):
        """Initialize Claude RAG system"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.embedding_model = None
        self.milvus_host = "localhost"
        self.milvus_port = "19530"

        # Initialize Anthropic client
        if self.base_url:
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

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

    def scrape_website(self, url):
        """
        Scrape content from a website

        Args:
            url: Website URL to scrape

        Returns:
            dict with title and content
        """
        try:
            print(f"[Scraping] Fetching {url}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get title
            title = soup.title.string if soup.title else url

            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)

            print(f"[Scraping] ✓ Extracted {len(content)} characters")

            return {
                'title': title,
                'content': content[:10000],  # Limit to 10k chars
                'url': url,
                'source_type': 'website',
                'score': 1.0  # Max score for explicitly provided content
            }

        except Exception as e:
            print(f"[Scraping] Error: {e}")
            return None

    def search_milvus(self, query, collection_name, top_k=5):
        """Search a single Milvus collection with hybrid search (exact match + semantic)"""
        if not self.connect_milvus():
            return []

        if not utility.has_collection(collection_name):
            return []

        try:
            collection = Collection(name=collection_name)
            collection.load()

            # Get collection schema to determine available fields
            schema = collection.schema
            available_fields = [field.name for field in schema.fields]

            # Determine which fields to retrieve based on collection schema
            output_fields = []

            # Standard RAG collections (github_prs, jira_tickets, jira_issues, custom_notes)
            if "source_type" in available_fields:
                output_fields = ["source_type", "source_id", "title", "content", "metadata", "url"]
            # Codebase analysis collection
            elif "file_path" in available_fields and "content" in available_fields:
                output_fields = ["file_path", "file_name", "language", "content", "content_summary",
                                "functions", "classes", "repo_name", "github_url"]
            # Action logs collection
            elif "action_type" in available_fields and "endpoint" in available_fields:
                output_fields = ["action_type", "endpoint", "parameters", "status", "result_summary",
                                "error_message", "metadata"]
            # GitHub personas collection
            elif "username" in available_fields and "persona_description" in available_fields:
                output_fields = ["username", "display_name", "role", "persona_description",
                                "statistics", "patterns"]
            # Audit collection
            elif "repo_name" in available_fields and "total_files_found" in available_fields:
                output_fields = ["repo_name", "repo_path", "total_files_found", "files_analyzed",
                                "status", "processing_time_seconds"]
            else:
                # Fallback: get any content-like fields available
                possible_content_fields = ["content", "title", "file_path", "action_type", "username", "repo_name"]
                output_fields = [f for f in possible_content_fields if f in available_fields]

            # Ensure we have at least some fields to output
            if not output_fields:
                output_fields = [available_fields[1]] if len(available_fields) > 1 else []

            # HYBRID SEARCH: Try exact match first for JIRA tickets
            documents = []
            exact_match_found = False

            # Extract ticket ID if present (for JIRA collections)
            if collection_name in ['jira_tickets', 'jira_issues'] and 'source_id' in output_fields:
                import re
                ticket_pattern = r'([A-Z]+-\d+)'
                match = re.search(ticket_pattern, query)

                if match:
                    ticket_id = match.group(1)
                    print(f"[RAG] Attempting exact match for {ticket_id}")

                    try:
                        exact_results = collection.query(
                            expr=f"source_id == '{ticket_id}'",
                            output_fields=output_fields,
                            limit=1
                        )

                        if exact_results:
                            print(f"[RAG] ✓ Found exact match for {ticket_id}")
                            exact_match_found = True

                            # Build document from exact match
                            for result in exact_results:
                                doc = {
                                    'score': 1.0,  # Perfect match
                                    'collection': collection_name,
                                    'match_type': 'exact',
                                    'title': result.get('title', ''),
                                    'content': result.get('content', ''),
                                    'source_id': result.get('source_id', ''),
                                    'source_type': result.get('source_type', ''),
                                    'url': result.get('url', ''),
                                }
                                documents.append(doc)
                    except Exception as e:
                        print(f"[RAG] Exact match failed: {e}")

            # If no exact match, do semantic search
            if not exact_match_found:
                model = self.load_embedding_model()
                query_embedding = model.encode([query]).tolist()

                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                results = collection.search(
                    data=query_embedding,
                    anns_field="embedding",
                    param=search_params,
                    limit=top_k,
                    output_fields=output_fields
                )

                # Process semantic search results
                for hits in results:
                    for hit in hits:
                        # Build document based on collection type
                        doc = {
                            'score': round(1 / (1 + hit.distance), 4),
                            'collection': collection_name,
                            'match_type': 'semantic'
                        }

                        # Extract fields based on collection type
                        if "source_type" in output_fields:
                            # Standard RAG collections
                            doc.update({
                                'title': hit.entity.get('title', ''),
                                'content': hit.entity.get('content', ''),
                                'source_id': hit.entity.get('source_id', ''),
                                'source_type': hit.entity.get('source_type', ''),
                                'url': hit.entity.get('url', ''),
                            })
                        elif "file_path" in output_fields:
                            # Codebase analysis
                            doc.update({
                                'title': hit.entity.get('file_path', ''),
                                'content': hit.entity.get('content', '')[:1000],  # Limit content length
                                'source_type': f"{hit.entity.get('language', 'code')} file",
                                'source_id': hit.entity.get('file_name', ''),
                                'url': hit.entity.get('github_url', ''),
                                'file_path': hit.entity.get('file_path', ''),
                                'functions': hit.entity.get('functions', ''),
                                'classes': hit.entity.get('classes', ''),
                            })
                        elif "action_type" in output_fields:
                            # Action logs
                            doc.update({
                                'title': f"{hit.entity.get('action_type', '')} - {hit.entity.get('endpoint', '')}",
                                'content': hit.entity.get('result_summary', '') or hit.entity.get('error_message', ''),
                                'source_type': 'action_log',
                                'source_id': hit.entity.get('action_type', ''),
                                'url': '',
                                'parameters': hit.entity.get('parameters', ''),
                            })
                        elif "username" in output_fields:
                            # GitHub personas
                            doc.update({
                                'title': f"{hit.entity.get('display_name', '')} (@{hit.entity.get('username', '')})",
                                'content': hit.entity.get('persona_description', ''),
                                'source_type': 'developer_persona',
                                'source_id': hit.entity.get('username', ''),
                                'url': '',
                                'role': hit.entity.get('role', ''),
                            })
                        elif "repo_name" in output_fields and "total_files_found" in output_fields:
                            # Audit logs
                            doc.update({
                                'title': f"Audit: {hit.entity.get('repo_name', '')}",
                                'content': f"Files analyzed: {hit.entity.get('files_analyzed', 0)}, Status: {hit.entity.get('status', '')}",
                                'source_type': 'audit_log',
                                'source_id': hit.entity.get('repo_name', ''),
                                'url': '',
                            })
                        else:
                            # Fallback for unknown collection types
                            doc.update({
                                'title': str(hit.entity.get(output_fields[0], '')),
                                'content': str(hit.entity),
                                'source_type': collection_name,
                                'source_id': '',
                                'url': '',
                            })

                        documents.append(doc)

            collection.release()
            return documents

        except Exception as e:
            print(f"Error searching {collection_name}: {e}")
            return []

    def search_all_collections(self, query, top_k_per_collection=3):
        """Search across ALL Milvus collections"""
        if not self.connect_milvus():
            print("[RAG] ❌ Failed to connect to Milvus")
            return []

        all_collections = utility.list_collections()
        print(f"\n[RAG] 🔍 Searching {len(all_collections)} collections: {all_collections}")
        print(f"[RAG] Retrieving top {top_k_per_collection} documents per collection\n")

        # Load the embedding model to get the expected dimension
        model = self.load_embedding_model()
        expected_dim = model.get_sentence_embedding_dimension()

        all_documents = []
        search_summary = []

        for collection_name in all_collections:
            try:
                # Check if collection has data
                collection = Collection(name=collection_name)
                collection.load()
                num_entities = collection.num_entities

                if num_entities == 0:
                    print(f"[RAG]   ⚠️  {collection_name}: EMPTY (0 documents)")
                    search_summary.append(f"{collection_name}: EMPTY")
                    collection.release()
                    continue

                # Check embedding dimension compatibility
                schema = collection.schema
                embedding_dim = None
                for field in schema.fields:
                    if field.name == "embedding":
                        embedding_dim = field.params.get('dim')
                        break

                if embedding_dim and embedding_dim != expected_dim:
                    print(f"[RAG]   ⚠️  {collection_name}: SKIPPED (dimension mismatch: {embedding_dim} vs {expected_dim})")
                    search_summary.append(f"{collection_name}: INCOMPATIBLE")
                    collection.release()
                    continue

                print(f"[RAG]   🔎 {collection_name}: {num_entities} total documents in DB")

                # Search this collection
                docs = self.search_milvus(query, collection_name, top_k_per_collection)
                all_documents.extend(docs)

                if docs:
                    print(f"[RAG]   ✓  {collection_name}: Retrieved {len(docs)} relevant docs")
                    search_summary.append(f"{collection_name}: {len(docs)} docs")
                else:
                    print(f"[RAG]   ⚠️  {collection_name}: 0 relevant docs found")
                    search_summary.append(f"{collection_name}: 0 relevant")

            except Exception as e:
                print(f"[RAG]   ❌ {collection_name}: Error - {e}")
                search_summary.append(f"{collection_name}: ERROR")

        # Ensure diversity: Interleave documents from different collections
        # BUT prioritize exact matches first
        from collections import defaultdict
        docs_by_collection = defaultdict(list)
        exact_matches = []
        semantic_docs = []

        # Separate exact matches from semantic matches
        for doc in all_documents:
            if doc.get('match_type') == 'exact':
                exact_matches.append(doc)
            else:
                semantic_docs.append(doc)
                docs_by_collection[doc['collection']].append(doc)

        # Sort exact matches by score (should all be 1.0 but just in case)
        exact_matches.sort(key=lambda x: x['score'], reverse=True)

        # Sort each collection's semantic docs by relevance
        for coll in docs_by_collection:
            docs_by_collection[coll].sort(key=lambda x: x['score'], reverse=True)

        # Interleave semantic documents to ensure diversity
        semantic_interleaved = []
        max_docs = max(len(docs) for docs in docs_by_collection.values()) if docs_by_collection else 0

        for i in range(max_docs):
            for coll_name in sorted(docs_by_collection.keys()):
                if i < len(docs_by_collection[coll_name]):
                    semantic_interleaved.append(docs_by_collection[coll_name][i])

        # Combine: exact matches first, then diverse semantic results
        diverse_documents = exact_matches + semantic_interleaved

        print(f"\n[RAG] {'='*70}")
        print(f"[RAG] SEARCH SUMMARY:")
        for summary in search_summary:
            print(f"[RAG]   - {summary}")
        print(f"[RAG] TOTAL RETRIEVED: {len(diverse_documents)} documents across all collections")
        if exact_matches:
            print(f"[RAG] EXACT MATCHES: {len(exact_matches)} exact match(es) prioritized at top")
        print(f"[RAG] DIVERSE ORDERING: Interleaved from all sources for balanced context")
        print(f"[RAG] {'='*70}\n")

        return diverse_documents

    def ask_claude(self, question, context_documents, website_content=None):
        """
        Ask Claude with context from multiple sources

        Args:
            question: User's question
            context_documents: List of documents from Milvus
            website_content: Optional scraped website content

        Returns:
            Claude's response
        """
        # Build context
        context_parts = []

        # Add website content first if provided
        if website_content:
            context_parts.append(
                f"Website Content (Directly Provided):\n"
                f"Title: {website_content['title']}\n"
                f"URL: {website_content['url']}\n"
                f"Content: {website_content['content'][:2000]}\n"
            )

        # Add Milvus documents
        for i, doc in enumerate(context_documents):
            source_label = f"{doc.get('collection', 'unknown')} - {doc.get('source_type', 'unknown')}"
            context_parts.append(
                f"Document {i+1} [{source_label}] (Relevance: {doc['score']}):\n"
                f"Title: {doc['title']}\n"
                f"Content: {doc['content'][:1000]}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Analyze document sources for context awareness
        collections_present = set(doc.get('collection', '') for doc in context_documents)
        collection_summary = ", ".join(sorted(collections_present)) if collections_present else "unknown"

        # Build prompt
        prompt = f"""You are an expert analyst specializing in technical documentation and enterprise software. Your task is to thoroughly analyze the provided context from MULTIPLE data sources and deliver precise, actionable insights.

CONTEXT SOURCES: You have access to information from: {collection_summary}
This includes: JIRA tickets, codebase analysis, GitHub PRs, developer personas, action logs, and custom notes.

RETRIEVED CONTEXT FROM DATABASE ({len(context_documents)} documents):
{context}

USER QUESTION: {question}

ANALYSIS INSTRUCTIONS:
1. THOROUGHLY ANALYZE ALL CONTEXT:
   - Read and understand EVERY document provided from ALL collections
   - Look for patterns, connections, and related information across different data sources
   - Consider technical details, configurations, requirements, and limitations
   - Identify any conflicting information and resolve it logically
   - Cross-reference information: e.g., JIRA tickets → related code changes → PR discussions

2. MULTI-SOURCE SYNTHESIS:
   - Combine insights from different collections (JIRA + Code + PRs + Logs)
   - Connect related concepts across sources:
     * JIRA ticket issues → code implementation in codebase_analysis
     * Developer personas → their PR contributions
     * Action logs → system behavior patterns
     * Code analysis → related JIRA tickets and requirements
   - Extract both explicit facts and implicit conclusions
   - Consider the full picture across all data sources, not just individual fragments

3. COMPREHENSIVE ANSWER REQUIREMENTS:
   - Be direct and natural - no preambles like "Based on the context"
   - Provide comprehensive, technical answers with specific details from multiple sources
   - Include:
     * JIRA ticket details (ID, status, description, priority)
     * Code implementation details (file paths, functions, classes)
     * PR information (changes, discussions, reviews)
     * Configuration steps, requirements, compatibility info
     * Developer context if relevant
   - Reference specific features, versions, or limitations when available
   - If information is partial, clearly state what's known and what's uncertain

4. QUALITY CHECKS:
   - Does your answer directly address the question?
   - Have you used ALL relevant information from ALL collections provided?
   - Are you being specific (not generic)?
   - Have you connected related information across different sources?
   - Would this answer help someone implement or understand the solution?

5. HANDLING INSUFFICIENT DATA:
   - If context lacks critical information, state what's missing
   - Recommend checking official documentation and resources
   - Use general knowledge to supplement when appropriate
   - Be clear about what comes from context vs. general knowledge

6. CONFIDENCE ASSESSMENT:
   After your answer, provide your confidence level in the answer's accuracy on a new line:
   ANSWER_CONFIDENCE: [score from 0.0 to 1.0]

   Guidelines for answer confidence:
   - 0.9-1.0: Very certain, well-documented in sources or general knowledge
   - 0.7-0.9: Confident, good information available
   - 0.5-0.7: Moderate confidence, some uncertainty
   - 0.3-0.5: Low confidence, limited information
   - 0.0-0.3: Very uncertain, speculative

ANSWER (detailed, technical, actionable, synthesizing ALL sources):"""

        try:
            print("[Claude] Sending request...")
            start_time = time.time()

            message = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,  # Increased for detailed analysis
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_time_ms = int((time.time() - start_time) * 1000)
            answer = message.content[0].text

            # Extract answer confidence if provided
            answer_confidence = None
            if "ANSWER_CONFIDENCE:" in answer:
                try:
                    # Extract confidence score from answer
                    confidence_line = [line for line in answer.split('\n') if 'ANSWER_CONFIDENCE:' in line][0]
                    confidence_str = confidence_line.split('ANSWER_CONFIDENCE:')[1].strip()
                    answer_confidence = float(confidence_str)
                    # Remove confidence line from answer
                    answer = answer.replace(confidence_line, '').strip()
                except:
                    pass

            # Extract token usage from API response
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

            print(f"[Claude] ✓ Received response ({len(answer)} chars)")
            print(f"[Claude] Tokens: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
            if answer_confidence:
                print(f"[Claude] Answer Confidence: {answer_confidence:.2f}")

            # Store token usage info for return
            self._last_usage = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'response_time_ms': response_time_ms,
                'answer_confidence': answer_confidence
            }

            # Append response time to answer
            response_time_seconds = response_time_ms / 1000
            answer += f"\n\n---\n*Responded in {response_time_seconds:.1f} seconds*"

            return answer

        except Exception as e:
            print(f"[Claude] Error: {e}")
            return f"Error communicating with Claude: {str(e)}"

    def calculate_confidence(self, sources, num_documents):
        """
        Calculate confidence score based on source quality and quantity

        Factors:
        - Average relevance score of sources
        - Number of sources found
        - Diversity of source types
        - Presence of high-quality sources (score > 0.8)

        Returns:
            dict with confidence score and breakdown
        """
        if not sources:
            return {
                'score': 0.0,
                'level': 'No Data',
                'factors': {
                    'source_quality': 0.0,
                    'source_quantity': 0.0,
                    'source_diversity': 0.0,
                    'high_quality_sources': 0
                }
            }

        # Factor 1: Average relevance score (40% weight)
        avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
        source_quality = avg_score * 0.4

        # Factor 2: Source quantity (20% weight)
        # Normalize: 1 source = 0%, 10+ sources = 100%
        quantity_factor = min(num_documents / 10.0, 1.0) * 0.2

        # Factor 3: Source diversity (20% weight)
        # Count unique collections/source types
        unique_sources = len(set(s.get('collection', s.get('source_type', '')) for s in sources))
        diversity_factor = min(unique_sources / 3.0, 1.0) * 0.2  # 3+ types = max

        # Factor 4: High-quality sources (20% weight)
        # Count sources with score > 0.8
        high_quality_count = sum(1 for s in sources if s.get('score', 0) > 0.8)
        high_quality_factor = min(high_quality_count / 3.0, 1.0) * 0.2  # 3+ = max

        # Total confidence score
        total_confidence = source_quality + quantity_factor + diversity_factor + high_quality_factor

        # Determine confidence level
        if total_confidence >= 0.8:
            level = 'Very High'
        elif total_confidence >= 0.65:
            level = 'High'
        elif total_confidence >= 0.5:
            level = 'Medium'
        elif total_confidence >= 0.3:
            level = 'Low'
        else:
            level = 'Very Low'

        return {
            'score': round(total_confidence, 3),
            'level': level,
            'factors': {
                'source_quality': round(avg_score, 3),
                'source_quantity': num_documents,
                'source_diversity': unique_sources,
                'high_quality_sources': high_quality_count
            }
        }

    def query_with_context(self, question, collection_name="all", website_url=None, top_k=5):
        """
        Answer question using RAG with optional website scraping

        Args:
            question: User's question
            collection_name: Milvus collection or "all" for all collections
            website_url: Optional website URL to scrape and include
            top_k: Number of documents to retrieve per collection

        Returns:
            dict with answer and sources
        """
        print(f"\n{'='*70}")
        print(f"[Claude RAG] Question: {question}")
        if website_url:
            print(f"[Claude RAG] Website: {website_url}")
        print(f"{'='*70}\n")

        # Scrape website if provided
        website_content = None
        if website_url:
            website_content = self.scrape_website(website_url)
            if not website_content:
                print("[Claude RAG] Warning: Failed to scrape website, continuing with Milvus data...")

        # Increase retrieval for better context - get more documents for analysis
        enhanced_top_k = max(top_k, 7)  # Minimum 7 documents per collection
        print(f"[Claude RAG] Retrieving top {enhanced_top_k} documents per source for better analysis")

        # Search Milvus collections
        if collection_name == "all" or collection_name == "all_collections":
            documents = self.search_all_collections(question, top_k_per_collection=enhanced_top_k)
        else:
            documents = self.search_milvus(question, collection_name, enhanced_top_k)

        # Combine sources
        all_sources = []
        if website_content:
            all_sources.append(website_content)
        all_sources.extend(documents)

        if not all_sources:
            return {
                'answer': "No relevant information found. Please check if Milvus is running or provide a valid website URL.",
                'sources': [],
                'model': 'claude-sonnet-4-5'
            }

        # Get answer from Claude
        answer = self.ask_claude(question, documents, website_content)

        # Calculate source confidence (retrieval quality)
        source_confidence = self.calculate_confidence(all_sources, len(documents))

        # Get answer confidence from Claude's self-assessment
        usage_info = getattr(self, '_last_usage', None)
        answer_confidence_score = usage_info.get('answer_confidence', None) if usage_info else None

        # Determine overall confidence (use answer confidence if available, otherwise source confidence)
        if answer_confidence_score is not None:
            # Use answer confidence as primary, but consider source quality
            overall_score = answer_confidence_score

            # Determine level
            if overall_score >= 0.8:
                overall_level = 'Very High'
            elif overall_score >= 0.65:
                overall_level = 'High'
            elif overall_score >= 0.5:
                overall_level = 'Medium'
            elif overall_score >= 0.3:
                overall_level = 'Low'
            else:
                overall_level = 'Very Low'

            confidence = {
                'score': round(overall_score, 3),
                'level': overall_level,
                'answer_confidence': round(answer_confidence_score, 3),
                'source_confidence': source_confidence,
                'type': 'dual'  # Indicates both scores available
            }
        else:
            # Fall back to source confidence only
            confidence = source_confidence
            confidence['type'] = 'source_only'

        # Track token usage
        tracker = get_tracker()

        if usage_info:
            tracker.track_usage(
                model='claude-sonnet-4-5',
                question=question,
                collection=collection_name,
                input_tokens=usage_info['input_tokens'],
                output_tokens=usage_info['output_tokens'],
                documents_retrieved=len(documents),
                response_time_ms=usage_info['response_time_ms']
            )

        return {
            'answer': answer,
            'sources': all_sources,
            'model': 'claude-sonnet-4-5',
            'website_scraped': website_url if website_content else None,
            'token_usage': usage_info,
            'confidence_score': confidence
        }


def main():
    """Example usage"""
    print("="*70)
    print("CLAUDE RAG SYSTEM - Online AI with Milvus + Website Scraping")
    print("="*70)

    rag = ClaudeRAG()

    # Example 1: Search all collections
    result = rag.query_with_context(
        question="What firewall Docker issues are in development?",
        collection_name="all",
        top_k=3
    )

    print(f"\nQuestion: {result.get('question', 'N/A')}")
    print(f"\nAnswer ({result['model']}):")
    print(result['answer'])
    print(f"\nSources: {len(result['sources'])}")

    # Example 2: With website scraping
    result = rag.query_with_context(
        question="What are the latest features in this documentation?",
        collection_name="all",
        website_url="https://docs.python.org/3/whatsnew/3.13.html",
        top_k=2
    )

    print(f"\n\nQuestion: {result.get('question', 'N/A')}")
    print(f"Website: {result.get('website_scraped', 'N/A')}")
    print(f"\nAnswer ({result['model']}):")
    print(result['answer'])


if __name__ == "__main__":
    main()
