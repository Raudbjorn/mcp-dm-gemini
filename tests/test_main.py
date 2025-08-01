import pytest
from unittest.mock import patch, MagicMock
from main import search, add_source, generate_map, get_rulebook_personality, get_character_creation_rules, generate_backstory, generate_npc, manage_session, create_content_pack, install_content_pack
from ttrpg_assistant.data_models.models import SearchResult, ContentChunk

@pytest.mark.asyncio
@patch('main.redis_manager')
@patch('ttrpg_assistant.embedding_service.embedding.EmbeddingService')
async def test_search_tool(MockEmbeddingService, mock_redis_manager):
    """Test the 'search' tool."""
    mock_embedding_service_instance = MockEmbeddingService.return_value
    mock_embedding_service_instance.generate_embedding.return_value = [0.1] * 384
    mock_redis_manager.vector_search.return_value = [
        SearchResult(
            content_chunk=ContentChunk(
                id="1", rulebook="test", system="test", content_type="rule",
                title="Test Rule", content="This is a test.", page_number=1,
                section_path=[], embedding=b'', metadata={}
            ),
            relevance_score=0.9, match_type="semantic"
        )
    ]

    result = await search(query="test")
    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["content_chunk"]["title"] == "Test Rule"

@pytest.mark.asyncio
@patch('main.redis_manager')
@patch('main.pdf_parser')
async def test_add_source_tool(mock_pdf_parser, mock_redis_manager):
    """Test the 'add_source' tool."""
    mock_pdf_parser.create_chunks.return_value = [{"id": "1"}]
    mock_pdf_parser.extract_personality_text.return_value = "personality"

    result = await add_source(pdf_path="dummy.pdf", rulebook_name="Test Book", system="Test")
    assert result["status"] == "success"
    mock_redis_manager.store_rulebook_content.assert_called_once()
    mock_redis_manager.store_rulebook_personality.assert_called_once_with("Test Book", "personality")

@pytest.mark.asyncio
async def test_generate_map_tool():
    """Test the 'generate_map' tool."""
    result = await generate_map(map_description="A test map")
    assert "map_svg" in result
    assert "<svg" in result["map_svg"]

@pytest.mark.asyncio
@patch('main.redis_manager')
async def test_get_rulebook_personality(mock_redis_manager):
    """Test the 'get_rulebook_personality' tool."""
    mock_redis_manager.get_rulebook_personality.return_value = "test personality"
    result = await get_rulebook_personality("test book")
    assert result["personality"] == "test personality"

@pytest.mark.asyncio
@patch('main.redis_manager')
@patch('ttrpg_assistant.embedding_service.embedding.EmbeddingService')
async def test_get_character_creation_rules(MockEmbeddingService, mock_redis_manager):
    """Test the 'get_character_creation_rules' tool."""
    mock_embedding_service_instance = MockEmbeddingService.return_value
    mock_embedding_service_instance.generate_embedding.return_value = [0.1] * 384
    mock_redis_manager.vector_search.return_value = [
        SearchResult(
            content_chunk=ContentChunk(
                id="1", rulebook="test", system="test", content_type="rule",
                title="Character Creation", content="These are the rules.", page_number=1,
                section_path=[], embedding=b'', metadata={}
            ),
            relevance_score=0.9, match_type="semantic"
        )
    ]
    result = await get_character_creation_rules("test book")
    assert result["rules"] == "These are the rules."

@pytest.mark.asyncio
@patch('main.redis_manager')
async def test_generate_backstory(mock_redis_manager):
    """Test the 'generate_backstory' tool."""
    mock_redis_manager.get_rulebook_personality.return_value = "test personality"
    result = await generate_backstory("test book", {"name": "test char"})
    assert "backstory" in result

@pytest.mark.asyncio
@patch('main.redis_manager')
@patch('ttrpg_assistant.embedding_service.embedding.EmbeddingService')
async def test_generate_npc(MockEmbeddingService, mock_redis_manager):
    """Test the 'generate_npc' tool."""
    mock_embedding_service_instance = MockEmbeddingService.return_value
    mock_embedding_service_instance.generate_embedding.return_value = [0.1] * 384
    mock_redis_manager.get_rulebook_personality.return_value = "test personality"
    mock_redis_manager.vector_search.return_value = []
    result = await generate_npc("test book", 1, "test npc")
    assert "npc" in result

@pytest.mark.asyncio
@patch('main.redis_manager')
async def test_manage_session(mock_redis_manager):
    """Test the 'manage_session' tool."""
    mock_redis_manager.redis_client.exists.return_value = False
    result = await manage_session("start", "test campaign", "test session")
    assert result["status"] == "success"

@pytest.mark.asyncio
@patch('main.content_packager')
@patch('main.redis_manager')
async def test_create_content_pack(mock_redis_manager, mock_content_packager):
    """Test the 'create_content_pack' tool."""
    mock_redis_manager.get_rulebook_personality.return_value = "test personality"
    result = await create_content_pack("test source", "test.pack")
    assert result["status"] == "success"
    mock_content_packager.create_pack.assert_called_once()

@pytest.mark.asyncio
@patch('main.content_packager')
async def test_install_content_pack(mock_content_packager):
    """Test the 'install_content_pack' tool."""
    mock_content_packager.load_pack.return_value = ([], "")
    result = await install_content_pack("test.pack")
    assert result["status"] == "success"
    mock_content_packager.load_pack.assert_called_once()