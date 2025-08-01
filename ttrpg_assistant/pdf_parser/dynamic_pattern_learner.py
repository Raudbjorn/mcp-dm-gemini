import re
import json
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import pickle
from pathlib import Path
import numpy as np

from ttrpg_assistant.logger import logger

# Try to import optional dependencies for advanced pattern learning
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Advanced NLP pattern learning will be disabled.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Clustering-based pattern learning will be disabled.")


@dataclass
class PatternInfo:
    pattern: str
    confidence: float
    frequency: int
    examples: List[str]
    context_words: List[str]


class DynamicPatternLearner:
    """Learns content patterns dynamically from processed documents"""
    
    def __init__(self, cache_file: Optional[str] = "learned_patterns.pkl"):
        self.cache_file = cache_file
        self.learned_patterns = {}
        self.pattern_stats = defaultdict(lambda: defaultdict(int))
        
        # Load spaCy for NLP analysis if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except IOError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
        
        # Base patterns to start with (existing ones as seeds)
        self.seed_patterns = {
            'stat_block': [
                r'(?:STR|Strength)\s*:?\s*\d+',
                r'AC\s*:?\s*\d+',
                r'HP\s*:?\s*\d+',
                r'Hit Points\s*:?\s*\d+',
                r'(?:STR|DEX|CON|INT|WIS|CHA)\s+\d+\s*\([+\-]?\d+\)'
            ],
            'spell': [
                r'(?:1st|2nd|3rd|[4-9]th)\s*-?\s*level',
                r'Casting Time\s*:',
                r'Components\s*:?\s*[VSM]',
                r'Duration\s*:',
                r'Range\s*:'
            ],
            'dice_mechanics': [
                r'\d+d\d+(?:\s*[+\-]\s*\d+)?',
                r'DC\s*\d+',
                r'Difficulty Class\s*\d+'
            ],
            'table': [
                r'\|\s*\w+\s*\|',
                r'^\s*\d+\s+\w+\s+\d+',
                r'Table\s*\d*\s*[-:]'
            ],
            'general': []
        }
        
        # Load existing patterns if available
        self.load_patterns()
        
        # Pattern discovery parameters
        self.min_frequency = 3
        self.min_confidence = 0.6
    
    def analyze_documents(self, documents: List[str], labels: Optional[List[str]] = None):
        """Analyze a collection of documents to learn patterns"""
        logger.info(f"Analyzing {len(documents)} documents for pattern learning")
        
        # If no labels provided, try to auto-classify first
        if not labels:
            labels = self._auto_classify_documents(documents)
        
        # Learn patterns for each content type
        content_groups = defaultdict(list)
        for doc, label in zip(documents, labels):
            if label:
                content_groups[label].append(doc)
        
        for content_type, docs in content_groups.items():
            if len(docs) >= self.min_frequency:  # Only learn if we have enough examples
                self._learn_patterns_for_type(content_type, docs)
        
        # Save learned patterns
        self.save_patterns()
        
        logger.info(f"Learned patterns for {len(content_groups)} content types")
    
    def _auto_classify_documents(self, documents: List[str]) -> List[str]:
        """Automatically classify documents using existing seed patterns"""
        labels = []
        
        for doc in documents:
            best_type = None
            best_score = 0
            
            # Test against seed patterns
            for content_type, patterns in self.seed_patterns.items():
                score = 0
                for pattern in patterns:
                    try:
                        matches = len(re.findall(pattern, doc, re.IGNORECASE))
                        score += matches
                    except re.error:
                        continue
                
                if score > best_score:
                    best_score = score
                    best_type = content_type
            
            # Use heuristics if no pattern matches
            if not best_type or best_score == 0:
                best_type = self._classify_with_heuristics(doc)
            
            labels.append(best_type)
        
        return labels
    
    def _classify_with_heuristics(self, doc: str) -> str:
        """Classify document using heuristic rules"""
        doc_lower = doc.lower()
        
        # Stat block indicators
        if any(stat in doc_lower for stat in ['str ', 'dex ', 'con ', 'int ', 'wis ', 'cha ']):
            if any(indicator in doc_lower for indicator in ['ac ', 'hp ', 'hit points']):
                return 'stat_block'
        
        # Spell indicators
        if any(indicator in doc_lower for indicator in ['spell', 'cantrip', 'level spell', 'casting time']):
            return 'spell'
        
        # Table indicators
        if '|' in doc or re.search(r'\d+\s+\w+\s+\d+', doc):
            return 'table'
        
        # Dice mechanics
        if re.search(r'\d+d\d+', doc):
            return 'dice_mechanics'
        
        # Default to general
        return 'general'
    
    def _learn_patterns_for_type(self, content_type: str, documents: List[str]):
        """Learn patterns for a specific content type"""
        logger.debug(f"Learning patterns for content type: {content_type}")
        
        # Extract common structures
        structural_patterns = self._extract_structural_patterns(documents)
        
        # Extract keyword patterns
        keyword_patterns = self._extract_keyword_patterns(documents)
        
        # Extract format patterns
        format_patterns = self._extract_format_patterns(documents)
        
        # Combine and validate patterns
        all_patterns = structural_patterns + keyword_patterns + format_patterns
        validated_patterns = self._validate_patterns(all_patterns, documents)
        
        # Store learned patterns
        if content_type not in self.learned_patterns:
            self.learned_patterns[content_type] = []
        
        for pattern_info in validated_patterns:
            # Avoid duplicates
            if not any(p.pattern == pattern_info.pattern for p in self.learned_patterns[content_type]):
                self.learned_patterns[content_type].append(pattern_info)
        
        logger.debug(f"Learned {len(validated_patterns)} new patterns for {content_type}")
    
    def _extract_structural_patterns(self, documents: List[str]) -> List[PatternInfo]:
        """Extract patterns based on document structure"""
        patterns = []
        
        # Common line patterns
        line_patterns = defaultdict(int)
        for doc in documents:
            lines = doc.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # Generalize the line structure
                    generalized = self._generalize_line(line)
                    if generalized:
                        line_patterns[generalized] += 1
        
        # Convert frequent patterns to regex
        for pattern, freq in line_patterns.items():
            if freq >= self.min_frequency:
                try:
                    # Test if it's a valid regex
                    re.compile(pattern)
                    patterns.append(PatternInfo(
                        pattern=pattern,
                        confidence=min(freq / len(documents), 1.0),
                        frequency=freq,
                        examples=[],
                        context_words=[]
                    ))
                except re.error:
                    continue
        
        return patterns
    
    def _generalize_line(self, line: str) -> Optional[str]:
        """Convert a specific line into a generalized pattern"""
        if len(line) < 5:  # Skip very short lines
            return None
        
        # Replace numbers with \d+
        pattern = re.sub(r'\d+', r'\\d+', line)
        
        # Replace common words that might vary
        pattern = re.sub(r'\b[A-Z][a-zA-Z]*\b', r'[A-Za-z]+', pattern)
        
        # Escape special regex characters
        pattern = re.escape(pattern)
        
        # Un-escape the patterns we want to keep
        pattern = pattern.replace('\\\\d\\+', r'\\d+')
        pattern = pattern.replace('\\[A-Za-z\\]\\+', r'[A-Za-z]+')
        
        # Only return if it's not too generic or too specific
        if pattern.count(r'\\d+') > 0 or pattern.count('[A-Za-z]+') > 0:
            return pattern
        
        return None
    
    def _extract_keyword_patterns(self, documents: List[str]) -> List[PatternInfo]:
        """Extract patterns based on common keywords and phrases"""
        patterns = []
        
        # Find common phrases using n-grams
        all_text = ' '.join(documents).lower()
        
        # Extract 2-grams and 3-grams
        for n in [2, 3]:
            ngrams = self._extract_ngrams(all_text, n)
            common_ngrams = {ngram: count for ngram, count in ngrams.items() 
                           if count >= self.min_frequency}
            
            for ngram, freq in common_ngrams.items():
                # Convert to regex pattern
                words = ngram.split()
                if len(words) == n and all(len(w) > 2 for w in words):
                    # Create flexible pattern
                    pattern_parts = []
                    for word in words:
                        if word.isdigit():
                            pattern_parts.append(r'\d+')
                        else:
                            pattern_parts.append(re.escape(word))
                    
                    pattern = r'\b' + r'\s+'.join(pattern_parts) + r'\b'
                    
                    patterns.append(PatternInfo(
                        pattern=pattern,
                        confidence=min(freq / len(documents), 1.0),
                        frequency=freq,
                        examples=[ngram],
                        context_words=words
                    ))
        
        return patterns
    
    def _extract_ngrams(self, text: str, n: int) -> Counter:
        """Extract n-grams from text"""
        words = re.findall(r'\b\w+\b', text)
        ngrams = []
        
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)
        
        return Counter(ngrams)
    
    def _extract_format_patterns(self, documents: List[str]) -> List[PatternInfo]:
        """Extract patterns based on formatting (colons, brackets, etc.)"""
        patterns = []
        
        # Common format patterns
        format_indicators = [
            r'\w+\s*:\s*\d+',           # "HP: 25"
            r'\w+\s*:\s*\w+',           # "Type: Dragon"
            r'\(\w+\)',                 # "(fire)"
            r'\[\w+\]',                 # "[range]" 
            r'\w+\s*\(\d+\)',          # "Strength (18)"
            r'\d+\s*\(\+?\-?\d+\)',    # "18 (+4)"
            r'\w+\s*\+\d+',            # "Attack +5"
            r'\d+\s*ft\.?',            # "30 ft"
            r'\d+\s*gp',               # "100 gp"
        ]
        
        for pattern in format_indicators:
            total_matches = 0
            examples = []
            
            for doc in documents:
                try:
                    matches = re.findall(pattern, doc, re.IGNORECASE)
                    total_matches += len(matches)
                    examples.extend(matches[:2])  # Keep some examples
                except re.error:
                    continue
            
            if total_matches >= self.min_frequency:
                patterns.append(PatternInfo(
                    pattern=pattern,
                    confidence=min(total_matches / (len(documents) * 10), 1.0),
                    frequency=total_matches,
                    examples=examples[:5],
                    context_words=[]
                ))
        
        return patterns
    
    def _validate_patterns(self, patterns: List[PatternInfo], documents: List[str]) -> List[PatternInfo]:
        """Validate patterns and filter out low-quality ones"""
        validated = []
        
        for pattern_info in patterns:
            # Test pattern validity
            try:
                compiled_pattern = re.compile(pattern_info.pattern, re.IGNORECASE)
            except re.error:
                continue
            
            # Test against documents
            match_count = 0
            total_chars = 0
            
            for doc in documents:
                matches = compiled_pattern.findall(doc)
                match_count += len(matches)
                total_chars += len(doc)
            
            # Calculate metrics
            if match_count >= self.min_frequency:
                # Avoid overly broad patterns
                average_doc_length = total_chars / len(documents) if documents else 1
                if match_count / len(documents) < average_doc_length / 100:  # Not too frequent
                    pattern_info.confidence = min(match_count / len(documents), 1.0)
                    validated.append(pattern_info)
        
        # Sort by confidence
        validated.sort(key=lambda x: x.confidence, reverse=True)
        
        return validated
    
    def get_patterns_for_type(self, content_type: str) -> List[str]:
        """Get all patterns for a content type (learned + seed)"""
        patterns = []
        
        # Add seed patterns
        if content_type in self.seed_patterns:
            patterns.extend(self.seed_patterns[content_type])
        
        # Add learned patterns
        if content_type in self.learned_patterns:
            learned = [p.pattern for p in self.learned_patterns[content_type] 
                      if p.confidence >= self.min_confidence]
            patterns.extend(learned)
        
        return patterns
    
    def save_patterns(self):
        """Save learned patterns to cache file"""
        if self.cache_file:
            try:
                cache_data = {
                    'learned_patterns': {
                        content_type: [asdict(pattern) for pattern in patterns]
                        for content_type, patterns in self.learned_patterns.items()
                    },
                    'pattern_stats': dict(self.pattern_stats)
                }
                
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(cache_data, f)
                
                logger.info(f"Saved learned patterns to {self.cache_file}")
            except Exception as e:
                logger.error(f"Failed to save patterns: {e}")
    
    def load_patterns(self):
        """Load learned patterns from cache file"""
        if self.cache_file and Path(self.cache_file).exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Reconstruct PatternInfo objects
                for content_type, pattern_dicts in cache_data['learned_patterns'].items():
                    self.learned_patterns[content_type] = [
                        PatternInfo(**pattern_dict) for pattern_dict in pattern_dicts
                    ]
                
                self.pattern_stats = defaultdict(lambda: defaultdict(int), cache_data['pattern_stats'])
                
                logger.info(f"Loaded learned patterns from {self.cache_file}")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def analyze_new_document(self, content: str, known_type: Optional[str] = None) -> str:
        """Analyze a single new document and optionally learn from it"""
        if known_type:
            # Learn patterns from this labeled example
            self._learn_patterns_for_type(known_type, [content])
            return known_type
        else:
            # Classify using current patterns
            return self._classify_document(content)
    
    def _classify_document(self, content: str) -> str:
        """Classify a document using all available patterns"""
        scores = defaultdict(float)
        
        # Test against all pattern types
        for content_type in set(list(self.seed_patterns.keys()) + list(self.learned_patterns.keys())):
            patterns = self.get_patterns_for_type(content_type)
            
            for pattern in patterns:
                try:
                    matches = len(re.findall(pattern, content, re.IGNORECASE))
                    scores[content_type] += matches
                except re.error:
                    continue
        
        # Return best match or default
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general'
    
    def get_pattern_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about learned patterns"""
        stats = {}
        
        for content_type, patterns in self.learned_patterns.items():
            stats[content_type] = {
                'total_patterns': len(patterns),
                'high_confidence': len([p for p in patterns if p.confidence > 0.8]),
                'medium_confidence': len([p for p in patterns if 0.6 <= p.confidence <= 0.8]),
                'total_frequency': sum(p.frequency for p in patterns)
            }
        
        return stats