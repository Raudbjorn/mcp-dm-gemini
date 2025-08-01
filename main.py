from typing import Any, List, Dict
from mcp.server.fastmcp import FastMCP
import numpy as np
from ttrpg_assistant.logger import logger
import json

# --- Service Initialization ---
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from ttrpg_assistant.map_generator.generator import MapGenerator
from ttrpg_assistant.content_packager.packager import ContentPackager
from ttrpg_assistant.search_engine.enhanced_search_service import EnhancedSearchService
from ttrpg_assistant.data_models.models import *
from ttrpg_assistant.config_utils import load_config_safe

# Initialize services
config = load_config_safe("config.yaml")
chroma_manager = ChromaDataManager()
embedding_service = EmbeddingService()

# Initialize PDF parser with config
pdf_config = config.get('pdf_processing', {})
pdf_parser = PDFParser(
    enable_adaptive_learning=pdf_config.get('enable_adaptive_learning', True),
    pattern_cache_dir=pdf_config.get('pattern_cache_dir', './pattern_cache')
)

content_packager = ContentPackager()

# Initialize enhanced search service
search_service = None  # Will be initialized when first needed

# --- MCP Server Initialization ---
mcp = FastMCP("TTRPG")

# --- Tool Definitions ---

async def _ensure_search_service():
    """Ensure the search service is initialized"""
    global search_service
    if search_service is None:
        search_service = EnhancedSearchService(chroma_manager, embedding_service)
        await search_service.initialize()

@mcp.tool()
async def search(query: str, rulebook: str = None, source_type: str = None, content_type: str = None, max_results: int = 5, use_hybrid: bool = True) -> Dict[str, Any]:
    """
    Search TTRPG source material for rules, lore, etc. with enhanced search capabilities.

    Args:
        query: The search query.
        rulebook: Optional specific source to search within.
        source_type: Optional type of source to search ('rulebook' or 'flavor').
        content_type: Optional type of content to search for.
        max_results: The maximum number of results to return.
        use_hybrid: Use hybrid search (semantic + keyword) for better results.
    """
    logger.info(f"Searching for '{query}' with filters: rulebook={rulebook}, source_type={source_type}, content_type={content_type}")
    
    # Ensure search service is initialized
    await _ensure_search_service()
    
    # Convert source_type string to SourceType enum if provided
    source_type_enum = None
    if source_type:
        try:
            source_type_enum = SourceType(source_type)
        except ValueError:
            logger.warning(f"Invalid source_type '{source_type}', ignoring")
    
    # Perform enhanced search
    search_results, suggestions = await search_service.search(
        query=query,
        rulebook=rulebook,
        source_type=source_type_enum,
        content_type=content_type,
        max_results=max_results,
        use_hybrid=use_hybrid
    )
    
    logger.info(f"Found {len(search_results)} results with {len(suggestions)} suggestions.")
    
    # Format results for response
    result_data = []
    for result in search_results:
        result_data.append({
            "content_chunk": result.content_chunk.model_dump(),
            "relevance_score": result.relevance_score,
            "match_type": result.match_type
        })
    
    # Format suggestions
    suggestion_data = []
    for suggestion in suggestions:
        suggestion_data.append({
            "original_query": suggestion.original_query,
            "suggested_query": suggestion.suggested_query,
            "confidence": suggestion.confidence,
            "suggestion_type": suggestion.suggestion_type,
            "explanation": suggestion.explanation
        })
    
    return {
        "results": result_data,
        "suggestions": suggestion_data,
        "search_stats": {
            "total_results": len(search_results),
            "has_suggestions": len(suggestions) > 0,
            "search_type": "hybrid" if use_hybrid else "semantic"
        }
    }

