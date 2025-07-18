from ttrpg_assistant.redis_manager.manager import RedisDataManager
from ttrpg_assistant.embedding_service.embedding import EmbeddingService
from ttrpg_assistant.pdf_parser.parser import PDFParser
from functools import lru_cache

@lru_cache(maxsize=None)
def get_redis_manager():
    return RedisDataManager()

@lru_cache(maxsize=None)
def get_embedding_service():
    return EmbeddingService()

@lru_cache(maxsize=None)
def get_pdf_parser():
    return PDFParser()
