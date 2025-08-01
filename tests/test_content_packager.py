import unittest
import os
import zipfile
import json
from ttrpg_assistant.content_packager.packager import ContentPackager
from ttrpg_assistant.data_models.models import ContentChunk, SourceType

class TestContentPackager(unittest.TestCase):

    def setUp(self):
        self.packager = ContentPackager()
        self.test_pack_path = "data/test_pack.zip"
        self.dummy_chunks = [
            ContentChunk(
                id="1",
                rulebook="Test Book",
                system="Test System",
                source_type=SourceType.RULEBOOK,
                content_type="rule",
                title="Test Rule",
                content="This is a test rule.",
                page_number=1,
                section_path=["Chapter 1"],
                embedding=b'\x00\x01\x02',
                metadata={}
            )
        ]
        self.dummy_personality = "This is a test personality."

    def tearDown(self):
        if os.path.exists(self.test_pack_path):
            os.remove(self.test_pack_path)

    def test_create_and_load_content_pack(self):
        # Create the content pack
        self.packager.create_pack(
            chunks=self.dummy_chunks,
            personality=self.dummy_personality,
            output_path=self.test_pack_path
        )

        # Check that the file was created
        self.assertTrue(os.path.exists(self.test_pack_path))

        # Check that the file is a valid zip file with the correct contents
        with zipfile.ZipFile(self.test_pack_path, 'r') as zf:
            self.assertIn('chunks.json', zf.namelist())
            self.assertIn('personality.txt', zf.namelist())

        # Load the content pack
        loaded_chunks, loaded_personality = self.packager.load_pack(self.test_pack_path)

        # Check that the loaded data matches the original data
        self.assertEqual(len(loaded_chunks), 1)
        self.assertEqual(loaded_chunks[0].id, self.dummy_chunks[0].id)
        self.assertEqual(loaded_personality, self.dummy_personality)

if __name__ == '__main__':
    unittest.main()
