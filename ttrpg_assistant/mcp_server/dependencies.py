from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from ttrpg_assistant.personality_service.personality_manager import PersonalityManager
from ttrpg_assistant.config_utils import load_config_safe
from functools import lru_cache

@lru_cache(maxsize=None)
def get_chroma_manager():
    return ChromaDataManager()

@lru_cache(maxsize=None)
def get_embedding_service():
    return EmbeddingService()

@lru_cache(maxsize=None)
def get_pdf_parser():
    """Create PDF parser with configuration from config.yaml"""
    config = load_config_safe("config.yaml")
    pdf_config = config.get('pdf_processing', {})
    
    return PDFParser(
        enable_adaptive_learning=pdf_config.get('enable_adaptive_learning', True),
        pattern_cache_dir=pdf_config.get('pattern_cache_dir', './pattern_cache')
    )

@lru_cache(maxsize=None)
def get_personality_manager():
    """Create personality manager with ChromaDB data manager"""
    chroma_manager = get_chroma_manager()
    return PersonalityManager(chroma_manager)