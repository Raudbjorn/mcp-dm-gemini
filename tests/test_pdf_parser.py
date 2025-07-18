import unittest
import os
from unittest.mock import MagicMock
from ttrpg_assistant.pdf_parser.parser import PDFParser

class TestPDFParser(unittest.TestCase):

    def setUp(self):
        self.parser = PDFParser()
        self.test_pdf_path = "data/sample.pdf"
        self.table_pdf_path = "data/sample_with_table.pdf"
        self.toc_pdf_path = "data/sample_with_toc.pdf"

    @unittest.skipIf(not os.path.exists("data/sample.pdf"), "Sample PDF not found")
    def test_extract_text(self):
        data = self.parser.extract_text(self.test_pdf_path)
        self.assertIn("text", data)
        self.assertIsInstance(data["text"], str)
        self.assertGreater(len(data["text"]), 0)

    @unittest.skipIf(not os.path.exists("data/sample.pdf"), "Sample PDF not found")
    def test_extract_personality_text(self):
        text = self.parser.extract_personality_text(self.test_pdf_path)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    @unittest.skipIf(not os.path.exists("data/sample_with_table.pdf"), "Sample PDF with table not found")
    def test_extract_tables(self):
        tables = self.parser.extract_tables(self.table_pdf_path)
        self.assertIsInstance(tables, list)

    @unittest.skipIf(not os.path.exists("data/sample_with_toc.pdf"), "Sample PDF with ToC not found")
    def test_get_toc(self):
        toc = self.parser.get_toc(self.toc_pdf_path)
        self.assertIsInstance(toc, list)

    def test_identify_sections(self):
        # This is a simplified mock of the pypdf outline.
        # A better test would use a real PDF with a known ToC.
        mock_item_1_1 = MagicMock()
        mock_item_1_1.title = "Section 1.1"
        mock_item_1_1.page_number = 2
        mock_item_1_1.children = []

        mock_item_1_2 = MagicMock()
        mock_item_1_2.title = "Section 1.2"
        mock_item_1_2.page_number = 3
        mock_item_1_2.children = []

        mock_item_1 = MagicMock()
        mock_item_1.title = "Chapter 1"
        mock_item_1.page_number = 1
        mock_item_1.children = [mock_item_1_1, mock_item_1_2]

        mock_item_2 = MagicMock()
        mock_item_2.title = "Chapter 2"
        mock_item_2.page_number = 4
        mock_item_2.children = []
        
        mock_toc = [mock_item_1, mock_item_2]

        sections = self.parser.identify_sections(mock_toc)

        self.assertEqual(len(sections), 4)
        self.assertEqual(sections[0]['title'], 'Chapter 1')
        self.assertEqual(sections[0]['path'], ['Chapter 1'])
        self.assertEqual(sections[1]['title'], 'Section 1.1')
        self.assertEqual(sections[1]['path'], ['Chapter 1', 'Section 1.1'])
        self.assertEqual(sections[2]['title'], 'Section 1.2')
        self.assertEqual(sections[2]['path'], ['Chapter 1', 'Section 1.2'])
        self.assertEqual(sections[3]['title'], 'Chapter 2')
        self.assertEqual(sections[3]['path'], ['Chapter 2'])


    @unittest.skipIf(not os.path.exists("data/sample_with_toc.pdf"), "Sample PDF with ToC not found")
    def test_create_chunks(self):
        chunks = self.parser.create_chunks(self.toc_pdf_path)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        self.assertIn("id", chunks[0])
        self.assertIn("text", chunks[0])
        self.assertIn("page_number", chunks[0])
        self.assertIn("section", chunks[0])

if __name__ == '__main__':
    unittest.main()
