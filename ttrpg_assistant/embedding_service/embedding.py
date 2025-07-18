from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Manages text-to-vector conversion and similarity search"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Convert text to vector embedding"""
        return self.model.encode(text).tolist()

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Efficiently process multiple texts"""
        return self.model.encode(texts).tolist()
