import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..data_models.personality_models import RPGPersonality, VernacularPattern, PersonalityTrait, PersonalityPrompt
from ..data_models.models import ContentChunk
from .personality_extractor import PersonalityExtractor
from ..chromadb_manager.manager import ChromaDataManager


class PersonalityManager:
    """Manages personality profiles and vernacular for RPG systems"""
    
    def __init__(self, data_manager: ChromaDataManager):
        self.data_manager = data_manager
        self.extractor = PersonalityExtractor()
        self.logger = logging.getLogger(__name__)
        
        # Collection name for personality data
        self.personality_collection = "personalities"
        
        # Initialize collection if it doesn't exist
        self._ensure_personality_collection()
    
    def _ensure_personality_collection(self):
        """Ensure the personality collection exists"""
        try:
            # Check if collection exists, create if not
            collections = self.data_manager.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if self.personality_collection not in collection_names:
                self.data_manager.client.create_collection(
                    name=self.personality_collection,
                    metadata={"description": "RPG system personality profiles"}
                )
                self.logger.info(f"Created personality collection: {self.personality_collection}")
        except Exception as e:
            self.logger.error(f"Error ensuring personality collection: {e}")
    
    def extract_and_store_personality(self, chunks: List[ContentChunk], system_name: str) -> Optional[RPGPersonality]:
        """Extract personality from chunks and store it"""
        try:
            # Extract personality
            personality = self.extractor.extract_personality(chunks, system_name)
            
            # Store personality
            self.store_personality(personality)
            
            self.logger.info(f"Extracted and stored personality for {system_name}")
            return personality
            
        except Exception as e:
            self.logger.error(f"Error extracting personality for {system_name}: {e}")
            return None
    
    def store_personality(self, personality: RPGPersonality):
        """Store a personality profile"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            
            # Convert personality to document format
            document = personality.to_dict()
            
            # Use system name as ID
            doc_id = personality.system_name.lower().replace(" ", "_")
            
            # Store document
            collection.upsert(
                ids=[doc_id],
                documents=[json.dumps(document)],
                metadatas=[{
                    "system_name": personality.system_name,
                    "personality_name": personality.personality_name,
                    "tone": personality.tone,
                    "perspective": personality.perspective,
                    "formality_level": personality.formality_level,
                    "confidence_score": personality.confidence_score,
                    "created_at": personality.created_at.isoformat(),
                    "vernacular_count": len(personality.vernacular_patterns)
                }]
            )
            
            self.logger.info(f"Stored personality profile for {personality.system_name}")
            
        except Exception as e:
            self.logger.error(f"Error storing personality: {e}")
            raise
    
    def get_personality(self, system_name: str) -> Optional[RPGPersonality]:
        """Get personality profile for a system"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            doc_id = system_name.lower().replace(" ", "_")
            
            result = collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if not result['documents'] or len(result['documents']) == 0:
                return None
            
            # Parse document
            document_data = json.loads(result['documents'][0])
            personality = RPGPersonality.from_dict(document_data)
            
            return personality
            
        except Exception as e:
            self.logger.error(f"Error getting personality for {system_name}: {e}")
            return None
    
    def get_personality_summary(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of personality data for a system"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            doc_id = system_name.lower().replace(" ", "_")
            
            result = collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not result['metadatas'] or len(result['metadatas']) == 0:
                return None
            
            metadata = result['metadatas'][0]
            
            # Get example phrases from full personality if needed
            personality = self.get_personality(system_name)
            example_phrases = personality.example_phrases[:3] if personality else []
            
            return {
                "system_name": metadata.get("system_name"),
                "personality_name": metadata.get("personality_name"),
                "tone": metadata.get("tone"),
                "perspective": metadata.get("perspective"),
                "formality_level": metadata.get("formality_level"),
                "confidence_score": metadata.get("confidence_score"),
                "vernacular_count": metadata.get("vernacular_count", 0),
                "created_at": metadata.get("created_at"),
                "system_context": personality.system_context if personality else "",
                "description": personality.description if personality else "",
                "example_phrases": example_phrases
            }
            
        except Exception as e:
            self.logger.error(f"Error getting personality summary for {system_name}: {e}")
            return None
    
    def list_personalities(self) -> List[str]:
        """List all available personality systems"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            
            result = collection.get(include=["metadatas"])
            
            if not result['metadatas']:
                return []
            
            systems = [metadata.get("system_name") for metadata in result['metadatas']]
            return [s for s in systems if s]  # Filter out None values
            
        except Exception as e:
            self.logger.error(f"Error listing personalities: {e}")
            return []
    
    def get_vernacular_for_system(self, system_name: str) -> List[Dict[str, Any]]:
        """Get vernacular terms for a system"""
        try:
            personality = self.get_personality(system_name)
            
            if not personality or not personality.vernacular_patterns:
                return []
            
            # Convert VernacularPattern objects to dictionaries
            vernacular = []
            for pattern in personality.vernacular_patterns:
                vernacular.append({
                    "term": pattern.term,
                    "definition": pattern.definition,
                    "context": pattern.context,
                    "frequency": pattern.frequency,
                    "examples": pattern.examples,
                    "category": pattern.category
                })
            
            # Sort by frequency
            vernacular.sort(key=lambda x: x["frequency"], reverse=True)
            
            return vernacular
            
        except Exception as e:
            self.logger.error(f"Error getting vernacular for {system_name}: {e}")
            return []
    
    def generate_personality_prompt(self, system_name: str, query: str, context: str = "") -> Optional[PersonalityPrompt]:
        """Generate a personality-aware prompt for a system"""
        try:
            personality = self.get_personality(system_name)
            
            if not personality:
                return None
            
            return self.extractor.generate_personality_prompt(personality, query, context)
            
        except Exception as e:
            self.logger.error(f"Error generating personality prompt for {system_name}: {e}")
            return None
    
    def create_personality_comparison(self, systems: List[str]) -> Dict[str, Any]:
        """Create a comparison between personality systems"""
        try:
            comparison_matrix = {}
            
            for system in systems:
                summary = self.get_personality_summary(system)
                if summary:
                    comparison_matrix[system] = {
                        "tone": summary["tone"],
                        "perspective": summary["perspective"],
                        "formality": summary["formality_level"],
                        "confidence": summary["confidence_score"],
                        "vernacular_count": summary["vernacular_count"]
                    }
            
            # Calculate similarity metrics
            similarities = {}
            for i, system1 in enumerate(systems):
                for system2 in systems[i+1:]:
                    if system1 in comparison_matrix and system2 in comparison_matrix:
                        # Simple similarity based on matching characteristics
                        matches = 0
                        total = 3  # tone, perspective, formality
                        
                        if comparison_matrix[system1]["tone"] == comparison_matrix[system2]["tone"]:
                            matches += 1
                        if comparison_matrix[system1]["perspective"] == comparison_matrix[system2]["perspective"]:
                            matches += 1
                        if comparison_matrix[system1]["formality"] == comparison_matrix[system2]["formality"]:
                            matches += 1
                        
                        similarity = matches / total
                        similarities[f"{system1} vs {system2}"] = similarity
            
            return {
                "comparison_matrix": comparison_matrix,
                "similarities": similarities,
                "systems_compared": len(comparison_matrix)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating personality comparison: {e}")
            return {"comparison_matrix": {}, "similarities": {}, "systems_compared": 0}
    
    def get_personality_stats(self) -> Dict[str, Any]:
        """Get statistics about all personality profiles"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            
            result = collection.get(include=["metadatas"])
            
            if not result['metadatas']:
                return {
                    "total_personalities": 0,
                    "average_confidence": 0,
                    "total_vernacular_terms": 0
                }
            
            metadatas = result['metadatas']
            
            # Calculate stats
            total_personalities = len(metadatas)
            confidences = [m.get("confidence_score", 0) for m in metadatas]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0
            total_vernacular_terms = sum(m.get("vernacular_count", 0) for m in metadatas)
            
            # Group by characteristics
            personalities_by_tone = {}
            personalities_by_formality = {}
            personalities_by_perspective = {}
            
            for metadata in metadatas:
                tone = metadata.get("tone", "unknown")
                formality = metadata.get("formality_level", "unknown")
                perspective = metadata.get("perspective", "unknown")
                
                personalities_by_tone[tone] = personalities_by_tone.get(tone, 0) + 1
                personalities_by_formality[formality] = personalities_by_formality.get(formality, 0) + 1
                personalities_by_perspective[perspective] = personalities_by_perspective.get(perspective, 0) + 1
            
            return {
                "total_personalities": total_personalities,
                "average_confidence": average_confidence,
                "total_vernacular_terms": total_vernacular_terms,
                "personalities_by_tone": personalities_by_tone,
                "personalities_by_formality": personalities_by_formality,
                "personalities_by_perspective": personalities_by_perspective
            }
            
        except Exception as e:
            self.logger.error(f"Error getting personality stats: {e}")
            return {
                "total_personalities": 0,
                "average_confidence": 0,
                "total_vernacular_terms": 0
            }
    
    def enhance_search_response(self, response: str, system_name: str, query: str) -> str:
        """Enhance a search response with personality-aware language"""
        try:
            personality = self.get_personality(system_name)
            
            if not personality:
                return response
            
            # Get personality prompt for context
            personality_prompt = self.generate_personality_prompt(system_name, query, response)
            
            if not personality_prompt:
                return response
            
            # Simple enhancement - add personality-appropriate introduction and conclusion
            enhanced_response = ""
            
            # Add personality-aware introduction based on tone
            if personality.tone == "mysterious":
                enhanced_response += "The ancient archives whisper of the following knowledge...\n\n"
            elif personality.tone == "authoritative":
                enhanced_response += "The official records state the following:\n\n"
            elif personality.tone == "formal":
                enhanced_response += "According to the documented sources:\n\n"
            elif personality.tone == "scholarly":
                enhanced_response += "My research reveals the following information:\n\n"
            
            enhanced_response += response
            
            # Add personality-aware conclusion
            if personality.tone == "mysterious" and personality.vernacular_patterns:
                enhanced_response += "\n\nMay this knowledge serve you well in your endeavors..."
            elif personality.tone == "authoritative":
                enhanced_response += "\n\nThis information is provided in accordance with official guidelines."
            
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Error enhancing search response: {e}")
            return response
    
    def delete_personality(self, system_name: str) -> bool:
        """Delete a personality profile"""
        try:
            collection = self.data_manager.client.get_collection(self.personality_collection)
            doc_id = system_name.lower().replace(" ", "_")
            
            collection.delete(ids=[doc_id])
            
            self.logger.info(f"Deleted personality profile for {system_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting personality for {system_name}: {e}")
            return False