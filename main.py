from typing import Any, List, Dict
from mcp.server.fastmcp import FastMCP
import numpy as np
from ttrpg_assistant.logger import logger
import json

# --- Service Initialization ---
from ttrpg_assistant.redis_manager.manager import RedisDataManager
from ttrpg_assistant.pdf_parser.parser import PDFParser
from ttrpg_assistant.map_generator.generator import MapGenerator
from ttrpg_assistant.content_packager.packager import ContentPackager
from ttrpg_assistant.data_models.models import *

redis_manager = RedisDataManager()
pdf_parser = PDFParser()
content_packager = ContentPackager()

# --- MCP Server Initialization ---
mcp = FastMCP("TTRPG")

# --- Tool Definitions ---

@mcp.tool()
async def search(query: str, rulebook: str = None, source_type: str = None, content_type: str = None, max_results: int = 5) -> Dict[str, Any]:
    """
    Search TTRPG source material for rules, lore, etc.

    Args:
        query: The search query.
        rulebook: Optional specific source to search within.
        source_type: Optional type of source to search ('rulebook' or 'flavor').
        content_type: Optional type of content to search for.
        max_results: The maximum number of results to return.
    """
    logger.info(f"Searching for '{query}' with filters: rulebook={rulebook}, source_type={source_type}, content_type={content_type}")
    from ttrpg_assistant.embedding_service.embedding import EmbeddingService
    embedding_service = EmbeddingService()
    
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    filters = []
    if rulebook: filters.append(f"@rulebook:{rulebook}")
    if source_type: filters.append(f"@source_type:{source_type}")
    if content_type: filters.append(f"@content_type:{content_type}")
    filter_str = " ".join(filters) if filters else "*"
    
    search_results = redis_manager.vector_search("rulebook_index", query_embedding, max_results, filter_str)
    logger.info(f"Found {len(search_results)} results.")
    return {"results": [r.model_dump() for r in search_results]}

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
    chunks_data = pdf_parser.create_chunks(pdf_path)
    content_chunks = []
    for chunk in chunks_data:
        if isinstance(chunk, ContentChunk):
            content_chunks.append(chunk)
        else:
            content_chunks.append(
                ContentChunk(
                    id=chunk['id'], rulebook=rulebook_name, system=system,
                    source_type=SourceType(source_type), content_type="text",
                    title=chunk.get('section', {}).get('title', ''),
                    content=chunk.get('text', ''), page_number=chunk.get('page_number', 0),
                    section_path=chunk.get('section', {}).get('path', []),
                    embedding=b"", metadata=chunk.get('metadata', {})
                )
            )

    redis_manager.store_rulebook_content("rulebook_index", content_chunks)
    personality = pdf_parser.extract_personality_text(pdf_path)
    redis_manager.store_rulebook_personality(rulebook_name, personality)
    logger.info(f"Source '{rulebook_name}' added successfully.")
    return {"status": "success", "message": f"Source '{rulebook_name}' added successfully."}

@mcp.tool()
async def get_rulebook_personality(rulebook_name: str) -> Dict[str, str]:
    """Get the personality for a rulebook."""
    logger.info(f"Getting personality for '{rulebook_name}'")
    personality = redis_manager.get_rulebook_personality(rulebook_name)
    if not personality:
        logger.warning(f"Personality not found for '{rulebook_name}'")
        return {"error": "Personality not found for this rulebook."}
    return {"personality": personality}

@mcp.tool()
async def get_character_creation_rules(rulebook_name: str) -> Dict[str, str]:
    """Get the character creation rules for a rulebook."""
    logger.info(f"Getting character creation rules for '{rulebook_name}'")
    from ttrpg_assistant.embedding_service.embedding import EmbeddingService
    embedding_service = EmbeddingService()
    query = "character creation rules"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    results = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=1,
        filters=f"@rulebook:{rulebook_name} @source_type:rulebook"
    )
    
    if not results:
        logger.warning(f"Character creation rules not found for '{rulebook_name}'")
        return {"error": "Character creation rules not found."}
        
    return {"rules": results[0].content_chunk.content}

@mcp.tool()
async def generate_backstory(rulebook_name: str, character_details: Dict[str, Any], player_params: str = None, flavor_sources: List[str] = []) -> Dict[str, str]:
    """Generate a backstory for a character."""
    logger.info(f"Generating backstory for a character in '{rulebook_name}'")
    personalities = [redis_manager.get_rulebook_personality(rulebook_name)]
    for source in flavor_sources:
        personalities.append(redis_manager.get_rulebook_personality(source))
    
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
    from ttrpg_assistant.embedding_service.embedding import EmbeddingService
    embedding_service = EmbeddingService()
    personalities = [redis_manager.get_rulebook_personality(rulebook_name)]
    for source in flavor_sources:
        personalities.append(redis_manager.get_rulebook_personality(source))

    query = "monster stat block or non-player character"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    examples = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=3,
        filters=f"@rulebook:{rulebook_name} @source_type:rulebook"
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
    """Manage a game session."""
    logger.info(f"Managing session '{session_id}' in campaign '{campaign_id}' with action '{action}'")
    session_key = f"session:{campaign_id}:{session_id}"

    if action == "start":
        if redis_manager.redis_client.exists(session_key):
            logger.warning(f"Session '{session_id}' already exists.")
            return {"error": "Session already exists."}
        redis_manager.redis_client.hset(session_key, mapping={"notes": "[]", "initiative_order": "[]", "monsters": "[]"})
        return {"status": "success", "message": "Session started."}

    if not redis_manager.redis_client.exists(session_key):
        logger.warning(f"Session '{session_id}' not found.")
        return {"error": "Session not found."}

    session_data = redis_manager.redis_client.hgetall(session_key)
    notes = json.loads(session_data.get("notes", "[]"))
    initiative_order = json.loads(session_data.get("initiative_order", "[]"))
    monsters = json.loads(session_data.get("monsters", "[]"))

    if action == "add_note":
        if not data or "note" not in data:
            return {"error": "Note data is required."}
        notes.append(data['note'])
        redis_manager.redis_client.hset(session_key, "notes", json.dumps(notes))
        return {"status": "success"}

    elif action == "set_initiative":
        if not data or "order" not in data:
            return {"error": "Initiative order data is required."}
        initiative_order = [InitiativeEntry(**e).model_dump() for e in data['order']]
        redis_manager.redis_client.hset(session_key, "initiative_order", json.dumps(initiative_order))
        return {"status": "success"}

    elif action == "add_monster":
        if not data or "monster" not in data:
            return {"error": "Monster data is required."}
        monster = MonsterState(**data['monster'])
        monsters.append(monster.model_dump())
        redis_manager.redis_client.hset(session_key, "monsters", json.dumps(monsters))
        return {"status": "success"}

    elif action == "update_monster_hp":
        if not data or "name" not in data or "hp" not in data:
            return {"error": "Monster name and hp are required."}
        for monster in monsters:
            if monster['name'] == data['name']:
                monster['current_hp'] = data['hp']
                break
        redis_manager.redis_client.hset(session_key, "monsters", json.dumps(monsters))
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
    personality = redis_manager.get_rulebook_personality(source_name)
    
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

if __name__ == "__main__":
    logger.info("Starting TTRPG Assistant MCP Server")
    mcp.run(transport='stdio')
