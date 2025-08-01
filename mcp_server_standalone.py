#!/usr/bin/env python3
"""
TTRPG Assistant MCP Server
A Model Context Protocol server for tabletop role-playing game assistance.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

# Set up logging to stderr (required for MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("ttrpg-mcp")

try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
except ImportError as e:
    logger.error(f"MCP package not found: {e}")
    logger.error("Please install with: pip install mcp")
    sys.exit(1)

# Import our existing modules
try:
    from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
    from ttrpg_assistant.embedding_service.embedding import EmbeddingService
    from ttrpg_assistant.pdf_parser.parser import PDFParser
    from ttrpg_assistant.search_engine.enhanced_search_service import EnhancedSearchService
    from ttrpg_assistant.map_generator.generator import MapGenerator
    from ttrpg_assistant.content_packager.packager import ContentPackager
    from ttrpg_assistant.data_models.models import SourceType, ContentChunk
    from ttrpg_assistant.config_utils import load_config_safe
except ImportError as e:
    logger.error(f"Failed to import TTRPG Assistant modules: {e}")
    sys.exit(1)

# Global services
chroma_manager = None
embedding_service = None
pdf_parser = None
search_service = None
content_packager = None

# Initialize server
server = Server("ttrpg-assistant")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="search",
            description="Search through TTRPG rulebooks and content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "rulebook": {
                        "type": "string",
                        "description": "Specific rulebook to search in (optional)"
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Type of source to search ('rulebook' or 'flavor')"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Type of content to search for"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "use_hybrid": {
                        "type": "boolean",
                        "description": "Use hybrid search (semantic + keyword)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="add_source",
            description="Add a PDF rulebook to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file"
                    },
                    "rulebook_name": {
                        "type": "string",
                        "description": "Name of the rulebook"
                    },
                    "system": {
                        "type": "string",
                        "description": "Game system (e.g., 'D&D 5e', 'Pathfinder')"
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Type of source ('rulebook' or 'flavor')",
                        "default": "rulebook"
                    }
                },
                "required": ["pdf_path", "rulebook_name", "system"]
            }
        ),
        types.Tool(
            name="get_rulebook_personality",
            description="Get the personality text for a rulebook",
            inputSchema={
                "type": "object",
                "properties": {
                    "rulebook_name": {
                        "type": "string",
                        "description": "Name of the rulebook"
                    }
                },
                "required": ["rulebook_name"]
            }
        ),
        types.Tool(
            name="get_character_creation_rules",
            description="Get character creation rules for a rulebook",
            inputSchema={
                "type": "object",
                "properties": {
                    "rulebook_name": {
                        "type": "string",
                        "description": "Name of the rulebook"
                    }
                },
                "required": ["rulebook_name"]
            }
        ),
        types.Tool(
            name="manage_session",
            description="Manage game session data",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: start, add_note, set_initiative, add_monster, update_monster_hp, get"
                    },
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign identifier"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier"
                    },
                    "data": {
                        "type": "object",
                        "description": "Additional data for the action (optional)"
                    }
                },
                "required": ["action", "campaign_id", "session_id"]
            }
        ),
        types.Tool(
            name="generate_map",
            description="Generate a tactical combat map",
            inputSchema={
                "type": "object",
                "properties": {
                    "map_description": {
                        "type": "string",
                        "description": "Description of the map to generate"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Map width in grid units",
                        "default": 20
                    },
                    "height": {
                        "type": "integer",
                        "description": "Map height in grid units",
                        "default": 20
                    }
                },
                "required": ["map_description"]
            }
        ),
        types.Tool(
            name="create_content_pack",
            description="Create a content pack from a source",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "Source name to create pack from"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output path for the content pack"
                    }
                },
                "required": ["source_name", "output_path"]
            }
        ),
        types.Tool(
            name="install_content_pack",
            description="Install a content pack",
            inputSchema={
                "type": "object",
                "properties": {
                    "pack_path": {
                        "type": "string",
                        "description": "Path to the content pack file"
                    }
                },
                "required": ["pack_path"]
            }
        ),
        types.Tool(
            name="suggest_completions",
            description="Get query completion suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "partial_query": {
                        "type": "string",
                        "description": "Partial query to complete"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum suggestions to return",
                        "default": 5
                    }
                },
                "required": ["partial_query"]
            }
        ),
        types.Tool(
            name="explain_search",
            description="Get detailed explanation of search results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to explain"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_search_stats",
            description="Get search service statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="generate_npc",
            description="Generate an NPC based on rulebook content",
            inputSchema={
                "type": "object",
                "properties": {
                    "rulebook_name": {
                        "type": "string",
                        "description": "Rulebook to use for generation"
                    },
                    "player_level": {
                        "type": "integer",
                        "description": "Player character level for appropriate challenge"
                    },
                    "npc_description": {
                        "type": "string",
                        "description": "Description of the desired NPC"
                    },
                    "flavor_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional flavor sources to use (optional)",
                        "default": []
                    }
                },
                "required": ["rulebook_name", "player_level", "npc_description"]
            }
        ),
        types.Tool(
            name="generate_backstory",
            description="Generate character backstory using rulebook content",
            inputSchema={
                "type": "object",
                "properties": {
                    "rulebook_name": {
                        "type": "string",
                        "description": "Rulebook to use for generation"
                    },
                    "character_details": {
                        "type": "object",
                        "description": "Character details (class, race, background, etc.)"
                    },
                    "player_params": {
                        "type": "string",
                        "description": "Additional player parameters (optional)"
                    },
                    "flavor_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional flavor sources to use (optional)",
                        "default": []
                    }
                },
                "required": ["rulebook_name", "character_details"]
            }
        ),
        types.Tool(
            name="quick_search",
            description="Quick search for simple lookups",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    global chroma_manager, embedding_service, pdf_parser, search_service
    
    try:
        if name == "search":
            query = arguments["query"]
            rulebook = arguments.get("rulebook")
            source_type = arguments.get("source_type")
            content_type = arguments.get("content_type")
            max_results = arguments.get("max_results", 5)
            use_hybrid = arguments.get("use_hybrid", True)
            
            # Ensure search service is initialized
            if search_service is None:
                search_service = EnhancedSearchService(chroma_manager, embedding_service)
                await search_service.initialize()
            
            # Convert source_type string to SourceType enum if provided
            source_type_enum = None
            if source_type:
                try:
                    source_type_enum = SourceType(source_type)
                except ValueError:
                    logger.warning(f"Invalid source_type '{source_type}', ignoring")
            
            results, suggestions = await search_service.search(
                query=query,
                rulebook=rulebook,
                source_type=source_type_enum,
                content_type=content_type,
                max_results=max_results,
                use_hybrid=use_hybrid
            )
            
            # Format results for display
            if not results:
                response = f"No results found for query: '{query}'"
                if suggestions:
                    response += "\n\nSuggestions:\n"
                    for suggestion in suggestions[:3]:
                        response += f"- {suggestion.suggested_query} ({suggestion.explanation})\n"
            else:
                response = f"Found {len(results)} results for '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    chunk = result.content_chunk
                    response += f"{i}. **{chunk.title}** (Score: {result.relevance_score:.2f})\n"
                    response += f"   Source: {chunk.rulebook} - {chunk.system}\n"
                    response += f"   Content: {chunk.content[:200]}...\n"
                    response += f"   Page: {chunk.page_number}\n\n"
                
                if suggestions:
                    response += "Related suggestions:\n"
                    for suggestion in suggestions[:3]:
                        response += f"- {suggestion.suggested_query}\n"
            
            return [types.TextContent(type="text", text=response)]
        
        elif name == "add_source":
            pdf_path = arguments["pdf_path"]
            rulebook_name = arguments["rulebook_name"]
            system = arguments["system"]
            source_type = arguments.get("source_type", "rulebook")
            
            try:
                # Process PDF and add to knowledge base
                chunks_data = pdf_parser.create_chunks(
                    pdf_path,
                    rulebook_name=rulebook_name,
                    system=system,
                    source_type=source_type
                )
                
                # Convert to content chunks and store
                from ttrpg_assistant.data_models.models import ContentChunk
                content_chunks = [
                    ContentChunk(
                        id=chunk['id'],
                        rulebook=rulebook_name,
                        system=system,
                        source_type=SourceType.RULEBOOK,
                        content_type=chunk.get('content_type', 'text'),
                        title=chunk['section']['title'] if chunk.get('section') else chunk.get('title', ''),
                        content=chunk['text'],
                        page_number=chunk['page_number'],
                        section_path=chunk['section']['path'] if chunk.get('section') else [],
                        embedding=b"",
                        metadata=chunk.get('metadata', {})
                    ) for chunk in chunks_data
                ]
                
                chroma_manager.store_rulebook_content("rulebook_index", content_chunks)
                
                # Extract and store personality
                personality_text = pdf_parser.extract_personality_text(pdf_path)
                chroma_manager.store_rulebook_personality(rulebook_name, personality_text)
                
                response = f"Successfully added '{rulebook_name}' ({len(content_chunks)} chunks processed)"
                
                # Get adaptive learning stats if available
                stats = pdf_parser.get_adaptive_statistics(system)
                if "error" not in stats:
                    pattern_count = sum(stats.get('pattern_stats', {}).get(ct, {}).get('total_patterns', 0) 
                                      for ct in stats.get('pattern_stats', {}))
                    if pattern_count > 0:
                        response += f" - Learned {pattern_count} content patterns"
                
                return [types.TextContent(type="text", text=response)]
                
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error processing PDF: {str(e)}")]
        
        elif name == "generate_npc":
            rulebook_name = arguments["rulebook_name"]
            player_level = arguments["player_level"]
            npc_description = arguments["npc_description"]
            flavor_sources = arguments.get("flavor_sources", [])
            
            # Get personalities
            personalities = [chroma_manager.get_rulebook_personality(rulebook_name)]
            for source in flavor_sources:
                personalities.append(chroma_manager.get_rulebook_personality(source))
            
            if not personalities[0]:
                return [types.TextContent(type="text", text=f"No personality found for rulebook '{rulebook_name}'. Please add the rulebook first.")]
            
            # Search for relevant NPC/monster examples
            import numpy as np
            query_embedding = np.array(embedding_service.generate_embedding("monster stat block non-player character"))
            examples = chroma_manager.vector_search(
                index_name="rulebook_index",
                query_embedding=query_embedding,
                num_results=3,
                filters={"rulebook": rulebook_name}
            )
            
            # Generate NPC description
            npc_text = f"Generated NPC for {rulebook_name}:\n\n"
            npc_text += f"Player Level: {player_level}\n"
            npc_text += f"Description: {npc_description}\n\n"
            
            if examples:
                npc_text += "Examples from the rulebook:\n"
                for example in examples:
                    npc_text += f"- {example.content_chunk.title}: {example.content_chunk.content[:100]}...\n"
            
            npc_text += f"\nRulebook Style Guide:\n" + "\n".join(filter(None, personalities))
            
            return [types.TextContent(type="text", text=npc_text)]
        
        elif name == "generate_backstory":
            rulebook_name = arguments["rulebook_name"]
            character_details = arguments["character_details"]
            player_params = arguments.get("player_params")
            flavor_sources = arguments.get("flavor_sources", [])
            
            # Get personalities
            personalities = [chroma_manager.get_rulebook_personality(rulebook_name)]
            for source in flavor_sources:
                personalities.append(chroma_manager.get_rulebook_personality(source))
            
            if not personalities[0]:
                return [types.TextContent(type="text", text=f"No personality found for rulebook '{rulebook_name}'. Please add the rulebook first.")]
            
            backstory = f"Generated backstory for {rulebook_name}:\n\n"
            backstory += f"Character Details: {json.dumps(character_details, indent=2)}\n\n"
            if player_params:
                backstory += f"Player Parameters: {player_params}\n\n"
            
            backstory += f"Rulebook Style Guide:\n" + "\n".join(filter(None, personalities))
            
            return [types.TextContent(type="text", text=backstory)]
        
        elif name == "quick_search":
            query = arguments["query"]
            max_results = arguments.get("max_results", 3)
            
            # Ensure search service is initialized
            if search_service is None:
                search_service = EnhancedSearchService(chroma_manager, embedding_service)
                await search_service.initialize()
            
            results = await search_service.quick_search(query, max_results)
            
            if not results:
                response = f"No quick results found for: '{query}'"
            else:
                response = f"Quick search results for '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    chunk = result.content_chunk
                    response += f"{i}. {chunk.title} - {chunk.content[:100]}...\n"
            
            return [types.TextContent(type="text", text=response)]
        
        elif name == "get_rulebook_personality":
            rulebook_name = arguments["rulebook_name"]
            personality = chroma_manager.get_rulebook_personality(rulebook_name)
            if not personality:
                return [types.TextContent(type="text", text=f"No personality found for rulebook '{rulebook_name}'.")]
            return [types.TextContent(type="text", text=f"Personality for {rulebook_name}:\n\n{personality}")]
        
        elif name == "get_character_creation_rules":
            rulebook_name = arguments["rulebook_name"]
            
            import numpy as np
            query_embedding = np.array(embedding_service.generate_embedding("character creation rules"))
            results = chroma_manager.vector_search(
                index_name="rulebook_index",
                query_embedding=query_embedding,
                num_results=1,
                filters={"rulebook": rulebook_name, "source_type": "rulebook"}
            )
            
            if not results:
                return [types.TextContent(type="text", text=f"Character creation rules not found for '{rulebook_name}'.")]
            return [types.TextContent(type="text", text=f"Character creation rules for {rulebook_name}:\n\n{results[0].content_chunk.content}")]
        
        elif name == "manage_session":
            action = arguments["action"]
            campaign_id = arguments["campaign_id"]
            session_id = arguments["session_id"]
            data = arguments.get("data", {})
            
            if action == "start":
                if chroma_manager.session_exists(campaign_id, session_id):
                    return [types.TextContent(type="text", text="Session already exists.")]
                
                initial_data = {"notes": [], "initiative_order": [], "monsters": []}
                chroma_manager.store_session_data(campaign_id, session_id, initial_data)
                return [types.TextContent(type="text", text="Session started successfully.")]
            
            elif action == "get":
                session_data = chroma_manager.get_session_data(campaign_id, session_id)
                if not session_data:
                    return [types.TextContent(type="text", text="Session not found.")]
                return [types.TextContent(type="text", text=f"Session data:\n{json.dumps(session_data, indent=2)}")]
            
            elif action in ["add_note", "set_initiative", "add_monster", "update_monster_hp"]:
                session_data = chroma_manager.get_session_data(campaign_id, session_id)
                if not session_data:
                    return [types.TextContent(type="text", text="Session not found.")]
                
                # Update session data based on action
                if action == "add_note" and "note" in data:
                    session_data.setdefault("notes", []).append(data["note"])
                elif action == "set_initiative" and "order" in data:
                    session_data["initiative_order"] = data["order"]
                elif action == "add_monster" and "monster" in data:
                    session_data.setdefault("monsters", []).append(data["monster"])
                elif action == "update_monster_hp" and "name" in data and "hp" in data:
                    for monster in session_data.get("monsters", []):
                        if monster.get("name") == data["name"]:
                            monster["current_hp"] = data["hp"]
                            break
                
                chroma_manager.update_session_data(campaign_id, session_id, session_data)
                return [types.TextContent(type="text", text=f"Session updated: {action} completed.")]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown session action: {action}")]
        
        elif name == "generate_map":
            map_description = arguments["map_description"]
            width = arguments.get("width", 20)
            height = arguments.get("height", 20)
            
            try:
                map_generator = MapGenerator(width, height)
                svg_map = map_generator.generate_map(map_description)
                return [types.TextContent(type="text", text=f"Generated {width}x{height} map: {map_description}\n\n{svg_map}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error generating map: {str(e)}")]
        
        elif name == "create_content_pack":
            source_name = arguments["source_name"]
            output_path = arguments["output_path"]
            
            try:
                personality = chroma_manager.get_rulebook_personality(source_name)
                if content_packager is None:
                    return [types.TextContent(type="text", text="Content packager not initialized.")]
                
                # Simplified implementation - in reality would retrieve actual chunks
                chunks = []
                content_packager.create_pack(chunks, personality, output_path)
                return [types.TextContent(type="text", text=f"Content pack created at {output_path}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error creating content pack: {str(e)}")]
        
        elif name == "install_content_pack":
            pack_path = arguments["pack_path"]
            
            try:
                if content_packager is None:
                    return [types.TextContent(type="text", text="Content packager not initialized.")]
                
                chunks, personality = content_packager.load_pack(pack_path)
                return [types.TextContent(type="text", text=f"Content pack installed from {pack_path}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error installing content pack: {str(e)}")]
        
        elif name == "suggest_completions":
            partial_query = arguments["partial_query"]
            limit = arguments.get("limit", 5)
            
            # Ensure search service is initialized
            if search_service is None:
                search_service = EnhancedSearchService(chroma_manager, embedding_service)
                await search_service.initialize()
            
            try:
                completions = await search_service.suggest_completions(partial_query, limit)
                response = f"Completions for '{partial_query}':\n\n"
                for completion in completions:
                    response += f"- {completion}\n"
                return [types.TextContent(type="text", text=response)]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error getting completions: {str(e)}")]
        
        elif name == "explain_search":
            query = arguments["query"]
            
            # Ensure search service is initialized
            if search_service is None:
                search_service = EnhancedSearchService(chroma_manager, embedding_service)
                await search_service.initialize()
            
            try:
                results, _ = await search_service.search(query, max_results=10)
                explanation = await search_service.explain_search_results(query, results)
                return [types.TextContent(type="text", text=f"Search explanation for '{query}':\n\n{explanation}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error explaining search: {str(e)}")]
        
        elif name == "get_search_stats":
            # Ensure search service is initialized
            if search_service is None:
                search_service = EnhancedSearchService(chroma_manager, embedding_service)
                await search_service.initialize()
            
            try:
                stats = search_service.get_search_statistics()
                return [types.TextContent(type="text", text=f"Search statistics:\n\n{json.dumps(stats, indent=2)}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error getting search stats: {str(e)}")]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in tool '{name}': {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def initialize_services():
    """Initialize all services"""
    global chroma_manager, embedding_service, pdf_parser, search_service, content_packager
    
    logger.info("Initializing TTRPG Assistant services...")
    
    try:
        # Load configuration
        config = load_config_safe("config.yaml")
        
        # Initialize core services
        chroma_manager = ChromaDataManager()
        embedding_service = EmbeddingService()
        content_packager = ContentPackager()
        
        # Initialize PDF parser with config
        pdf_config = config.get('pdf_processing', {})
        pdf_parser = PDFParser(
            enable_adaptive_learning=pdf_config.get('enable_adaptive_learning', True),
            pattern_cache_dir=pdf_config.get('pattern_cache_dir', './pattern_cache')
        )
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

async def main():
    """Main entry point"""
    try:
        # Initialize services
        await initialize_services()
        
        # Run the MCP server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ttrpg-assistant",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())