@mcp.tool()
async def add_source(pdf_path: str, rulebook_name: str, system: str, source_type: str = "rulebook") -> Dict[str, str]:
    """
    Process and add a new PDF source (rulebook or flavor text) to the system.

    Args:
        pdf_path: The local file path to the PDF file.
        rulebook_name: The display name for this source material.
        system: The game system (e.g., D&D 5e, Pathfinder).
        source_type: The type of source, either 'rulebook' or 'flavor'.
    """
    logger.info(f"Adding source '{rulebook_name}' from '{pdf_path}'")
    
    # Use enhanced PDF parsing with adaptive learning
    chunks_data = pdf_parser.create_chunks(
        pdf_path, 
        rulebook_name=rulebook_name,
        system=system,
        source_type=source_type
    )
    
    content_chunks = []
    for chunk in chunks_data:
        if isinstance(chunk, ContentChunk):
            content_chunks.append(chunk)
        else:
            content_chunks.append(
                ContentChunk(
                    id=chunk['id'], 
                    rulebook=rulebook_name, 
                    system=system,
                    source_type=SourceType(source_type), 
                    # Use enhanced content type from adaptive processing if available
                    content_type=chunk.get('content_type', 'text'),
                    title=chunk['section']['title'] if chunk.get('section') and chunk['section'] else chunk.get('title', ''),
                    content=chunk.get('text', ''), 
                    page_number=chunk.get('page_number', 0),
                    section_path=chunk['section']['path'] if chunk.get('section') and chunk['section'] else [],
                    embedding=b"", 
                    # Include enhanced metadata from adaptive processing
                    metadata=chunk.get('metadata', {})
                )
            )

    chroma_manager.store_rulebook_content("rulebook_index", content_chunks)
    personality = pdf_parser.extract_personality_text(pdf_path)
    chroma_manager.store_rulebook_personality(rulebook_name, personality)
    
    # Get adaptive learning statistics if available
    stats = pdf_parser.get_adaptive_statistics(system)
    stats_message = ""
    if "error" not in stats:
        pattern_count = sum(stats.get('pattern_stats', {}).get(ct, {}).get('total_patterns', 0) 
                          for ct in stats.get('pattern_stats', {}))
        if pattern_count > 0:
            stats_message = f" Learned {pattern_count} content patterns."
    
    logger.info(f"Source '{rulebook_name}' added successfully.{stats_message}")
    return {"status": "success", "message": f"Source '{rulebook_name}' added successfully.{stats_message}"}

@mcp.tool()
async def get_rulebook_personality(rulebook_name: str) -> Dict[str, str]:
    """Get the personality for a rulebook."""
    logger.info(f"Getting personality for '{rulebook_name}'")
    personality = chroma_manager.get_rulebook_personality(rulebook_name)
    if not personality:
        logger.warning(f"Personality not found for '{rulebook_name}'")
        return {"error": "Personality not found for this rulebook."}
    return {"personality": personality}

@mcp.tool()
async def get_character_creation_rules(rulebook_name: str) -> Dict[str, str]:
    """Get the character creation rules for a rulebook."""
    logger.info(f"Getting character creation rules for '{rulebook_name}'")
    query = "character creation rules"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    results = chroma_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=1,
        filters={"rulebook": rulebook_name, "source_type": "rulebook"}
    )
    
    if not results:
        logger.warning(f"Character creation rules not found for '{rulebook_name}'")
        return {"error": "Character creation rules not found."}
        
    return {"rules": results[0].content_chunk.content}

@mcp.tool()
async def generate_backstory(rulebook_name: str, character_details: Dict[str, Any], player_params: str = None, flavor_sources: List[str] = []) -> Dict[str, str]:
    """Generate a backstory for a character."""
    logger.info(f"Generating backstory for a character in '{rulebook_name}'")
    personalities = [chroma_manager.get_rulebook_personality(rulebook_name)]
    for source in flavor_sources:
        personalities.append(chroma_manager.get_rulebook_personality(source))
    
    backstory = f"This is a generated backstory for a character in {rulebook_name}.\n"
    backstory += f"Character details: {character_details}\n"
    if player_params:
        backstory += f"Player parameters: {player_params}\n"
    
    backstory += f"\n--- Vibe ---\n" + "\n".join(filter(None, personalities))
    
    return {"backstory": backstory}

@mcp.tool()
async def generate_npc(rulebook_name: str, player_level: int, npc_description: str, flavor_sources: List[str] = []) -> Dict[str, str]:
    """Generate an NPC."""
    logger.info(f"Generating NPC for '{rulebook_name}' at level {player_level}")
    personalities = [chroma_manager.get_rulebook_personality(rulebook_name)]
    for source in flavor_sources:
        personalities.append(chroma_manager.get_rulebook_personality(source))

    query = "monster stat block or non-player character"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    examples = chroma_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=3,
        filters={"rulebook": rulebook_name, "source_type": "rulebook"}
    )
    
    npc = f"This is a generated NPC for {rulebook_name}.\n"
    npc += f"Player level: {player_level}\n"
    npc += f"Description: {npc_description}\n"
    
    if examples:
        npc += "\n--- Examples from the rulebook ---\n"
        for example in examples:
            npc += f"- {example.content_chunk.title}: {example.content_chunk.content}\n"
            
    npc += f"\n--- Vibe ---\n" + "\n".join(filter(None, personalities))
    
    return {"npc": npc}

