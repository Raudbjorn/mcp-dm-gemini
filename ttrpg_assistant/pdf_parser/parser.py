from typing import Dict, Any, List, Optional
from pypdf import PdfReader
import uuid

from ttrpg_assistant.data_models.models import ContentChunk, SourceType
from ttrpg_assistant.logger import logger
from .adaptive_processor import AdaptivePDFProcessor, PatternBasedContentClassifier


class PDFParser:
    """Enhanced PDF parser with adaptive pattern learning and intelligent content classification"""

    def __init__(self, enable_adaptive_learning: bool = True, pattern_cache_dir: str = "./pattern_cache"):
        """Initialize PDF parser with optional adaptive learning capabilities"""
        self.enable_adaptive_learning = enable_adaptive_learning
        
        if self.enable_adaptive_learning:
            self.adaptive_processor = AdaptivePDFProcessor(pattern_cache_dir)
            self.classifier = PatternBasedContentClassifier(self.adaptive_processor)
            logger.info("PDF parser initialized with adaptive learning enabled")
        else:
            self.adaptive_processor = None
            self.classifier = None
            logger.info("PDF parser initialized in basic mode")

    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text while preserving structure"""
        reader = PdfReader(pdf_path)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
        
        return {"text": text_content}

    def extract_personality_text(self, pdf_path: str, num_pages: int = 5) -> str:
        """Extracts text from the first few pages to determine personality."""
        reader = PdfReader(pdf_path)
        personality_text = ""
        for i, page in enumerate(reader.pages):
            if i >= num_pages:
                break
            personality_text += page.extract_text() + "\n"
        return personality_text

    def get_toc(self, pdf_path: str) -> List[Any]:
        """Extract table of contents"""
        reader = PdfReader(pdf_path)
        return reader.outline

    def _identify_sections_recursive(self, toc: List[Any], parent_path: List[str]) -> List[Dict[str, Any]]:
        sections = []
        for item in toc:
            if isinstance(item, list):
                sections.extend(self._identify_sections_recursive(item, parent_path))
            else:
                current_path = parent_path + [item.title]
                sections.append({
                    "title": item.title,
                    "page_number": item.page_number,
                    "path": current_path
                })
                if hasattr(item, 'children'):
                    sections.extend(self._identify_sections_recursive(item.children, current_path))
        return sections

    def identify_sections(self, toc: List[Any]) -> List[Dict[str, Any]]:
        """Use table of contents to identify logical sections"""
        return self._identify_sections_recursive(toc, [])

    def create_chunks(self, pdf_path: str, rulebook_name: Optional[str] = None, 
                     system: Optional[str] = None, source_type: str = "rulebook",
                     chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create searchable chunks with metadata - enhanced with adaptive learning if enabled"""
        
        # If adaptive learning is enabled and we have the required parameters, use it
        if (self.enable_adaptive_learning and self.adaptive_processor and 
            rulebook_name and system):
            
            try:
                # Use adaptive processing to get ContentChunk objects
                content_chunks = self.adaptive_processor.process_pdf_with_learning(
                    pdf_path, rulebook_name, system, source_type
                )
                
                # Convert ContentChunk objects to dictionaries for backward compatibility
                chunks = []
                for chunk in content_chunks:
                    chunks.append({
                        "id": chunk.id,
                        "text": chunk.content,
                        "page_number": chunk.page_number,
                        "section": {
                            "title": chunk.title,
                            "path": chunk.section_path
                        },
                        # Enhanced metadata from adaptive processing
                        "content_type": chunk.content_type,
                        "metadata": chunk.metadata,
                        "system": chunk.system,
                        "rulebook": chunk.rulebook,
                        "source_type": chunk.source_type
                    })
                
                logger.info(f"Created {len(chunks)} adaptive chunks for {rulebook_name}")
                return chunks
                
            except Exception as e:
                logger.error(f"Adaptive processing failed, falling back to basic chunking: {e}")
                # Fall through to basic processing
        
        # Basic chunking (original implementation + enhancements)
        return self._create_basic_chunks(pdf_path, chunk_size, overlap, 
                                       rulebook_name, system, source_type)
    
    def _create_basic_chunks(self, pdf_path: str, chunk_size: int, overlap: int,
                           rulebook_name: Optional[str] = None, 
                           system: Optional[str] = None,
                           source_type: str = "rulebook") -> List[Dict[str, Any]]:
        """Create basic chunks using the original algorithm with some enhancements"""
        reader = PdfReader(pdf_path)
        chunks = []
        
        toc = self.get_toc(pdf_path)
        sections = self.identify_sections(toc)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue

            current_section = None
            for section in sections:
                if section["page_number"] == i:
                    current_section = section
            
            # Enhanced chunking with content classification if available
            if self.classifier:
                # Try to classify the page content
                try:
                    content_type, confidence = self.classifier.classify_content_with_confidence(text)
                except Exception as e:
                    logger.debug(f"Content classification failed: {e}")
                    content_type, confidence = "general", 0.5
            else:
                content_type, confidence = "general", 0.5
            
            for j in range(0, len(text), chunk_size - overlap):
                chunk_text = text[j:j + chunk_size]
                
                chunk_data = {
                    "id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "page_number": i + 1,
                    "section": current_section,
                    "content_type": content_type,
                    "confidence": confidence
                }
                
                # Add enhanced metadata if available
                if rulebook_name:
                    chunk_data["rulebook"] = rulebook_name
                if system:
                    chunk_data["system"] = system
                chunk_data["source_type"] = source_type
                
                chunks.append(chunk_data)

        logger.info(f"Created {len(chunks)} basic chunks")
        return chunks
    
    def get_adaptive_statistics(self, system: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about learned patterns"""
        if not self.adaptive_processor:
            return {"error": "Adaptive learning not enabled"}
        
        if system:
            return self.adaptive_processor.get_system_statistics(system)
        else:
            return {
                "pattern_stats": self.adaptive_processor.pattern_learner.get_pattern_stats(),
                "total_systems": len(self.adaptive_processor.system_patterns),
                "pattern_cache_dir": str(self.adaptive_processor.pattern_cache_dir)
            }
    
    def retrain_with_feedback(self, content: str, correct_type: str):
        """Allow retraining patterns based on user feedback"""
        if self.adaptive_processor:
            self.adaptive_processor.retrain_on_feedback(content, correct_type)
        else:
            logger.warning("Adaptive learning not enabled, cannot retrain patterns")
    
    def get_content_patterns(self) -> Dict[str, List[str]]:
        """Get all learned content patterns"""
        if self.classifier:
            return self.classifier.get_content_patterns()
        else:
            return {}
    
    def classify_content(self, content: str) -> tuple[str, float]:
        """Classify content using learned patterns"""
        if self.classifier:
            return self.classifier.classify_content_with_confidence(content)
        else:
            return "general", 0.5
