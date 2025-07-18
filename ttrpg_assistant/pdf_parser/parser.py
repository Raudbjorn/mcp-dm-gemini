from typing import Dict, Any, List
from pypdf import PdfReader
import uuid

class PDFParser:
    """Handles extraction and structuring of PDF content"""

    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text while preserving structure"""
        reader = PdfReader(pdf_path)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
        
        return {"text": text_content}

    def extract_personality_text(self, pdf_path: str, num_pages: int = 5) -> str:
        """Extracts text from the first few pages to determine personality."""
        reader = PdfReader(pdf_path)
        personality_text = ""
        for i, page in enumerate(reader.pages):
            if i >= num_pages:
                break
            personality_text += page.extract_text() + "\n"
        return personality_text

    def get_toc(self, pdf_path: str) -> List[Any]:
        """Extract table of contents"""
        reader = PdfReader(pdf_path)
        return reader.outline

    def _identify_sections_recursive(self, toc: List[Any], parent_path: List[str]) -> List[Dict[str, Any]]:
        sections = []
        for item in toc:
            if isinstance(item, list):
                sections.extend(self._identify_sections_recursive(item, parent_path))
            else:
                current_path = parent_path + [item.title]
                sections.append({
                    "title": item.title,
                    "page_number": item.page_number,
                    "path": current_path
                })
                if hasattr(item, 'children'):
                    sections.extend(self._identify_sections_recursive(item.children, current_path))
        return sections

    def identify_sections(self, toc: List[Any]) -> List[Dict[str, Any]]:
        """Use table of contents to identify logical sections"""
        return self._identify_sections_recursive(toc, [])

    def create_chunks(self, pdf_path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create searchable chunks with metadata"""
        reader = PdfReader(pdf_path)
        chunks = []
        
        toc = self.get_toc(pdf_path)
        sections = self.identify_sections(toc)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue

            current_section = None
            for section in sections:
                if section["page_number"] == i:
                    current_section = section
            
            for j in range(0, len(text), chunk_size - overlap):
                chunk_text = text[j:j + chunk_size]
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "page_number": i + 1,
                    "section": current_section
                })

        return chunks
