from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ttrpg_assistant.redis_manager.manager import RedisDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from .dependencies import get_redis_manager, get_embedding_service, get_pdf_parser
import numpy as np
from typing import Dict, Any, List
from ttrpg_assistant.data_models.models import ContentChunk

router = APIRouter()

class SearchRulebookInput(BaseModel):
    query: str
    rulebook: str = None
    content_type: str = None
    max_results: int = 5

class ManageCampaignInput(BaseModel):
    action: str
    campaign_id: str
    data_type: str = None
    data_id: str = None
    data: Dict[str, Any] = None

class AddRulebookInput(BaseModel):
    pdf_path: str
    rulebook_name: str
    system: str

class GetRulebookPersonalityInput(BaseModel):
    rulebook_name: str

class GetCharacterCreationRulesInput(BaseModel):
    rulebook_name: str

class GenerateBackstoryInput(BaseModel):
    rulebook_name: str
    character_details: Dict[str, Any]
    player_params: str = None

class GenerateNPCInput(BaseModel):
    rulebook_name: str
    player_level: int
    npc_description: str


@router.post("/search_rulebook")
async def search_rulebook(
    input: SearchRulebookInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    query_embedding = np.array(embedding_service.generate_embedding(input.query))
    
    filters = []
    if input.rulebook:
        filters.append(f"@rulebook:{input.rulebook}")
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

@router.post("/add_rulebook")
async def add_rulebook(
    input: AddRulebookInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    pdf_parser: PDFParser = Depends(get_pdf_parser)
):
    # This is a simplified implementation. A real implementation would need to handle
    # duplicate detection and progress reporting.
    
    chunks_data = pdf_parser.create_chunks(input.pdf_path)
    
    content_chunks = [
        ContentChunk(
            id=chunk['id'],
            rulebook=input.rulebook_name,
            system=input.system,
            content_type="rule", # This is a simplification
            title=chunk['section']['title'] if chunk.get('section') else '',
            content=chunk['text'],
            page_number=chunk['page_number'],
            section_path=chunk['section']['path'] if chunk.get('section') else [],
            embedding=b"",
            metadata={}
        ) for chunk in chunks_data
    ]
    
    redis_manager.store_rulebook_content("rulebook_index", content_chunks)

    # Extract and store personality
    personality_text = pdf_parser.extract_personality_text(input.pdf_path)
    redis_manager.store_rulebook_personality(input.rulebook_name, personality_text)
    
    return {"status": "success", "message": f"Rulebook '{input.rulebook_name}' added successfully."}

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
        filters=f"@rulebook:{input.rulebook_name}"
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Character creation rules not found.")
        
    return {"rules": results[0].content_chunk.content}

@router.post("/generate_backstory")
async def generate_backstory(
    input: GenerateBackstoryInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager)
):
    personality = redis_manager.get_rulebook_personality(input.rulebook_name)
    if not personality:
        raise HTTPException(status_code=404, detail="Personality not found for this rulebook.")

    # This is a simplified implementation. A real implementation would use a powerful
    # generative model to create a backstory.
    
    backstory = f"This is a generated backstory for a character in {input.rulebook_name}.\n"
    backstory += f"Character details: {input.character_details}\n"
    if input.player_params:
        backstory += f"Player parameters: {input.player_params}\n"
    
    backstory += f"\n--- Rulebook Vibe ---\n{personality}"
    
    return {"backstory": backstory}

@router.post("/generate_npc")
async def generate_npc(
    input: GenerateNPCInput,
    redis_manager: RedisDataManager = Depends(get_redis_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    personality = redis_manager.get_rulebook_personality(input.rulebook_name)
    if not personality:
        raise HTTPException(status_code=404, detail="Personality not found for this rulebook.")

    # Find relevant examples of NPCs or monsters
    query = "monster stat block or non-player character"
    query_embedding = np.array(embedding_service.generate_embedding(query))
    
    examples = redis_manager.vector_search(
        index_name="rulebook_index",
        query_embedding=query_embedding,
        num_results=3,
        filters=f"@rulebook:{input.rulebook_name}"
    )
    
    # This is a simplified implementation. A real implementation would use a powerful
    # generative model to create an NPC.
    
    npc = f"This is a generated NPC for {input.rulebook_name}.\n"
    npc += f"Player level: {input.player_level}\n"
    npc += f"Description: {input.npc_description}\n"
    
    if examples:
        npc += "\n--- Examples from the rulebook ---\n"
        for example in examples:
            npc += f"- {example.content_chunk.title}: {example.content_chunk.content}\n"
            
    npc += f"\n--- Rulebook Vibe ---\n{personality}"
    
    return {"npc": npc}
