#!/usr/bin/env python3
"""
Ollama RAG (Retrieval Augmented Generation) Integration
Offline AI reasoning with Milvus vector search
"""

import requests
import json
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility


class OllamaRAG:
    def __init__(self, ollama_host="http://localhost:11434", model_name="llama3.2"):
        """
        Initialize Ollama RAG system

        Args:
            ollama_host: Ollama API endpoint
            model_name: Ollama model to use (e.g., 'llama3.2', 'deepseek-r1', 'qwen2.5')
        """
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.embedding_model = None
        self.milvus_host = "localhost"
        self.milvus_port = "19530"

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

    def search_milvus(self, query, collection_name="jira_tickets", top_k=5):
        """
        Search Milvus for relevant documents

        Args:
            query: User's search query
            collection_name: Milvus collection to search
            top_k: Number of results to return

        Returns:
            List of relevant documents
        """
        if not self.connect_milvus():
            return []

        if not utility.has_collection(collection_name):
            print(f"Collection {collection_name} does not exist")
            return []

        try:
            # Load model and generate embedding
            model = self.load_embedding_model()
            query_embedding = model.encode([query]).tolist()

            # Load collection and search
            collection = Collection(name=collection_name)
            collection.load()

            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["source_type", "source_id", "title", "content", "metadata", "url"]
            )

            # Format results
            documents = []
            for hits in results:
                for hit in hits:
                    documents.append({
                        'title': hit.entity.get('title', ''),
                        'content': hit.entity.get('content', ''),
                        'source_id': hit.entity.get('source_id', ''),
                        'source_type': hit.entity.get('source_type', ''),
                        'url': hit.entity.get('url', ''),
                        'score': round(1 / (1 + hit.distance), 4),
                        'collection': collection_name
                    })

            collection.release()
            return documents

        except Exception as e:
            print(f"Error searching Milvus: {e}")
            return []

    def search_all_collections(self, query, top_k_per_collection=3):
        """
        Search across ALL collections for comprehensive context

        Args:
            query: User's search query
            top_k_per_collection: Number of results per collection

        Returns:
            List of relevant documents from all sources
        """
        if not self.connect_milvus():
            print("[RAG] ❌ Failed to connect to Milvus")
            return []

        # Get all available collections
        all_collections = utility.list_collections()
        print(f"\n[RAG] 🔍 Searching {len(all_collections)} collections: {all_collections}")
        print(f"[RAG] Retrieving top {top_k_per_collection} documents per collection\n")

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
                continue

        # Ensure diversity: Interleave documents from different collections
        # Group documents by collection
        from collections import defaultdict
        docs_by_collection = defaultdict(list)
        for doc in all_documents:
            docs_by_collection[doc['collection']].append(doc)

        # Sort each collection's docs by relevance
        for coll in docs_by_collection:
            docs_by_collection[coll].sort(key=lambda x: x['score'], reverse=True)

        # Interleave documents to ensure diversity
        diverse_documents = []
        max_docs = max(len(docs) for docs in docs_by_collection.values()) if docs_by_collection else 0

        for i in range(max_docs):
            for coll_name in sorted(docs_by_collection.keys()):
                if i < len(docs_by_collection[coll_name]):
                    diverse_documents.append(docs_by_collection[coll_name][i])

        print(f"\n[RAG] {'='*70}")
        print(f"[RAG] SEARCH SUMMARY:")
        for summary in search_summary:
            print(f"[RAG]   - {summary}")
        print(f"[RAG] TOTAL RETRIEVED: {len(diverse_documents)} documents across all collections")
        print(f"[RAG] DIVERSE ORDERING: Interleaved from all sources for balanced context")
        print(f"[RAG] {'='*70}\n")

        return diverse_documents

    def ask_ollama(self, prompt, stream=False):
        """
        Send prompt to Ollama for reasoning

        Args:
            prompt: The prompt to send
            stream: Whether to stream the response

        Returns:
            Response from Ollama
        """
        url = f"{self.ollama_host}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            if stream:
                # Return generator for streaming
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        yield data.get('response', '')
            else:
                data = response.json()
                return data.get('response', 'No response from Ollama')

        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)"
        except Exception as e:
            return f"Error: {str(e)}"

    def calculate_confidence(self, sources, num_documents):
        """
        Calculate confidence score based on source quality and quantity

        Returns:
            dict with confidence score and breakdown
        """
        if not sources:
            return {
                'score': 0.0,
                'level': 'No Data',
                'factors': {
                    'source_quality': 0.0,
                    'source_quantity': 0,
                    'source_diversity': 0,
                    'high_quality_sources': 0
                }
            }

        # Factor 1: Average relevance score (40% weight)
        avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
        source_quality = avg_score * 0.4

        # Factor 2: Source quantity (20% weight)
        quantity_factor = min(num_documents / 10.0, 1.0) * 0.2

        # Factor 3: Source diversity (20% weight)
        unique_sources = len(set(s.get('collection', '') for s in sources))
        diversity_factor = min(unique_sources / 3.0, 1.0) * 0.2

        # Factor 4: High-quality sources (20% weight)
        high_quality_count = sum(1 for s in sources if s.get('score', 0) > 0.8)
        high_quality_factor = min(high_quality_count / 3.0, 1.0) * 0.2

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

    def query_with_context(self, question, collection_name="jira_tickets", top_k=3):
        """
        Answer question using RAG (Retrieval Augmented Generation)

        Args:
            question: User's question
            collection_name: Milvus collection to search (use "all" for all collections)
            top_k: Number of documents to retrieve

        Returns:
            dict with answer and sources
        """
        print(f"\n[RAG] Question: {question}")

        # Increase retrieval for better analysis
        enhanced_top_k = max(top_k, 7)  # Minimum 7 documents per collection
        print(f"[RAG] Enhanced retrieval: {enhanced_top_k} documents per source")

        # Step 1: Retrieve relevant documents
        if collection_name == "all" or collection_name == "all_collections":
            print(f"[RAG] Searching ALL collections...")
            documents = self.search_all_collections(question, top_k_per_collection=enhanced_top_k)
        else:
            print(f"[RAG] Searching {collection_name}...")
            documents = self.search_milvus(question, collection_name, enhanced_top_k)

        if not documents:
            return {
                'answer': "No relevant information found in the database. Please check if Milvus is running and contains data.",
                'sources': []
            }

        print(f"[RAG] Found {len(documents)} relevant documents")

        # Step 2: Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(documents):
            source_label = f"{doc.get('collection', 'unknown')} - {doc.get('source_type', 'unknown')}"
            context_parts.append(
                f"Document {i+1} [{source_label}] (Relevance: {doc['score']}):\n"
                f"Title: {doc['title']}\n"
                f"Content: {doc['content'][:1000]}"
            )
        context = "\n\n".join(context_parts)

        # Step 3: Build prompt for Ollama
        prompt = f"""You are an expert analyst. Thoroughly analyze the provided context and deliver precise insights.

RETRIEVED CONTEXT:
{context}

USER QUESTION: {question}

ANALYSIS INSTRUCTIONS:
1. Read and understand ALL documents carefully
2. Look for patterns and connections across documents
3. Extract technical details, configurations, requirements, limitations
4. Synthesize information from multiple sources
5. Be direct - no preambles like "Based on the context"
6. Provide comprehensive, technical, actionable answers
7. Reference specific features, versions, or compatibility info
8. If information is partial, state what's known and what's missing
9. If information is insufficient, suggest checking official documentation

10. CONFIDENCE ASSESSMENT:
   After your answer, provide your confidence level in the answer's accuracy on a new line:
   ANSWER_CONFIDENCE: [score from 0.0 to 1.0]

   Guidelines:
   - 0.9-1.0: Very certain, well-documented
   - 0.7-0.9: Confident, good information
   - 0.5-0.7: Moderate confidence
   - 0.3-0.5: Low confidence
   - 0.0-0.3: Very uncertain

ANSWER (detailed and technical):"""

        print("[RAG] Sending to Ollama for reasoning...")

        # Step 4: Get answer from Ollama
        answer = self.ask_ollama(prompt, stream=False)

        # Extract answer confidence if provided
        answer_confidence_score = None
        if "ANSWER_CONFIDENCE:" in answer:
            try:
                confidence_line = [line for line in answer.split('\n') if 'ANSWER_CONFIDENCE:' in line][0]
                confidence_str = confidence_line.split('ANSWER_CONFIDENCE:')[1].strip()
                answer_confidence_score = float(confidence_str)
                answer = answer.replace(confidence_line, '').strip()
                print(f"[RAG] Answer Confidence: {answer_confidence_score:.2f}")
            except:
                pass

        # Calculate source confidence (retrieval quality)
        source_confidence = self.calculate_confidence(documents, len(documents))

        # Determine overall confidence
        if answer_confidence_score is not None:
            overall_score = answer_confidence_score

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
                'type': 'dual'
            }
        else:
            confidence = source_confidence
            confidence['type'] = 'source_only'

        return {
            'answer': answer,
            'sources': documents,
            'model': self.model_name,
            'confidence_score': confidence
        }

    def check_ollama_status(self):
        """Check if Ollama is running and available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return True, [m['name'] for m in models]
            return False, []
        except:
            return False, []


def main():
    """Example usage"""
    print("="*70)
    print("OLLAMA RAG SYSTEM - Offline AI with Milvus")
    print("="*70)

    # Initialize
    rag = OllamaRAG(model_name="llama3.2")  # Change to your preferred model

    # Check Ollama status
    print("\nChecking Ollama status...")
    is_running, models = rag.check_ollama_status()

    if not is_running:
        print("❌ Ollama is not running!")
        print("\nTo start Ollama:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Run: ollama serve")
        print("  3. Pull a model: ollama pull llama3.2")
        return

    print(f"✓ Ollama is running!")
    print(f"  Available models: {', '.join(models)}")

    # Example questions
    questions = [
        "What are the firewall issues related to Docker?",
        "Tell me about feature flags and authorization",
        "What security training tasks were completed?"
    ]

    for question in questions:
        print("\n" + "="*70)
        result = rag.query_with_context(question, collection_name="jira_tickets", top_k=3)

        print(f"\nQuestion: {question}")
        print(f"\nAnswer ({result['model']}):")
        print(result['answer'])

        print(f"\nSources ({len(result['sources'])} documents):")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source['title']} (Score: {source['score']})")
            print(f"     URL: {source['url']}")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
