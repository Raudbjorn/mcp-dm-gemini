from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from ttrpg_assistant.map_generator.generator import MapGenerator
from ttrpg_assistant.content_packager.packager import ContentPackager
from ttrpg_assistant.search_engine.enhanced_search_service import EnhancedSearchService
from ttrpg_assistant.personality_service.personality_manager import PersonalityManager
from .dependencies import get_chroma_manager, get_embedding_service, get_pdf_parser, get_personality_manager
import numpy as np
from typing import Dict, Any, List, Optional
from ttrpg_assistant.data_models.models import ContentChunk, InitiativeEntry, MonsterState, SourceType, MapGenerationInput
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class SearchInput(BaseModel):
    query: str
    rulebook: str = None
    source_type: SourceType = None
    content_type: str = None
    max_results: int = 5
    use_hybrid: bool = True
    context: Optional[Dict[str, Any]] = None

class QuerySuggestionResponse(BaseModel):
    original_query: str
    suggested_query: str
    confidence: float
    suggestion_type: str
    explanation: str

class ManageCampaignInput(BaseModel):
    action: str
    campaign_id: str
    data_type: str = None
    data_id: str = None
    data: Dict[str, Any] = None

class AddSourceInput(BaseModel):
    pdf_path: str
    rulebook_name: str
    system: str
    source_type: SourceType = SourceType.RULEBOOK

class GetRulebookPersonalityInput(BaseModel):
    rulebook_name: str

class GetCharacterCreationRulesInput(BaseModel):
    rulebook_name: str

class GenerateBackstoryInput(BaseModel):
    rulebook_name: str
    character_details: Dict[str, Any]
    player_params: str = None
    flavor_sources: List[str] = []

class GenerateNPCInput(BaseModel):
    rulebook_name: str
    player_level: int
    npc_description: str
    flavor_sources: List[str] = []

class ManageSessionInput(BaseModel):
    action: str
    campaign_id: str
    session_id: str
    data: Dict[str, Any] = None

class CreateContentPackInput(BaseModel):
    source_name: str
    output_path: str

class InstallContentPackInput(BaseModel):
    pack_path: str

class QuickSearchInput(BaseModel):
    query: str
    max_results: int = 3

class QueryCompletionInput(BaseModel):
    partial_query: str
    limit: int = 5

class SearchExplanationInput(BaseModel):
    query: str
    result_ids: List[str] = []

class ManagePersonalityInput(BaseModel):
    action: str  # "get", "list", "summary", "vernacular", "compare", "stats"
    system_name: str = None
    systems: List[str] = []

@router.post("/search")
async def search(
    input: SearchInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    # Initialize enhanced search service
    search_service = EnhancedSearchService(chroma_manager, embedding_service)
    
    # Perform enhanced search
    results, suggestions = await search_service.search(
        query=input.query,
        rulebook=input.rulebook,
        source_type=input.source_type,
        content_type=input.content_type,
        max_results=input.max_results,
        context=input.context,
        use_hybrid=input.use_hybrid
    )
    
    # Convert suggestions to response format
    suggestion_responses = [
        QuerySuggestionResponse(
            original_query=s.original_query,
            suggested_query=s.suggested_query,
            confidence=s.confidence,
            suggestion_type=s.suggestion_type,
            explanation=s.explanation
        ) for s in suggestions
    ]
    
    # Enhance results with personality context if available
    enhanced_results = results
    personality_context = None
    
    if results and hasattr(results[0], 'content_chunk') and results[0].content_chunk:
        system_name = results[0].content_chunk.system
        personality_summary = personality_manager.get_personality_summary(system_name)
        
        if personality_summary:
            personality_context = {
                "system_name": system_name,
                "personality_name": personality_summary.get("personality_name"),
                "tone": personality_summary.get("tone"),
                "perspective": personality_summary.get("perspective"),
                "example_phrases": personality_summary.get("example_phrases", [])[:3]
            }
    
    return {
        "results": enhanced_results,
        "suggestions": suggestion_responses,
        "personality_context": personality_context,
        "search_stats": {
            "total_results": len(results),
            "has_suggestions": len(suggestions) > 0,
            "search_type": "hybrid" if input.use_hybrid else "semantic",
            "personality_enhanced": personality_context is not None
        }
    }

@router.post("/manage_campaign")
async def manage_campaign(
    input: ManageCampaignInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager)
):
    if input.action == "create":
        if not input.data or not input.data_type:
            raise HTTPException(status_code=400, detail="Data and data_type are required for create action")
        data_id = chroma_manager.store_campaign_data(input.campaign_id, input.data_type, input.data)
        return {"status": "success", "data_id": data_id}
    
    elif input.action == "read":
        results = chroma_manager.get_campaign_data(input.campaign_id, input.data_type, input.data_id)
        return {"results": results}

    elif input.action == "update":
        if not input.data_id or not input.data or not input.data_type:
            raise HTTPException(status_code=400, detail="Data ID, data, and data_type are required for update action")
        success = chroma_manager.update_campaign_data(input.campaign_id, input.data_type, input.data_id, input.data)
        if not success:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"status": "success"}

    elif input.action == "delete":
        if not input.data_id or not input.data_type:
            raise HTTPException(status_code=400, detail="Data ID and data_type are required for delete action")
        success = chroma_manager.delete_campaign_data(input.campaign_id, input.data_type, input.data_id)
        if not success:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"status": "success"}

    elif input.action == "export":
        data = chroma_manager.export_campaign_data(input.campaign_id)
        return {"data": data}

    elif input.action == "import":
        if not input.data:
            raise HTTPException(status_code=400, detail="Data is required for import action")
        chroma_manager.import_campaign_data(input.campaign_id, input.data)
        return {"status": "success"}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.post("/add_source")
