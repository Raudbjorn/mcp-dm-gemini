from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timezone

class ContentChunk(BaseModel):
    id: str
    rulebook: str
    system: str  # D&D 5e, Pathfinder, etc.
    content_type: str  # rule, spell, monster, item
    title: str
    content: str
    page_number: int
    section_path: List[str]  # ["Chapter 1", "Combat", "Attack Rolls"]
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
    match_type: str  # "semantic", "keyword", "exact"
    highlighted_text: str = None