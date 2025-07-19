import json
from typing import List, Tuple
from ttrpg_assistant.data_models.models import ContentChunk
from ttrpg_assistant.logger import logger
import numpy as np

class ContentPackager:
    def create_pack(self, chunks: List[ContentChunk], personality: str, output_path: str):
        logger.info(f"Creating content pack at '{output_path}'")
        
        # Convert bytes to list for JSON serialization
        for chunk in chunks:
            if isinstance(chunk.embedding, bytes):
                chunk.embedding = np.frombuffer(chunk.embedding, dtype=np.float32).tolist()

        pack_data = {
            "chunks": [chunk.model_dump() for chunk in chunks],
            "personality": personality
        }
        with open(output_path, "w") as f:
            json.dump(pack_data, f)
        logger.info("Content pack created successfully.")

    def load_pack(self, pack_path: str) -> Tuple[List[ContentChunk], str]:
        logger.info(f"Loading content pack from '{pack_path}'")
        with open(pack_path, "r") as f:
            pack_data = json.load(f)
        
        chunks_data = pack_data["chunks"]
        for chunk_data in chunks_data:
            if 'embedding' in chunk_data and isinstance(chunk_data['embedding'], list):
                chunk_data['embedding'] = np.array(chunk_data['embedding'], dtype=np.float32).tobytes()

        chunks = [ContentChunk(**chunk_data) for chunk_data in chunks_data]
        personality = pack_data["personality"]
        logger.info("Content pack loaded successfully.")
        return chunks, personality