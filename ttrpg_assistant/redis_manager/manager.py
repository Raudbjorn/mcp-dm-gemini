import redis
import numpy as np
from typing import List, Dict, Any
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from ttrpg_assistant.data_models.models import ContentChunk, SearchResult
from ttrpg_assistant.logger import logger
import uuid
import json
from enum import Enum

class RedisDataManager:
    def __init__(self, host='localhost', port=6379):
        try:
            self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise e

    def create_index(self, index_name: str, schema: List[Any]):
        try:
            self.redis_client.ft(index_name).info()
            logger.info(f"Index '{index_name}' already exists.")
        except redis.exceptions.ResponseError:
            definition = IndexDefinition(prefix=[f"{index_name}:"], index_type=IndexType.HASH)
            self.redis_client.ft(index_name).create_index(fields=schema, definition=definition)
            logger.info(f"Created index '{index_name}'.")

    def store_rulebook_content(self, index_name: str, content_chunks: List[ContentChunk]):
        pipe = self.redis_client.pipeline()
        for chunk in content_chunks:
            key = f"{index_name}:{chunk.id}"
            # Convert the entire chunk to a dictionary, then serialize complex fields to JSON strings
            chunk_dict = chunk.model_dump()
            for field, value in chunk_dict.items():
                if isinstance(value, (dict, list)):
                    chunk_dict[field] = json.dumps(value)
                elif isinstance(value, Enum):
                    chunk_dict[field] = value.value
            pipe.hset(key, mapping=chunk_dict)
        pipe.execute()
        logger.info(f"Stored {len(content_chunks)} content chunks in '{index_name}'.")

    def store_rulebook_personality(self, rulebook_name: str, personality: str):
        key = f"personality:{rulebook_name}"
        self.redis_client.set(key, personality)
        logger.info(f"Stored personality for '{rulebook_name}'.")

    def get_rulebook_personality(self, rulebook_name: str) -> str:
        key = f"personality:{rulebook_name}"
        personality = self.redis_client.get(key)
        logger.info(f"Retrieved personality for '{rulebook_name}'.")
        return personality

    def vector_search(self, index_name: str, query_embedding: np.ndarray, num_results: int, filters: str = "*") -> List[SearchResult]:
        query = (
            Query(f"{filters}=>[KNN {num_results} @embedding $query_vec as score]")
            .sort_by("score")
            .return_fields("id", "rulebook", "system", "source_type", "content_type", "title", "content", "page_number", "section_path", "score")
            .dialect(2)
        )
        
        query_params = {"query_vec": query_embedding.astype(np.float32).tobytes()}
        
        results = self.redis_client.ft(index_name).search(query, query_params).docs
        
        search_results = []
        for doc in results:
            content_chunk = ContentChunk(
                id=doc.id,
                rulebook=doc.rulebook,
                system=doc.system,
                source_type=doc.source_type,
                content_type=doc.content_type,
                title=doc.title,
                content=doc.content,
                page_number=int(doc.page_number),
                section_path=eval(doc.section_path),
                embedding=b"",
                metadata={}
            )
            search_results.append(SearchResult(content_chunk=content_chunk, relevance_score=float(doc.score), match_type="semantic"))
            
        logger.info(f"Performed vector search on '{index_name}' and found {len(search_results)} results.")
        return search_results

    def store_campaign_data(self, campaign_id: str, data_type: str, data: Dict[str, Any]) -> str:
        data_id = data.get("id", None) or str(uuid.uuid4())
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        self.redis_client.hset(key, mapping=data)
        logger.info(f"Stored data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
        return data_id

    def get_campaign_data(self, campaign_id: str, data_type: str, data_id: str = None) -> List[Dict[str, Any]]:
        if data_id:
            key = f"campaign:{campaign_id}:{data_type}:{data_id}"
            data = self.redis_client.hgetall(key)
            logger.info(f"Retrieved data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
            return [data] if data else []
        else:
            keys = self.redis_client.keys(f"campaign:{campaign_id}:{data_type}:*")
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.hgetall(key)
            results = pipe.execute()
            logger.info(f"Retrieved {len(results)} data entries for campaign '{campaign_id}' of type '{data_type}'.")
            return results

    def update_campaign_data(self, campaign_id: str, data_type: str, data_id: str, data: Dict[str, Any]) -> bool:
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        if not self.redis_client.exists(key):
            logger.warning(f"Data not found for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
            return False
        self.redis_client.hset(key, mapping=data)
        logger.info(f"Updated data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
        return True

    def delete_campaign_data(self, campaign_id: str, data_type: str, data_id: str) -> bool:
        key = f"campaign:{campaign_id}:{data_type}:{data_id}"
        if not self.redis_client.exists(key):
            logger.warning(f"Data not found for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
            return False
        self.redis_client.delete(key)
        logger.info(f"Deleted data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
        return True

    def export_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        keys = self.redis_client.keys(f"campaign:{campaign_id}:*")
        pipe = self.redis_client.pipeline()
        for key in keys:
            pipe.hgetall(key)
        results = pipe.execute()
        
        data = {}
        for i, key in enumerate(keys):
            data_type = key.split(":")[2]
            if data_type not in data:
                data[data_type] = []
            data[data_type].append(results[i])
            
        logger.info(f"Exported campaign data for '{campaign_id}'.")
        return data

    def import_campaign_data(self, campaign_id: str, data: Dict[str, Any]):
        for data_type, items in data.items():
            for item in items:
                self.store_campaign_data(campaign_id, data_type, item)
        logger.info(f"Imported campaign data for '{campaign_id}'.")