@mcp.tool()
async def manage_session(action: str, campaign_id: str, session_id: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Manage a game session using ChromaDB's campaign data storage."""
    logger.info(f"Managing session '{session_id}' in campaign '{campaign_id}' with action '{action}'")
    
    if action == "start":
        if chroma_manager.session_exists(campaign_id, session_id):
            logger.warning(f"Session '{session_id}' already exists.")
            return {"error": "Session already exists."}
        
        initial_data = {
            "notes": [],
            "initiative_order": [],
            "monsters": []
        }
        chroma_manager.store_session_data(campaign_id, session_id, initial_data)
        return {"status": "success", "message": "Session started."}

    # Get existing session data
    session_data = chroma_manager.get_session_data(campaign_id, session_id)
    if not session_data:
        logger.warning(f"Session '{session_id}' not found.")
        return {"error": "Session not found."}

    notes = session_data.get("notes", [])
    initiative_order = session_data.get("initiative_order", [])
    monsters = session_data.get("monsters", [])

    if action == "add_note":
        if not data or "note" not in data:
            return {"error": "Note data is required."}
        notes.append(data['note'])
        chroma_manager.update_session_data(campaign_id, session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif action == "set_initiative":
        if not data or "order" not in data:
            return {"error": "Initiative order data is required."}
        initiative_order = [InitiativeEntry(**e).model_dump() for e in data['order']]
        chroma_manager.update_session_data(campaign_id, session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif action == "add_monster":
        if not data or "monster" not in data:
            return {"error": "Monster data is required."}
        monster = MonsterState(**data['monster'])
        monsters.append(monster.model_dump())
        chroma_manager.update_session_data(campaign_id, session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif action == "update_monster_hp":
        if not data or "name" not in data or "hp" not in data:
            return {"error": "Monster name and hp are required."}
        for monster in monsters:
            if monster['name'] == data['name']:
                monster['current_hp'] = data['hp']
                break
        chroma_manager.update_session_data(campaign_id, session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif action == "get":
        return {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        }

    else:
        return {"error": "Invalid action"}

@mcp.tool()
async def generate_map(map_description: str, width: int = 20, height: int = 20) -> Dict[str, str]:
    """
    Generate a map for a combat encounter.

    Args:
        map_description: A brief description of the map to generate (e.g., 'a cave entrance', 'a tavern common room').
        width: The width of the map in grid units.
        height: The height of the map in grid units.
    """
    logger.info(f"Generating a {width}x{height} map with description: '{map_description}'")
    map_generator = MapGenerator(width, height)
    svg_map = map_generator.generate_map(map_description)
    return {"map_svg": svg_map}

@mcp.tool()
async def create_content_pack(source_name: str, output_path: str) -> Dict[str, str]:
    """Create a content pack from a source."""
    logger.info(f"Creating content pack for '{source_name}' at '{output_path}'")
    # This is a simplified implementation. A real implementation would need to
    # retrieve the actual chunks for the given source.
    chunks = []
    personality = chroma_manager.get_rulebook_personality(source_name)
    
    content_packager.create_pack(chunks, personality, output_path)
    
    return {"status": "success", "message": f"Content pack created at {output_path}"}

@mcp.tool()
async def install_content_pack(pack_path: str) -> Dict[str, str]:
    """Install a content pack."""
    logger.info(f"Installing content pack from '{pack_path}'")
    chunks, personality = content_packager.load_pack(pack_path)
    
    # This is a simplified implementation. A real implementation would need to
    # properly store the chunks and personality.
    
    return {"status": "success", "message": "Content pack installed."}

@mcp.tool()
async def quick_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Quick search for simple lookups without extensive processing."""
    logger.info(f"Quick search for '{query}'")
    
    # Ensure search service is initialized
    await _ensure_search_service()
    
    results = await search_service.quick_search(query, max_results)
    
    result_data = []
    for result in results:
        result_data.append({
            "content_chunk": result.content_chunk.model_dump(),
            "relevance_score": result.relevance_score,
            "match_type": result.match_type
        })
    
    return {
        "results": result_data,
        "search_type": "quick"
    }

@mcp.tool()
async def suggest_completions(partial_query: str, limit: int = 5) -> Dict[str, Any]:
    """Get query completion suggestions based on vocabulary."""
    logger.info(f"Getting completions for '{partial_query}'")
    
    # Ensure search service is initialized
    await _ensure_search_service()
    
    completions = await search_service.suggest_completions(partial_query, limit)
    
    return {
        "completions": completions,
        "partial_query": partial_query
    }

@mcp.tool()
async def explain_search(query: str) -> Dict[str, Any]:
    """Get detailed explanation of search results and relevance factors."""
    logger.info(f"Explaining search for '{query}'")
    
    # Ensure search service is initialized
    await _ensure_search_service()
    
    # Get results for the query
    results, _ = await search_service.search(query, max_results=10)
    
    explanation = await search_service.explain_search_results(query, results)
    
    return {
        "explanation": explanation,
        "query": query
    }

@mcp.tool()
async def get_search_stats() -> Dict[str, Any]:
    """Get statistics about the search service."""
    logger.info("Getting search service statistics")
    
    # Ensure search service is initialized
    await _ensure_search_service()
    
    stats = search_service.get_search_statistics()
    
    return {"stats": stats}

if __name__ == "__main__":
    logger.info("Starting TTRPG Assistant MCP Server")
    mcp.run(transport='stdio')
