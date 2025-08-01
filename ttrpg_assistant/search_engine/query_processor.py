from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from difflib import SequenceMatcher
from collections import Counter, defaultdict
import json

from ttrpg_assistant.logger import logger


@dataclass
class QuerySuggestion:
    original_query: str
    suggested_query: str
    confidence: float
    suggestion_type: str  # 'spelling', 'synonym', 'completion', 'clarification'
    explanation: str


class QueryProcessor:
    """Enhanced query processing with spell checking, completion, and intent understanding"""
    
    def __init__(self, chroma_manager):
        self.chroma = chroma_manager
        
        # Build vocabulary from indexed content
        self.vocabulary = set()
        self.term_frequencies = defaultdict(int)
        self.common_phrases = {}
        
        # Common TTRPG abbreviations and expansions
        self.abbreviations = {
            'ac': 'armor class',
            'hp': 'hit points',
            'mp': 'magic points',
            'pc': 'player character',
            'npc': 'non-player character',
            'dm': 'dungeon master',
            'gm': 'game master',
            'cr': 'challenge rating',
            'xp': 'experience points',
            'str': 'strength',
            'dex': 'dexterity',
            'con': 'constitution',
            'int': 'intelligence',
            'wis': 'wisdom',
            'cha': 'charisma',
            'phb': 'players handbook',
            'dmg': 'dungeon masters guide',
            'mm': 'monster manual',
            'aoo': 'attack of opportunity'
        }
        
        # Common misspellings in TTRPG context
        self.common_misspellings = {
            'armour': 'armor',
            'defence': 'defense',
            'dexterity': 'dexterity',  # People often misspell this
            'rogue': 'rogue',  # vs 'rouge'
            'lightning': 'lightning',  # vs 'lightening'
            'lose': 'lose',  # vs 'loose'
            'magic': 'magic',  # vs 'magick'
        }
        
        # Query intent patterns
        self.intent_patterns = {
            'how_to': [
                r'how\s+(?:do|does|can)\s+(?:i|you|one)\s+(.+)',
                r'how\s+to\s+(.+)',
                r'what.*way.*to\s+(.+)'
            ],
            'definition': [
                r'what\s+(?:is|are)\s+(?:an?\s+)?(.+)',
                r'define\s+(.+)',
                r'(?:meaning|definition)\s+of\s+(.+)'
            ],
            'rules': [
                r'(.+)\s+rules?',
                r'rules?\s+for\s+(.+)',
                r'how\s+does\s+(.+)\s+work'
            ],
            'stats': [
                r'(.+)\s+stats?',
                r'statistics?\s+for\s+(.+)',
                r'(.+)\s+(?:ac|hp|damage|abilities)'
            ],
            'spell': [
                r'(.+)\s+spell',
                r'spell\s+(.+)',
                r'cast(?:ing)?\s+(.+)'
            ],
            'character': [
                r'character\s+(.+)',
                r'build\s+(.+)',
                r'creating?\s+(.+)\s+character'
            ]
        }
    
    def build_vocabulary_from_collections(self, collection_names: List[str]):
        """Build vocabulary from indexed collections for spell checking"""
        logger.info("Building vocabulary from collections...")
        
        for collection_name in collection_names:
            try:
                collection = self.chroma.client.get_collection(collection_name)
                results = collection.get()
                
                for doc in results['documents']:
                    if doc:
                        words = self._extract_terms(doc)
                        for word in words:
                            self.vocabulary.add(word.lower())
                            self.term_frequencies[word.lower()] += 1
                
                # Also get metadata terms
                for metadata in results['metadatas']:
                    if metadata and metadata.get('title'):
                        words = self._extract_terms(metadata['title'])
                        for word in words:
                            self.vocabulary.add(word.lower())
                            self.term_frequencies[word.lower()] += 1
            
            except Exception as e:
                logger.warning(f"Could not build vocabulary from collection '{collection_name}': {e}")
        
        logger.info(f"Built vocabulary with {len(self.vocabulary)} terms")
        self._build_common_phrases()
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text"""
        # Split on various delimiters and clean
        terms = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        # Filter out very common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been'}
        
        return [term for term in terms if term not in stop_words]
    
    def _build_common_phrases(self):
        """Build common phrases from term frequencies"""
        # For now, just identify high-frequency terms that could be phrases
        high_freq_terms = {term: freq for term, freq in self.term_frequencies.items() 
                          if freq > 5}
        
        # Look for compound terms
        for term in high_freq_terms:
            if '_' in term or '-' in term:
                self.common_phrases[term.replace('_', ' ').replace('-', ' ')] = term
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[QuerySuggestion]]:
        """Process query with spell checking, expansion, and suggestions"""
        suggestions = []
        processed_query = query.strip()
        
        # 1. Expand abbreviations
        expanded_query, expansion_suggestions = self._expand_abbreviations(processed_query)
        suggestions.extend(expansion_suggestions)
        processed_query = expanded_query
        
        # 2. Spell check
        corrected_query, spelling_suggestions = self._spell_check(processed_query)
        suggestions.extend(spelling_suggestions)
        processed_query = corrected_query
        
        # 3. Query completion/enhancement
        enhanced_query, completion_suggestions = self._enhance_query(processed_query, context)
        suggestions.extend(completion_suggestions)
        processed_query = enhanced_query
        
        # 4. Intent-based suggestions
        intent_suggestions = self._suggest_based_on_intent(processed_query)
        suggestions.extend(intent_suggestions)
        
        logger.debug(f"Processed query: '{query}' -> '{processed_query}' with {len(suggestions)} suggestions")
        
        return processed_query, suggestions
    
    def _expand_abbreviations(self, query: str) -> Tuple[str, List[QuerySuggestion]]:
        """Expand common TTRPG abbreviations"""
        suggestions = []
        expanded_query = query.lower()
        
        for abbrev, expansion in self.abbreviations.items():
            # Look for the abbreviation as a whole word
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, expanded_query):
                new_query = re.sub(pattern, expansion, expanded_query)
                if new_query != expanded_query:
                    suggestions.append(QuerySuggestion(
                        original_query=query,
                        suggested_query=new_query,
                        confidence=0.9,
                        suggestion_type='abbreviation',
                        explanation=f"Expanded '{abbrev}' to '{expansion}'"
                    ))
                    expanded_query = new_query
        
        return expanded_query, suggestions
    
    def _spell_check(self, query: str) -> Tuple[str, List[QuerySuggestion]]:
        """Check spelling and suggest corrections"""
        suggestions = []
        words = query.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.common_misspellings:
                # Direct correction
                corrected_word = word.replace(clean_word, self.common_misspellings[clean_word])
                corrected_words.append(corrected_word)
                
                suggestions.append(QuerySuggestion(
                    original_query=query,
                    suggested_query=' '.join(words[:len(corrected_words)-1] + [corrected_word] + words[len(corrected_words):]),
                    confidence=0.8,
                    suggestion_type='spelling',
                    explanation=f"Corrected '{clean_word}' to '{self.common_misspellings[clean_word]}'"
                ))
            
            elif clean_word not in self.vocabulary and len(clean_word) > 3:
                # Find closest match in vocabulary
                best_match = self._find_closest_match(clean_word)
                if best_match and self._similarity_score(clean_word, best_match) > 0.7:
                    corrected_word = word.replace(clean_word, best_match)
                    corrected_words.append(corrected_word)
                    
                    suggestions.append(QuerySuggestion(
                        original_query=query,
                        suggested_query=' '.join(words[:len(corrected_words)-1] + [corrected_word] + words[len(corrected_words):]),
                        confidence=self._similarity_score(clean_word, best_match),
                        suggestion_type='spelling',
                        explanation=f"Did you mean '{best_match}' instead of '{clean_word}'?"
                    ))
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        corrected_query = ' '.join(corrected_words)
        return corrected_query, suggestions
    
    def _find_closest_match(self, word: str) -> Optional[str]:
        """Find closest matching word in vocabulary"""
        if not self.vocabulary:
            return None
        
        best_match = None
        best_score = 0
        
        # First, try exact substring matches
        for vocab_word in self.vocabulary:
            if word in vocab_word or vocab_word in word:
                score = self._similarity_score(word, vocab_word)
                if score > best_score:
                    best_score = score
                    best_match = vocab_word
        
        # If no good substring match, try similarity
        if best_score < 0.6:
            for vocab_word in self.vocabulary:
                if abs(len(word) - len(vocab_word)) <= 2:  # Similar length
                    score = self._similarity_score(word, vocab_word)
                    if score > best_score:
                        best_score = score
                        best_match = vocab_word
        
        return best_match if best_score > 0.5 else None
    
    def _similarity_score(self, word1: str, word2: str) -> float:
        """Calculate similarity score between two words"""
        return SequenceMatcher(None, word1.lower(), word2.lower()).ratio()
    
    def _enhance_query(self, query: str, context: Optional[Dict[str, Any]]) -> Tuple[str, List[QuerySuggestion]]:
        """Enhance query based on context and common patterns"""
        suggestions = []
        enhanced_query = query
        
        # Add context if available
        if context:
            current_system = context.get('current_system')
            current_rulebook = context.get('current_rulebook')
            
            if current_system and current_system.lower() not in query.lower():
                enhanced_suggestion = f"{query} in {current_system}"
                suggestions.append(QuerySuggestion(
                    original_query=query,
                    suggested_query=enhanced_suggestion,
                    confidence=0.6,
                    suggestion_type='context',
                    explanation=f"Added current system context: {current_system}"
                ))
        
        # Suggest more specific queries for vague terms
        vague_terms = ['rules', 'how', 'mechanics', 'stats']
        for term in vague_terms:
            if term in query.lower() and len(query.split()) <= 3:
                suggestions.append(QuerySuggestion(
                    original_query=query,
                    suggested_query=f"{query} examples",
                    confidence=0.5,
                    suggestion_type='completion',
                    explanation="Consider adding 'examples' for more specific results"
                ))
                break
        
        return enhanced_query, suggestions
    
    def _suggest_based_on_intent(self, query: str) -> List[QuerySuggestion]:
        """Suggest alternative queries based on detected intent"""
        suggestions = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    topic = match.group(1).strip()
                    
                    # Suggest alternative phrasings
                    if intent == 'how_to':
                        suggestions.append(QuerySuggestion(
                            original_query=query,
                            suggested_query=f"{topic} rules",
                            confidence=0.6,
                            suggestion_type='intent',
                            explanation="Try searching for the rules directly"
                        ))
                        suggestions.append(QuerySuggestion(
                            original_query=query,
                            suggested_query=f"{topic} mechanics",
                            confidence=0.6,
                            suggestion_type='intent',
                            explanation="Search for game mechanics"
                        ))
                    
                    elif intent == 'definition':
                        suggestions.append(QuerySuggestion(
                            original_query=query,
                            suggested_query=f"{topic} explanation",
                            confidence=0.6,
                            suggestion_type='intent',
                            explanation="Search for detailed explanation"
                        ))
                    
                    break
        
        return suggestions
    
    def suggest_related_queries(self, original_query: str, search_results: List[Any]) -> List[QuerySuggestion]:
        """Suggest related queries based on search results"""
        suggestions = []
        
        if not search_results:
            # No results - suggest broader queries
            words = original_query.split()
            if len(words) > 1:
                for i in range(len(words)):
                    broader_query = ' '.join(words[:i] + words[i+1:])
                    suggestions.append(QuerySuggestion(
                        original_query=original_query,
                        suggested_query=broader_query,
                        confidence=0.5,
                        suggestion_type='broadening',
                        explanation="Try a broader search"
                    ))
        
        else:
            # Has results - suggest related topics from result metadata
            topics = set()
            for result in search_results[:5]:  # Look at top 5 results
                if hasattr(result, 'content_chunk'):
                    chunk = result.content_chunk
                    if chunk.title:
                        topics.update(self._extract_terms(chunk.title))
                    
                    # Extract topics from metadata
                    if hasattr(chunk, 'metadata') and chunk.metadata:
                        for key, value in chunk.metadata.items():
                            if isinstance(value, str):
                                topics.update(self._extract_terms(value))
            
            # Suggest queries with related topics
            query_words = set(self._extract_terms(original_query))
            related_topics = topics - query_words
            
            for topic in list(related_topics)[:3]:  # Top 3 related topics
                if len(topic) > 2:  # Skip very short terms
                    suggestions.append(QuerySuggestion(
                        original_query=original_query,
                        suggested_query=f"{original_query} {topic}",
                        confidence=0.4,
                        suggestion_type='related',
                        explanation=f"Also search for related topic: {topic}"
                    ))
        
        return suggestions