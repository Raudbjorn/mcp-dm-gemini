from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from ttrpg_assistant.logger import logger

class EmbeddingService:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        logger.info(f"Initializing EmbeddingService with model '{model_name}'")
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        logger.info(f"Generating embedding for text of length {len(text)}")
        return self.model.encode(text).tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"Generating embeddings for {len(texts)} texts.")
        return self.model.encode(texts).tolist()