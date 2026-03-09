# PDF Extractor Service
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        Returns cleaned text content.
        """
        text_parts = []

        doc = fitz.open(file_path)
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
        doc.close()

        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            raise ValueError("No text could be extracted from PDF")

        logger.info(f"Extracted {len(full_text)} characters from {file_path}")
        return full_text