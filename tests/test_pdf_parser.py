import unittest
import os
from ttrpg_assistant.pdf_parser.parser import PDFParser

class TestPDFParser(unittest.TestCase):

    def setUp(self):
        self.parser = PDFParser()
        self.test_pdf_path = "data/sample.pdf"

    def test_extract_text(self):
        data = self.parser.extract_text(self.test_pdf_path)
        self.assertIn("text", data)
        self.assertIsInstance(data["text"], str)
        self.assertGreater(len(data["text"]), 0)

    def test_extract_personality_text(self):
        text = self.parser.extract_personality_text(self.test_pdf_path)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    def test_get_toc(self):
        toc = self.parser.get_toc(self.test_pdf_path)
        self.assertIsInstance(toc, list)


if __name__ == '__main__':
    unittest.main()