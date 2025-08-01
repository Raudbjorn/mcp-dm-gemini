import chromadb
import numpy as np
import json
import uuid
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum

from ttrpg_assistant.data_models.models import ContentChunk, SearchResult
from ttrpg_assistant.logger import logger


class ChromaDataManager:
    """Handles all ChromaDB operations for both vector and traditional data"""

    def __init__(self, config_path: str = "config/config.yaml", persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client with persistent storage"""
        # Load config if it exists
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
            logger.warning(f"Config file {config_path} not found, using defaults")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            logger.info(f"Successfully connected to ChromaDB at {persist_directory}")
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            raise e
        
        # Collection for campaign data (using ChromaDB's document storage)
        self.campaign_collection = self._get_or_create_collection("campaign_data")

    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name)
        except (ValueError, Exception) as e:
            # Collection doesn't exist, create it
            logger.info(f"Creating collection '{name}' (error: {e})")
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

    def setup_vector_index(self, index_name: str, schema: Dict = None):
        """Create a collection (ChromaDB equivalent of Redis index)"""
        try:
            collection = self.client.get_collection(index_name)
            logger.info(f"Collection '{index_name}' already exists.")
            return collection
        except ValueError:
            collection = self.client.create_collection(
                name=index_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created collection '{index_name}'.")
            return collection

    def create_index(self, index_name: str, schema: List[Any] = None):
        """Create a collection (ChromaDB equivalent of Redis index) - for compatibility"""
        return self.setup_vector_index(index_name, schema)

    def store_rulebook_content(self, index_name: str, content_chunks: List[ContentChunk]):
        """Store content chunks in ChromaDB collection"""
        collection = self._get_or_create_collection(index_name)
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in content_chunks:
            ids.append(chunk.id)
            documents.append(chunk.content)
            
            # Convert embedding from bytes if needed
            if isinstance(chunk.embedding, bytes) and len(chunk.embedding) > 0:
                embedding = np.frombuffer(chunk.embedding, dtype=np.float32)
            elif isinstance(chunk.embedding, np.ndarray):
                embedding = chunk.embedding.astype(np.float32)
            else:
                # If no embedding, ChromaDB can generate one automatically
                embedding = None
            
            if embedding is not None:
                embeddings.append(embedding.tolist())
            
            # Prepare metadata (ChromaDB doesn't support nested objects directly)
            metadata = {
                "rulebook": chunk.rulebook,
                "system": chunk.system,
                "source_type": chunk.source_type.value if isinstance(chunk.source_type, Enum) else str(chunk.source_type),
                "content_type": chunk.content_type,
                "title": chunk.title,
                "page_number": chunk.page_number,
                "section_path": json.dumps(chunk.section_path),  # Serialize list as JSON
            }
            
            # Add any additional metadata
            if chunk.metadata:
                for key, value in chunk.metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[f"meta_{key}"] = value
                    else:
                        metadata[f"meta_{key}"] = json.dumps(value)
            
            metadatas.append(metadata)
        
        # Add to collection
        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        else:
            # Let ChromaDB generate embeddings
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        
        logger.info(f"Stored {len(content_chunks)} content chunks in '{index_name}'.")

    def store_rulebook_personality(self, rulebook_name: str, personality: str):
        """Store personality text in a dedicated collection"""
        personality_collection = self._get_or_create_collection("personalities")
        
        personality_collection.upsert(
            ids=[f"personality_{rulebook_name}"],
            documents=[personality],
            metadatas=[{"rulebook": rulebook_name, "type": "personality"}]
        )
        logger.info(f"Stored personality for '{rulebook_name}'.")

    def get_rulebook_personality(self, rulebook_name: str) -> Optional[str]:
        """Retrieve personality text"""
        personality_collection = self._get_or_create_collection("personalities")
        
        try:
            results = personality_collection.get(
                ids=[f"personality_{rulebook_name}"]
            )
            if results['documents']:
                personality = results['documents'][0]
                logger.info(f"Retrieved personality for '{rulebook_name}'.")
                return personality
            else:
                logger.warning(f"No personality found for '{rulebook_name}'.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving personality for '{rulebook_name}': {e}")
            return None

    def vector_search(self, index_name: str, query_embedding: np.ndarray = None, 
                     query_text: str = None, num_results: int = 10, 
                     filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform vector search using ChromaDB"""
        collection = self._get_or_create_collection(index_name)
        
        # Prepare the query
        query_kwargs = {"n_results": num_results}
        
        if query_embedding is not None:
            query_kwargs["query_embeddings"] = [query_embedding.astype(np.float32).tolist()]
        elif query_text is not None:
            query_kwargs["query_texts"] = [query_text]
        else:
            raise ValueError("Either query_embedding or query_text must be provided")
        
        # Add metadata filters if provided
        if filters and isinstance(filters, dict):
            # Use ChromaDB where clause format
            query_kwargs["where"] = filters
        
        try:
            results = collection.query(**query_kwargs)
            
            search_results = []
            for i in range(len(results['ids'][0])):
                doc_id = results['ids'][0][i]
                document = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0.0
                
                # Reconstruct ContentChunk from stored metadata
                content_chunk = ContentChunk(
                    id=doc_id,
                    rulebook=metadata.get('rulebook', ''),
                    system=metadata.get('system', ''),
                    source_type=metadata.get('source_type', ''),
                    content_type=metadata.get('content_type', ''),
                    title=metadata.get('title', ''),
                    content=document,
                    page_number=metadata.get('page_number', 0),
                    section_path=json.loads(metadata.get('section_path', '[]')),
                    embedding=b"",  # We don't need to store the full embedding
                    metadata={k[5:]: json.loads(v) if k.startswith('meta_') and v.startswith(('{', '[')) 
                             else v for k, v in metadata.items() if k.startswith('meta_')}
                )
                
                # Convert distance to similarity score (lower distance = higher similarity)
                relevance_score = 1.0 - distance
                
                search_results.append(
                    SearchResult(
                        content_chunk=content_chunk, 
                        relevance_score=relevance_score, 
                        match_type="semantic"
                    )
                )
            
            logger.info(f"Performed vector search on '{index_name}' and found {len(search_results)} results.")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            return []

    def store_campaign_data(self, campaign_id: str, data_type: str, data: Dict[str, Any]) -> str:
        """Store campaign data using ChromaDB's document storage"""
        data_id = data.get("id", None) or str(uuid.uuid4())
        
        # Prepare document content and metadata
        document_content = json.dumps(data)
        metadata = {
            "campaign_id": campaign_id,
            "data_type": data_type,
            "data_id": data_id
        }
        
        # Add searchable fields from data
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                metadata[f"data_{key}"] = value
        
        doc_id = f"campaign_{campaign_id}_{data_type}_{data_id}"
        
        self.campaign_collection.upsert(
            ids=[doc_id],
            documents=[document_content],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
        return data_id

    def get_campaign_data(self, campaign_id: str, data_type: str = None, data_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve campaign data"""
        if data_id and data_type:
            doc_id = f"campaign_{campaign_id}_{data_type}_{data_id}"
            try:
                results = self.campaign_collection.get(ids=[doc_id])
                if results['documents']:
                    data = json.loads(results['documents'][0])
                    logger.info(f"Retrieved data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
                    return [data]
                else:
                    return []
            except Exception as e:
                logger.error(f"Error retrieving campaign data: {e}")
                return []
        else:
            # Get all data for campaign and optionally data_type
            where_clause = {"campaign_id": campaign_id}
            if data_type:
                where_clause["data_type"] = data_type
                
            try:
                results = self.campaign_collection.get(where=where_clause)
                data_list = [json.loads(doc) for doc in results['documents']]
                logger.info(f"Retrieved {len(data_list)} data entries for campaign '{campaign_id}'{f' of type {data_type}' if data_type else ''}.")
                return data_list
            except Exception as e:
                logger.error(f"Error retrieving campaign data: {e}")
                return []

    def update_campaign_data(self, campaign_id: str, data_type: str, data_id: str, data: Dict[str, Any]) -> bool:
        """Update existing campaign data"""
        doc_id = f"campaign_{campaign_id}_{data_type}_{data_id}"
        
        try:
            # Check if exists
            existing = self.campaign_collection.get(ids=[doc_id])
            if not existing['documents']:
                logger.warning(f"Data not found for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
                return False
            
            # Update the data
            document_content = json.dumps(data)
            metadata = {
                "campaign_id": campaign_id,
                "data_type": data_type,
                "data_id": data_id
            }
            
            # Add searchable fields from data
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"data_{key}"] = value
            
            self.campaign_collection.upsert(
                ids=[doc_id],
                documents=[document_content],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
            return True
            
        except Exception as e:
            logger.error(f"Error updating campaign data: {e}")
            return False

    def delete_campaign_data(self, campaign_id: str, data_type: str, data_id: str) -> bool:
        """Delete campaign data"""
        doc_id = f"campaign_{campaign_id}_{data_type}_{data_id}"
        
        try:
            # Check if exists
            existing = self.campaign_collection.get(ids=[doc_id])
            if not existing['documents']:
                logger.warning(f"Data not found for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
                return False
            
            self.campaign_collection.delete(ids=[doc_id])
            logger.info(f"Deleted data for campaign '{campaign_id}' of type '{data_type}' with id '{data_id}'.")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting campaign data: {e}")
            return False

    def export_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        """Export all campaign data"""
        try:
            results = self.campaign_collection.get(
                where={"campaign_id": campaign_id}
            )
            
            data = {}
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                data_type = metadata['data_type']
                
                if data_type not in data:
                    data[data_type] = []
                
                data[data_type].append(json.loads(doc))
            
            logger.info(f"Exported campaign data for '{campaign_id}'.")
            return data
            
        except Exception as e:
            logger.error(f"Error exporting campaign data: {e}")
            return {}

    def import_campaign_data(self, campaign_id: str, data: Dict[str, Any]):
        """Import campaign data"""
        for data_type, items in data.items():
            for item in items:
                self.store_campaign_data(campaign_id, data_type, item)
        logger.info(f"Imported campaign data for '{campaign_id}'.")

    def list_collections(self) -> List[str]:
        """List all available collections"""
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection entirely"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            return False

    # Session management methods
    def store_session_data(self, campaign_id: str, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data"""
        try:
            session_data = {
                "notes": data.get("notes", []),
                "initiative_order": data.get("initiative_order", []),
                "monsters": data.get("monsters", [])
            }
            self.store_campaign_data(campaign_id, "session", {
                "id": session_id,
                "session_id": session_id,
                **session_data
            })
            return True
        except Exception as e:
            logger.error(f"Error storing session data: {e}")
            return False

    def get_session_data(self, campaign_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        try:
            results = self.get_campaign_data(campaign_id, "session", session_id)
            if results:
                return results[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving session data: {e}")
            return None

    def session_exists(self, campaign_id: str, session_id: str) -> bool:
        """Check if session exists"""
        return self.get_session_data(campaign_id, session_id) is not None

    def update_session_data(self, campaign_id: str, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            return self.update_campaign_data(campaign_id, "session", session_id, {
                "id": session_id,
                "session_id": session_id,
                **data
            })
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return False

    # Compatibility methods to match RedisDataManager interface
    def connect(self):
        """Compatibility method - ChromaDB doesn't need explicit connection"""
        return self.client

    def ping(self):
        """Compatibility method - check if ChromaDB is accessible"""
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False