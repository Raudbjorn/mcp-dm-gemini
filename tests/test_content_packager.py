import unittest
from unittest.mock import MagicMock, patch
from ttrpg_assistant.content_packager.packager import ContentPackager
from ttrpg_assistant.data_models.models import ContentChunk, SourceType

class TestContentPackager(unittest.TestCase):

    def setUp(self):
        self.packager = ContentPackager()
        self.dummy_chunks = [
            ContentChunk(
                id="1",
                rulebook="Test Rulebook",
                system="Test System",
                source_type=SourceType.RULEBOOK,
                content_type="rule",
                title="Test Rule",
                content="This is a test rule.",
                page_number=1,
                section_path=["Chapter 1"],
                embedding=b"",
                metadata={}
            )
        ]
        self.dummy_personality = "This is a test personality."
        self.test_pack_path = "data/test_pack.zip"

    def test_create_and_load_content_pack(self):
        # Create the content pack
        self.packager.create_pack(
            chunks=self.dummy_chunks,
            personality=self.dummy_personality,
            output_path=self.test_pack_path
        )

        # Load the content pack
        loaded_chunks, loaded_personality = self.packager.load_pack(self.test_pack_path)

        # Assert that the loaded data is correct
        self.assertEqual(len(loaded_chunks), 1)
        self.assertEqual(loaded_chunks[0].id, "1")
        self.assertEqual(loaded_personality, self.dummy_personality)

if __name__ == '__main__':
    unittest.main()