from typing import List, Tuple
import zipfile
import json
from ttrpg_assistant.data_models.models import ContentChunk

class ContentPackager:
    def create_pack(self, chunks: List[ContentChunk], personality: str, output_path: str):
        with zipfile.ZipFile(output_path, 'w') as zf:
            # Serialize and write chunks
            chunks_data = [chunk.model_dump_json() for chunk in chunks]
            zf.writestr('chunks.json', json.dumps(chunks_data))

            # Write personality
            zf.writestr('personality.txt', personality)

    def load_pack(self, pack_path: str) -> Tuple[List[ContentChunk], str]:
        with zipfile.ZipFile(pack_path, 'r') as zf:
            # Load and deserialize chunks
            with zf.open('chunks.json') as chunks_file:
                chunks_data = json.load(chunks_file)
                chunks = [ContentChunk.model_validate_json(chunk_json) for chunk_json in chunks_data]

            # Load personality
            with zf.open('personality.txt') as personality_file:
                personality = personality_file.read().decode('utf-8')

            return chunks, personality