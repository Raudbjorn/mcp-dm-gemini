import re
import nltk
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import json

from ..data_models.personality_models import RPGPersonality, VernacularPattern, PersonalityTrait, PersonalityPrompt
from ..data_models.models import ContentChunk


class PersonalityExtractor:
    """Extracts personality traits and vernacular from rulebook content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize, sent_tokenize
        
        self.stopwords = set(stopwords.words('english'))
        self.word_tokenize = word_tokenize
        self.sent_tokenize = sent_tokenize
        
        # Predefined system personalities (as fallbacks and examples)
        self.system_templates = {
            "D&D 5e": {
                "personality_name": "Wise Sage",
                "description": "A knowledgeable scholar with deep understanding of magical lore and adventure",
                "tone": "authoritative",
                "perspective": "omniscient",
                "formality_level": "medium",
                "preferred_structure": "academic",
                "system_context": "High fantasy world with magic, dragons, and heroic adventures",
                "example_phrases": [
                    "In the ancient texts, it is written...",
                    "The arcane mysteries reveal...",
                    "As any seasoned adventurer knows...",
                    "The magical weave responds to...",
                    "Legend speaks of..."
                ],
                "avoid_phrases": [
                    "basically", "kinda", "whatever", "I guess"
                ]
            },
            "Blades in the Dark": {
                "personality_name": "Shadowy Informant",
                "description": "A well-connected figure from the criminal underworld with refined Victorian sensibilities",
                "tone": "mysterious",
                "perspective": "conspiratorial",
                "formality_level": "high",
                "preferred_structure": "narrative",
                "system_context": "Industrial-era city of shadows, crime, and supernatural horror",
                "example_phrases": [
                    "Word on the street is...",
                    "The powers that be have arranged...",
                    "In the shadows of Doskvol...",
                    "A reliable source informs me...",
                    "One does not simply...",
                    "The whispers speak of..."
                ],
                "avoid_phrases": [
                    "cool", "awesome", "totally", "dude"
                ]
            },
            "Delta Green": {
                "personality_name": "Classified Handler",
                "description": "A government operative dealing with cosmic horror and classified information",
                "tone": "formal",
                "perspective": "authoritative",
                "formality_level": "high",
                "preferred_structure": "bullet_points",
                "system_context": "Modern conspiracy horror with government cover-ups and cosmic threats",
                "example_phrases": [
                    "According to classified reports...",
                    "Field agents should be advised...",
                    "The following information is compartmentalized...",
                    "Operational security requires...",
                    "Need-to-know basis only...",
                    "Agent, your mission parameters..."
                ],
                "avoid_phrases": [
                    "maybe", "I think", "probably", "casual"
                ]
            },
            "Call of Cthulhu": {
                "personality_name": "Antiquarian Scholar",
                "description": "An erudite academic with knowledge of forbidden lore and ancient mysteries",
                "tone": "scholarly",
                "perspective": "ominous",
                "formality_level": "high",
                "preferred_structure": "academic",
                "system_context": "1920s cosmic horror with ancient evils and sanity-threatening knowledge",
                "example_phrases": [
                    "In my research of forbidden texts...",
                    "The eldritch truth reveals...",
                    "Ancient manuscripts speak of...",
                    "I have uncovered disturbing evidence...",
                    "The implications are most unsettling...",
                    "One must approach such knowledge carefully..."
                ],
                "avoid_phrases": [
                    "fun", "exciting", "cool", "neat"
                ]
            },
            "Pathfinder": {
                "personality_name": "Learned Explorer",
                "description": "An experienced adventurer and scholar with practical wisdom",
                "tone": "authoritative",
                "perspective": "instructional",
                "formality_level": "medium",
                "preferred_structure": "academic",
                "system_context": "High fantasy world with complex magic and diverse creatures",
                "example_phrases": [
                    "From my travels, I have learned...",
                    "The wise adventurer knows...",
                    "Experience has taught me...",
                    "In the field, one discovers...",
                    "The lore of the ancients tells us..."
                ],
                "avoid_phrases": [
                    "whatever", "like", "totally"
                ]
            }
        }
    
    def extract_personality(self, chunks: List[ContentChunk], system_name: str) -> RPGPersonality:
        """Extract personality profile from rulebook content"""
        self.logger.info(f"Extracting personality profile for {system_name}")
        
        # Combine all text content
        all_text = " ".join([chunk.content for chunk in chunks])
        
        # Extract various personality components
        vernacular_patterns = self._extract_vernacular_patterns(chunks)
        personality_traits = self._extract_personality_traits(all_text, system_name)
        tone = self._analyze_tone(all_text)
        perspective = self._analyze_perspective(all_text)
        formality_level = self._analyze_formality(all_text)
        preferred_structure = self._analyze_structure_preference(chunks)
        
        # Generate contextual information
        system_context = self._extract_system_context(chunks)
        example_phrases = self._extract_example_phrases(all_text)
        avoid_phrases = self._identify_avoid_phrases(all_text)
        
        # Use template if available, otherwise generate
        template = self.system_templates.get(system_name, {})
        
        personality = RPGPersonality(
            system_name=system_name,
            personality_name=template.get("personality_name", f"{system_name} Assistant"),
            description=template.get("description", f"An assistant knowledgeable in {system_name}"),
            tone=template.get("tone", tone),
            perspective=template.get("perspective", perspective),
            formality_level=template.get("formality_level", formality_level),
            vernacular_patterns=vernacular_patterns,
            personality_traits=personality_traits,
            preferred_structure=template.get("preferred_structure", preferred_structure),
            example_phrases=template.get("example_phrases", example_phrases),
            avoid_phrases=template.get("avoid_phrases", avoid_phrases),
            system_context=template.get("system_context", system_context),
            response_style=self._generate_response_style(template.get("tone", tone), template.get("perspective", perspective)),
            extracted_from=[chunk.rulebook for chunk in chunks],
            created_at=datetime.now(),
            confidence_score=self._calculate_confidence_score(chunks, template)
        )
        
        return personality
    
    def _extract_vernacular_patterns(self, chunks: List[ContentChunk]) -> List[VernacularPattern]:
        """Extract unique terminology and vernacular from the text"""
        vernacular_patterns = []
        
        # Collect all text
        all_text = " ".join([chunk.content for chunk in chunks])
        
        # Find unique terms using various strategies
        unique_terms = self._find_unique_terms(all_text)
        technical_terms = self._find_technical_terms(chunks)
        neologisms = self._find_neologisms(all_text)
        
        # Combine all terms
        all_terms = {**unique_terms, **technical_terms, **neologisms}
        
        # Convert to VernacularPattern objects
        for term, info in all_terms.items():
            pattern = VernacularPattern(
                term=term,
                definition=info.get("definition", ""),
                context=info.get("context", ""),
                frequency=info.get("frequency", 0),
                examples=info.get("examples", []),
                category=self._categorize_term(term, info)
            )
            vernacular_patterns.append(pattern)
        
        # Sort by frequency and return top terms
        vernacular_patterns.sort(key=lambda x: x.frequency, reverse=True)
        return vernacular_patterns[:50]  # Limit to top 50
    
    def _find_unique_terms(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Find terms that appear frequently and might be system-specific"""
        # Look for capitalized terms that might be proper nouns or game terms
        capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Look for terms in quotes (often definitions)
        quoted_terms = re.findall(r'"([^"]*)"', text)
        
        # Look for terms followed by definition patterns
        definition_patterns = re.findall(r'\b([A-Z][a-z]+)\s+(?:is|means|refers to|:)', text)
        
        # Count frequencies
        term_counts = Counter(capitalized_terms + quoted_terms + definition_patterns)
        
        unique_terms = {}
        for term, count in term_counts.most_common(100):
            if len(term) > 2 and count > 2:  # Filter out short or rare terms
                # Try to find definition context
                definition_match = re.search(
                    rf'\b{re.escape(term)}\s+(?:is|means|refers to|:)\s+([^.!?]*[.!?])',
                    text, re.IGNORECASE
                )
                
                definition = definition_match.group(1) if definition_match else ""
                
                # Find example contexts
                examples = re.findall(
                    rf'[^.!?]*\b{re.escape(term)}\b[^.!?]*[.!?]',
                    text, re.IGNORECASE
                )[:3]  # Limit to 3 examples
                
                unique_terms[term] = {
                    "frequency": count,
                    "definition": definition,
                    "examples": examples,
                    "context": f"Appears {count} times in rulebook"
                }
        
        return unique_terms
    
    def _find_technical_terms(self, chunks: List[ContentChunk]) -> Dict[str, Any]:
        """Find technical game terms from specific content types"""
        technical_terms = {}
        
        for chunk in chunks:
            if chunk.content_type in ["rule", "spell", "monster", "item"]:
                # Look for terms that appear in headers or are emphasized
                terms = re.findall(r'\b[A-Z][A-Z\s]+\b', chunk.content)  # ALL CAPS
                for term in terms:
                    if len(term) > 3:
                        technical_terms[term] = {
                            "frequency": technical_terms.get(term, {}).get("frequency", 0) + 1,
                            "definition": f"Technical term from {chunk.content_type}",
                            "examples": [chunk.content[:100] + "..."],
                            "context": f"Found in {chunk.content_type} content"
                        }
        
        return technical_terms
    
    def _find_neologisms(self, text: str) -> Dict[str, Any]:
        """Find invented or unusual words"""
        # Look for words with unusual capitalization or structure
        neologisms = {}
        
        # Words with internal capitals (CamelCase)
        camel_case = re.findall(r'\b[a-z]+[A-Z][a-z]+\b', text)
        
        # Words with apostrophes or hyphens (often fantasy names)
        special_words = re.findall(r"\b[A-Za-z]+'[A-Za-z]+\b|\b[A-Za-z]+-[A-Za-z]+\b", text)
        
        for word in camel_case + special_words:
            if len(word) > 3:
                neologisms[word] = {
                    "frequency": text.count(word),
                    "definition": "Potentially invented term",
                    "examples": [],
                    "context": "Appears to be a neologism"
                }
        
        return neologisms
    
    def _categorize_term(self, term: str, info: Dict[str, Any]) -> str:
        """Categorize a vernacular term"""
        if "'" in term or "-" in term:
            return "neologism"
        elif term.isupper():
            return "technical"
        elif any(word in info.get("definition", "").lower() for word in ["spell", "magic", "cast"]):
            return "magical"
        elif any(word in info.get("definition", "").lower() for word in ["rule", "action", "turn"]):
            return "mechanical"
        else:
            return "general"
    
    def _extract_personality_traits(self, text: str, system_name: str) -> List[PersonalityTrait]:
        """Extract personality traits from writing style"""
        traits = []
        
        # Analyze sentence structure
        sentences = self.sent_tokenize(text)
        
        # Check for formal vs informal language
        formal_indicators = sum(1 for s in sentences if re.search(r'\b(shall|must|ought|furthermore|therefore|thus|hence)\b', s))
        informal_indicators = sum(1 for s in sentences if re.search(r'\b(gonna|wanna|yeah|ok|cool)\b', s))
        
        if formal_indicators > informal_indicators * 2:
            traits.append(PersonalityTrait(
                trait_name="Formal Speech",
                description="Uses formal, academic language",
                evidence_text=[s for s in sentences[:5] if re.search(r'\b(shall|must|ought|furthermore|therefore|thus|hence)\b', s)],
                confidence=0.8,
                examples=[]
            ))
        
        # Check for authoritative tone
        authoritative_indicators = sum(1 for s in sentences if re.search(r'\b(you must|it is required|always|never|clearly|obviously)\b', s))
        if authoritative_indicators > len(sentences) * 0.1:
            traits.append(PersonalityTrait(
                trait_name="Authoritative",
                description="Speaks with authority and certainty",
                evidence_text=[s for s in sentences[:5] if re.search(r'\b(you must|it is required|always|never|clearly|obviously)\b', s)],
                confidence=0.7,
                examples=[]
            ))
        
        # Check for mysterious/ominous tone
        mysterious_indicators = sum(1 for s in sentences if re.search(r'\b(ancient|forbidden|dark|shadow|mystery|whisper|secret)\b', s))
        if mysterious_indicators > len(sentences) * 0.05:
            traits.append(PersonalityTrait(
                trait_name="Mysterious",
                description="Uses mysterious and atmospheric language",
                evidence_text=[s for s in sentences[:5] if re.search(r'\b(ancient|forbidden|dark|shadow|mystery|whisper|secret)\b', s)],
                confidence=0.6,
                examples=[]
            ))
        
        return traits
    
    def _analyze_tone(self, text: str) -> str:
        """Analyze the overall tone of the text"""
        # Count indicators for different tones
        formal_count = len(re.findall(r'\b(shall|must|furthermore|therefore|thus|hence)\b', text))
        casual_count = len(re.findall(r'\b(you|your|let\'s|ok|cool|fun)\b', text))
        mysterious_count = len(re.findall(r'\b(ancient|forbidden|dark|shadow|mystery|whisper|secret)\b', text))
        authoritative_count = len(re.findall(r'\b(must|required|always|never|clearly|rule|law)\b', text))
        
        # Determine predominant tone
        tone_scores = {
            "formal": formal_count,
            "casual": casual_count,
            "mysterious": mysterious_count,
            "authoritative": authoritative_count
        }
        
        return max(tone_scores, key=tone_scores.get)
    
    def _analyze_perspective(self, text: str) -> str:
        """Analyze the narrative perspective"""
        first_person = len(re.findall(r'\b(I|me|my|we|us|our)\b', text))
        second_person = len(re.findall(r'\b(you|your|yourself)\b', text))
        third_person = len(re.findall(r'\b(he|she|it|they|them|character|player)\b', text))
        
        if second_person > first_person and second_person > third_person:
            return "instructional"
        elif first_person > third_person:
            return "personal"
        else:
            return "omniscient"
    
    def _analyze_formality(self, text: str) -> str:
        """Analyze formality level"""
        formal_indicators = len(re.findall(r'\b(shall|must|ought|furthermore|therefore|thus|hence|pursuant|wherein)\b', text))
        informal_indicators = len(re.findall(r'\b(gonna|wanna|yeah|ok|cool|awesome|fun|hey)\b', text))
        
        total_words = len(self.word_tokenize(text))
        formal_ratio = formal_indicators / total_words if total_words > 0 else 0
        informal_ratio = informal_indicators / total_words if total_words > 0 else 0
        
        if formal_ratio > informal_ratio * 2:
            return "high"
        elif informal_ratio > formal_ratio * 2:
            return "low"
        else:
            return "medium"
    
    def _analyze_structure_preference(self, chunks: List[ContentChunk]) -> str:
        """Analyze preferred content structure"""
        # Look at how content is organized
        bullet_points = sum(1 for chunk in chunks if re.search(r'\n\s*[•\*\-]', chunk.content))
        numbered_lists = sum(1 for chunk in chunks if re.search(r'\n\s*\d+\.', chunk.content))
        paragraphs = sum(1 for chunk in chunks if len(chunk.content.split('\n\n')) > 2)
        
        if bullet_points > numbered_lists and bullet_points > paragraphs:
            return "bullet_points"
        elif numbered_lists > paragraphs:
            return "numbered_lists"
        else:
            return "narrative"
    
    def _extract_system_context(self, chunks: List[ContentChunk]) -> str:
        """Extract context about the RPG system"""
        # Look for setting information
        all_text = " ".join([chunk.content for chunk in chunks])
        
        if re.search(r'\b(magic|spell|wizard|dragon|fantasy)\b', all_text):
            return "Fantasy setting with magic and supernatural elements"
        elif re.search(r'\b(technology|cyberpunk|future|space|sci-fi)\b', all_text):
            return "Science fiction or futuristic setting"
        elif re.search(r'\b(horror|fear|sanity|cosmic|eldritch)\b', all_text):
            return "Horror setting with psychological and supernatural threats"
        elif re.search(r'\b(crime|criminal|heist|gang|underworld)\b', all_text):
            return "Crime or underworld setting"
        else:
            return "Role-playing game setting"
    
    def _extract_example_phrases(self, text: str) -> List[str]:
        """Extract example phrases that show the writing style"""
        # Look for common introductory phrases
        phrases = re.findall(r'\b(In the|When a|If a|During|After|Before|As a|For example|Remember that|Note that)[^.!?]*[.!?]', text)
        return phrases[:10]  # Limit to 10 examples
    
    def _identify_avoid_phrases(self, text: str) -> List[str]:
        """Identify phrases that should be avoided based on the style"""
        # Look for informal language that doesn't match the tone
        avoid_phrases = []
        
        # If text is formal, avoid casual phrases
        if self._analyze_formality(text) == "high":
            avoid_phrases.extend(["basically", "kinda", "sorta", "whatever", "I guess", "like", "you know"])
        
        # If text is serious/dark, avoid upbeat phrases
        if re.search(r'\b(dark|horror|fear|death|shadow)\b', text):
            avoid_phrases.extend(["awesome", "cool", "fun", "exciting", "amazing"])
        
        return avoid_phrases
    
    def _generate_response_style(self, tone: str, perspective: str) -> str:
        """Generate response style instructions"""
        style_map = {
            ("formal", "authoritative"): "Respond with authority and precision, using formal language and clear structure.",
            ("mysterious", "omniscient"): "Respond with atmospheric language, hinting at deeper mysteries and hidden knowledge.",
            ("casual", "instructional"): "Respond in a friendly, approachable manner with practical advice.",
            ("scholarly", "academic"): "Respond with academic rigor, citing sources and providing detailed explanations."
        }
        
        return style_map.get((tone, perspective), "Respond helpfully and appropriately to the query.")
    
    def _calculate_confidence_score(self, chunks: List[ContentChunk], template: Dict[str, Any]) -> float:
        """Calculate confidence score for the personality extraction"""
        # Higher confidence if we have a predefined template
        base_confidence = 0.8 if template else 0.5
        
        # Increase confidence based on amount of content
        content_bonus = min(0.2, len(chunks) * 0.01)
        
        # Increase confidence based on content diversity
        content_types = set(chunk.content_type for chunk in chunks)
        diversity_bonus = len(content_types) * 0.05
        
        return min(1.0, base_confidence + content_bonus + diversity_bonus)
    
    def generate_personality_prompt(self, personality: RPGPersonality, query: str, context: str = "") -> PersonalityPrompt:
        """Generate a personality-aware prompt"""
        base_prompt = f"""
You are an assistant for the {personality.system_name} role-playing game system.
Your personality is that of a {personality.personality_name}: {personality.description}
"""
        
        personality_instructions = f"""
PERSONALITY TRAITS:
- Tone: {personality.tone}
- Perspective: {personality.perspective}
- Formality: {personality.formality_level}
- Response style: {personality.response_style}

SYSTEM CONTEXT:
{personality.system_context}
"""
        
        vernacular_instructions = ""
        if personality.vernacular_patterns:
            vernacular_instructions = "VERNACULAR TO USE:\n"
            for pattern in personality.vernacular_patterns[:10]:  # Top 10
                vernacular_instructions += f"- {pattern.term}: {pattern.definition}\n"
        
        if personality.example_phrases:
            vernacular_instructions += "\nEXAMPLE PHRASES TO USE:\n"
            for phrase in personality.example_phrases[:5]:
                vernacular_instructions += f"- {phrase}\n"
        
        if personality.avoid_phrases:
            vernacular_instructions += "\nPHRASES TO AVOID:\n"
            for phrase in personality.avoid_phrases:
                vernacular_instructions += f"- {phrase}\n"
        
        return PersonalityPrompt(
            system_name=personality.system_name,
            base_prompt=base_prompt,
            personality_instructions=personality_instructions,
            example_responses=[],
            vernacular_instructions=vernacular_instructions
        )