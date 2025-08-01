from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import re
import uuid
from collections import defaultdict
from pypdf import PdfReader

from ttrpg_assistant.data_models.models import ContentChunk, SourceType
from ttrpg_assistant.logger import logger
from .dynamic_pattern_learner import DynamicPatternLearner, PatternInfo


class AdaptivePDFProcessor:
    """PDF processor that adapts patterns based on the content it processes"""
    
    def __init__(self, pattern_cache_dir: str = "./pattern_cache"):
        self.pattern_cache_dir = Path(pattern_cache_dir)
        self.pattern_cache_dir.mkdir(exist_ok=True)
        
        # Initialize the pattern learner
        self.pattern_learner = DynamicPatternLearner(
            cache_file=str(self.pattern_cache_dir / "learned_patterns.pkl")
        )
        
        # Keep track of processed systems to build system-specific patterns
        self.system_patterns = {}
    
    def process_pdf_with_learning(self, pdf_path: str, rulebook_name: str, 
                                 system: str, source_type: str = "rulebook") -> List[ContentChunk]:
        """Process PDF and learn patterns specific to this system"""
        logger.info(f"Processing PDF with adaptive learning: {pdf_path}")
        
        # First, extract text and basic structure
        reader = PdfReader(pdf_path)
        all_text_sections = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                all_text_sections.append({
                    'text': text,
                    'page': page_num + 1
                })
        
        # If we have existing patterns for this system, use them
        system_cache_file = self.pattern_cache_dir / f"{system.lower().replace(' ', '_')}_patterns.json"
        
        if system_cache_file.exists():
            logger.info(f"Loading existing patterns for system: {system}")
            self._load_system_patterns(system, system_cache_file)
        
        # Analyze documents to learn/refine patterns
        documents = [section['text'] for section in all_text_sections]
        self.pattern_learner.analyze_documents(documents)
        
        # Now process with learned patterns
        chunks = self._create_adaptive_chunks(
            all_text_sections, rulebook_name, system, source_type
        )
        
        # Save system-specific patterns
        self._save_system_patterns(system, system_cache_file)
        
        logger.info(f"Created {len(chunks)} adaptive chunks for {rulebook_name}")
        return chunks
    
    def _create_adaptive_chunks(self, text_sections: List[Dict], rulebook_name: str, 
                               system: str, source_type: str) -> List[ContentChunk]:
        """Create chunks using dynamically learned patterns"""
        chunks = []
        
        for section in text_sections:
            text = section['text']
            page_num = section['page']
            
            # Classify the content using learned patterns
            content_type = self.pattern_learner._classify_document(text)
            
            # Extract metadata using learned patterns
            metadata = self._extract_adaptive_metadata(text, content_type, system)
            
            # Determine chunking strategy based on content type
            section_chunks = self._chunk_by_content_type(
                text, content_type, page_num, metadata, rulebook_name, system, source_type
            )
            
            chunks.extend(section_chunks)
        
        return chunks
    
    def _extract_adaptive_metadata(self, text: str, content_type: str, system: str) -> Dict[str, Any]:
        """Extract metadata using learned patterns"""
        metadata = {'content_type': content_type, 'system': system}
        
        # Get patterns for this content type
        patterns = self.pattern_learner.get_patterns_for_type(content_type)
        
        # Extract structured data using patterns
        extracted_data = defaultdict(list)
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Try to categorize the matches
                    pattern_key = self._categorize_pattern_matches(pattern, matches)
                    extracted_data[pattern_key].extend(matches)
            except re.error:
                continue
        
        # Convert to regular dict and add to metadata
        for key, values in extracted_data.items():
            if values:
                metadata[key] = list(set(values))  # Remove duplicates
        
        # System-specific extraction
        if system.lower() in ['d&d 5e', 'dnd 5e', 'dungeons & dragons', 'dungeons and dragons']:
            metadata.update(self._extract_dnd5e_metadata(text))
        elif system.lower() in ['pathfinder', 'pathfinder 2e', 'pathfinder 2nd edition']:
            metadata.update(self._extract_pathfinder_metadata(text))
        
        return metadata
    
    def _categorize_pattern_matches(self, pattern: str, matches: List[str]) -> str:
        """Categorize what type of data a pattern extracted"""
        pattern_lower = pattern.lower()
        
        if r'\d+' in pattern:
            if any(keyword in pattern_lower for keyword in ['hp', 'hit', 'health']):
                return 'hit_points'
            elif any(keyword in pattern_lower for keyword in ['ac', 'armor']):
                return 'armor_class'
            elif any(keyword in pattern_lower for keyword in ['str', 'dex', 'con', 'int', 'wis', 'cha']):
                return 'ability_scores'
            elif 'd' in pattern_lower and any(char.isdigit() for char in pattern):
                return 'dice_expressions'
            elif any(keyword in pattern_lower for keyword in ['dc', 'difficulty']):
                return 'difficulty_classes'
            else:
                return 'numeric_values'
        
        elif any(keyword in pattern_lower for keyword in ['spell', 'cantrip']):
            return 'spell_info'
        elif any(keyword in pattern_lower for keyword in ['level', 'tier']):
            return 'level_info'
        else:
            return 'text_patterns'
    
    def _extract_dnd5e_metadata(self, text: str) -> Dict[str, Any]:
        """Extract D&D 5e specific metadata"""
        metadata = {}
        
        # D&D 5e specific patterns that we learn dynamically
        dnd_patterns = {
            'challenge_rating': r'Challenge\s+Rating\s*:?\s*(\d+(?:/\d+)?)',
            'proficiency_bonus': r'Proficiency\s+Bonus\s*:?\s*\+(\d+)',
            'spell_slots': r'(\d+)(?:st|nd|rd|th)\s*level\s*\((\d+)\s*slots?\)',
            'damage_types': r'(fire|cold|lightning|thunder|poison|acid|necrotic|radiant|force|psychic)\s+damage',
            'conditions': r'(blinded|charmed|deafened|frightened|grappled|incapacitated|invisible|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious)',
            'saving_throws': r'(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving\s+throw'
        }
        
        for key, pattern in dnd_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
            except re.error:
                continue
        
        return metadata
    
    def _extract_pathfinder_metadata(self, text: str) -> Dict[str, Any]:
        """Extract Pathfinder specific metadata"""
        metadata = {}
        
        # Pathfinder specific patterns
        pf_patterns = {
            'traits': r'\[([A-Z]+)\]',  # [FIRE], [MAGICAL], etc.
            'actions': r'(◆|◇|↻|⬢)',  # Pathfinder action symbols
            'degrees_of_success': r'(Critical Success|Success|Failure|Critical Failure)',
            'rarity': r'(COMMON|UNCOMMON|RARE|UNIQUE)',
            'level': r'LEVEL\s+(\d+)'
        }
        
        for key, pattern in pf_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
            except re.error:
                continue
        
        return metadata
    
    def _chunk_by_content_type(self, text: str, content_type: str, page_num: int, 
                              metadata: Dict[str, Any], rulebook_name: str, 
                              system: str, source_type: str) -> List[ContentChunk]:
        """Create chunks using content-type-aware strategies"""
        chunks = []
        
        if content_type == 'stat_block':
            # Keep stat blocks as single chunks
            chunks.append(self._create_chunk(
                text, content_type, page_num, metadata, 
                rulebook_name, system, source_type,
                title=self._extract_creature_name(text)
            ))
        
        elif content_type == 'spell':
            # Keep spells as single chunks
            chunks.append(self._create_chunk(
                text, content_type, page_num, metadata,
                rulebook_name, system, source_type,
                title=self._extract_spell_name(text)
            ))
        
        elif content_type == 'table':
            # Keep tables intact
            chunks.append(self._create_chunk(
                text, content_type, page_num, metadata,
                rulebook_name, system, source_type,
                title="Table"
            ))
        
        else:
            # For general content, use intelligent chunking
            chunks.extend(self._smart_chunk_text(
                text, content_type, page_num, metadata,
                rulebook_name, system, source_type
            ))
        
        return chunks
    
    def _create_chunk(self, text: str, content_type: str, page_num: int,
                     metadata: Dict[str, Any], rulebook_name: str, system: str,
                     source_type: str, title: str = "") -> ContentChunk:
        """Create a single content chunk"""
        return ContentChunk(
            id=str(uuid.uuid4()),
            rulebook=rulebook_name,
            system=system,
            source_type=SourceType.RULEBOOK if source_type == "rulebook" else SourceType.FLAVOR,
            content_type=content_type,
            title=title,
            content=text,
            page_number=page_num,
            section_path=[title] if title else [],
            embedding=b"",
            metadata=metadata
        )
    
    def _smart_chunk_text(self, text: str, content_type: str, page_num: int,
                         metadata: Dict[str, Any], rulebook_name: str, 
                         system: str, source_type: str, 
                         chunk_size: int = 1000, overlap: int = 200) -> List[ContentChunk]:
        """Intelligently chunk text based on content structure"""
        chunks = []
        
        # Try to break at natural boundaries
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk.strip(), content_type, page_num, metadata,
                        rulebook_name, system, source_type
                    ))
                
                # Start new chunk
                if len(paragraph) > chunk_size:
                    # Split long paragraph
                    words = paragraph.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) <= chunk_size - overlap:
                            current_chunk += word + " "
                        else:
                            if current_chunk:
                                chunks.append(self._create_chunk(
                                    current_chunk.strip(), content_type, page_num, metadata,
                                    rulebook_name, system, source_type
                                ))
                            current_chunk = word + " "
                else:
                    current_chunk = paragraph + '\n\n'
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk.strip(), content_type, page_num, metadata,
                rulebook_name, system, source_type
            ))
        
        return chunks
    
    def _extract_creature_name(self, text: str) -> str:
        """Extract creature name from stat block"""
        lines = text.split('\n')
        for line in lines[:3]:  # Check first few lines
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['ac', 'hp', 'speed']):
                return line
        return "Creature"
    
    def _extract_spell_name(self, text: str) -> str:
        """Extract spell name from spell description"""
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Remove level indicators
        spell_name = re.sub(r'\d+(?:st|nd|rd|th)-level', '', first_line).strip()
        spell_name = re.sub(r'cantrip', '', spell_name, flags=re.IGNORECASE).strip()
        
        return spell_name if spell_name else "Spell"
    
    def _save_system_patterns(self, system: str, cache_file: Path):
        """Save system-specific patterns"""
        try:
            patterns_data = {
                'system': system,
                'learned_patterns': self.pattern_learner.learned_patterns,
                'stats': self.pattern_learner.get_pattern_stats()
            }
            
            with open(cache_file, 'w') as f:
                # Convert PatternInfo objects to dicts for JSON serialization
                serializable_data = {
                    'system': system,
                    'learned_patterns': {},
                    'stats': patterns_data['stats']
                }
                
                for content_type, patterns in patterns_data['learned_patterns'].items():
                    serializable_data['learned_patterns'][content_type] = [
                        {
                            'pattern': p.pattern,
                            'confidence': p.confidence,
                            'frequency': p.frequency,
                            'examples': p.examples,
                            'context_words': p.context_words
                        } for p in patterns
                    ]
                
                json.dump(serializable_data, f, indent=2)
            
            logger.info(f"Saved system patterns for {system}")
        except Exception as e:
            logger.error(f"Failed to save system patterns: {e}")
    
    def _load_system_patterns(self, system: str, cache_file: Path):
        """Load system-specific patterns"""
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to PatternInfo objects
            for content_type, pattern_dicts in data['learned_patterns'].items():
                if content_type not in self.pattern_learner.learned_patterns:
                    self.pattern_learner.learned_patterns[content_type] = []
                
                for pattern_dict in pattern_dicts:
                    pattern_info = PatternInfo(
                        pattern=pattern_dict['pattern'],
                        confidence=pattern_dict['confidence'],
                        frequency=pattern_dict['frequency'],
                        examples=pattern_dict['examples'],
                        context_words=pattern_dict['context_words']
                    )
                    self.pattern_learner.learned_patterns[content_type].append(pattern_info)
            
            logger.info(f"Loaded system patterns for {system}")
        except Exception as e:
            logger.error(f"Failed to load system patterns: {e}")
    
    def get_system_statistics(self, system: str) -> Dict[str, Any]:
        """Get statistics about patterns learned for a specific system"""
        return {
            'system': system,
            'pattern_stats': self.pattern_learner.get_pattern_stats(),
            'total_content_types': len(self.pattern_learner.learned_patterns),
            'most_common_patterns': self._get_most_common_patterns()
        }
    
    def _get_most_common_patterns(self) -> Dict[str, List[str]]:
        """Get the most commonly used patterns by content type"""
        common_patterns = {}
        
        for content_type, patterns in self.pattern_learner.learned_patterns.items():
            # Sort by frequency and confidence
            sorted_patterns = sorted(patterns, 
                                   key=lambda p: (p.frequency * p.confidence), 
                                   reverse=True)
            
            common_patterns[content_type] = [
                p.pattern for p in sorted_patterns[:5]  # Top 5 patterns
            ]
        
        return common_patterns
    
    def retrain_on_feedback(self, content: str, correct_type: str):
        """Retrain patterns based on user feedback"""
        logger.info(f"Retraining with feedback: content classified as {correct_type}")
        
        # Add this as a training example
        self.pattern_learner.analyze_new_document(content, correct_type)
        
        # Save updated patterns
        self.pattern_learner.save_patterns()


