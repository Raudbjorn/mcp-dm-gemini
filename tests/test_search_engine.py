import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from ttrpg_assistant.search_engine.query_processor import QueryProcessor, QuerySuggestion
from ttrpg_assistant.search_engine.hybrid_search import HybridSearchManager, SearchConfig
from ttrpg_assistant.search_engine.enhanced_search_service import EnhancedSearchService
from ttrpg_assistant.data_models.models import ContentChunk, SearchResult, SourceType
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService


class TestQueryProcessor:
    """Test query processing functionality"""
    
    @pytest.fixture
    def mock_chroma_manager(self):
        mock_manager = Mock()
        mock_client = Mock()
        mock_collection = Mock()
        
        # Mock collection results
        mock_collection.get.return_value = {
            'documents': ['armor class rules', 'hit points calculation', 'spell casting'],
            'metadatas': [
                {'title': 'Combat Rules'},
                {'title': 'Character Stats'},
                {'title': 'Magic System'}
            ]
        }
        
        mock_client.get_collection.return_value = mock_collection
        mock_manager.client = mock_client
        
        return mock_manager
    
    @pytest.fixture
    def query_processor(self, mock_chroma_manager):
        return QueryProcessor(mock_chroma_manager)
    
    def test_abbreviation_expansion(self, query_processor):
        """Test that TTRPG abbreviations are expanded correctly"""
        processed_query, suggestions = query_processor.process_query("what is ac")
        
        assert "armor class" in processed_query.lower()
        
        # Should have an abbreviation suggestion
        abbrev_suggestions = [s for s in suggestions if s.suggestion_type == 'abbreviation']
        assert len(abbrev_suggestions) > 0
        assert abbrev_suggestions[0].explanation.startswith("Expanded 'ac'")
    
    def test_spell_check_common_misspellings(self, query_processor):
        """Test spell checking for common TTRPG misspellings"""
        processed_query, suggestions = query_processor.process_query("armour class")
        
        assert "armor class" in processed_query.lower()
        
        # Should have a spelling suggestion
        spelling_suggestions = [s for s in suggestions if s.suggestion_type == 'spelling']
        assert len(spelling_suggestions) > 0
    
    def test_intent_detection(self, query_processor):
        """Test query intent detection"""
        # Test "how to" intent
        processed_query, suggestions = query_processor.process_query("how do I cast spells")
        
        intent_suggestions = [s for s in suggestions if s.suggestion_type == 'intent']
        assert len(intent_suggestions) > 0
        
        # Should suggest alternative phrasings
        suggested_queries = [s.suggested_query for s in intent_suggestions]
        assert any("rules" in sq for sq in suggested_queries)
    
    def test_build_vocabulary(self, query_processor):
        """Test vocabulary building from collections"""
        query_processor.build_vocabulary_from_collections(['test_collection'])
        
        # Should have built vocabulary from mock data
        assert len(query_processor.vocabulary) > 0
        assert 'armor' in query_processor.vocabulary or 'class' in query_processor.vocabulary


class TestHybridSearchManager:
    """Test hybrid search functionality"""
    
    @pytest.fixture
    def mock_chroma_manager(self):
        mock_manager = Mock()
        mock_client = Mock()
        mock_collection = Mock()
        
        # Mock collection data for BM25 indexing
        mock_collection.get.return_value = {
            'documents': [
                'Combat rules for armor class and hit points',
                'Spell casting mechanics and magic points',
                'Character creation and ability scores'
            ],
            'metadatas': [
                {'title': 'Combat', 'rulebook': 'PHB', 'system': 'D&D 5e'},
                {'title': 'Magic', 'rulebook': 'PHB', 'system': 'D&D 5e'},
                {'title': 'Characters', 'rulebook': 'PHB', 'system': 'D&D 5e'}
            ],
            'ids': ['doc1', 'doc2', 'doc3']
        }
        
        mock_client.get_collection.return_value = mock_collection
        mock_manager.client = mock_client
        
        # Mock vector search
        mock_manager.vector_search.return_value = [
            SearchResult(
                content_chunk=ContentChunk(
                    id='doc1',
                    rulebook='PHB',
                    system='D&D 5e',
                    source_type=SourceType.RULEBOOK,
                    content_type='rule',
                    title='Combat Rules',
                    content='Combat rules for armor class and hit points',
                    page_number=1,
                    section_path=['Combat'],
                    embedding=b'',
                    metadata={}
                ),
                relevance_score=0.8,
                match_type='semantic'
            )
        ]
        
        return mock_manager
    
    @pytest.fixture
    def mock_embedding_service(self):
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384  # Mock embedding
        return mock_service
    
    @pytest.fixture
    def hybrid_search(self, mock_chroma_manager, mock_embedding_service):
        return HybridSearchManager(mock_chroma_manager, mock_embedding_service)
    
    def test_query_expansion(self, hybrid_search):
        """Test query expansion with synonyms"""
        expanded_query, metadata = hybrid_search.expand_query("damage rules")
        
        # Should expand with synonyms
        assert "dmg" in expanded_query or "harm" in expanded_query
        assert metadata['intent'] in ['rules', 'general']
        assert 'damage' in metadata.get('focus_terms', [])
    
    @patch('ttrpg_assistant.search_engine.hybrid_search.BM25Okapi')
    def test_index_collection(self, mock_bm25, hybrid_search):
        """Test BM25 index building"""
        hybrid_search.index_collection_for_keyword_search('test_collection')
        
        # Should have created BM25 index
        mock_bm25.assert_called_once()
        assert 'test_collection' in hybrid_search.bm25_indices
        assert 'test_collection' in hybrid_search.document_store
    
    def test_tokenization(self, hybrid_search):
        """Test TTRPG-specific tokenization"""
        tokens = hybrid_search._tokenize_for_search("Cast a 2d6+3 spell for 15 damage")
        
        # Should handle dice notation
        assert 'dice' in tokens
        assert 'd' in tokens  # from 2d6
        assert any('plus' in token for token in tokens)  # Should contain 'plus' somewhere
    
    def test_search_config_determination(self, hybrid_search):
        """Test automatic search configuration based on query"""
        # Short query with game terms should use balanced weights
        config = hybrid_search._determine_search_config("AC rules", None)
        assert config.keyword_weight >= 0.5  # AC is a specific game term
        
        # Conceptual query should favor semantic search
        config = hybrid_search._determine_search_config("how to understand combat", None)
        assert config.semantic_weight > config.keyword_weight


