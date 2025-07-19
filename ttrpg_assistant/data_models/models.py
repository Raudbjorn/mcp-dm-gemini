from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class SourceType(str, Enum):
    RULEBOOK = "rulebook"
    FLAVOR = "flavor"

class ContentChunk(BaseModel):
    id: str
    rulebook: str
    system: str
    source_type: SourceType = SourceType.RULEBOOK
    content_type: str
    title: str
    content: str
    page_number: int
    section_path: List[str]
    embedding: bytes
    metadata: Dict[str, Any]
    tables: List[Any] = []

class CampaignData(BaseModel):
    id: str
    campaign_id: str
    data_type: str
    name: str
    content: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int
    tags: List[str] = None

class SearchResult(BaseModel):
    content_chunk: ContentChunk
    relevance_score: float
    match_type: str
    highlighted_text: str = None

class InitiativeEntry(BaseModel):
    name: str
    initiative: int

class MonsterState(BaseModel):
    name: str
    max_hp: int
    current_hp: int

class SessionData(CampaignData):
    notes: List[str] = []
    initiative_order: List[InitiativeEntry] = []
    monsters: List[MonsterState] = []

class MapGenerationInput(BaseModel):
    rulebook_name: str
    map_description: str
    width: int = 20
    height: int = 20

class SearchInput(BaseModel):
    query: str
    rulebook: str = None
    source_type: SourceType = None
    content_type: str = None
    max_results: int = 5

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