import chromadb
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
import re
from collections import defaultdict

from ttrpg_assistant.data_models.models import ContentChunk, SearchResult
from ttrpg_assistant.logger import logger


@dataclass
class SearchConfig:
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    min_score_threshold: float = 0.1
    max_results: int = 50
    enable_reranking: bool = True


class HybridSearchManager:
    """Enhanced search with semantic + keyword matching + query understanding"""
    
    def __init__(self, chroma_manager, embedding_service=None):
        self.chroma = chroma_manager
        self.embedding_service = embedding_service
        
        # BM25 for keyword search
        self.bm25_indices = {}  # collection_name -> BM25Okapi
        self.document_store = {}  # collection_name -> List[Dict]
        
        # Query expansion and understanding
        self.rule_synonyms = self._build_rule_synonyms()
        self.query_patterns = self._build_query_patterns()
    
    def index_collection_for_keyword_search(self, collection_name: str):
        """Build BM25 index for a collection"""
        try:
            collection = self.chroma.client.get_collection(collection_name)
            results = collection.get()
            
            documents = results['documents']
            metadatas = results['metadatas']
            ids = results['ids']
            
            # Prepare documents for BM25
            processed_docs = []
            doc_metadata = []
            
            for i, doc in enumerate(documents):
                # Combine document text with searchable metadata
                metadata = metadatas[i] if metadatas else {}
                searchable_text = doc
                
                # Add title and other searchable fields
                if metadata.get('title'):
                    searchable_text = f"{metadata['title']} {searchable_text}"
                
                # Tokenize for BM25
                tokens = self._tokenize_for_search(searchable_text)
                processed_docs.append(tokens)
                
                doc_metadata.append({
                    'id': ids[i],
                    'original_text': doc,
                    'metadata': metadata
                })
            
            # Build BM25 index
            if processed_docs:
                self.bm25_indices[collection_name] = BM25Okapi(processed_docs)
                self.document_store[collection_name] = doc_metadata
                logger.info(f"Built BM25 index for collection '{collection_name}' with {len(processed_docs)} documents")
            
        except Exception as e:
            logger.error(f"Error building BM25 index for '{collection_name}': {e}")
    
    def _tokenize_for_search(self, text: str) -> List[str]:
        """Enhanced tokenization for TTRPG content"""
        # Convert to lowercase and split on various delimiters
        text = text.lower()
        
        # Handle special TTRPG notation (dice, stats, etc.)
        text = re.sub(r'(\d+)d(\d+)', r'\1 d \2 dice roll', text)  # 2d6 -> 2 d 6 dice roll
        text = re.sub(r'\+(\d+)', r'plus \1', text)  # +3 -> plus 3
        text = re.sub(r'-(\d+)', r'minus \1', text)  # -2 -> minus 2
        
        # Split on punctuation and whitespace
        tokens = re.findall(r'\b\w+\b', text)
        
        # Add n-grams for important phrases
        tokens.extend(self._extract_ngrams(tokens, n=2))
        
        return tokens
    
    def _extract_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Extract n-grams from tokens"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = '_'.join(tokens[i:i+n])
            ngrams.append(ngram)
        return ngrams
    
    def _build_rule_synonyms(self) -> Dict[str, List[str]]:
        """Build synonyms for common TTRPG terms"""
        return {
            'damage': ['dmg', 'harm', 'injury', 'hurt'],
            'armor': ['ac', 'armor_class', 'defence', 'defense'],
            'spell': ['magic', 'cantrip', 'incantation', 'ritual'],
            'weapon': ['sword', 'bow', 'staff', 'blade', 'gun'],
            'monster': ['creature', 'enemy', 'foe', 'beast', 'npc'],
            'character': ['pc', 'player_character', 'hero', 'protagonist'],
            'skill': ['ability', 'proficiency', 'talent'],
            'save': ['saving_throw', 'resistance', 'check'],
            'roll': ['dice', 'check', 'test', 'throw'],
            'level': ['lvl', 'tier', 'rank'],
            'class': ['job', 'profession', 'archetype'],
            'race': ['species', 'ancestry', 'heritage'],
            'hp': ['health', 'hit_points', 'life', 'vitality'],
            'mp': ['mana', 'magic_points', 'spell_points']
        }
    
    def _build_query_patterns(self) -> Dict[str, str]:
        """Patterns to understand query intent"""
        patterns = {
            r'how\s+(?:do|does|can)\s+i\s+(\w+)': 'instruction',  # "how do I cast"
            r'what\s+(?:is|are)\s+(?:the\s+)?(\w+)': 'definition',  # "what is armor class"
            r'(\w+)\s+(?:rules?|mechanics?)': 'rules',  # "combat rules"
            r'(\w+)\s+(?:stats?|statistics?)': 'stats',  # "monster stats"
            r'list\s+(?:of\s+)?(\w+)': 'list',  # "list of spells"
            r'(\d+d\d+|\d+\+\d+)': 'dice_mechanics'  # dice rolls
        }
        return {pattern: intent for pattern, intent in patterns.items()}
    
    def expand_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Expand query with synonyms and extract intent"""
        expanded_terms = []
        original_terms = query.lower().split()
        query_metadata = {'intent': 'general', 'focus_terms': []}
        
        # Detect query intent
        for pattern, intent in self.query_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                query_metadata['intent'] = intent
                break
        
        # Expand with synonyms
        for term in original_terms:
            expanded_terms.append(term)
            if term in self.rule_synonyms:
                expanded_terms.extend(self.rule_synonyms[term])
                query_metadata['focus_terms'].append(term)
        
        # Create expanded query
        expanded_query = ' '.join(expanded_terms)
        
        logger.debug(f"Expanded query: '{query}' -> '{expanded_query}' with metadata: {query_metadata}")
        return expanded_query, query_metadata
    
    def hybrid_search(self, collection_name: str, query: str, 
                     config: Optional[SearchConfig] = None,
                     filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform hybrid semantic + keyword search"""
        if config is None:
            config = SearchConfig()
        
        # Expand query
        expanded_query, query_metadata = self.expand_query(query)
        
        # Semantic search
        semantic_results = self._semantic_search(collection_name, expanded_query, config.max_results, filters)
        
        # Keyword search
        keyword_results = self._keyword_search(collection_name, expanded_query, config.max_results)
        
        # Combine and rerank results
        combined_results = self._combine_results(
            semantic_results, keyword_results, config, query_metadata
        )
        
        # Apply minimum score threshold
        filtered_results = [
            result for result in combined_results 
            if result.relevance_score >= config.min_score_threshold
        ]
        
        logger.info(f"Hybrid search for '{query}' returned {len(filtered_results)} results")
        return filtered_results[:config.max_results]
    
    def _semantic_search(self, collection_name: str, query: str, max_results: int, 
                        filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform semantic search using ChromaDB"""
        try:
            if self.embedding_service:
                # Use embedding service to generate query embedding
                query_embedding = np.array(self.embedding_service.generate_embedding(query))
                return self.chroma.vector_search(
                    index_name=collection_name,
                    query_embedding=query_embedding,
                    num_results=max_results,
                    filters=filters
                )
            else:
                # Use ChromaDB's built-in embedding
                return self.chroma.vector_search(
                    index_name=collection_name,
                    query_text=query,
                    num_results=max_results,
                    filters=filters
                )
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def _keyword_search(self, collection_name: str, query: str, max_results: int) -> List[SearchResult]:
        """Perform keyword search using BM25"""
        if collection_name not in self.bm25_indices:
            logger.warning(f"No BM25 index for collection '{collection_name}'. Building now...")
            self.index_collection_for_keyword_search(collection_name)
        
        if collection_name not in self.bm25_indices:
            return []
        
        try:
            bm25 = self.bm25_indices[collection_name]
            doc_store = self.document_store[collection_name]
            
            # Tokenize query
            query_tokens = self._tokenize_for_search(query)
            
            # Get BM25 scores
            scores = bm25.get_scores(query_tokens)
            
            # Sort by score and get top results
            scored_docs = [(i, score) for i, score in enumerate(scores)]
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, (doc_idx, score) in enumerate(scored_docs[:max_results]):
                if score > 0:  # Only include documents with positive scores
                    doc_info = doc_store[doc_idx]
                    
                    # Convert to ContentChunk and SearchResult
                    metadata = doc_info['metadata']
                    content_chunk = ContentChunk(
                        id=doc_info['id'],
                        rulebook=metadata.get('rulebook', ''),
                        system=metadata.get('system', ''),
                        source_type=metadata.get('source_type', ''),
                        content_type=metadata.get('content_type', ''),
                        title=metadata.get('title', ''),
                        content=doc_info['original_text'],
                        page_number=metadata.get('page_number', 0),
                        section_path=metadata.get('section_path', []),
                        embedding=b"",
                        metadata={}
                    )
                    
                    # Normalize BM25 score to 0-1 range
                    normalized_score = min(score / 10.0, 1.0)
                    
                    results.append(SearchResult(
                        content_chunk=content_chunk,
                        relevance_score=normalized_score,
                        match_type="keyword"
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    def _combine_results(self, semantic_results: List[SearchResult], 
                        keyword_results: List[SearchResult],
                        config: SearchConfig,
                        query_metadata: Dict[str, Any]) -> List[SearchResult]:
        """Combine and rerank semantic and keyword results"""
        
        # Create a map of results by document ID
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            doc_id = result.content_chunk.id
            result_map[doc_id] = {
                'result': result,
                'semantic_score': result.relevance_score,
                'keyword_score': 0.0
            }
        
        # Add/update with keyword results
        for result in keyword_results:
            doc_id = result.content_chunk.id
            if doc_id in result_map:
                result_map[doc_id]['keyword_score'] = result.relevance_score
            else:
                result_map[doc_id] = {
                    'result': result,
                    'semantic_score': 0.0,
                    'keyword_score': result.relevance_score
                }
        
        # Calculate combined scores
        combined_results = []
        for doc_id, data in result_map.items():
            semantic_score = data['semantic_score']
            keyword_score = data['keyword_score']
            
            # Weighted combination
            combined_score = (
                config.semantic_weight * semantic_score + 
                config.keyword_weight * keyword_score
            )
            
            # Apply query-specific boosts
            combined_score = self._apply_query_boosts(
                combined_score, data['result'], query_metadata
            )
            
            # Create new SearchResult with combined score
            new_result = SearchResult(
                content_chunk=data['result'].content_chunk,
                relevance_score=combined_score,
                match_type="hybrid"
            )
            
            combined_results.append(new_result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return combined_results
    
    def _apply_query_boosts(self, base_score: float, result: SearchResult, 
                           query_metadata: Dict[str, Any]) -> float:
        """Apply query-specific score boosts"""
        boosted_score = base_score
        
        # Boost based on query intent
        intent = query_metadata.get('intent', 'general')
        chunk = result.content_chunk
        
        if intent == 'rules' and 'rule' in chunk.title.lower():
            boosted_score *= 1.2
        elif intent == 'stats' and any(term in chunk.content.lower() 
                                     for term in ['hp', 'ac', 'str', 'dex', 'con']):
            boosted_score *= 1.2
        elif intent == 'definition' and chunk.content_type == 'definition':
            boosted_score *= 1.3
        
        # Boost for exact title matches
        focus_terms = query_metadata.get('focus_terms', [])
        for term in focus_terms:
            if term.lower() in chunk.title.lower():
                boosted_score *= 1.1
        
        # Page number boost (earlier pages often have more fundamental rules)
        if chunk.page_number <= 50:
            boosted_score *= 1.05
        
        return min(boosted_score, 1.0)  # Cap at 1.0
    
    def smart_search(self, collection_name: str, query: str, 
                    context: Optional[Dict[str, Any]] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """High-level search that automatically adjusts strategy based on query"""
        
        # Determine search strategy based on query characteristics
        config = self._determine_search_config(query, context)
        
        # Perform hybrid search
        return self.hybrid_search(collection_name, query, config, filters)
    
    def _determine_search_config(self, query: str, context: Optional[Dict[str, Any]]) -> SearchConfig:
        """Automatically determine best search configuration"""
        config = SearchConfig()
        
        # Short queries benefit more from keyword search
        if len(query.split()) <= 3:
            config.semantic_weight = 0.4
            config.keyword_weight = 0.6
        
        # Specific game terms benefit from keyword search
        if any(term in query.lower() for term in ['d20', 'ac', 'hp', 'spell slot']):
            config.keyword_weight = 0.5
            config.semantic_weight = 0.5
        
        # Conceptual queries benefit from semantic search
        if any(word in query.lower() for word in ['how', 'why', 'explain', 'understand']):
            config.semantic_weight = 0.8
            config.keyword_weight = 0.2
        
        # Adjust based on context (e.g., current game session, rulebook)
        if context and context.get('current_rulebook'):
            config.max_results = 20  # More focused search
        
        return config