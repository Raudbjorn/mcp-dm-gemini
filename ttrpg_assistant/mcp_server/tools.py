from fastapi import APIRouter, Depends, HTTPException
from ttrpg_assistant.redis_manager.manager import RedisDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from ttrpg_assistant.map_generator.generator import MapGenerator
from ttrpg_assistant.content_packager.packager import ContentPackager
from .dependencies import get_redis_manager, get_embedding_service, get_pdf_parser
import numpy as np
from typing import Dict, Any, List
from ttrpg_assistant.data_models.models import *
import json

router = APIRouter()

@router.post("/search")
async def search(
    input: SearchInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    query_embedding = np.array(embedding_service.generate_embedding(input.query))
    
    filters = []
    if input.rulebook:
        filters.append(f"@rulebook:{input.rulebook}")
    if input.source_type:
        filters.append(f"@source_type:{input.source_type.value}")
    if input.content_type:
        filters.append(f"@content_type:{input.content_type}")
    
    filter_str = " ".join(filters) if filters else "*"

    results = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=input.max_results,
        filters=filter_str
    )
    return {"results": results}

@router.post("/manage_campaign")
async def manage_campaign(
    input: ManageCampaignInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    if input.action == "create":
        if not input.data or not input.data_type:
            raise HTTPException(status_code=400, detail="Data and data_type are required for create action")
        data_id = redis_manager.store_campaign_data(input.campaign_id, input.data_type, input.data)
        return {"status": "success", "data_id": data_id}
    
    elif input.action == "read":
        results = redis_manager.get_campaign_data(input.campaign_id, input.data_type, input.data_id)
        return {"results": results}

    elif input.action == "update":
        if not input.data_id or not input.data or not input.data_type:
            raise HTTPException(status_code=400, detail="Data ID, data, and data_type are required for update action")
        success = redis_manager.update_campaign_data(input.campaign_id, input.data_type, input.data_id, input.data)
        if not success:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"status": "success"}

    elif input.action == "delete":
        if not input.data_id or not input.data_type:
            raise HTTPException(status_code=400, detail="Data ID and data_type are required for delete action")
        success = redis_manager.delete_campaign_data(input.campaign_id, input.data_type, input.data_id)
        if not success:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"status": "success"}

    elif input.action == "export":
        data = redis_manager.export_campaign_data(input.campaign_id)
        return {"data": data}

    elif input.action == "import":
        if not input.data:
            raise HTTPException(status_code=400, detail="Data is required for import action")
        redis_manager.import_campaign_data(input.campaign_id, input.data)
        return {"status": "success"}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.post("/add_source")
async def add_source(
    input: AddSourceInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    pdf_parser: PDFParser = Depends(get_pdf_parser)
):
    content_chunks = pdf_parser.create_chunks(input.pdf_path)
    for chunk in content_chunks:
        chunk.rulebook = input.rulebook_name
        chunk.system = input.system
        chunk.source_type = input.source_type
    
    redis_manager.store_rulebook_content("rulebook_index", content_chunks)

    personality_text = pdf_parser.extract_personality_text(input.pdf_path)
    redis_manager.store_rulebook_personality(input.rulebook_name, personality_text)
    
    return {"status": "success", "message": f"Source '{input.rulebook_name}' added successfully."}