class TestEnhancedSearchService:
    """Test the complete enhanced search service"""
    
    @pytest.fixture
    def mock_chroma_manager(self):
        mock_manager = Mock()
        mock_client = Mock()
        mock_collection = Mock()
        
        mock_collection.get.return_value = {
            'documents': ['test document'],
            'metadatas': [{'title': 'Test'}],
            'ids': ['test1']
        }
        
        mock_client.get_collection.return_value = mock_collection
        mock_manager.client = mock_client
        mock_manager.vector_search.return_value = []
        
        return mock_manager
    
    @pytest.fixture
    def mock_embedding_service(self):
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384
        return mock_service
    
    @pytest.fixture
    def search_service(self, mock_chroma_manager, mock_embedding_service):
        return EnhancedSearchService(mock_chroma_manager, mock_embedding_service)
    
    @pytest.mark.asyncio
    async def test_initialization(self, search_service):
        """Test search service initialization"""
        await search_service.initialize(['test_collection'])
        
        assert search_service._initialized
        assert len(search_service.query_processor.vocabulary) >= 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_search(self, search_service):
        """Test the main search functionality"""
        await search_service.initialize()
        
        results, suggestions = await search_service.search(
            query="armor class rules",
            max_results=5,
            use_hybrid=True
        )
        
        # Should return results and suggestions
        assert isinstance(results, list)
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_quick_search(self, search_service):
        """Test quick search functionality"""
        await search_service.initialize()
        
        results = await search_service.quick_search("AC", max_results=3)
        
        assert isinstance(results, list)
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_suggest_completions(self, search_service):
        """Test query completion suggestions"""
        await search_service.initialize()
        
        completions = await search_service.suggest_completions("arm", limit=5)
        
        assert isinstance(completions, list)
        assert len(completions) <= 5
    
    @pytest.mark.asyncio
    async def test_explain_search_results(self, search_service):
        """Test search result explanation"""
        await search_service.initialize()
        
        # Create mock results
        mock_results = [
            SearchResult(
                content_chunk=ContentChunk(
                    id='test1',
                    rulebook='PHB',
                    system='D&D 5e',
                    source_type=SourceType.RULEBOOK,
                    content_type='rule',
                    title='Armor Class',
                    content='Rules for armor class calculation',
                    page_number=10,
                    section_path=['Combat'],
                    embedding=b'',
                    metadata={}
                ),
                relevance_score=0.9,
                match_type='hybrid'
            )
        ]
        
        explanation = await search_service.explain_search_results("armor class", mock_results)
        
        assert 'original_query' in explanation
        assert 'search_stats' in explanation
        assert 'result_analysis' in explanation
        assert explanation['search_stats']['total_results'] == 1
    
    def test_get_search_statistics(self, search_service):
        """Test search statistics retrieval"""
        stats = search_service.get_search_statistics()
        
        assert 'initialized' in stats
        assert 'vocabulary_size' in stats
        assert 'indexed_collections' in stats
        assert 'total_documents_indexed' in stats


class TestSearchIntegration:
    """Integration tests for the complete search system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_flow(self):
        """Test complete search flow from query to results"""
        # Mock all dependencies
        mock_chroma = Mock()
        mock_embedding = Mock()
        
        # Setup mock responses
        mock_chroma.client.get_collection.return_value.get.return_value = {
            'documents': ['Armor class determines how hard it is to hit you'],
            'metadatas': [{'title': 'Combat Rules', 'rulebook': 'PHB'}],
            'ids': ['combat_1']
        }
        
        mock_embedding.generate_embedding.return_value = [0.1] * 384
        
        mock_chroma.vector_search.return_value = [
            SearchResult(
                content_chunk=ContentChunk(
                    id='combat_1',
                    rulebook='PHB',
                    system='D&D 5e',
                    source_type=SourceType.RULEBOOK,
                    content_type='rule',
                    title='Combat Rules',
                    content='Armor class determines how hard it is to hit you',
                    page_number=1,
                    section_path=['Combat'],
                    embedding=b'',
                    metadata={}
                ),
                relevance_score=0.85,
                match_type='semantic'
            )
        ]
        
        # Create service and test
        service = EnhancedSearchService(mock_chroma, mock_embedding)
        await service.initialize()
        
        results, suggestions = await service.search("what is ac")
        
        # Verify results
        assert len(results) > 0
        assert results[0].content_chunk.title == 'Combat Rules'
        
        # Verify suggestions (should expand "ac" to "armor class")
        abbrev_suggestions = [s for s in suggestions if s.suggestion_type == 'abbreviation']
        assert len(abbrev_suggestions) > 0