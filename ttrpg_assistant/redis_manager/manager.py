import redis
import yaml
from typing import Dict, Any, List
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.data_models.models import ContentChunk, SearchResult, CampaignData
import numpy as np
import json
import uuid

class RedisDataManager:
    """Handles all Redis operations for both vector and traditional data"""

    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.redis_client = self.connect()
        self.embedding_service = EmbeddingService()

    def connect(self):
        """Create a Redis connection"""
        redis_config = self.config['redis']
        try:
            r = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                password=redis_config.get('password'),
                decode_responses=True # Use True for campaign data
            )
            r.ping()
            return r
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            return None

    def setup_vector_index(self, index_name: str, schema: Dict) -> None:
        """Create vector search index"""
        try:
            self.redis_client.ft(index_name).info()
            print(f"Index '{index_name}' already exists.")
        except redis.exceptions.ResponseError:
            # Index does not exist, so create it
            self.redis_client.ft(index_name).create_index(
                fields=schema,
                definition=IndexDefinition(prefix=[f"{index_name}:"], index_type=IndexType.JSON)
            )
            print(f"Created index '{index_name}'.")


    def store_rulebook_content(self, index_name: str, content: List[ContentChunk]) -> None:
        """Store parsed rulebook with embeddings"""
        # Switch to non-decoded responses for storing embeddings
        self.redis_client.decode_responses = False
        pipeline = self.redis_client.pipeline()
        for chunk in content:
            embedding = self.embedding_service.generate_embedding(chunk.content)
            chunk.embedding = np.array(embedding, dtype=np.float32).tobytes()
            pipeline.json().set(f"{index_name}:{chunk.id}", "$", chunk.model_dump())
        pipeline.execute()
        self.redis_client.decode_responses = True

    def store_rulebook_personality(self, rulebook_name: str, personality_text: str) -> None:
        """Stores the personality text for a rulebook."""
        key = f"rulebook_personality:{rulebook_name}"
        self.redis_client.set(key, personality_text)

    def get_rulebook_personality(self, rulebook_name: str) -> str:
        """Retrieves the personality text for a rulebook."""
        key = f"rulebook_personality:{rulebook_name}"
        return self.redis_client.get(key)


    def vector_search(self, index_name: str, query_embedding: np.ndarray, num_results: int = 5, filters: str = "*") -> List[SearchResult]:
        """Perform semantic search"""
        self.redis_client.decode_responses = False
        query = (
            Query(f"{filters}=>[KNN {num_results} @vector $query_vector AS vector_score]")
            .sort_by("vector_score")
            .return_fields("id", "vector_score", "$")
            .dialect(2)
        )
        
        query_params = {"query_vector": query_embedding.astype(np.float32).tobytes()}
        
        results = self.redis_client.ft(index_name).search(query, query_params).docs
        
        search_results = []
        for doc in results:
            content_chunk = ContentChunk.model_validate_json(doc.json)
            search_results.append(SearchResult(
                content_chunk=content_chunk,
                relevance_score=doc.vector_score,
                match_type="semantic"
            ))
        self.redis_client.decode_responses = True
        return search_results


    def store_campaign_data(self, campaign_id: str, data_type: str, data: Dict) -> str:
        """Store campaign information"""
        data_id = str(uuid.uuid4())
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        
        campaign_data = CampaignData(
            id=data_id,
            campaign_id=campaign_id,
            data_type=data_type,
            name=data.get("name", ""),
            content=data,
            version=1
        )
        
        self.redis_client.hset(key, mapping=campaign_data.model_dump())
        return data_id

    def get_campaign_data(self, campaign_id: str, data_type: str = None, data_id: str = None) -> List[Dict]:
        """Retrieve campaign information"""
        if data_id:
            pattern = f"campaign:{campaign_id}:{data_type}:{data_id}"
        elif data_type:
            pattern = f"campaign:{campaign_id}:{data_type}:*"
        else:
            pattern = f"campaign:{campaign_id}:*:*"
            
        keys = self.redis_client.keys(pattern)
        if not keys:
            return []
            
        data = []
        for key in keys:
            data.append(self.redis_client.hgetall(key))
        return data

    def update_campaign_data(self, campaign_id: str, data_type: str, data_id: str, data: Dict) -> bool:
        """Update campaign information"""
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        if not self.redis_client.exists(key):
            return False
        
        # Increment version
        version = int(self.redis_client.hget(key, "version")) + 1
        data['version'] = version
        
        self.redis_client.hset(key, mapping=data)
        return True

    def delete_campaign_data(self, campaign_id: str, data_type: str, data_id: str) -> bool:
        """Delete campaign information"""
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        return self.redis_client.delete(key) > 0

    def export_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        """Export all data for a campaign"""
        keys = self.redis_client.keys(f"campaign:{campaign_id}:*:*")
        if not keys:
            return {}
            
        campaign_data = {}
        for key in keys:
            data_type = key.split(":")[2]
            if data_type not in campaign_data:
                campaign_data[data_type] = []
            campaign_data[data_type].append(self.redis_client.hgetall(key))
            
        return campaign_data

    def import_campaign_data(self, campaign_id: str, data: Dict[str, Any]) -> None:
        """Import campaign data"""
        for data_type, items in data.items():
            for item in items:
                self.store_campaign_data(campaign_id, data_type, item)
