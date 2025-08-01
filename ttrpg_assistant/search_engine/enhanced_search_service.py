from typing import List, Dict, Any, Optional, Tuple
import asyncio

from ttrpg_assistant.data_models.models import SearchResult, SourceType
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from .query_processor import QueryProcessor, QuerySuggestion
from .hybrid_search import HybridSearchManager, SearchConfig
from ttrpg_assistant.logger import logger


class EnhancedSearchService:
    """Comprehensive search service combining query processing and hybrid search"""
    
    def __init__(self, chroma_manager: ChromaDataManager, embedding_service: EmbeddingService):
        self.chroma_manager = chroma_manager
        self.embedding_service = embedding_service
        
        # Initialize components
        self.query_processor = QueryProcessor(chroma_manager)
        self.hybrid_search = HybridSearchManager(chroma_manager, embedding_service)
        
        # Initialize vocabulary and indices
        self._initialized = False
    
    async def initialize(self, collection_names: Optional[List[str]] = None):
        """Initialize the search service with vocabulary and indices"""
        if self._initialized:
            return
        
        if collection_names is None:
            collection_names = ["rulebook_index"]  # Default collection
        
        logger.info("Initializing enhanced search service...")
        
        # Build vocabulary for query processing
        self.query_processor.build_vocabulary_from_collections(collection_names)
        
        # Build BM25 indices for hybrid search
        for collection_name in collection_names:
            self.hybrid_search.index_collection_for_keyword_search(collection_name)
        
        self._initialized = True
        logger.info("Enhanced search service initialized successfully")
    
    async def search(self, 
                    query: str,
                    rulebook: Optional[str] = None,
                    source_type: Optional[SourceType] = None,
                    content_type: Optional[str] = None,
                    max_results: int = 5,
                    context: Optional[Dict[str, Any]] = None,
                    use_hybrid: bool = True) -> Tuple[List[SearchResult], List[QuerySuggestion]]:
        """
        Comprehensive search with query processing and multiple search strategies
        
        Returns:
            Tuple of (search_results, query_suggestions)
        """
        # Ensure service is initialized
        if not self._initialized:
            await self.initialize()
        
        # Process the query
        processed_query, query_suggestions = self.query_processor.process_query(query, context)
        
        # Build filters
        filters = {}
        if rulebook:
            filters["rulebook"] = rulebook
        if source_type:
            filters["source_type"] = source_type.value if hasattr(source_type, 'value') else str(source_type)
        if content_type:
            filters["content_type"] = content_type
        
        # Perform search
        if use_hybrid:
            # Use hybrid search for best results
            config = SearchConfig(max_results=max_results)
            search_results = self.hybrid_search.smart_search(
                collection_name="rulebook_index",
                query=processed_query,
                context=context,
                filters=filters if filters else None
            )
        else:
            # Use traditional semantic search
            import numpy as np
            query_embedding = np.array(self.embedding_service.generate_embedding(processed_query))
            search_results = self.chroma_manager.vector_search(
                index_name="rulebook_index",
                query_embedding=query_embedding,
                num_results=max_results,
                filters=filters if filters else None
            )
        
        # Generate additional suggestions based on search results
        related_suggestions = self.query_processor.suggest_related_queries(query, search_results)
        all_suggestions = query_suggestions + related_suggestions
        
        # Remove duplicate suggestions
        unique_suggestions = []
        seen_queries = set()
        for suggestion in all_suggestions:
            if suggestion.suggested_query not in seen_queries:
                unique_suggestions.append(suggestion)
                seen_queries.add(suggestion.suggested_query)
        
        logger.info(f"Enhanced search for '{query}' returned {len(search_results)} results and {len(unique_suggestions)} suggestions")
        
        return search_results, unique_suggestions
    
    async def quick_search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Quick search without query processing for simple lookups"""
        if not self._initialized:
            await self.initialize()
        
        return self.hybrid_search.smart_search(
            collection_name="rulebook_index",
            query=query,
            context=None
        )[:max_results]
    
    async def suggest_completions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Suggest query completions based on vocabulary and common patterns"""
        if not self._initialized:
            await self.initialize()
        
        suggestions = []
        partial_lower = partial_query.lower().strip()
        
        if len(partial_lower) < 2:
            return suggestions
        
        # Find matching terms in vocabulary
        matching_terms = []
        for term in self.query_processor.vocabulary:
            if term.startswith(partial_lower):
                matching_terms.append(term)
        
        # Sort by frequency and take top matches
        freq_sorted = sorted(matching_terms, 
                           key=lambda t: self.query_processor.term_frequencies.get(t, 0), 
                           reverse=True)
        
        # Add high-frequency matches
        for term in freq_sorted[:limit]:
            if term not in suggestions:
                suggestions.append(term)
        
        # Add common TTRPG terms that match
        for abbrev, expansion in self.query_processor.abbreviations.items():
            if abbrev.startswith(partial_lower) or expansion.startswith(partial_lower):
                completion = expansion if abbrev.startswith(partial_lower) else abbrev
                if completion not in suggestions and len(suggestions) < limit:
                    suggestions.append(completion)
        
        return suggestions[:limit]
    
    async def explain_search_results(self, query: str, results: List[SearchResult]) -> Dict[str, Any]:
        """Provide explanation of why certain results were returned"""
        explanation = {
            "original_query": query,
            "processed_query": None,
            "search_strategy": "hybrid",
            "result_analysis": [],
            "search_stats": {
                "total_results": len(results),
                "avg_score": 0.0,
                "score_distribution": {"high": 0, "medium": 0, "low": 0}
            }
        }
        
        if not results:
            explanation["message"] = "No results found. Try a broader search or different terms."
            return explanation
        
        # Process query to show what happened
        processed_query, suggestions = self.query_processor.process_query(query)
        explanation["processed_query"] = processed_query
        
        # Analyze results
        scores = [r.relevance_score for r in results]
        explanation["search_stats"]["avg_score"] = sum(scores) / len(scores)
        
        for score in scores:
            if score >= 0.7:
                explanation["search_stats"]["score_distribution"]["high"] += 1
            elif score >= 0.4:
                explanation["search_stats"]["score_distribution"]["medium"] += 1
            else:
                explanation["search_stats"]["score_distribution"]["low"] += 1
        
        # Analyze top results
        for i, result in enumerate(results[:3]):
            analysis = {
                "rank": i + 1,
                "title": result.content_chunk.title,
                "score": result.relevance_score,
                "match_type": result.match_type,
                "relevance_factors": []
            }
            
            # Identify why this result was relevant
            chunk = result.content_chunk
            query_terms = set(processed_query.lower().split())
            
            # Check for title matches
            title_words = set(chunk.title.lower().split())
            title_matches = query_terms.intersection(title_words)
            if title_matches:
                analysis["relevance_factors"].append(f"Title contains: {', '.join(title_matches)}")
            
            # Check for content type relevance
            if chunk.content_type in ['rule', 'definition', 'stat_block']:
                analysis["relevance_factors"].append(f"Relevant content type: {chunk.content_type}")
            
            # Check for system/rulebook match
            if chunk.system or chunk.rulebook:
                analysis["relevance_factors"].append(f"From {chunk.rulebook} ({chunk.system})")
            
            explanation["result_analysis"].append(analysis)
        
        return explanation
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about the search service"""
        stats = {
            "initialized": self._initialized,
            "vocabulary_size": len(self.query_processor.vocabulary),
            "indexed_collections": list(self.hybrid_search.bm25_indices.keys()),
            "total_documents_indexed": sum(
                len(docs) for docs in self.hybrid_search.document_store.values()
            )
        }
        
        return stats