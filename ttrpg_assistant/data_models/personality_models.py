from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class VernacularPattern:
    """Represents a vernacular or speech pattern found in a rulebook"""
    term: str
    definition: str
    context: str
    frequency: int
    examples: List[str]
    category: str  # "neologism", "archaic", "technical", "slang", "formal", "magical", "mechanical"


@dataclass
class PersonalityTrait:
    """Represents a personality trait extracted from writing style"""
    trait_name: str
    description: str
    evidence_text: List[str]
    confidence: float
    examples: List[str]


@dataclass
class RPGPersonality:
    """Represents the personality profile for an RPG system"""
    system_name: str
    personality_name: str
    description: str
    
    # Core personality traits
    tone: str  # "formal", "casual", "mysterious", "authoritative", "whimsical"
    perspective: str  # "omniscient", "scholarly", "conspiratorial", "practical"
    formality_level: str  # "high", "medium", "low"
    
    # Speaking patterns
    vernacular_patterns: List[VernacularPattern]
    personality_traits: List[PersonalityTrait]
    
    # Response formatting preferences
    preferred_structure: str  # "academic", "narrative", "bullet_points", "conversational"
    example_phrases: List[str]
    avoid_phrases: List[str]
    
    # Contextual behavior
    system_context: str  # Background information about the RPG setting
    response_style: str  # How to format responses
    
    # Metadata
    extracted_from: List[str]  # Source rulebooks
    created_at: datetime
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "system_name": self.system_name,
            "personality_name": self.personality_name,
            "description": self.description,
            "tone": self.tone,
            "perspective": self.perspective,
            "formality_level": self.formality_level,
            "vernacular_patterns": [
                {
                    "term": vp.term,
                    "definition": vp.definition,
                    "context": vp.context,
                    "frequency": vp.frequency,
                    "examples": vp.examples,
                    "category": vp.category
                }
                for vp in self.vernacular_patterns
            ],
            "personality_traits": [
                {
                    "trait_name": pt.trait_name,
                    "description": pt.description,
                    "evidence_text": pt.evidence_text,
                    "confidence": pt.confidence,
                    "examples": pt.examples
                }
                for pt in self.personality_traits
            ],
            "preferred_structure": self.preferred_structure,
            "example_phrases": self.example_phrases,
            "avoid_phrases": self.avoid_phrases,
            "system_context": self.system_context,
            "response_style": self.response_style,
            "extracted_from": self.extracted_from,
            "created_at": self.created_at.isoformat(),
            "confidence_score": self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RPGPersonality':
        """Create from dictionary"""
        return cls(
            system_name=data["system_name"],
            personality_name=data["personality_name"],
            description=data["description"],
            tone=data["tone"],
            perspective=data["perspective"],
            formality_level=data["formality_level"],
            vernacular_patterns=[
                VernacularPattern(
                    term=vp["term"],
                    definition=vp["definition"],
                    context=vp["context"],
                    frequency=vp["frequency"],
                    examples=vp["examples"],
                    category=vp["category"]
                )
                for vp in data["vernacular_patterns"]
            ],
            personality_traits=[
                PersonalityTrait(
                    trait_name=pt["trait_name"],
                    description=pt["description"],
                    evidence_text=pt["evidence_text"],
                    confidence=pt["confidence"],
                    examples=pt["examples"]
                )
                for pt in data["personality_traits"]
            ],
            preferred_structure=data["preferred_structure"],
            example_phrases=data["example_phrases"],
            avoid_phrases=data["avoid_phrases"],
            system_context=data["system_context"],
            response_style=data["response_style"],
            extracted_from=data["extracted_from"],
            created_at=datetime.fromisoformat(data["created_at"]),
            confidence_score=data["confidence_score"]
        )


@dataclass
class PersonalityPrompt:
    """Represents a personality-aware prompt template"""
    system_name: str
    base_prompt: str
    personality_instructions: str
    example_responses: List[str]
    vernacular_instructions: str
    
    def format_prompt(self, query: str, context: str = "") -> str:
        """Format a prompt with personality context"""
        formatted_prompt = f"""
{self.base_prompt}

{self.personality_instructions}

{self.vernacular_instructions}

Context: {context}

Query: {query}

Please respond in character, using the appropriate tone, vernacular, and style for this RPG system.
"""
        return formatted_prompt.strip()


@dataclass
class PersonalityResponse:
    """Represents a personality-enhanced response"""
    original_response: str
    enhanced_response: str
    personality_elements_used: List[str]
    vernacular_terms_included: List[str]
    confidence_score: float
    system_name: str