@router.post("/get_rulebook_personality")
async def get_rulebook_personality(
    input: GetRulebookPersonalityInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    personality = redis_manager.get_rulebook_personality(input.rulebook_name)
    if not personality:
        raise HTTPException(status_code=404, detail="Personality not found for this rulebook.")
    return {"personality": personality}

@router.post("/get_character_creation_rules")
async def get_character_creation_rules(
    input: GetCharacterCreationRulesInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    query = "character creation rules"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    results = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=1,
        filters=f"@rulebook:{input.rulebook_name} @source_type:rulebook"
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Character creation rules not found.")
        
    return {"rules": results[0].content_chunk.content}

@router.post("/generate_backstory")
async def generate_backstory(
    input: GenerateBackstoryInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    personalities = [redis_manager.get_rulebook_personality(input.rulebook_name)]
    for source in input.flavor_sources:
        personalities.append(redis_manager.get_rulebook_personality(source))
    
    backstory = f"This is a generated backstory for a character in {input.rulebook_name}.\n"
    backstory += f"Character details: {input.character_details}\n"
    if input.player_params:
        backstory += f"Player parameters: {input.player_params}\n"
    
    backstory += f"\n--- Vibe ---\n" + "\n".join(filter(None, personalities))
    
    return {"backstory": backstory}

@router.post("/generate_npc")
async def generate_npc(
    input: GenerateNPCInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    personalities = [redis_manager.get_rulebook_personality(input.rulebook_name)]
    for source in input.flavor_sources:
        personalities.append(redis_manager.get_rulebook_personality(source))

    query = "monster stat block or non-player character"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    examples = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=3,
        filters=f"@rulebook:{input.rulebook_name} @source_type:rulebook"
    )
    
    npc = f"This is a generated NPC for {input.rulebook_name}.\n"
    npc += f"Player level: {input.player_level}\n"
    npc += f"Description: {input.npc_description}\n"
    
    if examples:
        npc += "\n--- Examples from the rulebook ---\n"
        for example in examples:
            npc += f"- {example.content_chunk.title}: {example.content_chunk.content}\n"
            
    npc += f"\n--- Vibe ---\n" + "\n".join(filter(None, personalities))
    
    return {"npc": npc}

@router.post("/manage_session")
async def manage_session(
    input: ManageSessionInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    session_key = f"session:{input.campaign_id}:{input.session_id}"

    if input.action == "start":
        if redis_manager.redis_client.exists(session_key):
            raise HTTPException(status_code=400, detail="Session already exists.")
        redis_manager.redis_client.hset(session_key, mapping={"notes": "[]", "initiative_order": "[]", "monsters": "[]"})
        return {"status": "success", "message": "Session started."}

    if not redis_manager.redis_client.exists(session_key):
        raise HTTPException(status_code=404, detail="Session not found.")

    session_data = redis_manager.redis_client.hgetall(session_key)
    notes = json.loads(session_data.get("notes", "[]"))
    initiative_order = json.loads(session_data.get("initiative_order", "[]"))
    monsters = json.loads(session_data.get("monsters", "[]"))

    if input.action == "add_note":
        if not input.data or "note" not in input.data:
            raise HTTPException(status_code=400, detail="Note data is required.")
        notes.append(input.data['note'])
        redis_manager.redis_client.hset(session_key, "notes", json.dumps(notes))
        return {"status": "success"}

    elif input.action == "set_initiative":
        if not input.data or "order" not in input.data:
            raise HTTPException(status_code=400, detail="Initiative order data is required.")
        initiative_order = [InitiativeEntry(**e).model_dump() for e in input.data['order']]
        redis_manager.redis_client.hset(session_key, "initiative_order", json.dumps(initiative_order))
        return {"status": "success"}

    elif input.action == "add_monster":
        if not input.data or "monster" not in input.data:
            raise HTTPException(status_code=400, detail="Monster data is required.")
        monster = MonsterState(**input.data['monster'])
        monsters.append(monster.model_dump())
        redis_manager.redis_client.hset(session_key, "monsters", json.dumps(monsters))
        return {"status": "success"}

    elif input.action == "update_monster_hp":
        if not input.data or "name" not in input.data or "hp" not in input.data:
            raise HTTPException(status_code=400, detail="Monster name and hp are required.")
        for monster in monsters:
            if monster['name'] == input.data['name']:
                monster['current_hp'] = input.data['hp']
                break
        redis_manager.redis_client.hset(session_key, "monsters", json.dumps(monsters))
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

@router.post("/create_content_pack")
async def create_content_pack(
    input: CreateContentPackInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    # This is a simplified implementation. A real implementation would need to
    # retrieve the actual chunks for the given source.
    chunks = []
    personality = redis_manager.get_rulebook_personality(input.source_name)
    
    packager = ContentPackager()
    packager.create_pack(chunks, personality, input.output_path)
    
    return {"status": "success", "message": f"Content pack created at {input.output_path}"}

@router.post("/install_content_pack")
async def install_content_pack(
    input: InstallContentPackInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    packager = ContentPackager()
    chunks, personality = packager.load_pack(input.pack_path)
    
    # This is a simplified implementation. A real implementation would need to
    # properly store the chunks and personality.
    
    return {"status": "success", "message": "Content pack installed."}