# Helper class to integrate dynamic patterns with your existing system
class PatternBasedContentClassifier:
    """Helper class to integrate dynamic patterns with existing system"""
    
    def __init__(self, adaptive_processor: AdaptivePDFProcessor):
        self.processor = adaptive_processor
        self.pattern_learner = adaptive_processor.pattern_learner
    
    def get_content_patterns(self) -> Dict[str, List[str]]:
        """Get all learned patterns in the format your existing code expects"""
        content_patterns = {}
        
        # Get all content types
        all_types = set(list(self.pattern_learner.seed_patterns.keys()) + 
                       list(self.pattern_learner.learned_patterns.keys()))
        
        for content_type in all_types:
            patterns = self.pattern_learner.get_patterns_for_type(content_type)
            if patterns:
                content_patterns[content_type] = patterns
        
        return content_patterns
    
    def classify_content_with_confidence(self, content: str) -> Tuple[str, float]:
        """Classify content and return confidence score"""
        content_type = self.pattern_learner._classify_document(content)
        
        # Calculate confidence based on pattern matches
        patterns = self.pattern_learner.get_patterns_for_type(content_type)
        total_matches = 0
        
        for pattern in patterns:
            try:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                total_matches += matches
            except re.error:
                continue
        
        # Normalize confidence (this is a simple heuristic)
        confidence = min(total_matches / 10.0, 1.0)
        
        return content_type, confidence
    
    def suggest_new_patterns(self, content_type: str, sample_texts: List[str]) -> List[str]:
        """Suggest new patterns for a content type based on sample texts"""
        # Temporarily learn from samples
        temp_learner = DynamicPatternLearner()
        temp_learner._learn_patterns_for_type(content_type, sample_texts)
        
        if content_type in temp_learner.learned_patterns:
            return [p.pattern for p in temp_learner.learned_patterns[content_type] 
                   if p.confidence > 0.7]
        
        return []