async def add_source(
    input: AddSourceInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    pdf_parser: PDFParser = Depends(get_pdf_parser),
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    # Use enhanced PDF parsing with adaptive learning
    chunks_data = pdf_parser.create_chunks(
        input.pdf_path, 
        rulebook_name=input.rulebook_name,
        system=input.system,
        source_type=input.source_type.value if hasattr(input.source_type, 'value') else str(input.source_type)
    )
    
    content_chunks = [
        ContentChunk(
            id=chunk['id'],
            rulebook=input.rulebook_name,
            system=input.system,
            source_type=input.source_type,
            # Use enhanced content type from adaptive processing if available
            content_type=chunk.get('content_type', 'text'),
            title=chunk['section']['title'] if chunk.get('section') and chunk['section'] else chunk.get('title', ''),
            content=chunk['text'],
            page_number=chunk['page_number'],
            section_path=chunk['section']['path'] if chunk.get('section') and chunk['section'] else [],
            embedding=b"",
            # Include enhanced metadata from adaptive processing
            metadata=chunk.get('metadata', {})
        ) for chunk in chunks_data
    ]
    
    chroma_manager.store_rulebook_content("rulebook_index", content_chunks)

    # Extract and store personality profile
    personality = personality_manager.extract_and_store_personality(content_chunks, input.system)
    
    # Get adaptive learning statistics if available
    stats = pdf_parser.get_adaptive_statistics(input.system)
    stats_message = ""
    if "error" not in stats:
        pattern_count = sum(stats.get('pattern_stats', {}).get(ct, {}).get('total_patterns', 0) 
                          for ct in stats.get('pattern_stats', {}))
        if pattern_count > 0:
            stats_message = f" Learned {pattern_count} content patterns."
    
    # Add personality information to success message
    personality_message = ""
    if personality:
        personality_message = f" Personality '{personality.personality_name}' extracted with {len(personality.vernacular_patterns)} vernacular terms."
    
    return {"status": "success", "message": f"Source '{input.rulebook_name}' added successfully.{stats_message}{personality_message}"}

@router.post("/get_rulebook_personality")
async def get_rulebook_personality(
    input: GetRulebookPersonalityInput,
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    personality = personality_manager.get_personality(input.rulebook_name)
    if not personality:
        raise HTTPException(status_code=404, detail="Personality not found for this rulebook.")
    return {"personality": personality.to_dict()}

@router.post("/get_character_creation_rules")
async def get_character_creation_rules(
    input: GetCharacterCreationRulesInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    query = "character creation rules"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    results = chroma_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=1,
        filters={"rulebook": input.rulebook_name, "source_type": "rulebook"}
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Character creation rules not found.")
        
    return {"rules": results[0].content_chunk.content}

@router.post("/generate_backstory")
async def generate_backstory(
    input: GenerateBackstoryInput,
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    # Get personality profiles
    personalities = []
    main_personality = personality_manager.get_personality(input.rulebook_name)
    if main_personality:
        personalities.append(main_personality.system_context + " - " + main_personality.description)
    
    for source in input.flavor_sources:
        source_personality = personality_manager.get_personality(source)
        if source_personality:
            personalities.append(source_personality.system_context + " - " + source_personality.description)
    
    backstory = f"This is a generated backstory for a character in {input.rulebook_name}.\n"
    backstory += f"Character details: {input.character_details}\n"
    if input.player_params:
        backstory += f"Player parameters: {input.player_params}\n"
    
    if personalities:
        backstory += f"\n--- Setting Context ---\n" + "\n".join(personalities)
    
    return {"backstory": backstory}

@router.post("/generate_npc")
async def generate_npc(
    input: GenerateNPCInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    # Get personality profiles
    personalities = []
    main_personality = personality_manager.get_personality(input.rulebook_name)
    if main_personality:
        personalities.append(main_personality.system_context + " - " + main_personality.description)
    
    for source in input.flavor_sources:
        source_personality = personality_manager.get_personality(source)
        if source_personality:
            personalities.append(source_personality.system_context + " - " + source_personality.description)

    query = "monster stat block or non-player character"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    examples = chroma_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=3,
        filters={"rulebook": input.rulebook_name, "source_type": "rulebook"}
    )
    
    npc = f"This is a generated NPC for {input.rulebook_name}.\n"
    npc += f"Player level: {input.player_level}\n"
    npc += f"Description: {input.npc_description}\n"
    
    if examples:
        npc += "\n--- Examples from the rulebook ---\n"
        for example in examples:
            npc += f"- {example.content_chunk.title}: {example.content_chunk.content}\n"
    
    if personalities:
        npc += f"\n--- Setting Context ---\n" + "\n".join(personalities)
    
    return {"npc": npc}

@router.post("/manage_session")
async def manage_session(
    input: ManageSessionInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager)
):
    if input.action == "start":
        if chroma_manager.session_exists(input.campaign_id, input.session_id):
            raise HTTPException(status_code=400, detail="Session already exists.")
        
        initial_data = {
            "notes": [],
            "initiative_order": [],
            "monsters": []
        }
        chroma_manager.store_session_data(input.campaign_id, input.session_id, initial_data)
        return {"status": "success", "message": "Session started."}

    # Get existing session data
    session_data = chroma_manager.get_session_data(input.campaign_id, input.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found.")

    notes = session_data.get("notes", [])
    initiative_order = session_data.get("initiative_order", [])
    monsters = session_data.get("monsters", [])

    if input.action == "add_note":
        if not input.data or "note" not in input.data:
            raise HTTPException(status_code=400, detail="Note data is required.")
        notes.append(input.data['note'])
        chroma_manager.update_session_data(input.campaign_id, input.session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif input.action == "set_initiative":
        if not input.data or "order" not in input.data:
            raise HTTPException(status_code=400, detail="Initiative order data is required.")
        initiative_order = [InitiativeEntry(**e).model_dump() for e in input.data['order']]
        chroma_manager.update_session_data(input.campaign_id, input.session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif input.action == "add_monster":
        if not input.data or "monster" not in input.data:
            raise HTTPException(status_code=400, detail="Monster data is required.")
        monster = MonsterState(**input.data['monster'])
        monsters.append(monster.model_dump())
        chroma_manager.update_session_data(input.campaign_id, input.session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif input.action == "update_monster_hp":
        if not input.data or "name" not in input.data or "hp" not in input.data:
            raise HTTPException(status_code=400, detail="Monster name and hp are required.")
        for monster in monsters:
            if monster['name'] == input.data['name']:
                monster['current_hp'] = input.data['hp']
                break
        chroma_manager.update_session_data(input.campaign_id, input.session_id, {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        })
        return {"status": "success"}

    elif input.action == "get":
        return {
            "notes": notes,
            "initiative_order": initiative_order,
            "monsters": monsters
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.post("/generate_map")
async def generate_map(
    input: MapGenerationInput
):
    map_generator = MapGenerator(input.width, input.height)
    svg_map = map_generator.generate_map(input.map_description)
    return {"map": svg_map}

@router.post("/manage_personality")
async def manage_personality(
    input: ManagePersonalityInput,
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    """Manage RPG personality profiles and vernacular"""
    
    if input.action == "get":
        if not input.system_name:
            raise HTTPException(status_code=400, detail="system_name is required for get action")
        
        personality = personality_manager.get_personality(input.system_name)
        if not personality:
            raise HTTPException(status_code=404, detail=f"No personality profile found for {input.system_name}")
        
        return {"personality": personality.to_dict()}
    
    elif input.action == "list":
        personalities = personality_manager.list_personalities()
        return {"personalities": personalities}
    
    elif input.action == "summary":
        if not input.system_name:
            raise HTTPException(status_code=400, detail="system_name is required for summary action")
        
        summary = personality_manager.get_personality_summary(input.system_name)
        if not summary:
            raise HTTPException(status_code=404, detail=f"No personality profile found for {input.system_name}")
        
        return {"summary": summary}
    
    elif input.action == "vernacular":
        if not input.system_name:
            raise HTTPException(status_code=400, detail="system_name is required for vernacular action")
        
        vernacular = personality_manager.get_vernacular_for_system(input.system_name)
        return {
            "system_name": input.system_name,
            "vernacular": vernacular,
            "count": len(vernacular)
        }
    
    elif input.action == "compare":
        if not input.systems or len(input.systems) < 2:
            raise HTTPException(status_code=400, detail="at least 2 systems are required for comparison")
        
        comparison = personality_manager.create_personality_comparison(input.systems)
        return {"comparison": comparison}
    
    elif input.action == "stats":
        stats = personality_manager.get_personality_stats()
        return {"stats": stats}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {input.action}")

@router.post("/create_content_pack")
async def create_content_pack(
    input: CreateContentPackInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    personality_manager: PersonalityManager = Depends(get_personality_manager)
):
    # This is a simplified implementation. A real implementation would need to
    # retrieve the actual chunks for the given source.
    chunks = []
    personality = personality_manager.get_personality(input.source_name)
    
    packager = ContentPackager()
    packager.create_pack(chunks, personality.to_dict() if personality else None, input.output_path)
    
    return {"status": "success", "message": f"Content pack created at {input.output_path}"}

@router.post("/install_content_pack")
async def install_content_pack(
    input: InstallContentPackInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager)
):
    packager = ContentPackager()
    chunks, personality = packager.load_pack(input.pack_path)
    
    # This is a simplified implementation. A real implementation would need to
    # properly store the chunks and personality.
    
    return {"status": "success", "message": "Content pack installed."}

@router.post("/quick_search")
async def quick_search(
    input: QuickSearchInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Quick search without extensive query processing for simple lookups"""
    search_service = EnhancedSearchService(chroma_manager, embedding_service)
    results = await search_service.quick_search(input.query, input.max_results)
    
    return {
        "results": results,
        "query": input.query,
        "search_type": "quick"
    }

@router.post("/suggest_completions")
async def suggest_completions(
    input: QueryCompletionInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Get query completion suggestions based on vocabulary"""
    search_service = EnhancedSearchService(chroma_manager, embedding_service)
    completions = await search_service.suggest_completions(input.partial_query, input.limit)
    
    return {
        "completions": completions,
        "partial_query": input.partial_query
    }

@router.post("/explain_search")
async def explain_search(
    input: SearchExplanationInput,
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Get explanation of why certain search results were returned"""
    search_service = EnhancedSearchService(chroma_manager, embedding_service)
    
    # Get results for the query
    results, _ = await search_service.search(input.query, max_results=10)
    
    # Filter to specific result IDs if provided
    if input.result_ids:
        results = [r for r in results if r.content_chunk.id in input.result_ids]
    
    explanation = await search_service.explain_search_results(input.query, results)
    
    return {
        "explanation": explanation,
        "query": input.query
    }

@router.get("/search_stats")
async def get_search_stats(
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Get statistics about the search service"""
    search_service = EnhancedSearchService(chroma_manager, embedding_service)
    stats = search_service.get_search_statistics()
    
    return {"stats": stats}

@router.get("/list_rulebooks")
async def list_rulebooks(
    chroma_manager: ChromaDataManager = Depends(get_chroma_manager)
):
    """List all available rulebooks with basic statistics"""
    try:
        # Get all collections
        collections = chroma_manager.list_collections()
        
        # Filter for rulebook-related collections and get stats
        rulebooks = []
        for collection_name in collections:
            if collection_name == "rulebook_index":
                # Get the rulebook_index collection to find unique rulebooks
                collection = chroma_manager._get_or_create_collection(collection_name)
                
                # Get all documents to extract unique rulebooks
                try:
                    results = collection.get()
                    if results and results.get('metadatas'):
                        # Extract unique rulebooks from metadata
                        rulebook_names = set()
                        for metadata in results['metadatas']:
                            if metadata.get('rulebook'):
                                rulebook_names.add(metadata['rulebook'])
                        
                        # Get stats for each rulebook
                        for rulebook_name in rulebook_names:
                            # Count documents for this rulebook
                            rulebook_results = collection.get(
                                where={"rulebook": rulebook_name}
                            )
                            
                            doc_count = len(rulebook_results.get('ids', [])) if rulebook_results else 0
                            
                            # Get system info if available
                            system = None
                            if rulebook_results and rulebook_results.get('metadatas'):
                                for metadata in rulebook_results['metadatas']:
                                    if metadata.get('system'):
                                        system = metadata['system']
                                        break
                            
                            rulebooks.append({
                                "name": rulebook_name,
                                "system": system or "Unknown",
                                "document_count": doc_count,
                                "collection": collection_name
                            })
                except Exception as e:
                    logger.error(f"Error getting stats for collection {collection_name}: {e}")
                    continue
        
        # Sort by name
        rulebooks.sort(key=lambda x: x['name'])
        
        return {
            "rulebooks": rulebooks,
            "total_count": len(rulebooks)
        }
    except Exception as e:
        logger.error(f"Error listing rulebooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list rulebooks: {str(e)}")